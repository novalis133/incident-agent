"""
IncidentAgent - Autonomous AI Agent for DevOps Incident Investigation

When PagerDuty fires at 3am, IncidentAgent investigates before you wake up.
Analyzes logs, correlates metrics, identifies root cause, suggests fixes — all in under 2 minutes.

Features:
- Multi-agent architecture with specialized sub-agents
- Iterative refinement investigation pattern
- Gradient AI integration (ADK, Knowledge Bases, Guardrails)
- Safe remediation with risk scoring
- Continuous learning from resolved incidents

Usage:
    from incidentagent import investigate_alert
    
    result = await investigate_alert(alert)
    print(f"Root cause: {result.root_cause.hypothesis}")
    print(f"Confidence: {result.confidence_score:.0%}")
"""

__version__ = "1.0.0"
__author__ = "Osama"

from incidentagent.schemas import (
    UnifiedAlert,
    TriageResult,
    InvestigationResult,
    RootCauseHypothesis,
    Remediation,
)

__all__ = [
    "UnifiedAlert",
    "TriageResult",
    "InvestigationResult",
    "RootCauseHypothesis",
    "Remediation",
    "__version__",
]
