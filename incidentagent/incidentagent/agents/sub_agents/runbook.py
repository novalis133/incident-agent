"""
Runbook Agent

Searches knowledge base for relevant runbooks and solutions.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from incidentagent.agents.base import SubAgent, register_agent
from incidentagent.knowledge.kb_client import get_kb_client
from incidentagent.schemas.evidence import AgentEvidence, Finding, FindingType, Severity

try:
    from gradient_adk import trace_tool, trace_retriever
except ImportError:
    def trace_tool(name):
        def decorator(fn):
            return fn
        return decorator
    def trace_retriever(name):
        def decorator(fn):
            return fn
        return decorator

from . import mock_data


@register_agent
class RunbookAgent(SubAgent):
    """
    Runbook Agent - Searches for relevant documentation.

    Uses Gradient Knowledge Base to find:
    - Troubleshooting guides
    - Runbooks
    - SOPs
    - Known issues
    """

    name = "RunbookAgent"
    description = "Searches knowledge base for runbooks and known solutions"

    @trace_tool("runbook-investigate")
    async def investigate(self, context: Dict[str, Any]) -> AgentEvidence:
        """Search runbooks for relevant procedures."""
        started_at = datetime.utcnow()
        alert = context.get("alert", {})
        service = alert.get("service")
        incident_time = self._parse_incident_time(alert)
        previous_findings = context.get("previous_findings", [])

        findings: List[Finding] = []
        errors: List[str] = []

        search_queries = self._build_search_queries(alert, previous_findings)

        for query in search_queries:
            try:
                runbook_findings = await self._search_runbooks(
                    query, service, incident_time,
                )
                for finding in runbook_findings:
                    if not any(f.title == finding.title for f in findings):
                        findings.append(finding)
            except Exception as e:
                errors.append(f"Runbook search failed for '{query}': {e}")
                self.logger.error("runbook_search_failed", query=query, error=str(e))

        self._link_to_investigation_findings(findings, previous_findings)

        confidence = self._calculate_confidence(findings)

        next_context = None
        if findings:
            top = max(findings, key=lambda f: f.confidence)
            next_context = (
                f"Search past incidents similar to current: "
                f"{alert.get('title', 'unknown alert')}. "
                f"Matching runbook: {top.title}."
            )

        return self._build_evidence(
            findings=findings,
            context=context,
            confidence=confidence,
            confidence_reasoning=self._explain_confidence(findings),
            started_at=started_at,
            suggests_next_agent="MemoryAgent",
            next_agent_context=next_context,
            errors=errors,
        )

    def get_tools(self) -> List[Dict[str, Any]]:
        """Return tools for Gradient function calling."""
        return [
            {
                "name": "search_runbooks",
                "description": "Search Gradient Knowledge Base for runbooks and troubleshooting guides",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "service": {"type": "string", "description": "Service name filter"},
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Tag filters",
                        },
                    },
                    "required": ["query"],
                },
            },
        ]

    def _parse_incident_time(self, alert: Dict[str, Any]) -> datetime:
        """Parse incident time from alert."""
        fired_at = alert.get("fired_at", datetime.utcnow().isoformat())
        if isinstance(fired_at, str):
            return datetime.fromisoformat(fired_at.replace("Z", "+00:00"))
        return fired_at

    def _build_search_queries(
        self,
        alert: Dict[str, Any],
        previous_findings: List[Any],
    ) -> List[str]:
        """Build search queries from alert and previous findings."""
        queries = []

        title = alert.get("title", "")
        if title:
            queries.append(title)

        description = alert.get("description", "")
        if description and description != title:
            queries.append(description)

        for pf in previous_findings:
            if not hasattr(pf, "findings"):
                continue
            for finding in pf.findings:
                if finding.confidence >= 0.7:
                    keywords = self._extract_keywords(finding.title)
                    if keywords:
                        queries.append(keywords)

        return queries[:5]

    def _extract_keywords(self, text: str) -> str:
        """Extract search-relevant keywords from finding text."""
        stop_words = {
            "the", "a", "an", "is", "at", "in", "on", "for", "to",
            "of", "and", "or", "with", "from", "by",
        }
        words = text.lower().split()
        keywords = [w.strip("():,.'\"") for w in words if w.lower().strip("():,.'\"") not in stop_words]
        return " ".join(keywords[:8])

    @trace_retriever("runbook-kb-search")
    async def _search_kb(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """Search the Gradient Knowledge Base for runbooks.

        Returns KB results if available, otherwise None to trigger fallback.
        """
        try:
            kb_client = get_kb_client()
            if not kb_client.is_available:
                return None
            return await kb_client.search_runbooks(query)
        except Exception as e:
            self.logger.warning("kb_search_unavailable", error=str(e))
            return None

    async def _search_runbooks(
        self,
        query: str,
        service: Optional[str],
        incident_time: datetime,
    ) -> List[Finding]:
        """Search for matching runbooks.

        Tries the Gradient Knowledge Base first; falls back to mock data
        when the KB is unavailable or returns no results.
        """
        kb_results = await self._search_kb(query)

        if kb_results is not None:
            # KB is available — convert its results into the mock-data shape
            # so the rest of the pipeline is unchanged.
            runbooks = self._kb_results_to_runbooks(kb_results, service)
        else:
            runbooks = mock_data.get_runbooks(query=query, service=service)

        findings: List[Finding] = []

        for runbook in runbooks:
            relevance = runbook.get("relevance_score", 0)
            if relevance < 0.5:
                continue

            confidence = min(0.90, relevance * 0.95)

            severity = Severity.HIGH if relevance > 0.85 else Severity.MEDIUM

            symptom_matches = self._match_symptoms(runbook, query)

            findings.append(Finding(
                id=self._generate_finding_id(),
                type=FindingType.RUNBOOK_MATCH,
                title=f"Runbook: {runbook['title']}",
                description=(
                    f"Found matching runbook with {relevance:.0%} relevance. "
                    f"Matching symptoms: {', '.join(symptom_matches) if symptom_matches else 'general match'}. "
                    f"Immediate actions available: {len(runbook.get('immediate_actions', []))}. "
                    f"Investigation steps: {len(runbook.get('investigation_steps', []))}."
                ),
                severity=severity,
                confidence=confidence,
                timestamp=incident_time,
                time_delta_from_incident="0m",
                affected_services=runbook.get("service_tags", []),
                evidence_source="gradient_knowledge_base",
                evidence_query=f"knowledge_base.search('{query[:50]}')",
                raw_evidence=(
                    f"runbook_id={runbook['id']} "
                    f"title={runbook['title']} "
                    f"relevance={relevance:.2f} "
                    f"actions={len(runbook.get('immediate_actions', []))}"
                ),
                is_actionable=True,
                suggested_action=self._format_immediate_actions(runbook),
                metadata={
                    "runbook_id": runbook["id"],
                    "relevance_score": relevance,
                    "symptom_matches": symptom_matches,
                    "immediate_actions": runbook.get("immediate_actions", []),
                    "investigation_steps": runbook.get("investigation_steps", []),
                    "content_path": runbook.get("content_path"),
                },
            ))

        return findings

    def _kb_results_to_runbooks(
        self,
        kb_results: List[Dict[str, Any]],
        service: Optional[str],
    ) -> List[Dict[str, Any]]:
        """Convert Gradient KB search results to the internal runbook shape."""
        runbooks = []
        for i, result in enumerate(kb_results):
            metadata = result.get("metadata", {})
            score = result.get("score", 0.75)
            content = result.get("content", result.get("text", ""))
            title = result.get("title", metadata.get("filename", f"Runbook {i + 1}"))

            # Extract a lightweight action list from the content
            immediate_actions: List[str] = []
            investigation_steps: List[str] = []
            for line in content.splitlines():
                stripped = line.strip().lstrip("0123456789.-) ")
                if not stripped:
                    continue
                if "**Immediate**" in line or (immediate_actions == [] and line.startswith("-")):
                    immediate_actions.append(stripped)
                elif line.startswith(tuple("0123456789")):
                    investigation_steps.append(stripped)

            runbooks.append({
                "id": metadata.get("filename", f"kb-{i}"),
                "title": title,
                "relevance_score": min(1.0, score),
                "symptoms": [],
                "service_tags": [service] if service else [],
                "immediate_actions": immediate_actions[:3],
                "investigation_steps": investigation_steps[:5],
                "content_path": metadata.get("filename"),
            })
        return runbooks

    def _match_symptoms(self, runbook: Dict[str, Any], query: str) -> List[str]:
        """Find matching symptoms between runbook and current context."""
        query_lower = query.lower()
        matches = []
        for symptom in runbook.get("symptoms", []):
            symptom_words = set(symptom.lower().split())
            query_words = set(query_lower.split())
            overlap = symptom_words & query_words
            if len(overlap) >= 2:
                matches.append(symptom)
        return matches

    def _format_immediate_actions(self, runbook: Dict[str, Any]) -> str:
        """Format immediate actions from runbook as suggested action."""
        actions = runbook.get("immediate_actions", [])
        if not actions:
            return "Follow runbook investigation steps"
        return f"Recommended: {actions[0]}"

    def _link_to_investigation_findings(
        self,
        runbook_findings: List[Finding],
        previous_findings: List[Any],
    ) -> None:
        """Link runbook findings to related investigation findings."""
        all_finding_ids = []
        for pf in previous_findings:
            if hasattr(pf, "findings"):
                for f in pf.findings:
                    if f.confidence >= 0.6:
                        all_finding_ids.append(f.id)

        for rf in runbook_findings:
            rf.related_findings.extend(all_finding_ids)
            if all_finding_ids:
                rf.correlation_strength = rf.confidence

    def _calculate_confidence(self, findings: List[Finding]) -> float:
        """Calculate overall confidence."""
        if not findings:
            return 0.15

        top_relevance = max(f.confidence for f in findings)

        if len(findings) > 1:
            top_relevance = min(0.92, top_relevance + 0.05)

        return round(top_relevance, 2)

    def _explain_confidence(self, findings: List[Finding]) -> str:
        """Explain confidence calculation."""
        if not findings:
            return "No matching runbooks found in knowledge base"

        top = max(findings, key=lambda f: f.confidence)
        return (
            f"Found {len(findings)} matching runbook(s). "
            f"Best match: {top.title} (relevance: {top.confidence:.0%}). "
            f"Actionable remediation steps are available."
        )
