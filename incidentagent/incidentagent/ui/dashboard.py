"""
IncidentIQ Dashboard

Single-page Streamlit application for AI-powered incident investigation.
Run with: streamlit run incidentagent/ui/dashboard.py
from the incidentiq/incidentagent directory.
"""

import asyncio
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

import streamlit as st

# ---------------------------------------------------------------------------
# Path setup — must happen before any incidentagent imports
# ---------------------------------------------------------------------------
sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
)

from incidentagent.main import investigate_alert
from incidentagent.schemas.alert import AlertSource, UnifiedAlert

# ---------------------------------------------------------------------------
# Page config (must be the very first Streamlit call)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="IncidentIQ",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
st.markdown(
    """
<style>
    /* Metric cards */
    .stMetric {
        background-color: #1e1e2e;
        padding: 1rem;
        border-radius: 0.5rem;
    }

    /* Severity text helpers */
    .severity-critical { color: #ff4444; font-weight: bold; }
    .severity-high     { color: #ff8800; font-weight: bold; }
    .severity-medium   { color: #ffcc00; }
    .severity-low      { color: #44bb44; }

    /* Risk badges */
    .risk-badge    { padding: 0.2rem 0.6rem; border-radius: 0.3rem; font-size: 0.8rem; font-weight: bold; }
    .risk-low      { background-color: #1b5e20; color: white; }
    .risk-medium   { background-color: #f57f17; color: white; }
    .risk-high     { background-color: #e65100; color: white; }
    .risk-critical { background-color: #b71c1c; color: white; }

    /* Header banner */
    .iq-header {
        background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #0d1117 100%);
        border: 1px solid #2a2a4a;
        border-radius: 12px;
        padding: 24px 32px;
        margin-bottom: 20px;
    }
    .iq-title {
        font-size: 2.4rem;
        font-weight: 800;
        background: linear-gradient(90deg, #4488ff, #aa44ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0;
        line-height: 1.1;
    }
    .iq-subtitle {
        color: #888;
        font-size: 1rem;
        margin-top: 4px;
    }
    .status-badge {
        display: inline-block;
        padding: 4px 14px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.06em;
    }
    .status-idle     { background: #1a2a1a; color: #44bb44; border: 1px solid #44bb44; }
    .status-running  { background: #1a1a2a; color: #4488ff; border: 1px solid #4488ff; }
    .status-complete { background: #2a1a2a; color: #aa44ff; border: 1px solid #aa44ff; }

    /* Root cause card */
    .root-cause-card {
        background: linear-gradient(135deg, #0d1117, #1a1a2e);
        border: 1px solid #2a2a4a;
        border-radius: 10px;
        padding: 20px 24px;
    }
    .root-cause-hypothesis {
        font-size: 1.1rem;
        color: #e0e0e0;
        line-height: 1.5;
        margin: 8px 0;
    }

    /* Blast radius pill */
    .service-pill {
        display: inline-block;
        background: #1e1e3a;
        color: #aaaaff;
        border: 1px solid #3333aa;
        border-radius: 20px;
        padding: 3px 12px;
        font-size: 0.8rem;
        margin: 3px;
    }

    /* Hide Streamlit footer */
    footer { visibility: hidden; }
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_SOURCE_OPTIONS: List[str] = ["prometheus", "pagerduty", "webhook", "manual"]
_SEVERITY_OPTIONS: List[str] = ["critical", "high", "medium", "low"]

_AGENT_DESCRIPTIONS: Dict[str, str] = {
    "DeployAgent": "Checks recent deployments and code changes that may have triggered the incident",
    "LogsAgent": "Searches Elasticsearch / CloudWatch logs for error patterns and stack traces",
    "MetricsAgent": "Queries Prometheus / Datadog for anomalous metric trends",
    "K8sAgent": "Inspects Kubernetes pod events, restarts, OOM kills, and resource limits",
    "RunbookAgent": "Searches the knowledge base for matching runbooks and historical fixes",
    "MemoryAgent": "Looks up similar past incidents and retrieves institutional memory",
}

_STATUS_SEQUENCE: List[str] = [
    "Triage Agent",
    "DeployAgent",
    "LogsAgent",
    "MetricsAgent",
    "K8sAgent",
    "RunbookAgent",
    "MemoryAgent",
    "Synthesizing root cause",
    "Generating remediation",
]


# ---------------------------------------------------------------------------
# Session state helpers
# ---------------------------------------------------------------------------
def _init_session_state() -> None:
    defaults: Dict[str, Any] = {
        "investigation_result": None,
        "investigation_status": "idle",  # idle | running | complete | error
        "investigation_error": None,
        "pending_form_data": None,  # form data to use on the "running" rerun
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _reset_investigation() -> None:
    st.session_state["investigation_result"] = None
    st.session_state["investigation_status"] = "idle"
    st.session_state["investigation_error"] = None
    st.session_state["pending_form_data"] = None


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
def _render_header() -> None:
    status = st.session_state.get("investigation_status", "idle")
    if status == "idle":
        status_html = '<span class="status-badge status-idle">IDLE</span>'
    elif status == "running":
        status_html = '<span class="status-badge status-running">INVESTIGATING...</span>'
    else:
        status_html = '<span class="status-badge status-complete">COMPLETE</span>'

    st.markdown(
        f"""
        <div class="iq-header">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 12px;">
                <div>
                    <div class="iq-title">IncidentIQ</div>
                    <div class="iq-subtitle">AI-Powered Incident Investigation</div>
                </div>
                <div style="margin-top: 6px;">{status_html}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
def _render_sidebar() -> float:
    with st.sidebar:
        st.markdown("## About")
        st.markdown(
            """
            **IncidentIQ** automates root-cause analysis for production incidents.
            It orchestrates six specialized sub-agents in sequence, each examining
            a different data source, then synthesizes findings into a ranked hypothesis
            with a safe remediation plan.
            """
        )

        st.markdown("---")
        st.markdown("## Sub-Agents")
        for agent, desc in _AGENT_DESCRIPTIONS.items():
            with st.expander(agent):
                st.caption(desc)

        st.markdown("---")
        st.markdown("## Settings")
        confidence_threshold = st.slider(
            "Confidence threshold",
            min_value=0.5,
            max_value=1.0,
            value=0.85,
            step=0.05,
            help="The investigation stops early when combined confidence exceeds this threshold.",
        )

        if st.session_state.get("investigation_status") not in ("idle", "running"):
            if st.button("Reset / New Investigation", use_container_width=True):
                _reset_investigation()
                st.rerun()

    return confidence_threshold


# ---------------------------------------------------------------------------
# Alert Input Form
# ---------------------------------------------------------------------------
def _render_alert_form() -> Optional[Dict[str, Any]]:
    """Render the alert input form. Returns form data dict if submitted, else None."""
    st.markdown("## Alert Input")

    with st.form("alert_form", clear_on_submit=False):
        col1, col2 = st.columns(2)

        with col1:
            alert_id = st.text_input("Alert ID", value="alert-demo-001")
            source = st.selectbox("Source", options=_SOURCE_OPTIONS, index=0)
            title = st.text_input(
                "Title",
                value="High error rate on payment-service",
            )
            description = st.text_area(
                "Description",
                value="Error rate exceeded 5% threshold for 5 minutes",
                height=80,
            )

        with col2:
            severity = st.selectbox("Severity", options=_SEVERITY_OPTIONS, index=0)
            service = st.text_input("Service", value="payment-service")
            environment = st.text_input("Environment", value="production")
            namespace = st.text_input("Namespace", value="payments")

        submitted = st.form_submit_button(
            "Investigate",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        return {
            "alert_id": alert_id.strip(),
            "source": source,
            "title": title.strip(),
            "description": description.strip(),
            "severity": severity,
            "service": service.strip(),
            "environment": environment.strip(),
            "namespace": namespace.strip(),
        }

    return None


# ---------------------------------------------------------------------------
# Investigation runner
# ---------------------------------------------------------------------------
def _run_investigation(form_data: Dict[str, Any]) -> None:
    """Build alert, run async investigation, store result in session state."""
    try:
        alert = UnifiedAlert(
            id=form_data["alert_id"],
            source=AlertSource(form_data["source"]),
            title=form_data["title"],
            description=form_data["description"],
            severity=form_data["severity"],
            service=form_data["service"] or None,
            environment=form_data["environment"] or "production",
            namespace=form_data["namespace"] or None,
            fired_at=datetime.utcnow(),
        )

        result = asyncio.run(investigate_alert(alert))
        st.session_state["investigation_result"] = result
        st.session_state["investigation_status"] = "complete"
        st.session_state["investigation_error"] = None

    except Exception as exc:
        st.session_state["investigation_status"] = "error"
        st.session_state["investigation_error"] = str(exc)


# ---------------------------------------------------------------------------
# Live progress display (shown during investigation)
# ---------------------------------------------------------------------------
def _render_progress_placeholder() -> None:
    st.markdown("---")
    st.markdown("## Investigation in Progress")
    with st.spinner("Running multi-agent investigation..."):
        pass  # The actual spinner is managed by the caller


# ---------------------------------------------------------------------------
# Results panel
# ---------------------------------------------------------------------------
def _render_results() -> None:
    from incidentagent.ui.components.evidence_card import render_evidence_cards
    from incidentagent.ui.components.remediation_panel import render_remediation_panel
    from incidentagent.ui.components.timeline import render_timeline

    result = st.session_state["investigation_result"]
    if result is None:
        return

    st.markdown("---")
    st.markdown("## Investigation Results")

    # --- Agent progress (retroactive) ---
    agents_used: List[str] = result.agents_used or []
    with st.expander("Agent execution trace", expanded=False):
        all_steps = ["Triage Agent"] + agents_used + ["Synthesizing root cause", "Generating remediation"]
        for step_name in all_steps:
            with st.status(step_name, state="complete"):
                st.write(f"{step_name} completed successfully.")

    # --- Root Cause Card ---
    st.markdown("### Root Cause")
    rc = result.root_cause
    rc_confidence = rc.confidence if rc else 0.0
    rc_category = rc.category.value if hasattr(rc.category, "value") else str(rc.category) if rc else "unknown"
    rc_hypothesis = rc.hypothesis if rc else "No hypothesis generated."
    rc_evidence_summary = rc.evidence_summary if rc else ""
    rc_trigger_event = rc.probable_trigger_event if rc else ""

    confidence_pct = int(rc_confidence * 100)
    conf_color = "#ff4444" if rc_confidence < 0.4 else "#ffcc00" if rc_confidence < 0.7 else "#44bb44"

    st.markdown(
        f"""
        <div class="root-cause-card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 10px;">
                <div>
                    <span style="font-size: 0.75rem; color: #888; text-transform: uppercase; letter-spacing: 0.08em;">
                        Category: {rc_category.upper()}
                    </span>
                </div>
                <span style="
                    background: {conf_color}22;
                    color: {conf_color};
                    border: 1px solid {conf_color};
                    padding: 3px 12px;
                    border-radius: 20px;
                    font-size: 0.85rem;
                    font-weight: 700;
                ">Confidence: {confidence_pct}%</span>
            </div>
            <div class="root-cause-hypothesis">{rc_hypothesis}</div>
            <div style="color: #aaa; font-size: 0.88rem; margin-top: 8px;">{rc_evidence_summary}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Confidence bar using st.progress
    st.progress(rc_confidence, text=f"Confidence: {confidence_pct}%")

    if rc and rc.causality_chain:
        with st.expander("Causality chain", expanded=False):
            for i, step in enumerate(rc.causality_chain):
                arrow = "" if i == len(rc.causality_chain) - 1 else " → "
                st.markdown(f"**{i + 1}.** {step}{arrow}")

    # --- Metrics Row ---
    st.markdown("### Investigation Metrics")
    duration = result.duration_seconds
    mins, secs = divmod(duration, 60)
    duration_str = f"{mins}m {secs}s" if mins else f"{secs}s"

    mc1, mc2, mc3, mc4, mc5 = st.columns(5)
    with mc1:
        st.metric("Duration", duration_str)
    with mc2:
        st.metric("Confidence", f"{confidence_pct}%")
    with mc3:
        st.metric("Agents Used", len(result.agents_used))
    with mc4:
        st.metric("Total Findings", result.total_findings)
    with mc5:
        st.metric("Time Saved", result.time_saved_estimate)

    # --- Blast Radius ---
    blast_radius = result.blast_radius
    affected_services = result.affected_services or []
    if affected_services or blast_radius:
        st.markdown("### Blast Radius")
        if affected_services:
            pills_html = " ".join(
                f'<span class="service-pill">{svc}</span>' for svc in affected_services
            )
            st.markdown(
                f'<div style="margin: 8px 0;">{pills_html}</div>',
                unsafe_allow_html=True,
            )
        if isinstance(blast_radius, dict) and blast_radius:
            with st.expander("Blast radius details", expanded=False):
                for k, v in blast_radius.items():
                    st.markdown(f"**{k}:** {v}")

    # --- Incident Timeline ---
    st.markdown("### Incident Timeline")
    timeline_events = result.incident_timeline or []
    if timeline_events:
        from incidentagent.ui.components.timeline import render_timeline
        render_timeline(timeline_events)
    else:
        st.info("No timeline events recorded.")

    # --- Evidence Cards ---
    st.markdown("### Evidence by Agent")
    full_evidence = result.full_evidence or []
    if full_evidence:
        from incidentagent.ui.components.evidence_card import render_evidence_cards
        render_evidence_cards(full_evidence)
    else:
        summary_evidence = result.evidence_summary or []
        if summary_evidence:
            for item in summary_evidence:
                st.markdown(
                    f"**{item.get('agent', 'Agent')}** — {item.get('findings', 0)} findings "
                    f"(confidence: {int(item.get('confidence', 0) * 100)}%)"
                )
        else:
            st.info("No evidence details available.")

    # --- Remediation Panel ---
    st.markdown("### Remediation Plan")
    if result.remediation:
        from incidentagent.ui.components.remediation_panel import render_remediation_panel
        render_remediation_panel(result.remediation)
    else:
        st.info("No remediation plan generated.")

    # --- Alternative Hypotheses ---
    if result.alternative_hypotheses:
        st.markdown("### Alternative Hypotheses")
        with st.expander(f"{len(result.alternative_hypotheses)} alternative hypothesis(es)", expanded=False):
            for alt in result.alternative_hypotheses:
                alt_conf = int(alt.confidence * 100)
                alt_cat = alt.category.value if hasattr(alt.category, "value") else str(alt.category)
                st.markdown(f"**Rank {alt.rank}** ({alt_cat}, {alt_conf}% confidence)")
                st.markdown(f"> {alt.hypothesis}")
                st.markdown("---")


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------
def main() -> None:
    _init_session_state()
    _render_header()
    confidence_threshold = _render_sidebar()

    current_status = st.session_state.get("investigation_status", "idle")

    # Show form only when idle or after completion
    if current_status in ("idle", "complete", "error"):
        form_data = _render_alert_form()

        if current_status == "error":
            error_msg = st.session_state.get("investigation_error", "Unknown error")
            st.error(f"Investigation failed: {error_msg}")

        if form_data is not None:
            # Validate required fields
            if not form_data["alert_id"]:
                st.error("Alert ID is required.")
                return
            if not form_data["title"]:
                st.error("Alert title is required.")
                return

            # Persist form data so it survives the rerun
            st.session_state["pending_form_data"] = form_data
            st.session_state["investigation_status"] = "running"
            st.session_state["investigation_result"] = None
            st.session_state["investigation_error"] = None
            st.rerun()

    elif current_status == "running":
        st.markdown("---")
        st.markdown("## Live Investigation")

        # Retrieve form data persisted from the submit step.
        # Fall back to demo defaults if somehow missing (e.g. direct page load).
        last_form: Dict[str, Any] = st.session_state.get("pending_form_data") or {
            "alert_id": "alert-demo-001",
            "source": "prometheus",
            "title": "High error rate on payment-service",
            "description": "Error rate exceeded 5% threshold for 5 minutes",
            "severity": "critical",
            "service": "payment-service",
            "environment": "production",
            "namespace": "payments",
        }

        agent_steps = [
            "Triage Agent — classifying alert type and building priority queue",
            "DeployAgent — checking recent deployments and code changes",
            "LogsAgent — scanning logs for error patterns and stack traces",
            "MetricsAgent — analysing Prometheus metrics for anomalies",
            "K8sAgent — inspecting Kubernetes pod events and resource limits",
            "RunbookAgent — searching knowledge base for matching runbooks",
            "MemoryAgent — querying historical incidents for similar patterns",
            "Synthesizing — building root cause hypotheses from evidence",
            "Remediating — generating safe remediation plan with guardrails",
        ]

        progress_bar = st.progress(0, text="Starting investigation...")
        status_placeholder = st.empty()

        def _update_ui(step_index: int, label: str) -> None:
            pct = int((step_index + 1) / len(agent_steps) * 100)
            progress_bar.progress(pct / 100, text=label)
            status_placeholder.info(f"Running: {label}")

        # We cannot truly stream because asyncio.run() is blocking.
        # Show the first step, run the investigation, then rerun to show results.
        _update_ui(0, agent_steps[0])

        with st.spinner("Investigation running — this may take 30-120 seconds..."):
            _run_investigation(last_form)

        st.rerun()

    # Render results if available
    if st.session_state.get("investigation_status") == "complete":
        _render_results()


if __name__ == "__main__":
    main()
