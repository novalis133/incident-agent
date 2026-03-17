"""
Investigator Master Agent

Orchestrates sub-agents in iterative refinement pattern.
"""

from datetime import datetime
from typing import Dict, List, Optional
import uuid

import structlog

try:
    from gradient_adk import trace_tool, trace_llm
except ImportError:
    def trace_tool(name):
        def decorator(fn):
            return fn
        return decorator
    def trace_llm(name):
        def decorator(fn):
            return fn
        return decorator

from incidentagent.agents.base import AgentRegistry
from incidentagent.llm.client import get_llm_client
from incidentagent.llm.prompts import SynthesisPrompt
from incidentagent.schemas.evidence import AgentEvidence
from incidentagent.schemas.investigation import InvestigationState
from incidentagent.schemas.root_cause import RootCauseHypothesis, RootCauseCategory, Synthesis

logger = structlog.get_logger()


class InvestigatorMaster:
    """
    Investigator Master - Orchestrates sub-agents.
    
    Implements iterative refinement pattern:
    1. Select next agent based on priority queue and context
    2. Call agent with accumulated context
    3. Update findings and confidence
    4. Synthesize hypotheses
    5. Repeat until confidence threshold or queue exhausted
    """
    
    def __init__(self):
        self.logger = logger.bind(agent="InvestigatorMaster")
    
    @trace_tool("investigator-orchestrate")
    async def investigate(self, state: InvestigationState) -> InvestigationState:
        """
        Run iterative investigation.
        
        Args:
            state: Current investigation state
        
        Returns:
            Updated state with evidence and hypotheses
        """
        self.logger.info(
            "investigation_loop_started",
            investigation_id=state.investigation_id,
            priority_queue=state.agents_remaining,
        )
        
        # Iterative refinement loop
        while state.should_continue and state.agents_remaining:
            # Check timeout
            if datetime.utcnow() >= state.timeout_at:
                state.should_continue = False
                state.stop_reason = "timeout"
                break
            
            # Step 1: Select next agent
            next_agent_name = await self._select_next_agent(state)
            state.current_agent = next_agent_name
            state.current_step += 1
            
            self.logger.info(
                "calling_agent",
                step=state.current_step,
                agent=next_agent_name,
            )
            
            # Step 2: Build context for agent
            context = self._build_context(state)
            
            # Step 3: Call agent
            try:
                agent = AgentRegistry.get(next_agent_name)
                evidence = await agent.investigate(context)
            except ValueError:
                # Agent not registered, skip
                self.logger.warning("agent_not_found", agent=next_agent_name)
                state.agents_remaining.remove(next_agent_name)
                continue
            except Exception as e:
                self.logger.exception("agent_failed", agent=next_agent_name, error=str(e))
                state.errors.append(f"{next_agent_name}: {str(e)}")
                state.agents_remaining.remove(next_agent_name)
                continue
            
            # Step 4: Update state
            state.all_evidence.append(evidence)
            state.agents_called.append(next_agent_name)
            state.agents_remaining.remove(next_agent_name)
            
            # Step 5: Synthesize findings
            synthesis = await self._synthesize(state)
            state.combined_confidence = synthesis.confidence
            state.root_cause_hypotheses = synthesis.hypotheses
            state.timeline = synthesis.timeline
            state.blast_radius = synthesis.blast_radius
            
            self.logger.info(
                "agent_completed",
                agent=next_agent_name,
                findings=evidence.finding_count,
                confidence=state.combined_confidence,
            )
            
            # Step 6: Check stopping conditions
            if state.combined_confidence >= state.confidence_threshold:
                state.should_continue = False
                state.stop_reason = "confidence_threshold_reached"
            elif evidence.early_stop_recommended:
                state.should_continue = False
                state.stop_reason = "agent_recommended_stop"
        
        self.logger.info(
            "investigation_loop_completed",
            steps=state.current_step,
            agents_used=state.agents_called,
            final_confidence=state.combined_confidence,
            stop_reason=state.stop_reason,
        )
        
        return state
    
    @trace_tool("agent-router")
    async def _select_next_agent(self, state: InvestigationState) -> str:
        """
        Select which agent to call next.
        
        Uses priority queue by default, but can be influenced by
        previous agent suggestions.
        """
        # Check if previous agent suggested next
        if state.all_evidence:
            last_evidence = state.all_evidence[-1]
            if (last_evidence.suggests_next_agent and 
                last_evidence.suggests_next_agent in state.agents_remaining):
                return last_evidence.suggests_next_agent
        
        # Use priority queue
        return state.agents_remaining[0]
    
    def _build_context(self, state: InvestigationState) -> Dict:
        """Build context for sub-agent call."""
        return {
            "investigation_id": state.investigation_id,
            "step_number": state.current_step,
            "alert": state.alert.model_dump(),
            "triage": state.triage.model_dump() if state.triage else None,
            "previous_findings": [e.model_dump() for e in state.all_evidence],
            "timeline_so_far": state.timeline,
            "hypotheses_so_far": [h.model_dump() for h in state.root_cause_hypotheses],
            "agents_called": state.agents_called,
        }
    
    async def _synthesize(self, state: InvestigationState) -> Synthesis:
        """
        Synthesize findings into root cause hypotheses.

        Attempts LLM synthesis first.  Falls back to the rule-based approach
        when no LLM is configured or the LLM call does not return a usable
        result.

        Args:
            state: Current investigation state with accumulated evidence.

        Returns:
            Synthesis containing confidence, hypotheses, timeline, and blast
            radius assessment.
        """
        # ------------------------------------------------------------------ #
        # Shared pre-computation used by both LLM and rule-based paths        #
        # ------------------------------------------------------------------ #

        # Weighted confidence from agent evidence
        if not state.all_evidence:
            confidence = 0.0
        else:
            total_weight = 0
            weighted_sum = 0.0
            for evidence in state.all_evidence:
                weight = len(evidence.findings) + 1
                weighted_sum += evidence.confidence * weight
                total_weight += weight
            confidence = weighted_sum / total_weight if total_weight > 0 else 0.0

        # Build a chronological timeline from findings
        timeline: List[Dict] = []
        for evidence in state.all_evidence:
            for finding in evidence.findings:
                timeline.append({
                    "timestamp": finding.timestamp.isoformat(),
                    "event": finding.title,
                    "source": evidence.agent_name,
                    "severity": finding.severity.value,
                })
        timeline.sort(key=lambda x: x["timestamp"])

        # Collect all affected services
        affected_services_set: set = set()
        for evidence in state.all_evidence:
            for finding in evidence.findings:
                affected_services_set.update(finding.affected_services)
        blast_radius = {
            "services": list(affected_services_set),
            "users_affected": "unknown",
        }

        # ------------------------------------------------------------------ #
        # LLM synthesis path                                                  #
        # ------------------------------------------------------------------ #
        llm = get_llm_client()
        if llm.is_available and state.all_evidence:
            llm_result = await self._llm_synthesize(llm, state, timeline)
            if llm_result:
                try:
                    llm_confidence = float(llm_result.get("confidence", confidence))
                    llm_confidence = max(0.0, min(1.0, llm_confidence))

                    # Determine the best trigger time from findings
                    trigger_time = datetime.utcnow()
                    if timeline:
                        try:
                            trigger_time = datetime.fromisoformat(
                                timeline[0]["timestamp"]
                            )
                        except (ValueError, KeyError):
                            pass

                    # Map LLM category string to RootCauseCategory enum
                    raw_category = llm_result.get("category", "unknown")
                    try:
                        category = RootCauseCategory(raw_category)
                    except ValueError:
                        category = RootCauseCategory.UNKNOWN

                    # Collect supporting evidence IDs from all findings
                    supporting_ids = [
                        finding.id
                        for evidence in state.all_evidence
                        for finding in evidence.findings
                    ]

                    hypothesis = RootCauseHypothesis(
                        id=f"rca-{uuid.uuid4().hex[:8]}",
                        rank=1,
                        hypothesis=llm_result.get("hypothesis", "Unknown root cause"),
                        category=category,
                        confidence=llm_confidence,
                        supporting_evidence=supporting_ids,
                        evidence_summary=llm_result.get("evidence_summary", ""),
                        probable_trigger_time=trigger_time,
                        probable_trigger_event=llm_result.get(
                            "probable_trigger_event", ""
                        ),
                        causality_chain=llm_result.get("causality_chain", []),
                        blast_radius_description=llm_result.get(
                            "blast_radius_description"
                        ),
                        reasoning=llm_result.get("reasoning", "LLM synthesis"),
                    )

                    self.logger.info(
                        "synthesis_llm_completed",
                        confidence=llm_confidence,
                        category=category,
                    )

                    return Synthesis(
                        confidence=llm_confidence,
                        hypotheses=[hypothesis],
                        timeline=timeline,
                        blast_radius=blast_radius,
                        should_continue=llm_confidence < state.confidence_threshold,
                    )
                except Exception as exc:
                    self.logger.warning(
                        "synthesis_llm_result_invalid",
                        error=str(exc),
                    )

        # ------------------------------------------------------------------ #
        # Rule-based fallback                                                 #
        # ------------------------------------------------------------------ #
        self.logger.info("synthesis_using_rule_based_fallback")

        hypotheses: List[RootCauseHypothesis] = []
        if state.all_evidence:
            best_finding = None
            best_confidence = 0.0
            for evidence in state.all_evidence:
                for finding in evidence.findings:
                    if finding.confidence > best_confidence:
                        best_confidence = finding.confidence
                        best_finding = finding

            if best_finding:
                hypotheses.append(RootCauseHypothesis(
                    id=f"rca-{uuid.uuid4().hex[:8]}",
                    rank=1,
                    hypothesis=f"{best_finding.title}: {best_finding.description}",
                    category=self._finding_type_to_category(best_finding.type),
                    confidence=confidence,
                    supporting_evidence=[best_finding.id],
                    evidence_summary=best_finding.description,
                    probable_trigger_time=best_finding.timestamp,
                    probable_trigger_event=best_finding.title,
                    reasoning=(
                        f"Based on {len(state.all_evidence)} agent investigations "
                        f"with combined confidence {confidence:.0%}"
                    ),
                ))

        return Synthesis(
            confidence=confidence,
            hypotheses=hypotheses,
            timeline=timeline,
            blast_radius=blast_radius,
            should_continue=confidence < state.confidence_threshold,
        )

    @trace_llm("investigator-synthesis")
    async def _llm_synthesize(
        self,
        llm,
        state: InvestigationState,
        timeline: List[Dict],
    ) -> Optional[Dict]:
        """Call the LLM to synthesize evidence into a root cause hypothesis.

        Args:
            llm: Initialised LLMClient instance.
            state: Current investigation state.
            timeline: Pre-built chronological timeline list.

        Returns:
            Parsed JSON dict from the LLM, or None on failure.
        """
        # Build a human-readable findings summary for the prompt
        findings_lines: List[str] = []
        for evidence in state.all_evidence:
            findings_lines.append(f"[{evidence.agent_name}] (confidence {evidence.confidence:.0%})")
            for finding in evidence.findings:
                findings_lines.append(
                    f"  - [{finding.severity.value.upper()}] {finding.title}: "
                    f"{finding.description} (confidence {finding.confidence:.0%})"
                )
        findings_summary = "\n".join(findings_lines) if findings_lines else "No findings yet."

        # Build a compact timeline string
        timeline_lines: List[str] = []
        for entry in timeline:
            timeline_lines.append(
                f"  {entry['timestamp']} [{entry['severity'].upper()}] "
                f"{entry['event']} (via {entry['source']})"
            )
        timeline_str = "\n".join(timeline_lines) if timeline_lines else "No timeline entries."

        # Determine alert_type string from triage result
        alert_type_str = (
            state.triage.alert_type.value if state.triage else "unknown"
        )

        prompt = SynthesisPrompt.format(
            alert_title=state.alert.title,
            alert_type=alert_type_str,
            findings_summary=findings_summary,
            timeline=timeline_str,
        )
        return await llm.complete_json(prompt, system_prompt=SynthesisPrompt.SYSTEM)
    
    def _finding_type_to_category(self, finding_type) -> RootCauseCategory:
        """Map finding type to root cause category."""
        from incidentagent.schemas.evidence import FindingType
        
        mapping = {
            FindingType.DEPLOYMENT: RootCauseCategory.DEPLOYMENT,
            FindingType.ERROR_SIGNATURE: RootCauseCategory.DEPLOYMENT,
            FindingType.RESOURCE_EXHAUSTION: RootCauseCategory.RESOURCE,
            FindingType.DEPENDENCY_FAILURE: RootCauseCategory.DEPENDENCY,
            FindingType.CONFIG_CHANGE: RootCauseCategory.CONFIG,
            FindingType.NETWORK_ISSUE: RootCauseCategory.NETWORK,
        }
        return mapping.get(finding_type, RootCauseCategory.UNKNOWN)
