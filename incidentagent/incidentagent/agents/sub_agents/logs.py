"""
Logs Agent

Searches application logs for errors and patterns.
"""

import re
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

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

# Optional ML classifier for log anomaly detection
_log_classifier = None


def _get_classifier():
    """Lazy-load the log anomaly classifier (if model is trained)."""
    global _log_classifier
    if _log_classifier is None:
        try:
            from models.log_classifier import LogClassifier
            _log_classifier = LogClassifier()
        except Exception:
            _log_classifier = False  # sentinel: tried and failed
    return _log_classifier if _log_classifier is not False else None


@register_agent
class LogsAgent(SubAgent):
    """
    Logs Agent - Searches logs for errors and anomalies.

    Research shows logs are primary source for 73% of root cause identification.

    Data sources:
    - Elasticsearch
    - Loki
    - CloudWatch Logs
    """

    name = "LogsAgent"
    description = "Searches application logs for errors, exceptions, and patterns"

    @trace_tool("logs-investigate")
    async def investigate(self, context: Dict[str, Any]) -> AgentEvidence:
        """Search logs for relevant errors and patterns."""
        started_at = datetime.utcnow()
        alert = context.get("alert", {})
        service = alert.get("service")
        incident_time = self._parse_incident_time(alert)
        previous_findings = context.get("previous_findings", [])

        findings: List[Finding] = []
        errors: List[str] = []

        try:
            error_findings = await self._analyze_error_logs(service, incident_time)
            findings.extend(error_findings)
        except Exception as e:
            errors.append(f"Error log analysis failed: {e}")
            self.logger.error("error_log_analysis_failed", error=str(e))

        try:
            pattern_findings = await self._analyze_error_patterns(service, incident_time)
            findings.extend(pattern_findings)
        except Exception as e:
            errors.append(f"Error pattern analysis failed: {e}")
            self.logger.error("error_pattern_analysis_failed", error=str(e))

        try:
            downstream_findings = await self._check_downstream_impact(service, incident_time)
            findings.extend(downstream_findings)
        except Exception as e:
            errors.append(f"Downstream impact check failed: {e}")
            self.logger.error("downstream_impact_check_failed", error=str(e))

        self._cross_reference_with_deploys(findings, previous_findings)

        # Enrich findings with ML classification (if model is available)
        self._classify_findings(findings)

        confidence = self._calculate_confidence(findings)

        next_context = None
        if findings:
            error_finding = next(
                (f for f in findings if f.type == FindingType.ERROR_SIGNATURE),
                findings[0],
            )
            next_context = (
                f"Check resource metrics for {service or 'affected service'}. "
                f"Key error: {error_finding.title}. "
                f"Look for resource exhaustion correlating with errors."
            )

        return self._build_evidence(
            findings=findings,
            context=context,
            confidence=confidence,
            confidence_reasoning=self._explain_confidence(findings),
            started_at=started_at,
            suggests_next_agent="MetricsAgent",
            next_agent_context=next_context,
            errors=errors,
        )

    def get_tools(self) -> List[Dict[str, Any]]:
        """Return tools for Gradient function calling."""
        return [
            {
                "name": "search_logs",
                "description": "Search Elasticsearch for log entries",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "service": {"type": "string", "description": "Service name"},
                        "level": {
                            "type": "string",
                            "enum": ["error", "warn", "info", "debug"],
                            "description": "Log level filter",
                        },
                        "start_time": {"type": "string", "description": "Start time (ISO format)"},
                        "end_time": {"type": "string", "description": "End time (ISO format)"},
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "get_error_count",
                "description": "Get error count aggregation over time",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "service": {"type": "string", "description": "Service name"},
                        "interval": {"type": "string", "description": "Bucket interval (e.g., 5m, 1h)"},
                    },
                    "required": ["service"],
                },
            },
        ]

    def _parse_incident_time(self, alert: Dict[str, Any]) -> datetime:
        """Parse incident time from alert."""
        fired_at = alert.get("fired_at", datetime.utcnow().isoformat())
        if isinstance(fired_at, str):
            return datetime.fromisoformat(fired_at.replace("Z", "+00:00"))
        return fired_at

    @trace_retriever("logs-error-search")
    async def _analyze_error_logs(
        self,
        service: Optional[str],
        incident_time: datetime,
    ) -> List[Finding]:
        """Analyze error logs for distinct error signatures."""
        logs = mock_data.get_error_logs(service=service)
        findings: List[Finding] = []
        seen_signatures: Dict[str, Dict[str, Any]] = {}

        for log_entry in logs:
            if log_entry.get("level") not in ("ERROR", "FATAL"):
                continue

            signature = self._extract_error_signature(log_entry)

            if signature in seen_signatures:
                seen_signatures[signature]["count"] += 1
                seen_signatures[signature]["pods"].add(log_entry.get("pod", "unknown"))
                continue

            seen_signatures[signature] = {
                "entry": log_entry,
                "count": 1,
                "pods": {log_entry.get("pod", "unknown")},
            }

        for signature, data in seen_signatures.items():
            entry = data["entry"]
            pod_count = len(data["pods"])
            occurrence_count = data["count"]

            log_time = datetime.fromisoformat(entry["@timestamp"])
            if log_time.tzinfo is None:
                log_time = log_time.replace(tzinfo=timezone.utc)

            confidence = self._score_error_signature(
                entry, pod_count, occurrence_count,
            )

            severity = Severity.CRITICAL if pod_count > 1 else Severity.HIGH

            findings.append(Finding(
                id=self._generate_finding_id(),
                type=FindingType.ERROR_SIGNATURE,
                title=f"Error: {self._truncate(entry['message'], 80)}",
                description=(
                    f"Error signature found across {pod_count} pod(s) "
                    f"with {occurrence_count} occurrence(s). "
                    f"Logger: {entry.get('logger', 'unknown')}. "
                    f"Stack trace root: {self._extract_root_cause_line(entry.get('stack_trace', ''))}"
                ),
                severity=severity,
                confidence=confidence,
                timestamp=log_time,
                time_delta_from_incident=self._format_relative_time(log_time, incident_time),
                affected_services=[entry.get("service", service or "unknown")],
                evidence_source="elasticsearch",
                evidence_query=(
                    f'service:"{entry.get("service", "*")}" AND '
                    f'level:ERROR AND message:"{self._truncate(entry["message"], 40)}"'
                ),
                raw_evidence=(
                    f"[{entry['@timestamp']}] {entry['level']} "
                    f"{entry.get('logger', '')} - {entry['message']}"
                ),
                evidence_url=f"http://kibana:5601/app/discover#/?_q=(query:'{entry.get('trace_id', '')}')",
                is_actionable=True,
                suggested_action=f"Investigate {entry.get('logger', 'source')}: {signature}",
                metadata={
                    "error_signature": signature,
                    "pod_count": pod_count,
                    "occurrence_count": occurrence_count,
                    "logger": entry.get("logger"),
                    "trace_id": entry.get("trace_id"),
                    "stack_trace_preview": entry.get("stack_trace", "")[:200],
                },
            ))

        return findings

    async def _analyze_error_patterns(
        self,
        service: Optional[str],
        incident_time: datetime,
    ) -> List[Finding]:
        """Analyze error count patterns for anomalies."""
        error_counts = mock_data.get_log_error_count(service or "payment-service")
        findings: List[Finding] = []

        buckets = error_counts.get("buckets", [])
        if len(buckets) < 3:
            return findings

        baseline_buckets = [b for b in buckets[:10] if b["count"] > 0]
        baseline_avg = (
            sum(b["count"] for b in baseline_buckets) / len(baseline_buckets)
            if baseline_buckets else 1
        )

        spike_start = None
        peak_count = 0
        for bucket in buckets:
            if bucket["count"] > baseline_avg * 5 and spike_start is None:
                spike_start = bucket["timestamp"]
            if bucket["count"] > peak_count:
                peak_count = bucket["count"]

        if spike_start is None:
            return findings

        spike_time = datetime.fromisoformat(spike_start)
        if spike_time.tzinfo is None:
            spike_time = spike_time.replace(tzinfo=timezone.utc)

        spike_ratio = peak_count / max(baseline_avg, 1)
        confidence = min(0.90, 0.5 + (spike_ratio / 100))

        findings.append(Finding(
            id=self._generate_finding_id(),
            type=FindingType.ANOMALY,
            title=f"Error rate spike: {spike_ratio:.0f}x above baseline",
            description=(
                f"Error count spiked from baseline avg of {baseline_avg:.1f}/bucket "
                f"to peak of {peak_count}/bucket ({spike_ratio:.0f}x increase). "
                f"Spike started at {spike_start}. "
                f"Total errors in window: {error_counts.get('total_errors', 0)}."
            ),
            severity=Severity.CRITICAL if spike_ratio > 10 else Severity.HIGH,
            confidence=confidence,
            timestamp=spike_time,
            time_delta_from_incident=self._format_relative_time(spike_time, incident_time),
            affected_services=[service or "unknown"],
            evidence_source="elasticsearch",
            evidence_query=f'service:"{service}" | stats count by @timestamp interval=5m',
            raw_evidence=(
                f"baseline_avg={baseline_avg:.1f}, peak={peak_count}, "
                f"ratio={spike_ratio:.1f}x, total={error_counts.get('total_errors', 0)}"
            ),
            is_actionable=False,
            suggested_action="Investigate error signatures to identify root cause",
            metadata={
                "baseline_avg": baseline_avg,
                "peak_count": peak_count,
                "spike_ratio": spike_ratio,
                "spike_start": spike_start,
                "total_errors": error_counts.get("total_errors", 0),
            },
        ))

        return findings

    async def _check_downstream_impact(
        self,
        service: Optional[str],
        incident_time: datetime,
    ) -> List[Finding]:
        """Check for downstream service impact in logs."""
        logs = mock_data.get_error_logs(service=service)
        findings: List[Finding] = []

        affected_services: Dict[str, List[Dict]] = {}
        for log_entry in logs:
            log_service = log_entry.get("service", "")
            if log_service != service and log_service:
                if log_service not in affected_services:
                    affected_services[log_service] = []
                affected_services[log_service].append(log_entry)

        for downstream_service, entries in affected_services.items():
            first_entry = entries[0]
            log_time = datetime.fromisoformat(first_entry["@timestamp"])
            if log_time.tzinfo is None:
                log_time = log_time.replace(tzinfo=timezone.utc)

            findings.append(Finding(
                id=self._generate_finding_id(),
                type=FindingType.CORRELATION,
                title=f"Downstream impact: {downstream_service} reporting errors",
                description=(
                    f"Service {downstream_service} is experiencing errors "
                    f"likely caused by {service or 'upstream service'}. "
                    f"{len(entries)} related log entries found. "
                    f"First error: {first_entry['message']}"
                ),
                severity=Severity.MEDIUM,
                confidence=0.70,
                timestamp=log_time,
                time_delta_from_incident=self._format_relative_time(log_time, incident_time),
                affected_services=[downstream_service, service or "unknown"],
                evidence_source="elasticsearch",
                evidence_query=f'service:"{downstream_service}" AND level:(ERROR OR WARN)',
                raw_evidence=f"[{first_entry['@timestamp']}] {first_entry['message']}",
                is_actionable=False,
                suggested_action=f"Fix upstream {service} to resolve downstream {downstream_service} issues",
                metadata={
                    "downstream_service": downstream_service,
                    "entry_count": len(entries),
                    "upstream_service": service,
                },
            ))

        return findings

    def _cross_reference_with_deploys(
        self,
        log_findings: List[Finding],
        previous_findings: List[Any],
    ) -> None:
        """Boost confidence of findings that correlate with deployment findings."""
        deploy_finding_ids = []
        for pf in previous_findings:
            if hasattr(pf, "findings"):
                for f in pf.findings:
                    if f.type == FindingType.DEPLOYMENT:
                        deploy_finding_ids.append(f.id)

        if not deploy_finding_ids:
            return

        for finding in log_findings:
            if finding.type == FindingType.ERROR_SIGNATURE:
                finding.related_findings.extend(deploy_finding_ids)
                finding.correlation_strength = 0.85

    def _classify_findings(self, findings: List[Finding]) -> None:
        """Enrich findings with ML-based log classification when available."""
        classifier = _get_classifier()
        if classifier is None:
            return

        for finding in findings:
            if finding.raw_evidence:
                try:
                    result = classifier.classify(finding.raw_evidence)
                    finding.metadata["ml_category"] = result["category"]
                    finding.metadata["ml_confidence"] = result["confidence"]
                except Exception:
                    pass

    def _extract_error_signature(self, log_entry: Dict[str, Any]) -> str:
        """Extract a normalized error signature from a log entry."""
        message = log_entry.get("message", "")
        exception_match = re.search(
            r'([\w.]+(?:Exception|Error|Failure))[:\s]',
            message,
        )
        if exception_match:
            return exception_match.group(1)
        return message[:80]

    def _extract_root_cause_line(self, stack_trace: str) -> str:
        """Extract the most relevant line from a stack trace."""
        if not stack_trace:
            return "No stack trace available"

        lines = stack_trace.strip().split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("at ") and "java.lang" not in line and "org.springframework" not in line:
                return line

        return lines[0][:100] if lines else "No stack trace available"

    def _score_error_signature(
        self,
        entry: Dict[str, Any],
        pod_count: int,
        occurrence_count: int,
    ) -> float:
        """Score an error signature based on severity indicators."""
        base = 0.50

        if pod_count > 1:
            base += 0.15

        if occurrence_count > 2:
            base += 0.10

        message = entry.get("message", "").lower()
        if any(kw in message for kw in ["null", "connection", "pool", "exhausted", "timeout"]):
            base += 0.10

        if entry.get("stack_trace"):
            base += 0.05

        return min(0.92, base)

    def _calculate_confidence(self, findings: List[Finding]) -> float:
        """Calculate overall confidence from all findings."""
        if not findings:
            return 0.20

        error_findings = [f for f in findings if f.type == FindingType.ERROR_SIGNATURE]
        anomaly_findings = [f for f in findings if f.type == FindingType.ANOMALY]

        base = max(f.confidence for f in findings)

        if error_findings and anomaly_findings:
            base = min(0.95, base + 0.08)

        if len(error_findings) > 1:
            base = min(0.95, base + 0.05)

        return round(base, 2)

    def _explain_confidence(self, findings: List[Finding]) -> str:
        """Explain confidence calculation."""
        if not findings:
            return "No relevant log entries found in the investigation window"

        error_count = sum(1 for f in findings if f.type == FindingType.ERROR_SIGNATURE)
        anomaly_count = sum(1 for f in findings if f.type == FindingType.ANOMALY)
        correlation_count = sum(1 for f in findings if f.type == FindingType.CORRELATION)

        parts = []
        if error_count:
            parts.append(f"{error_count} distinct error signature(s)")
        if anomaly_count:
            parts.append(f"{anomaly_count} error rate anomaly(ies)")
        if correlation_count:
            parts.append(f"{correlation_count} downstream impact(s)")

        top = max(findings, key=lambda f: f.confidence)
        return (
            f"Found {', '.join(parts)}. "
            f"Top signal: {top.title} (confidence: {top.confidence:.0%})"
        )

    def _truncate(self, text: str, max_len: int) -> str:
        """Truncate text with ellipsis."""
        if len(text) <= max_len:
            return text
        return text[:max_len - 3] + "..."

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
