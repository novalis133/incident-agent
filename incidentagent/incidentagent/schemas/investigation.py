"""
Investigation Schema

Investigation state and results.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from incidentagent.schemas.alert import UnifiedAlert
from incidentagent.schemas.evidence import AgentEvidence
from incidentagent.schemas.remediation import Remediation
from incidentagent.schemas.root_cause import RootCauseHypothesis, Synthesis
from incidentagent.schemas.triage import TriageResult


class InvestigationStatus(str, Enum):
    """Investigation status"""
    
    PENDING = "pending"         # Not started
    TRIAGING = "triaging"       # Running triage
    INVESTIGATING = "investigating"  # Running investigation
    SYNTHESIZING = "synthesizing"    # Building root cause
    REMEDIATING = "remediating"      # Generating remediation
    COMPLETED = "completed"     # Done
    FAILED = "failed"           # Error occurred
    TIMEOUT = "timeout"         # Timed out


class InvestigationState(BaseModel):
    """
    Running state of investigation.
    
    Maintained throughout the investigation lifecycle.
    """
    
    # Identity
    investigation_id: str = Field(..., description="Unique investigation ID")
    alert: UnifiedAlert = Field(..., description="Original alert")
    triage: Optional[TriageResult] = Field(
        default=None,
        description="Triage results"
    )
    
    # Status
    status: InvestigationStatus = Field(
        default=InvestigationStatus.PENDING,
        description="Current status"
    )
    
    # Progress
    current_step: int = Field(default=0, description="Current step number")
    agents_called: List[str] = Field(
        default_factory=list,
        description="Agents that have been called"
    )
    agents_remaining: List[str] = Field(
        default_factory=list,
        description="Agents still to call"
    )
    current_agent: Optional[str] = Field(
        default=None,
        description="Currently running agent"
    )
    
    # Evidence Accumulation
    all_evidence: List[AgentEvidence] = Field(
        default_factory=list,
        description="All evidence collected"
    )
    combined_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Combined confidence score"
    )
    
    # Synthesis (updated after each step)
    timeline: List[Dict] = Field(
        default_factory=list,
        description="Incident timeline"
    )
    blast_radius: Dict = Field(
        default_factory=dict,
        description="Blast radius assessment"
    )
    root_cause_hypotheses: List[RootCauseHypothesis] = Field(
        default_factory=list,
        description="Current hypotheses"
    )
    
    # Control
    should_continue: bool = Field(
        default=True,
        description="Should investigation continue?"
    )
    stop_reason: Optional[str] = Field(
        default=None,
        description="Reason for stopping"
    )
    confidence_threshold: float = Field(
        default=0.85,
        description="Threshold to stop investigation"
    )
    
    # Timing
    started_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When investigation started"
    )
    timeout_at: Optional[datetime] = Field(
        default=None,
        description="When investigation will timeout"
    )
    
    # Errors
    errors: List[str] = Field(
        default_factory=list,
        description="Any errors encountered"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "investigation_id": "inv-12345",
                "status": "investigating",
                "current_step": 2,
                "agents_called": ["DeployAgent", "LogsAgent"],
                "agents_remaining": ["MetricsAgent", "K8sAgent"],
                "current_agent": "LogsAgent",
                "combined_confidence": 0.75,
                "should_continue": True,
                "confidence_threshold": 0.85
            }
        }


class InvestigationResult(BaseModel):
    """
    Complete investigation output.
    
    Final result after investigation completes.
    """
    
    # Metadata
    investigation_id: str = Field(..., description="Unique investigation ID")
    alert_id: str = Field(..., description="Original alert ID")
    started_at: datetime = Field(..., description="When investigation started")
    completed_at: datetime = Field(..., description="When investigation completed")
    duration_seconds: int = Field(..., description="Total duration")
    
    # Status
    status: Literal["completed", "partial", "failed", "timeout"] = Field(
        ...,
        description="Final status"
    )
    
    # Alert Info
    alert_title: str = Field(..., description="Alert title")
    alert_severity: str = Field(..., description="Alert severity")
    affected_services: List[str] = Field(
        default_factory=list,
        description="Affected services"
    )
    
    # Investigation Summary
    agents_used: List[str] = Field(..., description="Agents that were called")
    total_findings: int = Field(..., description="Total findings count")
    
    # Root Cause
    root_cause: RootCauseHypothesis = Field(
        ...,
        description="Primary root cause hypothesis"
    )
    alternative_hypotheses: List[RootCauseHypothesis] = Field(
        default_factory=list,
        description="Alternative hypotheses"
    )
    
    # Timeline
    incident_timeline: List[Dict] = Field(
        ...,
        description="Incident timeline"
    )
    
    # Blast Radius
    blast_radius: Dict = Field(..., description="Impact assessment")
    
    # Remediation
    remediation: Remediation = Field(
        ...,
        description="Remediation plan"
    )
    
    # Evidence (summary and full)
    evidence_summary: List[Dict] = Field(
        ...,
        description="Evidence summary"
    )
    full_evidence: List[AgentEvidence] = Field(
        ...,
        description="Complete evidence"
    )
    
    # Metrics
    time_saved_estimate: str = Field(
        ...,
        description="Estimated time saved vs manual"
    )
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Final confidence score"
    )
    
    # Feedback (populated later)
    human_verified: bool = Field(
        default=False,
        description="Has human verified this?"
    )
    human_feedback: Optional[str] = Field(
        default=None,
        description="Human feedback if any"
    )
    feedback_score: Optional[int] = Field(
        default=None,
        ge=1,
        le=5,
        description="Rating 1-5"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "investigation_id": "inv-12345",
                "alert_id": "alert-12345",
                "started_at": "2026-02-21T03:15:05Z",
                "completed_at": "2026-02-21T03:16:45Z",
                "duration_seconds": 100,
                "status": "completed",
                "alert_title": "High error rate on payment-service",
                "alert_severity": "critical",
                "affected_services": ["payment-service", "checkout-service"],
                "agents_used": ["DeployAgent", "LogsAgent", "MetricsAgent"],
                "total_findings": 7,
                "confidence_score": 0.89,
                "time_saved_estimate": "~50 hours"
            }
        }
