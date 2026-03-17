"""
Triage Agent

Classifies alerts and determines investigation strategy.
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

from incidentagent.llm.client import LLMClient, get_llm_client
from incidentagent.llm.prompts import TriagePrompt
from incidentagent.schemas.alert import UnifiedAlert
from incidentagent.schemas.triage import (
    AlertType,
    TriageResult,
    get_investigation_priority,
)

logger = structlog.get_logger()


class TriageAgent:
    """
    Triage Agent - First step in investigation pipeline.

    Responsibilities:
    - Classify alert type (error_rate, latency, crash, etc.)
    - Assess severity
    - Identify affected services
    - Determine investigation priority queue

    Uses LLM classification when available; falls back to keyword-based
    rule matching when no API token is configured or the LLM call fails.
    """

    def __init__(self):
        self.logger = logger.bind(agent="TriageAgent")

    @trace_tool("triage-classify")
    async def triage(self, alert: UnifiedAlert) -> TriageResult:
        """
        Triage an alert and determine investigation strategy.

        Attempts LLM classification first.  If the LLM is unavailable or
        returns an unusable result, falls back to rule-based classification.

        Args:
            alert: The alert to triage.

        Returns:
            TriageResult with classification and priority queue.
        """
        self.logger.info("triage_started", alert_id=alert.id)

        llm = get_llm_client()

        alert_type: AlertType
        confidence: float
        reasoning: str
        affected_services: List[str]
        potential_blast_radius: Optional[str]
        requires_immediate: bool

        if llm.is_available:
            llm_result = await self._llm_classify(llm, alert)
            if llm_result:
                raw_type = llm_result.get("alert_type", "unknown")
                try:
                    alert_type = AlertType(raw_type)
                except ValueError:
                    alert_type = AlertType.UNKNOWN

                confidence = float(llm_result.get("confidence", 0.8))
                reasoning = llm_result.get("reasoning", "LLM classification")
                affected_services = llm_result.get(
                    "affected_services",
                    [alert.service] if alert.service else [],
                )
                potential_blast_radius = llm_result.get("potential_blast_radius")
                requires_immediate = bool(
                    llm_result.get(
                        "requires_immediate_attention",
                        alert.severity == "critical",
                    )
                )

                # Honour priority_agents from LLM if provided and non-empty
                llm_priority = llm_result.get("priority_agents")
                if llm_priority and isinstance(llm_priority, list) and llm_priority:
                    priority_queue = llm_priority
                else:
                    priority_queue = get_investigation_priority(alert_type)

                self.logger.info(
                    "triage_llm_classification",
                    alert_type=alert_type,
                    confidence=confidence,
                )

                result = TriageResult(
                    alert_id=alert.id,
                    triage_id=f"triage-{uuid.uuid4().hex[:8]}",
                    severity=alert.severity,
                    alert_type=alert_type,
                    affected_services=affected_services,
                    affected_environment=alert.environment or "production",
                    potential_blast_radius=potential_blast_radius,
                    priority_queue=priority_queue,
                    classification_confidence=confidence,
                    classification_reasoning=reasoning,
                    triaged_at=datetime.utcnow(),
                    requires_immediate_attention=requires_immediate,
                )

                self.logger.info(
                    "triage_completed",
                    source="llm",
                    alert_type=alert_type,
                    priority_queue=priority_queue,
                )
                return result

        # Fallback: rule-based classification
        self.logger.info("triage_using_rule_based_fallback", alert_id=alert.id)
        alert_type = self._classify_alert_type(alert)
        priority_queue = get_investigation_priority(alert_type)

        result = TriageResult(
            alert_id=alert.id,
            triage_id=f"triage-{uuid.uuid4().hex[:8]}",
            severity=alert.severity,
            alert_type=alert_type,
            affected_services=[alert.service] if alert.service else [],
            affected_environment=alert.environment or "production",
            priority_queue=priority_queue,
            classification_confidence=0.6,
            classification_reasoning=(
                f"Rule-based fallback: classified as {alert_type.value} "
                "from alert title keyword matching"
            ),
            triaged_at=datetime.utcnow(),
            requires_immediate_attention=alert.severity == "critical",
        )

        self.logger.info(
            "triage_completed",
            source="rule_based",
            alert_type=alert_type,
            priority_queue=priority_queue,
        )
        return result

    @trace_llm("triage-llm-classify")
    async def _llm_classify(
        self,
        llm: LLMClient,
        alert: UnifiedAlert,
    ) -> Optional[Dict]:
        """Call the LLM to classify the alert.

        Args:
            llm: Initialised LLMClient instance.
            alert: The alert to classify.

        Returns:
            Parsed JSON dict from the LLM, or None on failure.
        """
        prompt = TriagePrompt.format(
            alert_title=alert.title,
            alert_description=alert.description or "",
            severity=alert.severity,
            service=alert.service or "unknown",
            labels=alert.labels or {},
        )
        return await llm.complete_json(prompt, system_prompt=TriagePrompt.SYSTEM)
    
    def _classify_alert_type(self, alert: UnifiedAlert) -> AlertType:
        """
        Classify alert type based on title and labels.
        
        TODO: Replace with LLM classification.
        """
        title_lower = alert.title.lower()
        
        # Simple keyword matching
        if any(kw in title_lower for kw in ["error rate", "error_rate", "5xx", "4xx", "exception"]):
            return AlertType.ERROR_RATE
        elif any(kw in title_lower for kw in ["latency", "slow", "timeout", "response time"]):
            return AlertType.LATENCY
        elif any(kw in title_lower for kw in ["crash", "restart", "oom", "killed", "terminated"]):
            return AlertType.CRASH
        elif any(kw in title_lower for kw in ["cpu", "memory", "disk", "resource"]):
            return AlertType.RESOURCE
        elif any(kw in title_lower for kw in ["database", "redis", "kafka", "dependency"]):
            return AlertType.DEPENDENCY
        elif any(kw in title_lower for kw in ["config", "secret", "environment"]):
            return AlertType.CONFIG
        else:
            return AlertType.UNKNOWN
