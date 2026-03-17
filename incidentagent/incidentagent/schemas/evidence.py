"""
Evidence Schema

Findings and evidence collected by sub-agents.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class FindingType(str, Enum):
    """Types of findings that agents can report"""
    
    DEPLOYMENT = "deployment"                   # Recent deployment/release
    ERROR_SIGNATURE = "error_signature"         # Specific error/exception pattern
    RESOURCE_EXHAUSTION = "resource_exhaustion" # CPU/memory/disk issues
    DEPENDENCY_FAILURE = "dependency_failure"   # External service down
    ANOMALY = "anomaly"                         # Statistical anomaly detected
    CORRELATION = "correlation"                 # Correlated events
    HISTORICAL_MATCH = "historical_match"       # Similar past incident
    CONFIG_CHANGE = "config_change"             # Configuration modification
    POD_EVENT = "pod_event"                     # Kubernetes pod event
    NETWORK_ISSUE = "network_issue"             # Network-related finding
    RUNBOOK_MATCH = "runbook_match"             # Matching runbook found


class Severity(str, Enum):
    """Finding severity levels"""
    
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Finding(BaseModel):
    """
    Single piece of evidence from investigation.
    
    This is the core unit of information that agents produce.
    Designed for high-value early signals based on research:
    - Recent Changes (80% of incidents follow deployments)
    - Error Spike Start Time (pinpoints trigger)
    - Blast Radius (impact assessment)
    """
    
    # Identity
    id: str = Field(..., description="Unique finding ID")
    type: FindingType = Field(..., description="Type of finding")
    
    # Content
    title: str = Field(..., description="Brief finding title")
    description: str = Field(..., description="Detailed description")
    severity: Severity = Field(..., description="Finding severity")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score (0-1)"
    )
    
    # Timeline (critical for correlation)
    timestamp: datetime = Field(..., description="When this event occurred")
    time_delta_from_incident: str = Field(
        ...,
        description="Time relative to incident (e.g., '-2h 15m')"
    )
    
    # Blast Radius
    affected_services: List[str] = Field(
        default_factory=list,
        description="Services affected by this finding"
    )
    affected_users_estimate: Optional[int] = Field(
        default=None,
        description="Estimated number of users affected"
    )
    
    # Evidence Chain
    evidence_source: str = Field(
        ...,
        description="Data source (elasticsearch, prometheus, etc.)"
    )
    evidence_query: str = Field(
        ...,
        description="Query used to find this evidence"
    )
    raw_evidence: str = Field(
        ...,
        description="Raw evidence (log line, metric value, etc.)"
    )
    evidence_url: Optional[str] = Field(
        default=None,
        description="URL to view evidence in source system"
    )
    
    # Correlation
    related_findings: List[str] = Field(
        default_factory=list,
        description="IDs of related findings"
    )
    correlation_strength: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Strength of correlation (0-1)"
    )
    
    # Actionability
    is_actionable: bool = Field(
        default=False,
        description="Can we act on this finding directly?"
    )
    suggested_action: Optional[str] = Field(
        default=None,
        description="Suggested action if actionable"
    )
    
    # Metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional finding-specific data"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "finding-001",
                "type": "deployment",
                "title": "Deployment of payment-service v2.3.1",
                "description": "New version deployed 2 hours before incident",
                "severity": "high",
                "confidence": 0.85,
                "timestamp": "2026-02-21T01:15:00Z",
                "time_delta_from_incident": "-2h 0m",
                "affected_services": ["payment-service"],
                "evidence_source": "kubernetes",
                "evidence_query": "kubectl get deployments -n payments",
                "raw_evidence": "deployment.apps/payment-service scaled from 3 to 3",
                "is_actionable": True,
                "suggested_action": "Consider rollback to v2.3.0"
            }
        }


class AgentEvidence(BaseModel):
    """
    Complete evidence package from a sub-agent.
    
    Contains all findings from a single agent's investigation.
    """
    
    # Identity
    agent_name: str = Field(..., description="Name of the agent")
    agent_type: str = Field(..., description="Type/category of agent")
    
    # Reference
    investigation_id: str = Field(..., description="Parent investigation ID")
    step_number: int = Field(..., description="Step number in investigation")
    
    # Timing
    started_at: datetime = Field(..., description="When agent started")
    completed_at: datetime = Field(..., description="When agent completed")
    duration_ms: int = Field(..., description="Duration in milliseconds")
    
    # Findings
    findings: List[Finding] = Field(
        default_factory=list,
        description="List of findings"
    )
    finding_count: int = Field(
        default=0,
        description="Number of findings"
    )
    
    # Confidence Assessment
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall confidence from this agent"
    )
    confidence_reasoning: str = Field(
        ...,
        description="Explanation for confidence score"
    )
    
    # Iteration Hints (for Investigator Master)
    suggests_next_agent: Optional[str] = Field(
        default=None,
        description="Suggested next agent to call"
    )
    next_agent_context: Optional[str] = Field(
        default=None,
        description="Context to pass to next agent"
    )
    
    # Early Stopping Signals
    is_high_confidence: bool = Field(
        default=False,
        description="True if confidence > 0.85"
    )
    is_root_cause_candidate: bool = Field(
        default=False,
        description="True if findings suggest root cause"
    )
    early_stop_recommended: bool = Field(
        default=False,
        description="True if agent recommends stopping investigation"
    )
    
    # Errors
    errors: List[str] = Field(
        default_factory=list,
        description="Any errors encountered during investigation"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "agent_name": "DeployAgent",
                "agent_type": "deployment_checker",
                "investigation_id": "inv-12345",
                "step_number": 1,
                "started_at": "2026-02-21T03:15:10Z",
                "completed_at": "2026-02-21T03:15:15Z",
                "duration_ms": 5000,
                "findings": [],
                "finding_count": 1,
                "confidence": 0.85,
                "confidence_reasoning": "Found deployment 2h before incident with code changes to payment processing",
                "suggests_next_agent": "LogsAgent",
                "next_agent_context": "Check logs around 01:15:00 for payment-service errors",
                "is_high_confidence": True,
                "is_root_cause_candidate": True,
                "early_stop_recommended": False
            }
        }
