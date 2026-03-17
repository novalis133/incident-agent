"""
Remediation Panel Component

Displays remediation steps with risk-level coloring, commands, rollback plans,
and approval requirement indicators.
"""

from typing import Optional

import streamlit as st

from incidentagent.schemas.remediation import Remediation, RemediationStep, RiskLevel


_RISK_COLORS = {
    RiskLevel.LOW: ("#44bb44", "#1b5e20", "LOW"),
    RiskLevel.MEDIUM: ("#ffcc00", "#f57f17", "MED"),
    RiskLevel.HIGH: ("#ff8800", "#e65100", "HIGH"),
    RiskLevel.CRITICAL: ("#ff4444", "#b71c1c", "CRIT"),
}


def _risk_badge_html(risk_level: str) -> str:
    """Build an HTML badge for a risk level."""
    rl_str = risk_level.lower() if isinstance(risk_level, str) else risk_level.value
    try:
        rl_enum = RiskLevel(rl_str)
    except ValueError:
        rl_enum = RiskLevel.MEDIUM

    color, bg, label = _RISK_COLORS.get(rl_enum, ("#ffcc00", "#f57f17", "MED"))
    return (
        f'<span class="risk-badge" style="background-color: {bg}; color: white; '
        f'padding: 3px 10px; border-radius: 4px; font-size: 0.78rem; font-weight: 700; '
        f'letter-spacing: 0.05em;">{label}</span>'
    )


def _step_border_color(risk_level: str) -> str:
    """Return the left-border color for a step card based on its risk."""
    rl_str = risk_level.lower() if isinstance(risk_level, str) else risk_level.value
    try:
        rl_enum = RiskLevel(rl_str)
    except ValueError:
        rl_enum = RiskLevel.MEDIUM
    color, _, _ = _RISK_COLORS.get(rl_enum, ("#ffcc00", "#f57f17", "MED"))
    return color


def _render_step(step: RemediationStep) -> None:
    """Render a single remediation step card."""
    risk_str = step.risk_level.value if hasattr(step.risk_level, "value") else str(step.risk_level)
    border_color = _step_border_color(risk_str)

    with st.container():
        st.markdown(
            f"""
            <div style="
                border-left: 4px solid {border_color};
                background: #1a1a2a;
                border-radius: 6px;
                padding: 14px 18px;
                margin-bottom: 12px;
            ">
                <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span style="
                            background: {border_color}22;
                            color: {border_color};
                            border: 1px solid {border_color};
                            border-radius: 50%;
                            width: 28px;
                            height: 28px;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            font-weight: 700;
                            font-size: 0.85rem;
                            flex-shrink: 0;
                        ">{step.step_number}</span>
                        <span style="font-size: 1rem; font-weight: 600; color: #e0e0e0;">{step.action}</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        {_risk_badge_html(risk_str)}
                        {"<span style='background:#660000;color:white;padding:3px 8px;border-radius:4px;font-size:0.75rem;font-weight:700;'>APPROVAL REQUIRED</span>" if step.requires_approval else ""}
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if step.command:
        command_type = step.command_type or "bash"
        st.code(step.command, language=command_type)

    detail_cols = st.columns(2)

    with detail_cols[0]:
        if step.estimated_time:
            st.caption(f"Estimated time: **{step.estimated_time}**")

        if step.risk_reasoning:
            st.caption(f"Risk reasoning: {step.risk_reasoning}")

        if step.pre_conditions:
            st.markdown("**Pre-conditions:**")
            for cond in step.pre_conditions:
                st.markdown(f"- {cond}")

    with detail_cols[1]:
        if step.rollback_plan:
            st.markdown("**Rollback plan:**")
            st.info(step.rollback_plan)
            if step.rollback_command:
                st.code(step.rollback_command, language=step.command_type or "bash")

        if step.post_validation:
            st.markdown("**Post-validation:**")
            st.success(step.post_validation)

    if step.depends_on:
        st.caption(f"Depends on steps: {', '.join(str(d) for d in step.depends_on)}")

    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)


def render_remediation_panel(remediation: Remediation) -> None:
    """
    Render the full remediation plan panel.

    Args:
        remediation: The complete Remediation object from the investigation result.
    """
    if not remediation:
        st.info("No remediation plan generated yet.")
        return

    summary_cols = st.columns(4)
    with summary_cols[0]:
        st.metric("Total Steps", remediation.total_steps or len(remediation.steps))
    with summary_cols[1]:
        risk_pct = int(remediation.total_risk_score * 100)
        st.metric("Risk Score", f"{risk_pct}%")
    with summary_cols[2]:
        st.metric("Est. Resolution", remediation.estimated_resolution_time)
    with summary_cols[3]:
        approval_label = "Required" if remediation.requires_human_approval else "Not Required"
        st.metric("Approval", approval_label)

    st.markdown("---")

    st.markdown(f"**Summary:** {remediation.summary}")
    if remediation.detailed_explanation:
        with st.expander("Detailed explanation", expanded=False):
            st.write(remediation.detailed_explanation)

    if remediation.based_on_runbook:
        st.caption(f"Based on runbook: `{remediation.based_on_runbook}`")

    if remediation.similar_past_incident:
        past_rate = ""
        if remediation.past_success_rate is not None:
            past_rate = f" (success rate: {int(remediation.past_success_rate * 100)}%)"
        st.caption(f"Similar past incident: `{remediation.similar_past_incident}`{past_rate}")

    if remediation.warnings:
        for warning in remediation.warnings:
            st.warning(warning)

    if remediation.blocked_suggestions:
        with st.expander("Blocked suggestions (guardrails applied)", expanded=False):
            for suggestion in remediation.blocked_suggestions:
                st.markdown(f"- {suggestion}")
            if remediation.guardrails_applied:
                st.caption(f"Guardrails: {', '.join(remediation.guardrails_applied)}")

    st.markdown("### Remediation Steps")

    if not remediation.steps:
        st.info("No steps generated.")
        return

    for step in remediation.steps:
        _render_step(step)
        st.divider()
