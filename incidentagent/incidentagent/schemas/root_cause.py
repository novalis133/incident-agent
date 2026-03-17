"""
Root Cause Schema

Root cause hypothesis and analysis results.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class RootCauseCategory(str, Enum):
    """
    Categories of root causes.
    
    Based on research and industry patterns.
    """
    
    DEPLOYMENT = "deployment"           # Code/config deployment caused issue
    RESOURCE = "resource"               # Resource exhaustion (CPU/memory/disk)
    DEPENDENCY = "dependency"           # External service/database failure
    CONFIG = "config"                   # Configuration error
    NETWORK = "network"                 # Network issues
    SECURITY = "security"               # Security incident
    DATA = "data"                       # Data corruption/inconsistency
    CAPACITY = "capacity"               # Traffic/load exceeded capacity
    HUMAN_ERROR = "human_error"         # Manual action caused issue
    UNKNOWN = "unknown"                 # Cannot determine


class RootCauseHypothesis(BaseModel):
    """
    Root cause analysis result.
    
    Represents a hypothesis about what caused the incident.
    """
    
    # Identity
    id: str = Field(..., description="Unique hypothesis ID")
    rank: int = Field(default=1, description="Rank among hypotheses (1 = most likely)")
    
    # Core Hypothesis
    hypothesis: str = Field(
        ...,
        description="Clear statement of the root cause"
    )
    category: RootCauseCategory = Field(
        ...,
        description="Root cause category"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score (0-1)"
    )
    
    # Evidence
    supporting_evidence: List[str] = Field(
        ...,
        description="Finding IDs that support this hypothesis"
    )
    evidence_summary: str = Field(
        ...,
        description="Summary of supporting evidence"
    )
    contradicting_evidence: List[str] = Field(
        default_factory=list,
        description="Finding IDs that contradict this hypothesis"
    )
    
    # Timeline
    probable_trigger_time: datetime = Field(
        ...,
        description="When the root cause likely triggered"
    )
    probable_trigger_event: str = Field(
        ...,
        description="What event triggered the issue"
    )
    
    # Causality Chain
    causality_chain: List[str] = Field(
        default_factory=list,
        description="Chain of events: A → B → C"
    )
    
    # Impact
    affected_services: List[str] = Field(
        default_factory=list,
        description="Services affected by this root cause"
    )
    blast_radius_description: Optional[str] = Field(
        default=None,
        description="Description of impact scope"
    )
    
    # Metadata
    reasoning: str = Field(
        ...,
        description="Detailed reasoning for this hypothesis"
    )
    alternative_hypotheses: List[str] = Field(
        default_factory=list,
        description="IDs of alternative hypotheses considered"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "rca-001",
                "rank": 1,
                "hypothesis": "Connection leak in PaymentProcessor.java introduced in v2.3.1 caused connection pool exhaustion",
                "category": "deployment",
                "confidence": 0.89,
                "supporting_evidence": ["finding-001", "finding-002", "finding-003"],
                "evidence_summary": "Deployment of v2.3.1 at 01:15 correlates with error spike at 03:15. Logs show NullPointerException in PaymentProcessor.java. Metrics show connection pool at 100% capacity.",
                "probable_trigger_time": "2026-02-21T01:15:00Z",
                "probable_trigger_event": "Deployment of payment-service v2.3.1",
                "causality_chain": [
                    "Deployment of v2.3.1",
                    "New code has connection leak bug",
                    "Connections not released after use",
                    "Connection pool exhausted over 2 hours",
                    "New requests fail with NullPointerException",
                    "Error rate spikes to 15%"
                ],
                "affected_services": ["payment-service", "checkout-service"],
                "blast_radius_description": "All payment transactions affected, ~5000 users impacted",
                "reasoning": "Strong temporal correlation between deployment and error onset. Code diff shows changes to connection handling. Similar pattern seen in INC-2024-0892."
            }
        }


class Synthesis(BaseModel):
    """
    Intermediate synthesis during investigation.
    
    Updated after each agent completes.
    """
    
    # Confidence
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall investigation confidence"
    )
    
    # Hypotheses (ranked)
    hypotheses: List[RootCauseHypothesis] = Field(
        default_factory=list,
        description="Current root cause hypotheses"
    )
    
    # Timeline
    timeline: List[dict] = Field(
        default_factory=list,
        description="Incident timeline built from findings"
    )
    
    # Blast Radius
    blast_radius: dict = Field(
        default_factory=dict,
        description="Current blast radius assessment"
    )
    
    # Next Steps
    next_recommended_agent: Optional[str] = Field(
        default=None,
        description="Recommended next agent to call"
    )
    investigation_notes: str = Field(
        default="",
        description="Notes for next investigation step"
    )
    
    # Control
    should_continue: bool = Field(
        default=True,
        description="Should investigation continue?"
    )
    stop_reason: Optional[str] = Field(
        default=None,
        description="Reason for stopping if should_continue is False"
    )
