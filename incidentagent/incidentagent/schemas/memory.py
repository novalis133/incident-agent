"""
Memory Schema

Schemas for storing past incidents and training data.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ReasoningStep(BaseModel):
    """
    Single step in the reasoning chain.
    
    Used for training the model on how to reason about incidents.
    """
    
    step: int = Field(..., description="Step number")
    agent: str = Field(..., description="Agent that ran")
    finding: str = Field(..., description="Key finding from this step")
    reasoning: str = Field(..., description="Why this finding is relevant")
    confidence_delta: float = Field(
        default=0.0,
        description="How much this step changed confidence"
    )
    led_to: Optional[str] = Field(
        default=None,
        description="What this step led to"
    )


class StoredIncident(BaseModel):
    """
    Complete incident record for memory and training.
    
    Stored in Gradient Knowledge Base after resolution.
    """
    
    # Identity
    incident_id: str = Field(..., description="Unique incident ID")
    investigation_id: str = Field(..., description="Related investigation ID")
    created_at: datetime = Field(..., description="When incident was created")
    resolved_at: Optional[datetime] = Field(
        default=None,
        description="When incident was resolved"
    )
    
    # Original Alert
    alert: Dict = Field(..., description="Original alert data")
    alert_type: str = Field(..., description="Alert type classification")
    severity: str = Field(..., description="Severity level")
    affected_services: List[str] = Field(
        default_factory=list,
        description="Affected services"
    )
    environment: str = Field(default="production", description="Environment")
    
    # Investigation Metadata
    investigation_duration_seconds: int = Field(
        ...,
        description="How long investigation took"
    )
    agents_used: List[str] = Field(
        default_factory=list,
        description="Agents that were used"
    )
    findings: List[Dict] = Field(
        default_factory=list,
        description="All findings"
    )
    
    # Root Cause (for causality training)
    root_cause: Dict = Field(..., description="Root cause hypothesis")
    root_cause_category: str = Field(
        ...,
        description="Category (deployment, resource, etc.)"
    )
    root_cause_confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence in root cause"
    )
    
    # Reasoning Chain (for reasoning training)
    reasoning_chain: List[ReasoningStep] = Field(
        default_factory=list,
        description="Step-by-step reasoning"
    )
    
    # Remediation (for learning what works)
    remediation_attempted: List[Dict] = Field(
        default_factory=list,
        description="Remediation steps attempted"
    )
    remediation_successful: bool = Field(
        default=False,
        description="Was remediation successful?"
    )
    remediation_that_worked: Optional[Dict] = Field(
        default=None,
        description="The remediation that worked"
    )
    resolution_time_seconds: Optional[int] = Field(
        default=None,
        description="Time from alert to resolution"
    )
    
    # Feedback (for continuous improvement)
    human_verified: bool = Field(
        default=False,
        description="Did human verify the root cause?"
    )
    human_correction: Optional[str] = Field(
        default=None,
        description="Human correction if wrong"
    )
    feedback_score: Optional[int] = Field(
        default=None,
        ge=1,
        le=5,
        description="Human rating 1-5"
    )
    feedback_notes: Optional[str] = Field(
        default=None,
        description="Human feedback notes"
    )
    
    # Embeddings (for similarity search)
    alert_embedding: List[float] = Field(
        default_factory=list,
        description="Vector embedding of alert"
    )
    root_cause_embedding: List[float] = Field(
        default_factory=list,
        description="Vector embedding of root cause"
    )
    
    # Tags for filtering
    tags: List[str] = Field(
        default_factory=list,
        description="Tags for categorization"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "incident_id": "INC-2026-0001",
                "investigation_id": "inv-12345",
                "created_at": "2026-02-21T03:15:00Z",
                "resolved_at": "2026-02-21T03:45:00Z",
                "alert_type": "error_rate",
                "severity": "critical",
                "affected_services": ["payment-service"],
                "investigation_duration_seconds": 100,
                "agents_used": ["DeployAgent", "LogsAgent", "MetricsAgent"],
                "root_cause_category": "deployment",
                "root_cause_confidence": 0.89,
                "remediation_successful": True,
                "resolution_time_seconds": 1800,
                "human_verified": True,
                "feedback_score": 5
            }
        }


class CausalityTrainingExample(BaseModel):
    """
    Training data for root cause prediction.
    
    Used to fine-tune the model on causality.
    """
    
    # Identity
    example_id: str = Field(..., description="Unique example ID")
    source_incident_id: str = Field(..., description="Source incident")
    
    # Input: What the agent sees
    alert: Dict = Field(..., description="Alert data")
    findings: List[Dict] = Field(
        default_factory=list,
        description="Evidence from sub-agents"
    )
    
    # Output: What we want the model to learn
    root_cause: str = Field(..., description="The actual root cause")
    root_cause_category: str = Field(
        ...,
        description="Category for classification"
    )
    causality_chain: List[str] = Field(
        ...,
        description="Chain: Event A → B → C"
    )
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    quality_score: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Quality score for this example"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "example_id": "train-001",
                "source_incident_id": "INC-2026-0001",
                "alert": {"title": "High error rate on payment-service"},
                "findings": [
                    {"type": "deployment", "description": "v2.3.1 deployed 2h ago"},
                    {"type": "error_signature", "description": "NullPointerException"}
                ],
                "root_cause": "Connection leak in PaymentProcessor.java in v2.3.1",
                "root_cause_category": "deployment",
                "causality_chain": [
                    "Deployment of v2.3.1",
                    "Connection leak bug in new code",
                    "Connections not released",
                    "Pool exhausted",
                    "NullPointerException",
                    "Error rate spike"
                ]
            }
        }


class ReasoningTrainingExample(BaseModel):
    """
    Training data for investigation reasoning.
    
    Used to fine-tune the model on what to do next.
    """
    
    # Identity
    example_id: str = Field(..., description="Unique example ID")
    source_incident_id: str = Field(..., description="Source incident")
    
    # Input: Current state
    alert: Dict = Field(..., description="Alert data")
    current_findings: List[Dict] = Field(
        default_factory=list,
        description="Findings so far"
    )
    agents_called: List[str] = Field(
        default_factory=list,
        description="Agents already called"
    )
    
    # Output: What to do next
    next_action: str = Field(
        ...,
        description="'call_agent' or 'synthesize'"
    )
    next_agent: Optional[str] = Field(
        default=None,
        description="Which agent to call"
    )
    reasoning: str = Field(
        ...,
        description="Why this decision"
    )
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    quality_score: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Quality score"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "example_id": "reason-001",
                "source_incident_id": "INC-2026-0001",
                "alert": {"title": "High error rate"},
                "current_findings": [{"type": "deployment"}],
                "agents_called": ["DeployAgent"],
                "next_action": "call_agent",
                "next_agent": "LogsAgent",
                "reasoning": "Deployment found 2h before incident. Need to check logs to confirm deployment caused errors."
            }
        }


class SimilarIncidentMatch(BaseModel):
    """
    Result from searching similar past incidents.
    """
    
    incident_id: str
    similarity_score: float
    title: str
    root_cause: str
    root_cause_category: str
    remediation_that_worked: Optional[str]
    resolution_time_seconds: Optional[int]
    success_rate: Optional[float]
    
    # Why it's similar
    matching_factors: List[str] = Field(default_factory=list)
