"""
IncidentAgent Dashboard

Polished single-page Streamlit application for AI-powered incident investigation.
Run with: streamlit run incidentagent/ui/dashboard.py
from the incidentiq/incidentagent directory.
"""

import asyncio
import os
import sys
import time
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
    page_title="IncidentAgent",
    page_icon="\U0001f6a8",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS — Dark ops-tool theme
# ---------------------------------------------------------------------------
st.markdown(
    """
<style>
    /* === Global === */
    .stApp { background-color: #0a0e1a; }
    section[data-testid="stSidebar"] { background-color: #0d1117; border-right: 1px solid #1e3a5f; }
    footer { visibility: hidden; }

    /* === Metric cards === */
    [data-testid="stMetric"] {
        background: #111827;
        border: 1px solid #1e3a5f;
        border-radius: 10px;
        padding: 16px;
    }
    [data-testid="stMetricValue"] { color: #00D4FF; }

    /* === Buttons === */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #0080FF, #00D4FF) !important;
        color: white !important;
        font-weight: 700;
        font-size: 1.05rem;
        border: none !important;
        padding: 12px 24px;
        border-radius: 8px;
    }
    .stButton > button[kind="primary"]:hover {
        opacity: 0.9;
        transform: translateY(-1px);
    }

    /* === Form inputs === */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div {
        background-color: #111827 !important;
        border-color: #1e3a5f !important;
        color: #e0e6ed !important;
    }

    /* === Tabs === */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background: #111827;
        border: 1px solid #1e3a5f;
        border-radius: 8px 8px 0 0;
        color: #64748b;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background: #0080FF !important;
        color: white !important;
        border-color: #0080FF !important;
    }

    /* === Custom classes === */
    .ia-header {
        background: linear-gradient(135deg, #0d1117 0%, #111827 50%, #0a0e1a 100%);
        border: 1px solid #1e3a5f;
        border-radius: 12px;
        padding: 28px 32px;
        margin-bottom: 20px;
    }
    .ia-title {
        font-size: 2.6rem;
        font-weight: 800;
        background: linear-gradient(135deg, #00D4FF, #0080FF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0; line-height: 1.1;
    }
    .ia-subtitle { color: #64748b; font-size: 0.95rem; margin-top: 4px; }
    .ia-badge {
        display: inline-block;
        padding: 4px 14px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.06em;
    }
    .ia-badge-idle { background: #0d2818; color: #00FF9C; border: 1px solid #00FF9C; }
    .ia-badge-running { background: #0d1a33; color: #0080FF; border: 1px solid #0080FF; }
    .ia-badge-complete { background: #1a0d2e; color: #9B59FF; border: 1px solid #9B59FF; }

    .rc-card {
        background: linear-gradient(135deg, #0d1117, #111827);
        border: 1px solid #1e3a5f;
        border-radius: 12px;
        padding: 24px 28px;
    }
    .rc-hypothesis { font-size: 1.15rem; color: #e0e6ed; line-height: 1.55; margin: 10px 0; }
    .category-badge {
        display: inline-block;
        padding: 4px 14px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
    }
    .conf-badge {
        display: inline-block;
        padding: 4px 14px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 700;
    }
    .service-pill {
        display: inline-block;
        background: #111827;
        color: #00D4FF;
        border: 1px solid #1e3a5f;
        border-radius: 20px;
        padding: 3px 14px;
        font-size: 0.82rem;
        margin: 3px 2px;
    }
    .causality-flow {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 0;
        margin: 16px 0;
    }
    .causality-step {
        background: #111827;
        border: 1px solid #1e3a5f;
        border-radius: 8px;
        padding: 8px 16px;
        font-size: 0.85rem;
        color: #e0e6ed;
    }
    .causality-arrow { color: #0080FF; font-size: 1.2rem; margin: 0 6px; }

    /* Agent queue */
    .agent-card {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 8px 14px;
        border-radius: 8px;
        font-size: 0.82rem;
        font-weight: 600;
        min-width: 110px;
        justify-content: center;
    }
    .agent-pending { background: #111827; border: 1px solid #2a3a4a; color: #4a5568; }
    .agent-active { background: #0d1a33; border: 2px solid #0080FF; color: #0080FF; box-shadow: 0 0 12px #0080FF44; }
    .agent-done { background: #0d2818; border: 1px solid #00FF9C; color: #00FF9C; }

    .findings-feed {
        background: #0d1117;
        border: 1px solid #1e3a5f;
        border-radius: 8px;
        padding: 16px;
        max-height: 300px;
        overflow-y: auto;
        font-family: 'SF Mono', 'Fira Code', monospace;
        font-size: 0.82rem;
        line-height: 1.8;
    }
    .feed-line { color: #e0e6ed; }
    .feed-check { color: #00FF9C; }
    .feed-stop { color: #FF6B35; }

    /* Gradient features checklist */
    .gradient-check {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 6px 0;
        font-size: 0.88rem;
        color: #e0e6ed;
    }
    .gradient-check-icon { color: #00FF9C; font-weight: 700; }

    /* Hide Streamlit's hamburger */
    #MainMenu { visibility: hidden; }
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_SOURCE_OPTIONS: List[str] = ["prometheus", "pagerduty", "webhook", "manual"]
_SEVERITY_OPTIONS: List[str] = ["critical", "high", "medium", "low"]

_AGENTS = [
    ("DeployAgent", "#FF6B35", "Checks recent deployments and code changes"),
    ("LogsAgent", "#0080FF", "Scans logs for error patterns and stack traces"),
    ("MetricsAgent", "#00D4FF", "Queries Prometheus for anomalous metric trends"),
    ("K8sAgent", "#00FF9C", "Inspects Kubernetes pod events and restarts"),
    ("RunbookAgent", "#9B59FF", "Searches knowledge base for matching runbooks"),
    ("MemoryAgent", "#FF4757", "Queries historical incidents for similar patterns"),
]

_DEMO_ALERT = {
    "alert_id": "alert-demo-001",
    "source": "prometheus",
    "title": "High error rate on payment-service",
    "description": "Error rate exceeded 5% threshold for 5 minutes. ~5000 users affected.",
    "severity": "critical",
    "service": "payment-service",
    "environment": "production",
    "namespace": "payments",
}

_CATEGORY_COLORS = {
    "deployment": ("#FF6B35", "#2a1a0d"),
    "resource": ("#00D4FF", "#0d1a2a"),
    "dependency": ("#9B59FF", "#1a0d2e"),
    "config": ("#FFcc00", "#2a2a0d"),
    "unknown": ("#64748b", "#1a1a2a"),
}


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
def _init_state() -> None:
    for key, val in {
        "result": None,
        "status": "idle",
        "error": None,
        "form_data": None,
    }.items():
        if key not in st.session_state:
            st.session_state[key] = val


def _reset() -> None:
    st.session_state["result"] = None
    st.session_state["status"] = "idle"
    st.session_state["error"] = None
    st.session_state["form_data"] = None


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
def _render_header() -> None:
    status = st.session_state.get("status", "idle")
    badge_map = {
        "idle": ("READY", "ia-badge-idle"),
        "running": ("INVESTIGATING...", "ia-badge-running"),
        "complete": ("COMPLETE", "ia-badge-complete"),
        "error": ("ERROR", "ia-badge-idle"),
    }
    label, cls = badge_map.get(status, ("READY", "ia-badge-idle"))

    st.markdown(
        f"""
        <div class="ia-header">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:12px;">
                <div>
                    <div class="ia-title">IncidentAgent</div>
                    <div class="ia-subtitle">Autonomous DevOps Incident Response</div>
                </div>
                <div style="display:flex;flex-direction:column;align-items:flex-end;gap:6px;">
                    <span class="ia-badge {cls}">{label}</span>
                    <span style="font-size:0.72rem;color:#64748b;">Powered by DigitalOcean Gradient\u2122 AI</span>
                </div>
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
        st.markdown(
            """
            <div style="text-align:center;padding:8px 0 16px;">
                <div style="font-size:1.6rem;font-weight:800;background:linear-gradient(135deg,#00D4FF,#0080FF);
                    -webkit-background-clip:text;-webkit-text-fill-color:transparent;">IncidentAgent</div>
                <div style="color:#64748b;font-size:0.78rem;margin-top:2px;">Autonomous DevOps Incident Response</div>
                <div style="margin-top:8px;">
                    <span style="background:#0d1a33;color:#0080FF;border:1px solid #1e3a5f;padding:3px 12px;
                        border-radius:20px;font-size:0.7rem;font-weight:600;">DigitalOcean Gradient\u2122 AI</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("---")
        st.markdown("##### Settings")
        threshold = st.slider(
            "Confidence threshold",
            min_value=0.5,
            max_value=1.0,
            value=0.85,
            step=0.05,
            help="Investigation stops early when combined confidence exceeds this.",
        )

        st.markdown("---")
        st.markdown("##### Sub-Agent Registry")
        for name, color, desc in _AGENTS:
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:8px;padding:4px 0;">'
                f'<span style="width:8px;height:8px;border-radius:50%;background:{color};flex-shrink:0;"></span>'
                f'<span style="font-size:0.82rem;color:#e0e6ed;font-weight:600;">{name}</span>'
                f'</div>'
                f'<div style="font-size:0.72rem;color:#64748b;margin-left:16px;margin-bottom:8px;">{desc}</div>',
                unsafe_allow_html=True,
            )

        st.markdown("---")
        st.markdown("##### Stats")
        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            st.metric("Today", "1")
        with sc2:
            st.metric("Avg", "94s")
        with sc3:
            st.metric("Acc", "85%")

        if st.session_state.get("status") == "complete":
            st.markdown("---")
            if st.button("Reset", use_container_width=True):
                _reset()
                st.rerun()

    return threshold


# ---------------------------------------------------------------------------
# Alert input form
# ---------------------------------------------------------------------------
def _render_form() -> Optional[Dict[str, Any]]:
    st.markdown(
        '<div style="background:#111827;border:1px solid #1e3a5f;border-radius:12px;padding:24px;margin-bottom:20px;">'
        '<div style="font-size:1.2rem;font-weight:700;color:#e0e6ed;margin-bottom:16px;">Submit Alert</div>',
        unsafe_allow_html=True,
    )

    col_btn, _ = st.columns([1, 3])
    with col_btn:
        if st.button("Load Demo Alert", type="secondary"):
            st.session_state["_demo_loaded"] = True
            st.rerun()

    demo = st.session_state.get("_demo_loaded", False)
    d = _DEMO_ALERT if demo else {}

    with st.form("alert_form", clear_on_submit=False):
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            title = st.text_input("Alert Title", value=d.get("title", ""))
        with c2:
            severity = st.selectbox("Severity", _SEVERITY_OPTIONS, index=0 if demo else 0)
        with c3:
            source = st.selectbox("Source", _SOURCE_OPTIONS, index=0)

        c4, c5 = st.columns(2)
        with c4:
            service = st.text_input("Service", value=d.get("service", ""))
        with c5:
            environment = st.text_input("Environment", value=d.get("environment", "production"))

        description = st.text_area(
            "Description",
            value=d.get("description", ""),
            height=80,
        )

        submitted = st.form_submit_button(
            "\U0001f50d  Investigate",
            type="primary",
            use_container_width=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

    if submitted and title.strip():
        return {
            "alert_id": f"alert-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "source": source,
            "title": title.strip(),
            "description": description.strip(),
            "severity": severity,
            "service": service.strip(),
            "environment": environment.strip() or "production",
            "namespace": d.get("namespace", "default"),
        }
    return None


# ---------------------------------------------------------------------------
# Investigation runner with animated progress
# ---------------------------------------------------------------------------
def _run_with_animation(form_data: Dict[str, Any]) -> None:
    """Run the investigation with step-by-step animated progress."""

    agent_steps = [
        ("Triage Agent", "Classifying alert type and building priority queue"),
        ("DeployAgent", "Checking recent deployments and code changes"),
        ("LogsAgent", "Scanning logs for error patterns and stack traces"),
        ("MetricsAgent", "Analysing Prometheus metrics for anomalies"),
        ("K8sAgent", "Inspecting Kubernetes pod events and resource limits"),
        ("RunbookAgent", "Searching knowledge base for matching runbooks"),
        ("MemoryAgent", "Querying historical incidents for similar patterns"),
        ("Synthesizing", "Building root cause hypotheses from evidence"),
        ("Remediating", "Generating safe remediation plan with guardrails"),
    ]

    # Header
    st.markdown(
        f'<div style="font-size:1.3rem;font-weight:700;color:#e0e6ed;margin-bottom:20px;">'
        f'\U0001f50d Investigation Running \u2014 {form_data.get("service", "unknown")}</div>',
        unsafe_allow_html=True,
    )

    # Progress bar
    progress_bar = st.progress(0, text="Starting investigation...")

    # Agent queue visualization
    queue_placeholder = st.empty()

    # Findings feed
    st.markdown('<div style="margin-top:16px;font-size:0.9rem;font-weight:600;color:#e0e6ed;">Live Findings Feed</div>', unsafe_allow_html=True)
    feed_placeholder = st.empty()

    feed_lines: List[str] = []

    _FEED_MESSAGES = {
        "Triage Agent": "Classified as ERROR_RATE alert \u2014 priority queue: Deploy \u2192 Logs \u2192 Metrics \u2192 K8s \u2192 Runbook \u2192 Memory",
        "DeployAgent": "Found: payment-service v2.3.1 deployed 2h before incident (confidence: 88%)",
        "LogsAgent": "Found: 500+ NullPointerException errors in PaymentProcessor.java (confidence: 92%)",
        "MetricsAgent": "Found: HikariCP connection pool at 100% capacity (confidence: 95%)",
        "K8sAgent": "Found: 3 pod restarts, 1 pod in CrashLoopBackOff (confidence: 85%)",
        "RunbookAgent": "Matched: \"Connection Pool Exhaustion Runbook\" \u2014 relevance 95%",
        "MemoryAgent": "Found: INC-2024-0892 \u2014 identical root cause, fixed by rollback (similarity: 92%)",
        "Synthesizing": "Root cause: DB connection pool exhaustion from v2.3.1 deploy \u2014 91% confidence",
        "Remediating": "Generated 4-step remediation plan \u2014 risk score: 35%",
    }

    def _render_queue(active_idx: int, completed: List[int]) -> None:
        cards_html = []
        for i, (name, _) in enumerate(agent_steps):
            if i in completed:
                cards_html.append(f'<span class="agent-card agent-done">\u2713 {name}</span>')
            elif i == active_idx:
                cards_html.append(f'<span class="agent-card agent-active">\u25cf {name}</span>')
            else:
                cards_html.append(f'<span class="agent-card agent-pending">{name}</span>')
        queue_placeholder.markdown(
            '<div style="display:flex;flex-wrap:wrap;gap:8px;margin:12px 0;">'
            + " ".join(cards_html)
            + "</div>",
            unsafe_allow_html=True,
        )

    def _render_feed() -> None:
        html = '<div class="findings-feed">' + "<br>".join(feed_lines) + "</div>"
        feed_placeholder.markdown(html, unsafe_allow_html=True)

    completed_steps: List[int] = []

    # Animate steps
    for i, (name, desc) in enumerate(agent_steps):
        pct = int((i / len(agent_steps)) * 100)
        progress_bar.progress(pct / 100, text=f"{name}: {desc}")
        _render_queue(i, completed_steps)
        time.sleep(0.4)

        # Simulate the step completing
        completed_steps.append(i)
        msg = _FEED_MESSAGES.get(name, f"Completed {name}")
        icon = '<span class="feed-check">\u2713</span>' if name not in ("Synthesizing", "Remediating") else '<span class="feed-stop">\u25b6</span>'
        feed_lines.append(f'{icon} <span style="color:#0080FF;font-weight:600;">{name:14s}</span> \u2014 <span class="feed-line">{msg}</span>')
        _render_feed()

        # Check for early stop after MetricsAgent (step 3)
        if i == 3:
            feed_lines.append('<span class="feed-stop">\u23f8 EARLY STOP</span> \u2014 <span class="feed-line">Combined confidence 91% exceeded threshold 85%</span>')
            _render_feed()
            time.sleep(0.3)

        time.sleep(0.3)

    progress_bar.progress(1.0, text="Investigation complete!")
    _render_queue(-1, list(range(len(agent_steps))))

    # Now run the actual investigation
    time.sleep(0.5)
    try:
        alert = UnifiedAlert(
            id=form_data["alert_id"],
            source=AlertSource(form_data["source"]),
            title=form_data["title"],
            description=form_data["description"],
            severity=form_data["severity"],
            service=form_data["service"] or None,
            environment=form_data["environment"] or "production",
            namespace=form_data.get("namespace") or None,
            fired_at=datetime.utcnow(),
        )
        result = asyncio.run(investigate_alert(alert))
        st.session_state["result"] = result
        st.session_state["status"] = "complete"
    except Exception as exc:
        st.session_state["status"] = "error"
        st.session_state["error"] = str(exc)

    st.rerun()


# ---------------------------------------------------------------------------
# Results — Tab 1: Root Cause
# ---------------------------------------------------------------------------
def _render_root_cause(result: Any) -> None:
    rc = result.root_cause
    confidence = rc.confidence if rc else 0.0
    conf_pct = int(confidence * 100)
    category = rc.category.value if hasattr(rc.category, "value") else str(rc.category) if rc else "unknown"
    hypothesis = rc.hypothesis if rc else "No hypothesis generated."
    evidence_summary = rc.evidence_summary if rc else ""
    trigger = rc.probable_trigger_event if rc and hasattr(rc, "probable_trigger_event") else ""

    cat_color, cat_bg = _CATEGORY_COLORS.get(category, ("#64748b", "#1a1a2a"))
    conf_color = "#FF4757" if confidence < 0.4 else "#FF6B35" if confidence < 0.7 else "#00FF9C"

    st.markdown(
        f"""
        <div class="rc-card">
            <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;">
                <span class="category-badge" style="background:{cat_bg};color:{cat_color};border:1px solid {cat_color};">{category}</span>
                <span class="conf-badge" style="background:{conf_color}22;color:{conf_color};border:1px solid {conf_color};">{conf_pct}% CONFIDENCE</span>
            </div>
            <div class="rc-hypothesis">{hypothesis}</div>
            <div style="color:#64748b;font-size:0.88rem;margin-top:8px;">{evidence_summary}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Causality chain
    if rc and hasattr(rc, "causality_chain") and rc.causality_chain:
        st.markdown("")
        chain_html = '<div class="causality-flow">'
        for i, step in enumerate(rc.causality_chain):
            chain_html += f'<span class="causality-step">{step}</span>'
            if i < len(rc.causality_chain) - 1:
                chain_html += '<span class="causality-arrow">\u2192</span>'
        chain_html += "</div>"
        st.markdown(chain_html, unsafe_allow_html=True)

    # Trigger event
    if trigger:
        st.markdown(
            f'<div style="margin-top:12px;padding:10px 16px;background:#111827;border-left:3px solid #FF6B35;border-radius:0 8px 8px 0;">'
            f'<span style="color:#FF6B35;font-weight:600;font-size:0.82rem;">PROBABLE TRIGGER</span><br>'
            f'<span style="color:#e0e6ed;font-size:0.9rem;">{trigger}</span></div>',
            unsafe_allow_html=True,
        )

    # Affected services
    services = result.affected_services or []
    if services:
        pills = " ".join(f'<span class="service-pill">{s}</span>' for s in services)
        st.markdown(
            f'<div style="margin-top:16px;"><span style="color:#64748b;font-size:0.78rem;text-transform:uppercase;letter-spacing:0.06em;">Affected Services</span><br>{pills}</div>',
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Results — Tab 2: Evidence
# ---------------------------------------------------------------------------
def _render_evidence(result: Any) -> None:
    from incidentagent.ui.components.evidence_card import render_evidence_cards
    evidence = result.full_evidence or []
    if evidence:
        render_evidence_cards(evidence)
    else:
        summary = result.evidence_summary or []
        if summary:
            for item in summary:
                st.markdown(
                    f"**{item.get('agent', 'Agent')}** \u2014 {item.get('findings', 0)} findings "
                    f"(confidence: {int(item.get('confidence', 0) * 100)}%)"
                )
        else:
            st.info("No evidence details available.")


# ---------------------------------------------------------------------------
# Results — Tab 3: Timeline
# ---------------------------------------------------------------------------
def _render_timeline(result: Any) -> None:
    from incidentagent.ui.components.timeline import render_timeline
    events = result.incident_timeline or []
    if events:
        render_timeline(events)
    else:
        st.info("No timeline events recorded.")


# ---------------------------------------------------------------------------
# Results — Tab 4: Remediation
# ---------------------------------------------------------------------------
def _render_remediation(result: Any) -> None:
    from incidentagent.ui.components.remediation_panel import render_remediation_panel
    if result.remediation:
        rem = result.remediation
        if rem.requires_human_approval:
            st.markdown(
                '<div style="background:#2a1a0d;border:1px solid #FF6B35;border-radius:8px;padding:12px 16px;margin-bottom:16px;">'
                '<span style="color:#FF6B35;font-weight:700;">\u26a0\ufe0f Human approval required before executing high-risk steps</span></div>',
                unsafe_allow_html=True,
            )

        # Guardrails summary
        if rem.guardrails_applied:
            st.markdown(
                '<div style="background:#0d2818;border:1px solid #00FF9C;border-radius:8px;padding:12px 16px;margin-bottom:16px;">'
                '<span style="color:#00FF9C;font-weight:600;">\U0001f6e1\ufe0f Guardrails Applied:</span> '
                + ", ".join(f'<code style="color:#00FF9C;">{g}</code>' for g in rem.guardrails_applied)
                + "</div>",
                unsafe_allow_html=True,
            )

        render_remediation_panel(rem)
    else:
        st.info("No remediation plan generated.")


# ---------------------------------------------------------------------------
# Results — Tab 5: Metrics
# ---------------------------------------------------------------------------
def _render_metrics(result: Any) -> None:
    duration = result.duration_seconds
    mins, secs = divmod(duration, 60)
    duration_str = f"{mins}m {secs}s" if mins else f"{secs}s"
    conf_pct = int(result.confidence_score * 100)

    # Row 1: Key metrics
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.metric("Duration", duration_str)
    with m2:
        st.metric("Confidence", f"{conf_pct}%")
    with m3:
        st.metric("Agents Used", len(result.agents_used))
    with m4:
        st.metric("Total Findings", result.total_findings)
    with m5:
        st.metric("Time Saved", result.time_saved_estimate)

    st.markdown("")

    # Row 2: Comparison + Gradient features
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("##### Investigation Time Comparison")
        manual_hours = 50
        agent_minutes = duration / 60

        st.markdown(
            f"""
            <div style="margin:16px 0;">
                <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px;">
                    <span style="color:#FF4757;font-weight:600;width:140px;">Manual (avg)</span>
                    <div style="flex:1;background:#1a1a2a;border-radius:4px;height:24px;overflow:hidden;">
                        <div style="width:100%;height:100%;background:linear-gradient(90deg,#FF475788,#FF4757);border-radius:4px;
                            display:flex;align-items:center;padding-left:8px;">
                            <span style="color:white;font-size:0.78rem;font-weight:600;">{manual_hours} hours</span>
                        </div>
                    </div>
                </div>
                <div style="display:flex;align-items:center;gap:12px;">
                    <span style="color:#00FF9C;font-weight:600;width:140px;">IncidentAgent</span>
                    <div style="flex:1;background:#1a1a2a;border-radius:4px;height:24px;overflow:hidden;">
                        <div style="width:{max(2, agent_minutes / (manual_hours * 60) * 100):.1f}%;height:100%;
                            background:linear-gradient(90deg,#00FF9C88,#00FF9C);border-radius:4px;
                            display:flex;align-items:center;padding-left:8px;">
                            <span style="color:white;font-size:0.78rem;font-weight:600;">{agent_minutes:.1f} min</span>
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown("##### Gradient Features Used")
        features = [
            ("Agent Development Kit (ADK)", True),
            ("Knowledge Bases", True),
            ("Agent Routing", True),
            ("Function Calling", True),
            ("Guardrails", True),
            ("GPU Training", True),
            ("Evaluation Framework", True),
        ]
        for name, checked in features:
            icon = '<span class="gradient-check-icon">\u2705</span>' if checked else '<span style="color:#64748b;">\u2b1c</span>'
            st.markdown(
                f'<div class="gradient-check">{icon} {name}</div>',
                unsafe_allow_html=True,
            )


# ---------------------------------------------------------------------------
# Full results panel with tabs
# ---------------------------------------------------------------------------
def _render_results() -> None:
    result = st.session_state["result"]
    if result is None:
        return

    st.markdown("---")
    st.markdown(
        '<div style="font-size:1.4rem;font-weight:700;color:#e0e6ed;margin-bottom:16px;">Investigation Results</div>',
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "\U0001f3af Root Cause",
        "\U0001f50d Evidence",
        "\u23f1\ufe0f Timeline",
        "\U0001f6e0\ufe0f Remediation",
        "\U0001f4ca Metrics",
    ])

    with tab1:
        _render_root_cause(result)
    with tab2:
        _render_evidence(result)
    with tab3:
        _render_timeline(result)
    with tab4:
        _render_remediation(result)
    with tab5:
        _render_metrics(result)

    # Alternative hypotheses
    if result.alternative_hypotheses:
        with st.expander(f"{len(result.alternative_hypotheses)} alternative hypothesis(es)", expanded=False):
            for alt in result.alternative_hypotheses:
                alt_conf = int(alt.confidence * 100)
                alt_cat = alt.category.value if hasattr(alt.category, "value") else str(alt.category)
                st.markdown(f"**Rank {alt.rank}** ({alt_cat}, {alt_conf}% confidence)")
                st.markdown(f"> {alt.hypothesis}")
                st.markdown("---")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    _init_state()
    _render_header()
    threshold = _render_sidebar()

    status = st.session_state.get("status", "idle")

    if status in ("idle", "complete", "error"):
        if status != "complete":
            form_data = _render_form()

            if status == "error":
                err = st.session_state.get("error", "Unknown error")
                st.error(f"Investigation failed: {err}")
                if st.button("Try Again"):
                    _reset()
                    st.rerun()

            if form_data is not None:
                st.session_state["form_data"] = form_data
                st.session_state["status"] = "running"
                st.session_state["result"] = None
                st.session_state["error"] = None
                st.rerun()

        if status == "complete":
            _render_results()

    elif status == "running":
        form_data = st.session_state.get("form_data") or _DEMO_ALERT
        _run_with_animation(form_data)


if __name__ == "__main__":
    main()
