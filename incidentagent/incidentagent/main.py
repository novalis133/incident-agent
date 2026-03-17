"""
IncidentAgent Main Entry Point

Gradient ADK entrypoint and CLI.
"""

import asyncio
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import structlog

# Gradient ADK imports (will be available when deployed)
try:
    from gradient_adk import entrypoint, trace_llm, trace_tool, trace_retriever
except ImportError:
    # Mock decorators for local development
    def entrypoint(fn):
        return fn
    def trace_llm(name):
        def decorator(fn):
            return fn
        return decorator
    def trace_tool(name):
        def decorator(fn):
            return fn
        return decorator
    def trace_retriever(name):
        def decorator(fn):
            return fn
        return decorator

from incidentagent.schemas import (
    UnifiedAlert,
    TriageResult,
    InvestigationResult,
    InvestigationState,
    InvestigationStatus,
)
from incidentagent.schemas.root_cause import RootCauseHypothesis, RootCauseCategory
from incidentagent.schemas.config import get_settings

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@entrypoint
async def main(input: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main Gradient ADK entrypoint.
    
    This is called when the agent receives a request.
    
    Args:
        input: The input payload (alert data or command)
        context: Gradient context (session, user, etc.)
    
    Returns:
        Investigation result or error
    """
    logger.info("incidentagent_invoked", input_keys=list(input.keys()))
    
    try:
        # Determine request type
        action = input.get("action", "investigate")
        
        if action == "investigate":
            # Parse alert
            alert_data = input.get("alert", input)
            alert = UnifiedAlert(**alert_data)
            
            # Run investigation
            result = await investigate_alert(alert)
            
            return {
                "status": "success",
                "investigation_id": result.investigation_id,
                "root_cause": result.root_cause.model_dump(),
                "confidence": result.confidence_score,
                "remediation": result.remediation.model_dump(),
                "duration_seconds": result.duration_seconds,
            }
        
        elif action == "status":
            # Return investigation status
            investigation_id = input.get("investigation_id")
            # TODO: Implement status lookup
            return {"status": "not_implemented"}
        
        elif action == "feedback":
            # Record feedback on investigation
            investigation_id = input.get("investigation_id")
            feedback_score = input.get("score")
            feedback_notes = input.get("notes")
            # TODO: Implement feedback recording
            return {"status": "not_implemented"}
        
        else:
            return {
                "status": "error",
                "error": f"Unknown action: {action}"
            }
    
    except Exception as e:
        logger.exception("incidentagent_error", error=str(e))
        return {
            "status": "error",
            "error": str(e)
        }


@trace_tool("investigation-pipeline")
async def investigate_alert(alert: UnifiedAlert) -> InvestigationResult:
    """
    Run full investigation on an alert.
    
    This is the main investigation pipeline:
    1. Triage: Classify and prioritize
    2. Investigate: Run sub-agents iteratively
    3. Synthesize: Build root cause hypothesis
    4. Remediate: Generate safe remediation steps
    
    Args:
        alert: The alert to investigate
    
    Returns:
        Complete investigation result
    """
    from incidentagent.agents.triage import TriageAgent
    from incidentagent.agents.investigator import InvestigatorMaster
    from incidentagent.agents.remediation import RemediationAgent
    import incidentagent.agents.sub_agents  # noqa: F401 — triggers @register_agent
    
    settings = get_settings()
    started_at = datetime.utcnow()
    timeout_at = started_at + timedelta(seconds=settings.investigation.timeout_seconds)
    
    logger.info(
        "investigation_started",
        alert_id=alert.id,
        alert_title=alert.title,
        severity=alert.severity,
    )
    
    # Initialize state
    state = InvestigationState(
        investigation_id=f"inv-{alert.id}",
        alert=alert,
        status=InvestigationStatus.TRIAGING,
        started_at=started_at,
        timeout_at=timeout_at,
        confidence_threshold=settings.investigation.confidence_threshold,
    )
    
    try:
        # Step 1: Triage
        triage_agent = TriageAgent()
        triage_result = await triage_agent.triage(alert)
        state.triage = triage_result
        state.agents_remaining = triage_result.priority_queue.copy()
        state.status = InvestigationStatus.INVESTIGATING
        
        logger.info(
            "triage_completed",
            alert_type=triage_result.alert_type,
            priority_queue=triage_result.priority_queue,
        )
        
        # Step 2: Investigate
        investigator = InvestigatorMaster()
        state = await investigator.investigate(state)
        state.status = InvestigationStatus.SYNTHESIZING
        
        logger.info(
            "investigation_completed",
            agents_used=state.agents_called,
            confidence=state.combined_confidence,
            finding_count=sum(len(e.findings) for e in state.all_evidence),
        )
        
        # Step 3: Generate remediation
        state.status = InvestigationStatus.REMEDIATING
        remediation_agent = RemediationAgent()
        remediation = await remediation_agent.generate(
            root_cause=state.root_cause_hypotheses[0] if state.root_cause_hypotheses else None,
            evidence=state.all_evidence,
        )
        
        # Build final result
        completed_at = datetime.utcnow()
        duration = int((completed_at - started_at).total_seconds())
        
        result = InvestigationResult(
            investigation_id=state.investigation_id,
            alert_id=alert.id,
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=duration,
            status="completed",
            alert_title=alert.title,
            alert_severity=alert.severity,
            affected_services=state.triage.affected_services if state.triage else [],
            agents_used=state.agents_called,
            total_findings=sum(len(e.findings) for e in state.all_evidence),
            root_cause=state.root_cause_hypotheses[0] if state.root_cause_hypotheses else RootCauseHypothesis(
                id="rca-unknown",
                rank=1,
                hypothesis="Unable to determine root cause",
                category=RootCauseCategory.UNKNOWN,
                confidence=0.0,
                supporting_evidence=[],
                evidence_summary="Investigation completed without sufficient evidence",
                probable_trigger_time=started_at,
                reasoning="No root cause hypotheses generated",
            ),
            alternative_hypotheses=state.root_cause_hypotheses[1:] if state.root_cause_hypotheses else [],
            incident_timeline=state.timeline,
            blast_radius=state.blast_radius,
            remediation=remediation,
            evidence_summary=[
                {"agent": e.agent_name, "findings": len(e.findings), "confidence": e.confidence}
                for e in state.all_evidence
            ],
            full_evidence=state.all_evidence,
            time_saved_estimate=_estimate_time_saved(duration),
            confidence_score=state.combined_confidence,
        )
        
        logger.info(
            "result_generated",
            investigation_id=result.investigation_id,
            duration_seconds=duration,
            confidence=result.confidence_score,
        )
        
        return result
    
    except Exception as e:
        logger.exception("investigation_failed", error=str(e))
        raise


def _estimate_time_saved(investigation_seconds: int) -> str:
    """Estimate time saved vs manual investigation"""
    # Research shows manual RCA takes 50+ hours on average
    manual_hours = 50
    investigation_minutes = investigation_seconds / 60
    
    if investigation_minutes < 5:
        return f"~{manual_hours} hours (vs {investigation_minutes:.1f} minutes)"
    else:
        return f"~{manual_hours - (investigation_minutes / 60):.0f} hours"


def cli():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="IncidentAgent CLI")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # investigate command
    investigate_parser = subparsers.add_parser("investigate", help="Investigate an alert")
    investigate_parser.add_argument("--title", required=True, help="Alert title")
    investigate_parser.add_argument("--service", help="Affected service")
    investigate_parser.add_argument("--severity", default="high", help="Severity level")
    
    # dashboard command
    dashboard_parser = subparsers.add_parser("dashboard", help="Start dashboard")
    dashboard_parser.add_argument("--port", type=int, default=8501, help="Port")
    
    args = parser.parse_args()
    
    if args.command == "investigate":
        # Create alert from args
        alert = UnifiedAlert(
            id=f"cli-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            source="manual",
            title=args.title,
            service=args.service,
            severity=args.severity,
            fired_at=datetime.utcnow(),
        )
        
        # Run investigation
        result = asyncio.run(investigate_alert(alert))
        
        # Print result
        print(f"\n{'='*60}")
        print(f"Investigation Complete: {result.investigation_id}")
        print(f"{'='*60}")
        print(f"Duration: {result.duration_seconds}s")
        print(f"Confidence: {result.confidence_score:.0%}")
        print(f"\nRoot Cause: {result.root_cause.hypothesis}")
        print(f"Category: {result.root_cause.category}")
        print(f"\nRemediation: {result.remediation.summary}")
        print(f"Risk Score: {result.remediation.total_risk_score:.0%}")
        print(f"\nTime Saved: {result.time_saved_estimate}")
    
    elif args.command == "dashboard":
        import subprocess
        subprocess.run([
            "streamlit", "run", 
            "incidentagent/ui/dashboard.py",
            "--server.port", str(args.port)
        ])
    
    else:
        parser.print_help()


if __name__ == "__main__":
    cli()
