"""
Memory Agent

Searches past incidents for similar patterns.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from incidentagent.agents.base import SubAgent, register_agent
from incidentagent.knowledge.kb_client import get_kb_client
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


@register_agent
class MemoryAgent(SubAgent):
    """
    Memory Agent - Finds similar past incidents.

    Uses Gradient Knowledge Base to search:
    - Past resolved incidents
    - Successful remediations
    - Known patterns

    This is typically the last agent called. It provides:
    - Historical context for root cause validation
    - Proven remediation steps from past successes
    - Confidence boost when current incident matches a known pattern
    """

    name = "MemoryAgent"
    description = "Finds similar past incidents and what worked"

    @trace_tool("memory-investigate")
    async def investigate(self, context: Dict[str, Any]) -> AgentEvidence:
        """Find similar past incidents and their resolutions."""
        started_at = datetime.utcnow()
        alert = context.get("alert", {})
        service = alert.get("service")
        alert_type = context.get("alert_type", alert.get("alert_type", "error_rate"))
        incident_time = self._parse_incident_time(alert)
        previous_findings = context.get("previous_findings", [])

        findings: List[Finding] = []
        errors: List[str] = []

        search_queries = self._build_search_queries(alert, previous_findings)

        seen_incident_ids: set = set()

        for query in search_queries:
            try:
                incident_findings = await self._search_past_incidents(
                    query=query,
                    alert_type=alert_type,
                    service=service,
                    incident_time=incident_time,
                )
                for finding in incident_findings:
                    incident_id = finding.metadata.get("incident_id")
                    if incident_id and incident_id not in seen_incident_ids:
                        seen_incident_ids.add(incident_id)
                        findings.append(finding)
            except Exception as e:
                errors.append(f"Past incident search failed for '{query}': {e}")
                self.logger.error("past_incident_search_failed", query=query, error=str(e))

        self._cross_reference_findings(findings, previous_findings)

        confidence = self._calculate_confidence(findings)

        return self._build_evidence(
            findings=findings,
            context=context,
            confidence=confidence,
            confidence_reasoning=self._explain_confidence(findings, previous_findings),
            started_at=started_at,
            suggests_next_agent=None,
            next_agent_context=None,
            errors=errors,
        )

    def get_tools(self) -> List[Dict[str, Any]]:
        """Return tools for Gradient function calling."""
        return [
            {
                "name": "search_past_incidents",
                "description": "Search past incidents for similar patterns using Gradient Knowledge Base",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "alert_type": {
                            "type": "string",
                            "description": "Alert type filter",
                        },
                        "service": {"type": "string", "description": "Service name filter"},
                        "min_similarity": {
                            "type": "number",
                            "description": "Minimum similarity score (0-1)",
                        },
                    },
                    "required": ["query"],
                },
            },
        ]

    def _parse_incident_time(self, alert: Dict[str, Any]) -> datetime:
        """Parse incident time from alert."""
        fired_at = alert.get("fired_at", datetime.utcnow().isoformat())
        if isinstance(fired_at, str):
            return datetime.fromisoformat(fired_at.replace("Z", "+00:00"))
        return fired_at

    def _build_search_queries(
        self,
        alert: Dict[str, Any],
        previous_findings: List[Any],
    ) -> List[str]:
        """Build search queries from alert and investigation findings."""
        queries = []

        title = alert.get("title", "")
        if title:
            queries.append(title)

        service = alert.get("service", "")
        severity = alert.get("severity", "")
        if service and severity:
            queries.append(f"{service} {severity} incident")

        for pf in previous_findings:
            if not hasattr(pf, "findings"):
                continue
            for finding in pf.findings:
                if finding.confidence >= 0.75:
                    queries.append(finding.title)

        return queries[:4]

    @trace_retriever("memory-kb-search")
    async def _search_kb(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """Search the Gradient Knowledge Base for past incidents.

        Returns KB results if available, otherwise None to trigger fallback.
        """
        try:
            kb_client = get_kb_client()
            if not kb_client.is_available:
                return None
            return await kb_client.search_incidents(query)
        except Exception as e:
            self.logger.warning("kb_incidents_unavailable", error=str(e))
            return None

    def _kb_results_to_incidents(
        self,
        kb_results: List[Dict[str, Any]],
        alert_type: Optional[str],
        service: Optional[str],
    ) -> List[Dict[str, Any]]:
        """Convert Gradient KB search results to the internal incident shape."""
        incidents = []
        for i, result in enumerate(kb_results):
            metadata = result.get("metadata", {})
            score = result.get("score", 0.70)
            content = result.get("content", result.get("text", ""))
            title = result.get("title", f"Past Incident {i + 1}")

            # Parse resolution time from content heuristically
            resolution_seconds = 2700  # default 45 minutes
            for phrase in ("Time to resolve:", "resolved in"):
                idx = content.lower().find(phrase.lower())
                if idx != -1:
                    snippet = content[idx + len(phrase):idx + len(phrase) + 20].strip()
                    parts = snippet.split()
                    if parts:
                        try:
                            value = float(parts[0])
                            unit = parts[1].lower() if len(parts) > 1 else "minutes"
                            if "hour" in unit:
                                resolution_seconds = int(value * 3600)
                            else:
                                resolution_seconds = int(value * 60)
                        except ValueError:
                            pass
                    break

            # Derive category from metadata or content keywords
            category = metadata.get("category", "unknown")
            if category == "unknown":
                content_lower = content.lower()
                if "deploy" in content_lower or "rollback" in content_lower:
                    category = "deployment"
                elif "memory" in content_lower or "oom" in content_lower:
                    category = "resource"
                elif "connection" in content_lower or "pool" in content_lower:
                    category = "resource"
                elif "config" in content_lower:
                    category = "config"

            incidents.append({
                "incident_id": metadata.get("incident_id", f"KB-{i}"),
                "title": title,
                "similarity_score": min(1.0, score),
                "root_cause": content[:200] if content else "See KB document",
                "root_cause_category": category,
                "affected_services": [metadata.get("service", service)] if (metadata.get("service") or service) else [],
                "resolution_time_seconds": resolution_seconds,
                "remediation_that_worked": {
                    "summary": "See KB document for full resolution steps",
                    "steps": [],
                    "success_rate": 0.85,
                },
                "severity": "high",
                "tags": [category, metadata.get("service", "")],
            })
        return incidents

    async def _search_past_incidents(
        self,
        query: str,
        alert_type: Optional[str],
        service: Optional[str],
        incident_time: datetime,
    ) -> List[Finding]:
        """Search for similar past incidents.

        Tries the Gradient Knowledge Base first; falls back to mock data
        when the KB is unavailable or returns no results.
        """
        kb_results = await self._search_kb(query)

        if kb_results is not None:
            incidents = self._kb_results_to_incidents(kb_results, alert_type, service)
        else:
            incidents = mock_data.get_past_incidents(
                query=query,
                alert_type=alert_type,
                service=service,
            )

        findings: List[Finding] = []

        for incident in incidents:
            similarity = incident.get("similarity_score", 0)
            if similarity < 0.5:
                continue

            confidence = min(0.90, similarity * 0.95)

            severity = Severity.HIGH if similarity > 0.80 else Severity.MEDIUM

            remediation = incident.get("remediation_that_worked", {})
            resolution_minutes = incident.get("resolution_time_seconds", 0) / 60

            findings.append(Finding(
                id=self._generate_finding_id(),
                type=FindingType.HISTORICAL_MATCH,
                title=f"Past incident: {incident['title']}",
                description=(
                    f"Similar incident found with {similarity:.0%} similarity. "
                    f"Root cause: {incident.get('root_cause', 'unknown')}. "
                    f"Category: {incident.get('root_cause_category', 'unknown')}. "
                    f"Resolution: {remediation.get('summary', 'unknown')} "
                    f"(resolved in {resolution_minutes:.0f} minutes). "
                    f"Affected services: {', '.join(incident.get('affected_services', []))}."
                ),
                severity=severity,
                confidence=confidence,
                timestamp=incident_time,
                time_delta_from_incident="0m",
                affected_services=incident.get("affected_services", []),
                affected_users_estimate=None,
                evidence_source="gradient_knowledge_base",
                evidence_query=f"incidents.search('{query[:50]}', alert_type='{alert_type}')",
                raw_evidence=(
                    f"incident_id={incident['incident_id']} "
                    f"similarity={similarity:.2f} "
                    f"root_cause={incident.get('root_cause', 'unknown')[:80]} "
                    f"resolution_time={resolution_minutes:.0f}m"
                ),
                is_actionable=bool(remediation),
                suggested_action=self._format_remediation_suggestion(incident),
                metadata={
                    "incident_id": incident["incident_id"],
                    "similarity_score": similarity,
                    "root_cause": incident.get("root_cause"),
                    "root_cause_category": incident.get("root_cause_category"),
                    "remediation_summary": remediation.get("summary"),
                    "remediation_steps": remediation.get("steps", []),
                    "remediation_success_rate": remediation.get("success_rate"),
                    "resolution_time_seconds": incident.get("resolution_time_seconds"),
                    "original_severity": incident.get("severity"),
                    "tags": incident.get("tags", []),
                },
            ))

        return findings

    def _format_remediation_suggestion(self, incident: Dict[str, Any]) -> str:
        """Format remediation suggestion from past incident."""
        remediation = incident.get("remediation_that_worked", {})
        summary = remediation.get("summary", "")
        steps = remediation.get("steps", [])
        success_rate = remediation.get("success_rate", 0)

        if not summary:
            return "Review past incident for remediation guidance"

        suggestion = f"Based on {incident['incident_id']}: {summary}"
        if success_rate and success_rate > 0:
            suggestion += f" (success rate: {success_rate:.0%})"
        if steps:
            suggestion += f". Steps: {'; '.join(steps[:3])}"

        return suggestion

    def _cross_reference_findings(
        self,
        memory_findings: List[Finding],
        previous_findings: List[Any],
    ) -> None:
        """Cross-reference memory findings with investigation findings."""
        investigation_categories = set()
        investigation_finding_ids = []

        for pf in previous_findings:
            if not hasattr(pf, "findings"):
                continue
            for f in pf.findings:
                investigation_finding_ids.append(f.id)
                if f.type == FindingType.DEPLOYMENT:
                    investigation_categories.add("deployment")
                elif f.type == FindingType.RESOURCE_EXHAUSTION:
                    investigation_categories.add("resource")
                elif f.type == FindingType.ERROR_SIGNATURE:
                    investigation_categories.add("code")

        for mf in memory_findings:
            past_category = mf.metadata.get("root_cause_category", "")

            if past_category in investigation_categories:
                mf.confidence = min(0.92, mf.confidence + 0.08)
                mf.correlation_strength = 0.90

            mf.related_findings.extend(investigation_finding_ids[:5])

    def _calculate_confidence(self, findings: List[Finding]) -> float:
        """Calculate overall confidence."""
        if not findings:
            return 0.10

        base = max(f.confidence for f in findings)

        high_similarity = [f for f in findings if f.confidence > 0.75]
        if len(high_similarity) > 1:
            base = min(0.95, base + 0.05)

        return round(base, 2)

    def _explain_confidence(
        self,
        findings: List[Finding],
        previous_findings: List[Any],
    ) -> str:
        """Explain confidence calculation."""
        if not findings:
            return "No similar past incidents found in knowledge base"

        top = max(findings, key=lambda f: f.confidence)
        category = top.metadata.get("root_cause_category", "unknown")

        investigation_categories = set()
        for pf in previous_findings:
            if hasattr(pf, "findings"):
                for f in pf.findings:
                    if f.type == FindingType.DEPLOYMENT:
                        investigation_categories.add("deployment")
                    elif f.type == FindingType.RESOURCE_EXHAUSTION:
                        investigation_categories.add("resource")

        base = (
            f"Found {len(findings)} similar past incident(s). "
            f"Best match: {top.title} (similarity: {top.confidence:.0%}). "
            f"Past root cause category: {category}."
        )

        if category in investigation_categories:
            base += f" Matches current investigation pattern ({category})."

        return base
