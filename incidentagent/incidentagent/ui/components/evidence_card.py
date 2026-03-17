"""
Evidence Card Component

Displays AgentEvidence results with severity badges, confidence bars,
and expandable finding details.
"""

from typing import List

import streamlit as st

from incidentagent.schemas.evidence import AgentEvidence, Finding, Severity


_SEVERITY_COLORS = {
    Severity.CRITICAL: ("#ff4444", "#ff000022"),
    Severity.HIGH: ("#ff8800", "#ff880022"),
    Severity.MEDIUM: ("#ffcc00", "#ffcc0022"),
    Severity.LOW: ("#44bb44", "#44bb4422"),
    Severity.INFO: ("#4488ff", "#4488ff22"),
}

_SEVERITY_EMOJI = {
    Severity.CRITICAL: "CRIT",
    Severity.HIGH: "HIGH",
    Severity.MEDIUM: "MED",
    Severity.LOW: "LOW",
    Severity.INFO: "INFO",
}


def _severity_badge_html(severity: str) -> str:
    """Build inline HTML chip for a severity level."""
    sev_enum = Severity(severity.lower()) if severity.lower() in [s.value for s in Severity] else Severity.INFO
    color, bg = _SEVERITY_COLORS.get(sev_enum, ("#4488ff", "#4488ff22"))
    label = _SEVERITY_EMOJI.get(sev_enum, severity.upper())
    return (
        f'<span style="'
        f"background: {bg}; color: {color}; border: 1px solid {color}; "
        f"padding: 2px 8px; border-radius: 12px; font-size: 0.72rem; "
        f'font-weight: 700; letter-spacing: 0.06em;">{label}</span>'
    )


def _confidence_bar_html(confidence: float) -> str:
    """Build an inline HTML confidence progress bar."""
    pct = int(confidence * 100)
    color = "#ff4444" if confidence < 0.4 else "#ffcc00" if confidence < 0.7 else "#44bb44"
    return f"""
    <div style="margin: 6px 0;">
        <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: #888; margin-bottom: 3px;">
            <span>Confidence</span>
            <span style="color: {color}; font-weight: 600;">{pct}%</span>
        </div>
        <div style="background: #2a2a3a; border-radius: 4px; height: 6px; overflow: hidden;">
            <div style="
                width: {pct}%;
                height: 100%;
                background: linear-gradient(90deg, {color}88, {color});
                border-radius: 4px;
                transition: width 0.3s ease;
            "></div>
        </div>
    </div>
    """


def _render_finding(finding: Finding, finding_index: int, agent_name: str) -> None:
    """Render a single Finding inside an expander."""
    severity_str = str(finding.severity.value) if hasattr(finding.severity, "value") else str(finding.severity)
    sev_enum = (
        Severity(severity_str.lower())
        if severity_str.lower() in [s.value for s in Severity]
        else Severity.INFO
    )
    color, _ = _SEVERITY_COLORS.get(sev_enum, ("#4488ff", "#4488ff22"))

    expander_label = f"Finding {finding_index + 1}: {finding.title}"

    with st.expander(expander_label, expanded=False):
        col_left, col_right = st.columns([3, 1])

        with col_left:
            st.markdown(
                f'<span style="color: {color}; font-weight: 600;">'
                f'{finding.type.value if hasattr(finding.type, "value") else finding.type}'
                f"</span>",
                unsafe_allow_html=True,
            )
            st.markdown(f"**{finding.description}**")

        with col_right:
            st.markdown(
                _severity_badge_html(severity_str),
                unsafe_allow_html=True,
            )

        st.markdown(_confidence_bar_html(finding.confidence), unsafe_allow_html=True)

        detail_col1, detail_col2 = st.columns(2)
        with detail_col1:
            st.markdown(f"**Timestamp:** `{finding.timestamp}`")
            st.markdown(f"**Time delta:** `{finding.time_delta_from_incident}`")
            st.markdown(f"**Source:** `{finding.evidence_source}`")

        with detail_col2:
            if finding.affected_services:
                st.markdown(f"**Affected services:** {', '.join(finding.affected_services)}")
            if finding.affected_users_estimate is not None:
                st.markdown(f"**Affected users:** ~{finding.affected_users_estimate:,}")
            st.markdown(f"**Actionable:** {'Yes' if finding.is_actionable else 'No'}")

        st.markdown("**Raw Evidence:**")
        st.code(finding.raw_evidence, language="text")

        if finding.evidence_query:
            st.markdown("**Query Used:**")
            st.code(finding.evidence_query, language="text")

        if finding.is_actionable and finding.suggested_action:
            st.success(f"Suggested action: {finding.suggested_action}")

        if finding.evidence_url:
            st.markdown(f"[View in source system]({finding.evidence_url})")


def _render_agent_evidence(evidence: AgentEvidence) -> None:
    """Render one AgentEvidence block with all its findings."""
    agent_name = evidence.agent_name
    finding_count = evidence.finding_count or len(evidence.findings)
    confidence = evidence.confidence
    duration_s = evidence.duration_ms / 1000

    header_col, metric_col = st.columns([3, 1])
    with header_col:
        st.markdown(f"### {agent_name}")
        st.caption(f"Type: {evidence.agent_type} | Step {evidence.step_number} | Duration: {duration_s:.1f}s")

    with metric_col:
        st.markdown(_confidence_bar_html(confidence), unsafe_allow_html=True)

    if evidence.confidence_reasoning:
        st.info(evidence.confidence_reasoning)

    if evidence.errors:
        for err in evidence.errors:
            st.warning(f"Agent error: {err}")

    if not evidence.findings:
        st.caption("No findings from this agent.")
    else:
        for i, finding in enumerate(evidence.findings):
            _render_finding(finding, i, agent_name)

    if evidence.suggests_next_agent:
        st.caption(
            f"Suggested next agent: **{evidence.suggests_next_agent}**"
            + (f" — {evidence.next_agent_context}" if evidence.next_agent_context else "")
        )

    st.divider()


def render_evidence_cards(evidence_list: List[AgentEvidence]) -> None:
    """
    Render evidence cards for all agents in an investigation.

    Args:
        evidence_list: List of AgentEvidence objects collected during investigation.
    """
    if not evidence_list:
        st.info("No evidence collected yet.")
        return

    total_findings = sum(len(e.findings) for e in evidence_list)
    high_confidence = sum(1 for e in evidence_list if e.is_high_confidence)

    summary_cols = st.columns(3)
    with summary_cols[0]:
        st.metric("Agents Run", len(evidence_list))
    with summary_cols[1]:
        st.metric("Total Findings", total_findings)
    with summary_cols[2]:
        st.metric("High Confidence Agents", high_confidence)

    st.markdown("---")

    for evidence in evidence_list:
        _render_agent_evidence(evidence)
