"""
Triage Schema

Classification and routing results from Triage Agent.
"""

from datetime import datetime
from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class AlertType(str, Enum):
    """
    Alert classification types.
    
    Based on research: different alert types require different investigation strategies.
    """
    ERROR_RATE = "error_rate"       # High error percentage
    LATENCY = "latency"             # Slow response times
    CRASH = "crash"                 # Pod/service crashes, restarts
    RESOURCE = "resource"           # CPU/memory/disk exhaustion
    DEPENDENCY = "dependency"       # External service/database failures
    CONFIG = "config"               # Configuration/secret issues
    SECURITY = "security"           # Security-related alerts
    UNKNOWN = "unknown"             # Cannot classify


# Research-backed investigation priority by alert type
# Based on: 80% of incidents follow deployments within 1-4 hours
INVESTIGATION_PRIORITY = {
    AlertType.ERROR_RATE: ["DeployAgent", "LogsAgent", "MetricsAgent", "K8sAgent", "RunbookAgent", "MemoryAgent"],
    AlertType.LATENCY: ["MetricsAgent", "LogsAgent", "DeployAgent", "K8sAgent", "RunbookAgent", "MemoryAgent"],
    AlertType.CRASH: ["K8sAgent", "LogsAgent", "MetricsAgent", "DeployAgent", "RunbookAgent", "MemoryAgent"],
    AlertType.RESOURCE: ["MetricsAgent", "K8sAgent", "LogsAgent", "DeployAgent", "RunbookAgent", "MemoryAgent"],
    AlertType.DEPENDENCY: ["LogsAgent", "MetricsAgent", "DeployAgent", "K8sAgent", "RunbookAgent", "MemoryAgent"],
    AlertType.CONFIG: ["DeployAgent", "K8sAgent", "LogsAgent", "MetricsAgent", "RunbookAgent", "MemoryAgent"],
    AlertType.SECURITY: ["LogsAgent", "K8sAgent", "DeployAgent", "MetricsAgent", "RunbookAgent", "MemoryAgent"],
    AlertType.UNKNOWN: ["DeployAgent", "LogsAgent", "MetricsAgent", "K8sAgent", "RunbookAgent", "MemoryAgent"],
}


class TriageResult(BaseModel):
    """
    Output from Triage Agent.
    
    Contains classification and investigation plan.
    """
    
    # Reference
    alert_id: str = Field(..., description="ID of the triaged alert")
    triage_id: str = Field(..., description="Unique triage result ID")
    
    # Classification
    severity: Literal["critical", "high", "medium", "low"] = Field(
        ...,
        description="Assessed severity (may differ from alert)"
    )
    alert_type: AlertType = Field(
        ...,
        description="Classified alert type"
    )
    
    # Context
    affected_services: List[str] = Field(
        default_factory=list,
        description="List of affected services"
    )
    affected_environment: str = Field(
        default="production",
        description="Affected environment"
    )
    potential_blast_radius: Optional[str] = Field(
        default=None,
        description="Initial blast radius estimate"
    )
    
    # Investigation Plan
    priority_queue: List[str] = Field(
        ...,
        description="Ordered list of agents to call"
    )
    recommended_timeout: int = Field(
        default=300,
        description="Recommended investigation timeout in seconds"
    )
    
    # Classification Confidence
    classification_confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence in classification (0-1)"
    )
    classification_reasoning: str = Field(
        ...,
        description="Explanation for classification"
    )
    
    # Timing
    triaged_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When triage completed"
    )
    
    # Flags
    requires_immediate_attention: bool = Field(
        default=False,
        description="True if critical severity or known high-impact pattern"
    )
    similar_recent_alerts: int = Field(
        default=0,
        description="Count of similar alerts in last 24h"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "alert_id": "alert-12345",
                "triage_id": "triage-67890",
                "severity": "critical",
                "alert_type": "error_rate",
                "affected_services": ["payment-service", "checkout-service"],
                "affected_environment": "production",
                "potential_blast_radius": "All payment transactions",
                "priority_queue": ["DeployAgent", "LogsAgent", "MetricsAgent", "K8sAgent"],
                "recommended_timeout": 300,
                "classification_confidence": 0.92,
                "classification_reasoning": "High error rate with payment-related service indicates ERROR_RATE type. Severity critical due to payment processing impact.",
                "requires_immediate_attention": True,
                "similar_recent_alerts": 0
            }
        }


def get_investigation_priority(alert_type: AlertType) -> List[str]:
    """Get the investigation priority queue for an alert type."""
    return INVESTIGATION_PRIORITY.get(alert_type, INVESTIGATION_PRIORITY[AlertType.UNKNOWN])
