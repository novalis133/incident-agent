"""Structured prompts for LLM-powered analysis."""


class TriagePrompt:
    """Prompt for alert classification."""

    SYSTEM = "You are an expert Site Reliability Engineer. Classify incidents accurately."

    @staticmethod
    def format(
        alert_title: str,
        alert_description: str,
        severity: str,
        service: str,
        labels: dict,
    ) -> str:
        """Format a triage classification prompt.

        Args:
            alert_title: Title of the incoming alert.
            alert_description: Full alert description.
            severity: Alert severity level.
            service: Originating service name.
            labels: Key/value label metadata attached to the alert.

        Returns:
            Formatted prompt string ready to send to the LLM.
        """
        return f"""Classify this alert and determine the investigation strategy.

Alert Title: {alert_title}
Description: {alert_description}
Severity: {severity}
Service: {service}
Labels: {labels}

Respond with JSON:
{{
    "alert_type": "error_rate|latency|crash|resource|dependency|config|security|unknown",
    "confidence": 0.0-1.0,
    "reasoning": "explanation",
    "affected_services": ["service1", "service2"],
    "potential_blast_radius": "description of impact",
    "requires_immediate_attention": true/false,
    "priority_agents": ["AgentName1", "AgentName2"]
}}"""


class SynthesisPrompt:
    """Prompt for evidence synthesis."""

    SYSTEM = (
        "You are an expert incident investigator. "
        "Synthesize evidence into root cause hypotheses."
    )

    @staticmethod
    def format(
        alert_title: str,
        alert_type: str,
        findings_summary: str,
        timeline: str,
    ) -> str:
        """Format a synthesis prompt from accumulated investigation evidence.

        Args:
            alert_title: Title of the alert being investigated.
            alert_type: Classified alert type (e.g. error_rate, latency).
            findings_summary: Concatenated summary of all agent findings.
            timeline: Chronological timeline of events built from findings.

        Returns:
            Formatted prompt string ready to send to the LLM.
        """
        return f"""Synthesize the following investigation evidence into a root cause hypothesis.

Alert: {alert_title}
Alert Type: {alert_type}

Evidence Summary:
{findings_summary}

Timeline:
{timeline}

Respond with JSON:
{{
    "hypothesis": "Clear statement of root cause",
    "category": "deployment|resource|dependency|config|network|security|data|capacity|human_error|unknown",
    "confidence": 0.0-1.0,
    "evidence_summary": "Summary of supporting evidence",
    "probable_trigger_event": "What triggered the issue",
    "causality_chain": ["Event A", "Event B leads to C", "C causes symptoms"],
    "blast_radius_description": "Impact scope description",
    "reasoning": "Detailed reasoning"
}}"""


class RemediationPrompt:
    """Prompt for remediation generation."""

    SYSTEM = (
        "You are an expert SRE. Generate safe, actionable remediation steps. "
        "Never suggest destructive commands."
    )

    @staticmethod
    def format(
        hypothesis: str,
        category: str,
        affected_services: list,
        evidence_summary: str,
    ) -> str:
        """Format a remediation generation prompt.

        Args:
            hypothesis: Root cause hypothesis statement.
            category: Root cause category (e.g. deployment, resource).
            affected_services: List of services affected by the incident.
            evidence_summary: Summary of supporting evidence.

        Returns:
            Formatted prompt string ready to send to the LLM.
        """
        services_str = ", ".join(affected_services) if affected_services else "unknown"
        return f"""Generate safe remediation steps for this incident.

Root Cause: {hypothesis}
Category: {category}
Affected Services: {services_str}
Evidence: {evidence_summary}

SAFETY RULES:
- Never use rm -rf, DROP DATABASE, DELETE FROM, terraform destroy
- Always include rollback plans for risky steps
- Flag steps requiring human approval

Respond with JSON:
{{
    "summary": "Brief remediation summary",
    "steps": [
        {{
            "action": "Description of action",
            "command": "actual command or null",
            "command_type": "kubectl|bash|sql|none",
            "risk_level": "low|medium|high|critical",
            "risk_reasoning": "Why this risk level",
            "requires_approval": false,
            "rollback_plan": "How to undo",
            "estimated_time": "X minutes"
        }}
    ],
    "warnings": ["Any warnings"],
    "estimated_resolution_time": "Total time estimate"
}}"""
