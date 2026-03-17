"""
Kubernetes Agent

Checks Kubernetes events and pod status.
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


# Event severity mapping
EVENT_SEVERITY = {
    "OOMKilling": Severity.CRITICAL,
    "BackOff": Severity.HIGH,
    "Unhealthy": Severity.HIGH,
    "FailedScheduling": Severity.HIGH,
    "FailedMount": Severity.MEDIUM,
    "Pulling": Severity.INFO,
    "Pulled": Severity.INFO,
    "ScalingReplicaSet": Severity.INFO,
    "Created": Severity.INFO,
    "Started": Severity.INFO,
}


@register_agent
class K8sAgent(SubAgent):
    """
    K8s Agent - Analyzes Kubernetes events and pod status.

    Checks for:
    - Pod restarts
    - OOM kills
    - CrashLoopBackOff
    - Event warnings
    - Resource limits
    """

    name = "K8sAgent"
    description = "Analyzes Kubernetes events, pod status, restarts, OOM kills"

    @trace_tool("k8s-investigate")
    async def investigate(self, context: Dict[str, Any]) -> AgentEvidence:
        """Check Kubernetes for relevant events and pod issues."""
        started_at = datetime.utcnow()
        alert = context.get("alert", {})
        service = alert.get("service")
        namespace = alert.get("namespace")
        incident_time = self._parse_incident_time(alert)

        findings: List[Finding] = []
        errors: List[str] = []

        try:
            pod_findings = await self._analyze_pod_status(service, namespace, incident_time)
            findings.extend(pod_findings)
        except Exception as e:
            errors.append(f"Pod status analysis failed: {e}")
            self.logger.error("pod_status_analysis_failed", error=str(e))

        try:
            event_findings = await self._analyze_k8s_events(service, namespace, incident_time)
            findings.extend(event_findings)
        except Exception as e:
            errors.append(f"K8s events analysis failed: {e}")
            self.logger.error("k8s_events_analysis_failed", error=str(e))

        confidence = self._calculate_confidence(findings)

        next_context = None
        if findings:
            top = max(findings, key=lambda f: f.confidence)
            next_context = (
                f"Search runbooks for: {top.title}. "
                f"Kubernetes analysis shows pod issues for {service}."
            )

        return self._build_evidence(
            findings=findings,
            context=context,
            confidence=confidence,
            confidence_reasoning=self._explain_confidence(findings),
            started_at=started_at,
            suggests_next_agent="RunbookAgent",
            next_agent_context=next_context,
            errors=errors,
        )

    def get_tools(self) -> List[Dict[str, Any]]:
        """Return tools for Gradient function calling."""
        return [
            {
                "name": "get_pod_status",
                "description": "Get current status of pods for a service",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "service": {"type": "string", "description": "Service name"},
                        "namespace": {"type": "string", "description": "Kubernetes namespace"},
                    },
                    "required": ["namespace"],
                },
            },
            {
                "name": "get_pod_events",
                "description": "Get Kubernetes events for pods in a namespace",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "namespace": {"type": "string", "description": "Kubernetes namespace"},
                        "pod_name": {"type": "string", "description": "Specific pod name"},
                        "event_type": {
                            "type": "string",
                            "enum": ["Warning", "Normal"],
                            "description": "Event type filter",
                        },
                    },
                    "required": ["namespace"],
                },
            },
        ]

    def _parse_incident_time(self, alert: Dict[str, Any]) -> datetime:
        """Parse incident time from alert."""
        fired_at = alert.get("fired_at", datetime.utcnow().isoformat())
        if isinstance(fired_at, str):
            return datetime.fromisoformat(fired_at.replace("Z", "+00:00"))
        return fired_at

    @trace_retriever("k8s-pod-status")
    async def _analyze_pod_status(
        self,
        service: Optional[str],
        namespace: Optional[str],
        incident_time: datetime,
    ) -> List[Finding]:
        """Analyze pod status for issues."""
        pods = mock_data.get_k8s_pod_status(service=service, namespace=namespace)
        findings: List[Finding] = []

        crashing_pods = [p for p in pods if p["status"] == "CrashLoopBackOff"]
        restarting_pods = [p for p in pods if p.get("restarts", 0) > 0 and p["status"] != "CrashLoopBackOff"]
        not_ready_pods = [p for p in pods if not p.get("ready", True)]

        if crashing_pods:
            findings.append(self._build_crash_loop_finding(crashing_pods, incident_time))

        if restarting_pods:
            findings.append(self._build_restart_finding(restarting_pods, incident_time))

        oom_pods = [
            p for p in pods
            if p.get("last_restart_reason") == "OOMKilled"
        ]
        if oom_pods:
            findings.append(self._build_oom_finding(oom_pods, incident_time))

        return findings

    async def _analyze_k8s_events(
        self,
        service: Optional[str],
        namespace: Optional[str],
        incident_time: datetime,
    ) -> List[Finding]:
        """Analyze Kubernetes events for warning signals."""
        events = mock_data.get_k8s_events(service=service, namespace=namespace)
        findings: List[Finding] = []

        warning_events = [e for e in events if e["type"] == "Warning"]

        grouped: Dict[str, List[Dict]] = {}
        for event in warning_events:
            reason = event["reason"]
            if reason not in grouped:
                grouped[reason] = []
            grouped[reason].append(event)

        for reason, group in grouped.items():
            total_count = sum(e.get("count", 1) for e in group)
            affected_objects = list({e["object"] for e in group})

            most_recent = max(group, key=lambda e: e["timestamp"])
            event_time = datetime.fromisoformat(most_recent["timestamp"])
            if event_time.tzinfo is None:
                event_time = event_time.replace(tzinfo=timezone.utc)

            first_seen = min(group, key=lambda e: e.get("first_seen", e["timestamp"]))
            first_time = datetime.fromisoformat(first_seen.get("first_seen", first_seen["timestamp"]))
            if first_time.tzinfo is None:
                first_time = first_time.replace(tzinfo=timezone.utc)

            severity = EVENT_SEVERITY.get(reason, Severity.MEDIUM)
            if severity == Severity.INFO:
                continue

            confidence = self._score_k8s_event(reason, total_count, len(affected_objects))

            findings.append(Finding(
                id=self._generate_finding_id(),
                type=FindingType.POD_EVENT,
                title=f"K8s Warning: {reason} ({total_count} occurrences)",
                description=(
                    f"Kubernetes {reason} events detected across "
                    f"{len(affected_objects)} object(s). "
                    f"Total occurrences: {total_count}. "
                    f"Message: {most_recent['message']}. "
                    f"First seen: {first_seen.get('first_seen', 'unknown')}."
                ),
                severity=severity,
                confidence=confidence,
                timestamp=event_time,
                time_delta_from_incident=self._format_relative_time(event_time, incident_time),
                affected_services=[service or "unknown"],
                evidence_source="kubernetes",
                evidence_query=(
                    f"kubectl get events -n {namespace or 'default'} "
                    f"--field-selector reason={reason}"
                ),
                raw_evidence=(
                    f"type={most_recent['type']} reason={reason} "
                    f"object={most_recent['object']} count={total_count} "
                    f"message={most_recent['message']}"
                ),
                is_actionable=reason in ("OOMKilling", "BackOff"),
                suggested_action=self._suggest_event_action(reason),
                metadata={
                    "reason": reason,
                    "total_count": total_count,
                    "affected_objects": affected_objects,
                    "first_seen": first_seen.get("first_seen"),
                    "last_seen": most_recent["timestamp"],
                },
            ))

        return findings

    def _build_crash_loop_finding(
        self,
        pods: List[Dict[str, Any]],
        incident_time: datetime,
    ) -> Finding:
        """Build finding for CrashLoopBackOff pods."""
        total_restarts = sum(p.get("restarts", 0) for p in pods)
        pod_names = [p["name"] for p in pods]

        most_recent = max(pods, key=lambda p: p.get("last_restart_at", ""))
        restart_time = datetime.fromisoformat(most_recent["last_restart_at"])
        if restart_time.tzinfo is None:
            restart_time = restart_time.replace(tzinfo=timezone.utc)

        return Finding(
            id=self._generate_finding_id(),
            type=FindingType.POD_EVENT,
            title=f"CrashLoopBackOff: {len(pods)} pod(s) crashing",
            description=(
                f"{len(pods)} pod(s) in CrashLoopBackOff state with "
                f"{total_restarts} total restarts. "
                f"Last restart reason: {most_recent.get('last_restart_reason', 'unknown')}. "
                f"Affected pods: {', '.join(pod_names)}"
            ),
            severity=Severity.CRITICAL,
            confidence=0.88,
            timestamp=restart_time,
            time_delta_from_incident=self._format_relative_time(restart_time, incident_time),
            affected_services=[pods[0].get("name", "unknown").rsplit("-", 2)[0]],
            evidence_source="kubernetes",
            evidence_query=f"kubectl get pods -n {pods[0].get('namespace', 'default')} | grep CrashLoopBackOff",
            raw_evidence=(
                f"pods_crashing={len(pods)} total_restarts={total_restarts} "
                f"reason={most_recent.get('last_restart_reason', 'unknown')} "
                f"pods={', '.join(pod_names)}"
            ),
            is_actionable=True,
            suggested_action="Check pod logs and consider rollback if caused by recent deployment",
            metadata={
                "pod_count": len(pods),
                "total_restarts": total_restarts,
                "pod_names": pod_names,
                "last_restart_reason": most_recent.get("last_restart_reason"),
            },
        )

    def _build_restart_finding(
        self,
        pods: List[Dict[str, Any]],
        incident_time: datetime,
    ) -> Finding:
        """Build finding for pods with restarts."""
        total_restarts = sum(p.get("restarts", 0) for p in pods)

        most_recent = max(pods, key=lambda p: p.get("last_restart_at", ""))
        restart_time = datetime.fromisoformat(most_recent["last_restart_at"])
        if restart_time.tzinfo is None:
            restart_time = restart_time.replace(tzinfo=timezone.utc)

        return Finding(
            id=self._generate_finding_id(),
            type=FindingType.POD_EVENT,
            title=f"Pod restarts: {total_restarts} across {len(pods)} pod(s)",
            description=(
                f"{len(pods)} pod(s) experienced {total_restarts} total restarts. "
                f"Most recent reason: {most_recent.get('last_restart_reason', 'unknown')}. "
                f"Pods are currently {most_recent['status']}."
            ),
            severity=Severity.HIGH,
            confidence=0.72,
            timestamp=restart_time,
            time_delta_from_incident=self._format_relative_time(restart_time, incident_time),
            affected_services=[pods[0].get("name", "unknown").rsplit("-", 2)[0]],
            evidence_source="kubernetes",
            evidence_query=f"kubectl get pods -n {pods[0].get('namespace', 'default')} -o wide",
            raw_evidence=(
                f"restart_count={total_restarts} pod_count={len(pods)} "
                f"reason={most_recent.get('last_restart_reason', 'unknown')}"
            ),
            is_actionable=False,
            suggested_action="Monitor pod stability and check logs for restart cause",
            metadata={
                "pod_count": len(pods),
                "total_restarts": total_restarts,
                "restart_reason": most_recent.get("last_restart_reason"),
            },
        )

    def _build_oom_finding(
        self,
        pods: List[Dict[str, Any]],
        incident_time: datetime,
    ) -> Finding:
        """Build finding for OOMKilled pods."""
        pod_names = [p["name"] for p in pods]
        memory_limits = list({p.get("memory_limit", "unknown") for p in pods})

        most_recent = max(pods, key=lambda p: p.get("last_restart_at", ""))
        restart_time = datetime.fromisoformat(most_recent["last_restart_at"])
        if restart_time.tzinfo is None:
            restart_time = restart_time.replace(tzinfo=timezone.utc)

        return Finding(
            id=self._generate_finding_id(),
            type=FindingType.RESOURCE_EXHAUSTION,
            title=f"OOMKilled: {len(pods)} pod(s) killed for exceeding memory limits",
            description=(
                f"{len(pods)} pod(s) were OOMKilled (Out of Memory). "
                f"Memory limit: {', '.join(memory_limits)}. "
                f"This indicates the application is consuming more memory than allocated, "
                f"possibly due to a memory leak. "
                f"Affected pods: {', '.join(pod_names)}"
            ),
            severity=Severity.CRITICAL,
            confidence=0.85,
            timestamp=restart_time,
            time_delta_from_incident=self._format_relative_time(restart_time, incident_time),
            affected_services=[pods[0].get("name", "unknown").rsplit("-", 2)[0]],
            evidence_source="kubernetes",
            evidence_query=f"kubectl describe pod {pods[0]['name']} -n {pods[0].get('namespace', 'default')}",
            raw_evidence=(
                f"OOMKilled pods={len(pods)} memory_limit={', '.join(memory_limits)} "
                f"pods={', '.join(pod_names)}"
            ),
            is_actionable=True,
            suggested_action=(
                f"Increase memory limit (current: {', '.join(memory_limits)}) "
                "or investigate memory leak. Consider rollback if caused by recent deployment."
            ),
            metadata={
                "pod_count": len(pods),
                "pod_names": pod_names,
                "memory_limits": memory_limits,
            },
        )

    def _score_k8s_event(self, reason: str, count: int, affected_objects: int) -> float:
        """Score a Kubernetes event based on severity indicators."""
        base_scores = {
            "OOMKilling": 0.85,
            "BackOff": 0.78,
            "Unhealthy": 0.70,
            "FailedScheduling": 0.65,
            "FailedMount": 0.55,
        }
        base = base_scores.get(reason, 0.50)

        if count > 5:
            base = min(0.92, base + 0.05)
        if affected_objects > 1:
            base = min(0.92, base + 0.05)

        return base

    def _suggest_event_action(self, reason: str) -> str:
        """Suggest action for a Kubernetes event type."""
        actions = {
            "OOMKilling": "Increase memory limits or investigate memory leak",
            "BackOff": "Check pod logs: kubectl logs <pod> --previous",
            "Unhealthy": "Check readiness/liveness probes and application health endpoint",
            "FailedScheduling": "Check node resources: kubectl describe nodes",
            "FailedMount": "Check PVC status and storage backend",
        }
        return actions.get(reason, "Investigate Kubernetes event")

    def _calculate_confidence(self, findings: List[Finding]) -> float:
        """Calculate overall confidence from all findings."""
        if not findings:
            return 0.20

        base = max(f.confidence for f in findings)

        has_crash = any("CrashLoop" in f.title for f in findings)
        has_oom = any("OOMKilled" in f.title for f in findings)

        if has_crash and has_oom:
            base = min(0.95, base + 0.07)

        return round(base, 2)

    def _explain_confidence(self, findings: List[Finding]) -> str:
        """Explain confidence calculation."""
        if not findings:
            return "No Kubernetes issues detected in the investigation window"

        pod_events = sum(1 for f in findings if f.type == FindingType.POD_EVENT)
        resource_issues = sum(1 for f in findings if f.type == FindingType.RESOURCE_EXHAUSTION)

        parts = []
        if pod_events:
            parts.append(f"{pod_events} pod event(s)")
        if resource_issues:
            parts.append(f"{resource_issues} resource issue(s)")

        top = max(findings, key=lambda f: f.confidence)
        return (
            f"Found {' and '.join(parts)}. "
            f"Most critical: {top.title} (confidence: {top.confidence:.0%})"
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
