"""
Alert Schema

Unified alert format normalized from multiple sources.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class AlertSource(str, Enum):
    """Supported alert sources"""
    PROMETHEUS = "prometheus"
    PAGERDUTY = "pagerduty"
    WEBHOOK = "webhook"
    MANUAL = "manual"


class UnifiedAlert(BaseModel):
    """
    Normalized alert format from any source.
    
    All alert adapters convert their raw format to this schema.
    """
    
    # Identity
    id: str = Field(..., description="Unique alert ID")
    source: AlertSource = Field(..., description="Source system")
    
    # Content
    title: str = Field(..., description="Alert title/summary")
    description: str = Field(default="", description="Detailed description")
    severity: Literal["critical", "high", "medium", "low"] = Field(
        default="medium",
        description="Alert severity level"
    )
    
    # Context
    service: Optional[str] = Field(
        default=None,
        description="Affected service name"
    )
    environment: Optional[str] = Field(
        default="production",
        description="Environment (production, staging, dev)"
    )
    namespace: Optional[str] = Field(
        default=None,
        description="Kubernetes namespace if applicable"
    )
    labels: Dict[str, str] = Field(
        default_factory=dict,
        description="Additional labels/tags"
    )
    annotations: Dict[str, str] = Field(
        default_factory=dict,
        description="Additional annotations"
    )
    
    # Timing
    fired_at: datetime = Field(..., description="When alert fired")
    received_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When we received it"
    )
    
    # External references
    external_url: Optional[str] = Field(
        default=None,
        description="URL to alert in source system"
    )
    external_incident_id: Optional[str] = Field(
        default=None,
        description="Incident ID in external system (e.g., PagerDuty)"
    )
    
    # Raw data
    raw_payload: Dict = Field(
        default_factory=dict,
        description="Original alert payload for reference"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "alert-12345",
                "source": "prometheus",
                "title": "High error rate on payment-service",
                "description": "Error rate exceeded 5% threshold for 5 minutes",
                "severity": "critical",
                "service": "payment-service",
                "environment": "production",
                "namespace": "payments",
                "labels": {
                    "team": "payments",
                    "tier": "critical"
                },
                "fired_at": "2026-02-21T03:15:00Z",
                "received_at": "2026-02-21T03:15:05Z",
                "raw_payload": {}
            }
        }


class AlertBatch(BaseModel):
    """Multiple alerts (for batch processing)"""
    
    alerts: List[UnifiedAlert]
    batch_id: str
    received_at: datetime = Field(default_factory=datetime.utcnow)
