"""
Deploy Agent

Investigates recent deployments and code changes.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List

from incidentagent.agents.base import SubAgent, register_agent
from incidentagent.schemas.evidence import AgentEvidence, Finding, FindingType, Severity

try:
    from gradient_adk import trace_tool
except ImportError:
    def trace_tool(name):
        def decorator(fn):
            return fn
        return decorator

from . import mock_data


@register_agent
class DeployAgent(SubAgent):
    """
    Deploy Agent - Checks recent deployments and changes.

    Research shows 80% of incidents follow deployments within 1-4 hours.
    This agent prioritizes finding recent changes that correlate with the incident.

    Data sources:
    - Kubernetes deployments
    - Git commits/releases
    - ConfigMap changes
    - CI/CD pipelines
    """

    name = "DeployAgent"
    description = "Investigates recent deployments, releases, and configuration changes"

    @trace_tool("deploy-investigate")
    async def investigate(self, context: Dict[str, Any]) -> AgentEvidence:
        """
        Find recent deployments that may correlate with incident.

        Args:
            context: Investigation context

        Returns:
            Evidence about recent deployments
        """
        started_at = datetime.utcnow()
        alert = context.get("alert", {})
        service = alert.get("service")
        incident_time = self._parse_incident_time(alert)

        findings: List[Finding] = []
        errors: List[str] = []

        try:
            k8s_findings = await self._check_k8s_deployments(service, incident_time)
            findings.extend(k8s_findings)
        except Exception as e:
            errors.append(f"K8s deployment check failed: {e}")
            self.logger.error("k8s_deployment_check_failed", error=str(e))

        try:
            git_findings = await self._check_git_changes(service, incident_time)
            findings.extend(git_findings)
        except Exception as e:
            errors.append(f"Git changes check failed: {e}")
            self.logger.error("git_changes_check_failed", error=str(e))

        try:
            config_findings = await self._check_config_changes(service, incident_time)
            findings.extend(config_findings)
        except Exception as e:
            errors.append(f"Config changes check failed: {e}")
            self.logger.error("config_changes_check_failed", error=str(e))

        confidence = self._calculate_confidence(findings, incident_time)

        next_context = None
        if findings:
            deploy_finding = next(
                (f for f in findings if f.type == FindingType.DEPLOYMENT),
                findings[0],
            )
            next_context = (
                f"Check logs around {deploy_finding.timestamp.isoformat()} "
                f"for {service or 'affected service'} errors related to: "
                f"{deploy_finding.title}"
            )

        return self._build_evidence(
            findings=findings,
            context=context,
            confidence=confidence,
            confidence_reasoning=self._explain_confidence(findings, incident_time),
            started_at=started_at,
            suggests_next_agent="LogsAgent" if findings else "MetricsAgent",
            next_agent_context=next_context,
            errors=errors,
        )

    def get_tools(self) -> List[Dict[str, Any]]:
        """Return tools for Gradient function calling."""
        return [
            {
                "name": "list_k8s_deployments",
                "description": "List recent Kubernetes deployments for a service",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "service": {"type": "string", "description": "Service name"},
                        "namespace": {"type": "string", "description": "Kubernetes namespace"},
                        "hours_back": {"type": "integer", "description": "Hours to look back"},
                    },
                    "required": ["service"],
                },
            },
            {
                "name": "get_git_commits",
                "description": "Get recent Git commits for a service",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "repo": {"type": "string", "description": "Repository name"},
                        "hours_back": {"type": "integer", "description": "Hours to look back"},
                    },
                    "required": ["repo"],
                },
            },
            {
                "name": "get_configmap_changes",
                "description": "Get recent ConfigMap changes for a service",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "service": {"type": "string", "description": "Service name"},
                        "namespace": {"type": "string", "description": "Kubernetes namespace"},
                    },
                    "required": ["service"],
                },
            },
        ]

    def _parse_incident_time(self, alert: Dict[str, Any]) -> datetime:
        """Parse incident time from alert, with fallback."""
        fired_at = alert.get("fired_at", datetime.utcnow().isoformat())
        if isinstance(fired_at, str):
            return datetime.fromisoformat(fired_at.replace("Z", "+00:00"))
        return fired_at

    async def _check_k8s_deployments(
        self,
        service: str,
        incident_time: datetime,
    ) -> List[Finding]:
        """Check Kubernetes for recent deployments."""
        deployments = mock_data.get_k8s_deployments(service=service)
        findings: List[Finding] = []

        for deploy in deployments:
            deploy_time = datetime.fromisoformat(deploy["updated_at"])
            if deploy_time.tzinfo is None:
                deploy_time = deploy_time.replace(tzinfo=timezone.utc)

            incident_aware = incident_time
            if incident_aware.tzinfo is None:
                incident_aware = incident_aware.replace(tzinfo=timezone.utc)

            hours_before = (incident_aware - deploy_time).total_seconds() / 3600

            if hours_before < 0 or hours_before > 24:
                continue

            confidence = self._score_deployment_proximity(hours_before)
            severity = Severity.HIGH if hours_before < 4 else Severity.MEDIUM

            time_delta = self._format_time_delta(hours_before)

            findings.append(Finding(
                id=self._generate_finding_id(),
                type=FindingType.DEPLOYMENT,
                title=f"Deployment of {deploy['name']} {deploy['image'].split(':')[-1]}",
                description=(
                    f"Service {deploy['name']} was deployed to "
                    f"{deploy['image'].split(':')[-1]} (from {deploy['previous_image'].split(':')[-1]}) "
                    f"{time_delta} before the incident. "
                    f"Change cause: {deploy.get('change_cause', 'unknown')}. "
                    f"Initiated by: {deploy.get('initiated_by', 'unknown')}."
                ),
                severity=severity,
                confidence=confidence,
                timestamp=deploy_time,
                time_delta_from_incident=f"-{time_delta}",
                affected_services=[deploy["name"]],
                evidence_source="kubernetes",
                evidence_query=f"kubectl rollout history deployment/{deploy['name']} -n {deploy['namespace']}",
                raw_evidence=(
                    f"deployment.apps/{deploy['name']} "
                    f"image={deploy['image']} "
                    f"revision={deploy.get('revision', 'unknown')} "
                    f"status={deploy['status']}"
                ),
                is_actionable=True,
                suggested_action=f"Consider rollback: kubectl rollout undo deployment/{deploy['name']} -n {deploy['namespace']}",
                metadata={
                    "previous_image": deploy["previous_image"],
                    "replicas": deploy["replicas"],
                    "rollout_duration_seconds": deploy.get("rollout_duration_seconds"),
                    "revision": deploy.get("revision"),
                },
            ))

        return findings

    async def _check_git_changes(
        self,
        service: str,
        incident_time: datetime,
    ) -> List[Finding]:
        """Check Git for recent commits with suspicious changes."""
        commits = mock_data.get_git_commits(service=service)
        findings: List[Finding] = []

        suspicious_patterns = [
            "connection", "pool", "timeout", "retry", "database",
            "cache", "memory", "thread", "concurrent",
        ]

        for commit in commits:
            commit_time = datetime.fromisoformat(commit["timestamp"])
            if commit_time.tzinfo is None:
                commit_time = commit_time.replace(tzinfo=timezone.utc)

            message_lower = commit["message"].lower()
            files_str = " ".join(commit["files_changed"]).lower()
            combined = f"{message_lower} {files_str}"

            matched_patterns = [p for p in suspicious_patterns if p in combined]

            if not matched_patterns:
                continue

            confidence = min(0.85, 0.4 + len(matched_patterns) * 0.15)

            findings.append(Finding(
                id=self._generate_finding_id(),
                type=FindingType.DEPLOYMENT,
                title=f"Suspicious commit: {commit['message'][:60]}",
                description=(
                    f"Commit {commit['sha']} by {commit['author']} "
                    f"modified {len(commit['files_changed'])} files "
                    f"({commit['additions']} additions, {commit['deletions']} deletions). "
                    f"Matches suspicious patterns: {', '.join(matched_patterns)}. "
                    f"Files: {', '.join(commit['files_changed'][:3])}"
                ),
                severity=Severity.MEDIUM,
                confidence=confidence,
                timestamp=commit_time,
                time_delta_from_incident=self._format_relative_time(commit_time, incident_time),
                affected_services=[commit.get("repo", service or "unknown")],
                evidence_source="git",
                evidence_query=f"git log --oneline -1 {commit['sha']}",
                raw_evidence=f"{commit['sha']} {commit['message']}",
                is_actionable=False,
                suggested_action=f"Review commit {commit['sha']} for potential issues",
                metadata={
                    "sha": commit["sha"],
                    "author": commit["author"],
                    "files_changed": commit["files_changed"],
                    "matched_patterns": matched_patterns,
                },
            ))

        return findings

    async def _check_config_changes(
        self,
        service: str,
        incident_time: datetime,
    ) -> List[Finding]:
        """Check for ConfigMap changes."""
        changes = mock_data.get_configmap_changes(service=service)
        findings: List[Finding] = []

        for change in changes:
            change_time = datetime.fromisoformat(change["changed_at"])
            if change_time.tzinfo is None:
                change_time = change_time.replace(tzinfo=timezone.utc)

            diff_parts = []
            for key in change.get("changed_keys", []):
                old_val = change.get("previous_values", {}).get(key, "?")
                new_val = change.get("new_values", {}).get(key, "?")
                diff_parts.append(f"{key}: {old_val} -> {new_val}")

            findings.append(Finding(
                id=self._generate_finding_id(),
                type=FindingType.CONFIG_CHANGE,
                title=f"ConfigMap change: {change['name']}",
                description=(
                    f"ConfigMap {change['name']} in namespace {change['namespace']} "
                    f"was modified by {change.get('changed_by', 'unknown')}. "
                    f"Changed keys: {', '.join(change.get('changed_keys', []))}. "
                    f"Changes: {'; '.join(diff_parts)}"
                ),
                severity=Severity.MEDIUM,
                confidence=0.6,
                timestamp=change_time,
                time_delta_from_incident=self._format_relative_time(change_time, incident_time),
                affected_services=[change["name"].replace("-config", "")],
                evidence_source="kubernetes",
                evidence_query=f"kubectl get configmap {change['name']} -n {change['namespace']} -o yaml",
                raw_evidence=f"ConfigMap {change['name']}: {'; '.join(diff_parts)}",
                is_actionable=True,
                suggested_action=f"Review config change and consider reverting: {'; '.join(diff_parts)}",
                metadata={
                    "changed_keys": change.get("changed_keys", []),
                    "previous_values": change.get("previous_values", {}),
                    "new_values": change.get("new_values", {}),
                },
            ))

        return findings

    def _score_deployment_proximity(self, hours_before: float) -> float:
        """Score deployment based on temporal proximity to incident."""
        if hours_before <= 1:
            return 0.90
        if hours_before <= 2:
            return 0.85
        if hours_before <= 4:
            return 0.75
        if hours_before <= 8:
            return 0.55
        if hours_before <= 12:
            return 0.40
        return 0.25

    def _calculate_confidence(
        self,
        findings: List[Finding],
        incident_time: datetime,
    ) -> float:
        """Calculate overall confidence based on all findings."""
        if not findings:
            return 0.15

        deployment_findings = [f for f in findings if f.type == FindingType.DEPLOYMENT]
        config_findings = [f for f in findings if f.type == FindingType.CONFIG_CHANGE]

        base = max(f.confidence for f in findings)

        if deployment_findings and config_findings:
            base = min(0.95, base + 0.10)

        if len(findings) > 2:
            base = min(0.95, base + 0.05)

        return round(base, 2)

    def _explain_confidence(
        self,
        findings: List[Finding],
        incident_time: datetime,
    ) -> str:
        """Explain confidence calculation."""
        if not findings:
            return "No recent deployments or changes found in the investigation window"

        deployment_count = sum(1 for f in findings if f.type == FindingType.DEPLOYMENT)
        config_count = sum(1 for f in findings if f.type == FindingType.CONFIG_CHANGE)

        parts = []
        if deployment_count:
            parts.append(f"{deployment_count} deployment(s)")
        if config_count:
            parts.append(f"{config_count} config change(s)")

        top = max(findings, key=lambda f: f.confidence)

        return (
            f"Found {' and '.join(parts)} near incident time. "
            f"Highest correlation: {top.title} (confidence: {top.confidence:.0%})"
        )

    def _format_time_delta(self, hours: float) -> str:
        """Format hours as human-readable time delta."""
        total_minutes = int(hours * 60)
        h = total_minutes // 60
        m = total_minutes % 60
        if h > 0:
            return f"{h}h {m}m"
        return f"{m}m"

    def _format_relative_time(self, event_time: datetime, incident_time: datetime) -> str:
        """Format time relative to incident."""
        event_aware = event_time
        incident_aware = incident_time
        if event_aware.tzinfo is None:
            event_aware = event_aware.replace(tzinfo=timezone.utc)
        if incident_aware.tzinfo is None:
            incident_aware = incident_aware.replace(tzinfo=timezone.utc)

        diff_seconds = (incident_aware - event_aware).total_seconds()
        prefix = "-" if diff_seconds > 0 else "+"
        abs_seconds = abs(diff_seconds)
        hours = int(abs_seconds // 3600)
        minutes = int((abs_seconds % 3600) // 60)

        if hours > 0:
            return f"{prefix}{hours}h {minutes}m"
        return f"{prefix}{minutes}m"
