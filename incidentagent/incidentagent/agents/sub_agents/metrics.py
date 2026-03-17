"""
Metrics Agent

Queries metrics for anomalies and resource issues.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from incidentagent.agents.base import SubAgent, register_agent
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


# Metric queries to run for each alert type
METRIC_QUERIES = {
    "error_rate": ["error_rate", "latency", "connections", "cpu", "memory"],
    "latency": ["latency", "cpu", "memory", "connections", "error_rate"],
    "crash": ["memory", "cpu", "error_rate"],
    "resource": ["cpu", "memory", "connections"],
}

DEFAULT_QUERIES = ["error_rate", "cpu", "memory", "latency", "connections"]


@register_agent
class MetricsAgent(SubAgent):
    """
    Metrics Agent - Analyzes metrics for anomalies.

    Data sources:
    - Prometheus
    - Datadog
    - CloudWatch Metrics
    """

    name = "MetricsAgent"
    description = "Analyzes metrics for resource exhaustion, latency spikes, anomalies"

    @trace_tool("metrics-investigate")
    async def investigate(self, context: Dict[str, Any]) -> AgentEvidence:
        """Analyze metrics around incident time."""
        started_at = datetime.utcnow()
        alert = context.get("alert", {})
        service = alert.get("service")
        incident_time = self._parse_incident_time(alert)
        alert_type = context.get("alert_type", alert.get("alert_type", "error_rate"))

        findings: List[Finding] = []
        errors: List[str] = []

        queries = METRIC_QUERIES.get(alert_type, DEFAULT_QUERIES)

        for query_key in queries:
            try:
                metric_findings = await self._analyze_metric(
                    query_key, service, incident_time,
                )
                findings.extend(metric_findings)
            except Exception as e:
                errors.append(f"Metric query '{query_key}' failed: {e}")
                self.logger.error("metric_query_failed", query=query_key, error=str(e))

        findings.sort(key=lambda f: f.confidence, reverse=True)

        confidence = self._calculate_confidence(findings)

        next_context = None
        if findings:
            top = findings[0]
            next_context = (
                f"Check Kubernetes pod events for {service}. "
                f"Metrics show: {top.title}. "
                f"Look for OOMKills, restarts, and pod health issues."
            )

        return self._build_evidence(
            findings=findings,
            context=context,
            confidence=confidence,
            confidence_reasoning=self._explain_confidence(findings),
            started_at=started_at,
            suggests_next_agent="K8sAgent",
            next_agent_context=next_context,
            errors=errors,
        )

    def get_tools(self) -> List[Dict[str, Any]]:
        """Return tools for Gradient function calling."""
        return [
            {
                "name": "query_prometheus",
                "description": "Query Prometheus metrics using PromQL",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "PromQL query"},
                        "start": {"type": "string", "description": "Start time (ISO format)"},
                        "end": {"type": "string", "description": "End time (ISO format)"},
                        "step": {"type": "string", "description": "Query step (e.g., 5m)"},
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "check_metric_anomaly",
                "description": "Check if a metric shows anomalous behavior",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "metric": {"type": "string", "description": "Metric name"},
                        "service": {"type": "string", "description": "Service name"},
                        "threshold": {"type": "number", "description": "Anomaly threshold"},
                    },
                    "required": ["metric", "service"],
                },
            },
        ]

    def _parse_incident_time(self, alert: Dict[str, Any]) -> datetime:
        """Parse incident time from alert."""
        fired_at = alert.get("fired_at", datetime.utcnow().isoformat())
        if isinstance(fired_at, str):
            return datetime.fromisoformat(fired_at.replace("Z", "+00:00"))
        return fired_at

    @trace_retriever("metrics-prometheus-query")
    async def _analyze_metric(
        self,
        query_key: str,
        service: Optional[str],
        incident_time: datetime,
    ) -> List[Finding]:
        """Analyze a single metric type for anomalies."""
        metric_data = mock_data.get_prometheus_metrics(query=query_key, service=service)

        if not metric_data.get("is_anomalous"):
            return []

        anomaly_type = metric_data.get("anomaly_type", "unknown")
        finding_type, severity, title, description = self._classify_anomaly(
            query_key, metric_data, anomaly_type,
        )

        values = metric_data.get("values", [])
        anomaly_start = self._detect_anomaly_start(values, metric_data)

        anomaly_time = incident_time
        if anomaly_start:
            anomaly_time = datetime.fromisoformat(anomaly_start)
            if anomaly_time.tzinfo is None:
                anomaly_time = anomaly_time.replace(tzinfo=timezone.utc)

        confidence = self._score_metric_anomaly(metric_data, anomaly_type)

        return [Finding(
            id=self._generate_finding_id(),
            type=finding_type,
            title=title,
            description=description,
            severity=severity,
            confidence=confidence,
            timestamp=anomaly_time,
            time_delta_from_incident=self._format_relative_time(anomaly_time, incident_time),
            affected_services=[service or metric_data.get("service", "unknown")],
            evidence_source="prometheus",
            evidence_query=f"{metric_data.get('metric', query_key)}{{service='{service}'}}",
            raw_evidence=self._format_raw_evidence(metric_data),
            is_actionable=anomaly_type in ("pool_exhaustion", "memory_leak_pattern"),
            suggested_action=self._suggest_action(query_key, metric_data),
            metadata={
                "metric_name": metric_data.get("metric"),
                "anomaly_type": anomaly_type,
                "current_value": metric_data.get("current"),
                "threshold": metric_data.get("threshold"),
                "usage_percent": metric_data.get("usage_percent"),
                "values_timeline": values[-3:] if values else [],
            },
        )]

    def _classify_anomaly(
        self,
        query_key: str,
        metric_data: Dict[str, Any],
        anomaly_type: str,
    ) -> tuple:
        """Classify the anomaly into finding type, severity, title, and description."""
        if query_key == "cpu":
            current = metric_data.get("current", 0)
            threshold = metric_data.get("threshold", 0.80)
            return (
                FindingType.RESOURCE_EXHAUSTION,
                Severity.CRITICAL if current > 0.90 else Severity.HIGH,
                f"CPU usage at {current:.0%} (threshold: {threshold:.0%})",
                (
                    f"CPU usage has been steadily increasing and is now at {current:.0%}, "
                    f"exceeding the {threshold:.0%} threshold. "
                    f"Pattern: {anomaly_type}. This indicates compute resource pressure."
                ),
            )

        if query_key == "memory":
            usage_pct = metric_data.get("usage_percent", 0)
            current = metric_data.get("current", 0)
            limit = metric_data.get("limit", 0)
            return (
                FindingType.RESOURCE_EXHAUSTION,
                Severity.CRITICAL if usage_pct > 90 else Severity.HIGH,
                f"Memory usage at {usage_pct:.1f}% ({current / 1_048_576:.0f}MB / {limit / 1_048_576:.0f}MB)",
                (
                    f"Memory usage is at {usage_pct:.1f}% of limit. "
                    f"Pattern: {anomaly_type}. "
                    f"Memory has been growing steadily, suggesting a possible memory leak."
                ),
            )

        if query_key == "error_rate":
            current = metric_data.get("current", 0)
            threshold = metric_data.get("threshold", 0.05)
            return (
                FindingType.ANOMALY,
                Severity.CRITICAL if current > 0.50 else Severity.HIGH,
                f"Error rate at {current:.0%} (threshold: {threshold:.0%})",
                (
                    f"HTTP 5xx error rate is at {current:.0%}, "
                    f"which is {current / threshold:.0f}x the {threshold:.0%} threshold. "
                    f"Pattern: {anomaly_type}."
                ),
            )

        if query_key == "latency":
            p99 = metric_data.get("current_p99", 0)
            baseline_p99 = metric_data.get("baseline_p99", 0)
            ratio = p99 / baseline_p99 if baseline_p99 > 0 else 0
            return (
                FindingType.ANOMALY,
                Severity.CRITICAL if ratio > 20 else Severity.HIGH,
                f"P99 latency at {p99:.1f}s (baseline: {baseline_p99:.2f}s, {ratio:.0f}x)",
                (
                    f"P99 latency has degraded from {baseline_p99:.2f}s baseline "
                    f"to {p99:.1f}s ({ratio:.0f}x increase). "
                    f"P50: {metric_data.get('current_p50', 'N/A')}s. "
                    f"Pattern: {anomaly_type}."
                ),
            )

        if query_key == "connections":
            current = metric_data.get("current", 0)
            max_pool = metric_data.get("max_pool_size", 0)
            usage_pct = metric_data.get("usage_percent", 0)
            return (
                FindingType.RESOURCE_EXHAUSTION,
                Severity.CRITICAL if usage_pct >= 100 else Severity.HIGH,
                f"Connection pool at {usage_pct:.0f}% ({current}/{max_pool})",
                (
                    f"Connection pool is at {usage_pct:.0f}% capacity "
                    f"({current}/{max_pool} active connections). "
                    f"Pattern: {anomaly_type}. "
                    f"Pool exhaustion causes connection timeouts and request failures."
                ),
            )

        return (
            FindingType.ANOMALY,
            Severity.MEDIUM,
            f"Anomaly detected in {query_key}",
            f"Metric {query_key} shows anomalous behavior: {anomaly_type}",
        )

    def _detect_anomaly_start(
        self,
        values: List[Dict[str, Any]],
        metric_data: Dict[str, Any],
    ) -> Optional[str]:
        """Detect when the anomaly started from the values timeline."""
        if not values or len(values) < 2:
            return None

        threshold = metric_data.get("threshold")
        if threshold is not None:
            for val in values:
                if val["value"] > threshold:
                    return val["timestamp"]

        for i in range(1, len(values)):
            prev = values[i - 1]["value"]
            curr = values[i]["value"]
            if prev > 0 and curr / prev > 1.5:
                return values[i]["timestamp"]

        return values[-1]["timestamp"]

    def _score_metric_anomaly(
        self,
        metric_data: Dict[str, Any],
        anomaly_type: str,
    ) -> float:
        """Score the anomaly based on severity and type."""
        base = 0.50

        usage_pct = metric_data.get("usage_percent", 0)
        if usage_pct >= 100:
            base = 0.88
        elif usage_pct >= 90:
            base = 0.78
        elif usage_pct >= 80:
            base = 0.65

        threshold = metric_data.get("threshold")
        current = metric_data.get("current")
        if threshold and current and threshold > 0:
            ratio = current / threshold
            if ratio > 10:
                base = max(base, 0.85)
            elif ratio > 5:
                base = max(base, 0.75)
            elif ratio > 2:
                base = max(base, 0.65)

        if anomaly_type == "pool_exhaustion":
            base = max(base, 0.88)
        elif anomaly_type == "memory_leak_pattern":
            base = max(base, 0.80)
        elif anomaly_type == "spike":
            base = max(base, 0.75)

        return min(0.92, base)

    def _format_raw_evidence(self, metric_data: Dict[str, Any]) -> str:
        """Format metric data as raw evidence string."""
        parts = [f"metric={metric_data.get('metric', 'unknown')}"]

        if "current" in metric_data:
            parts.append(f"current={metric_data['current']}")
        if "threshold" in metric_data:
            parts.append(f"threshold={metric_data['threshold']}")
        if "usage_percent" in metric_data:
            parts.append(f"usage={metric_data['usage_percent']}%")
        if "max_pool_size" in metric_data:
            parts.append(f"pool_max={metric_data['max_pool_size']}")

        parts.append(f"anomaly_type={metric_data.get('anomaly_type', 'unknown')}")
        return ", ".join(parts)

    def _suggest_action(self, query_key: str, metric_data: Dict[str, Any]) -> str:
        """Suggest remediation action based on metric type."""
        actions = {
            "cpu": "Scale up replicas or increase CPU limits",
            "memory": "Investigate memory leak, consider increasing memory limits or restarting pods",
            "error_rate": "Check application logs for error root cause",
            "latency": "Check downstream dependencies and resource utilization",
            "connections": "Increase connection pool size or fix connection leak",
        }
        return actions.get(query_key, "Investigate metric anomaly")

    def _calculate_confidence(self, findings: List[Finding]) -> float:
        """Calculate overall confidence from all metric findings."""
        if not findings:
            return 0.20

        base = max(f.confidence for f in findings)

        resource_findings = [f for f in findings if f.type == FindingType.RESOURCE_EXHAUSTION]
        anomaly_findings = [f for f in findings if f.type == FindingType.ANOMALY]

        if resource_findings and anomaly_findings:
            base = min(0.95, base + 0.05)

        if len(findings) >= 3:
            base = min(0.95, base + 0.03)

        return round(base, 2)

    def _explain_confidence(self, findings: List[Finding]) -> str:
        """Explain confidence calculation."""
        if not findings:
            return "No metric anomalies detected in the investigation window"

        resource_count = sum(1 for f in findings if f.type == FindingType.RESOURCE_EXHAUSTION)
        anomaly_count = sum(1 for f in findings if f.type == FindingType.ANOMALY)

        parts = []
        if resource_count:
            parts.append(f"{resource_count} resource exhaustion signal(s)")
        if anomaly_count:
            parts.append(f"{anomaly_count} metric anomaly(ies)")

        top = max(findings, key=lambda f: f.confidence)
        return (
            f"Found {' and '.join(parts)}. "
            f"Strongest signal: {top.title} (confidence: {top.confidence:.0%})"
        )

    def _format_relative_time(self, event_time: datetime, incident_time: datetime) -> str:
        """Format time relative to incident."""
        event_aware = event_time if event_time.tzinfo else event_time.replace(tzinfo=timezone.utc)
        incident_aware = incident_time if incident_time.tzinfo else incident_time.replace(tzinfo=timezone.utc)

        diff_seconds = (incident_aware - event_aware).total_seconds()
        prefix = "-" if diff_seconds > 0 else "+"
        abs_seconds = abs(diff_seconds)
        hours = int(abs_seconds // 3600)
        minutes = int((abs_seconds % 3600) // 60)

        if hours > 0:
            return f"{prefix}{hours}h {minutes}m"
        return f"{prefix}{minutes}m"
