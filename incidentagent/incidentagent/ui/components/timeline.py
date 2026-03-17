"""
Timeline Component

Renders a vertical timeline of incident events with severity-colored dots.
Each event is a dict with keys: timestamp, event, source, severity.
"""

from typing import Any, Dict, List

import streamlit as st


_SEVERITY_COLORS: Dict[str, str] = {
    "critical": "#ff4444",
    "high": "#ff8800",
    "medium": "#ffcc00",
    "low": "#44bb44",
    "info": "#4488ff",
}

_SEVERITY_BG: Dict[str, str] = {
    "critical": "rgba(255, 68, 68, 0.1)",
    "high": "rgba(255, 136, 0, 0.1)",
    "medium": "rgba(255, 204, 0, 0.1)",
    "low": "rgba(68, 187, 68, 0.1)",
    "info": "rgba(68, 136, 255, 0.1)",
}


def _format_timestamp(ts: Any) -> str:
    """Format a timestamp value to a readable string."""
    if ts is None:
        return "Unknown time"
    if hasattr(ts, "strftime"):
        return ts.strftime("%Y-%m-%d %H:%M:%S UTC")
    return str(ts)


def _build_event_html(event: Dict[str, Any], index: int, total: int) -> str:
    """Build HTML for a single timeline event."""
    severity = str(event.get("severity", "info")).lower()
    color = _SEVERITY_COLORS.get(severity, "#4488ff")
    bg_color = _SEVERITY_BG.get(severity, "rgba(68, 136, 255, 0.1)")
    timestamp = _format_timestamp(event.get("timestamp"))
    event_text = event.get("event", "Unknown event")
    source = event.get("source", "unknown")

    connector_html = (
        f'<div style="width: 2px; height: 20px; background: #333; margin: 0 auto;"></div>'
        if index < total - 1
        else ""
    )

    return f"""
    <div style="display: flex; align-items: flex-start; margin-bottom: 4px;">
        <div style="display: flex; flex-direction: column; align-items: center; min-width: 20px; margin-right: 16px;">
            <div style="
                width: 16px;
                height: 16px;
                border-radius: 50%;
                background-color: {color};
                border: 2px solid {color};
                box-shadow: 0 0 8px {color}66;
                flex-shrink: 0;
                margin-top: 4px;
            "></div>
            {connector_html}
        </div>
        <div style="
            flex: 1;
            background: {bg_color};
            border: 1px solid {color}44;
            border-left: 3px solid {color};
            border-radius: 6px;
            padding: 10px 14px;
            margin-bottom: 4px;
        ">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 6px;">
                <span style="color: {color}; font-weight: 600; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.05em;">
                    {severity}
                </span>
                <span style="color: #888; font-size: 0.75rem; font-family: monospace;">
                    {timestamp}
                </span>
            </div>
            <div style="color: #e0e0e0; font-size: 0.92rem; margin-top: 4px; line-height: 1.4;">
                {event_text}
            </div>
            <div style="color: #666; font-size: 0.75rem; margin-top: 4px;">
                Source: <span style="color: #aaa;">{source}</span>
            </div>
        </div>
    </div>
    """


def render_timeline(events: List[Dict[str, Any]]) -> None:
    """
    Render a vertical timeline of incident events.

    Args:
        events: List of event dicts. Each dict should contain:
                - timestamp: datetime or str - when the event occurred
                - event: str - description of the event
                - source: str - which system/agent produced this
                - severity: str - critical/high/medium/low/info
    """
    if not events:
        st.info("No timeline events recorded for this investigation.")
        return

    st.markdown(
        """
        <style>
        .timeline-container {
            padding: 8px 0;
            max-height: 600px;
            overflow-y: auto;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    total = len(events)
    html_parts = ['<div class="timeline-container">']
    for i, event in enumerate(events):
        html_parts.append(_build_event_html(event, i, total))
    html_parts.append("</div>")

    st.markdown("".join(html_parts), unsafe_allow_html=True)
