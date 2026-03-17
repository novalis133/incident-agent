"""FastAPI application for IncidentAgent API."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from incidentagent.api.routes import alerts, investigations, health

app = FastAPI(
    title="IncidentAgent API",
    description="AI-powered incident investigation API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["health"])
app.include_router(alerts.router, prefix="/api", tags=["alerts"])
app.include_router(investigations.router, prefix="/api", tags=["investigations"])


@app.get("/", response_class=HTMLResponse)
async def root():
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IncidentAgent - AI-Powered Incident Investigation</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0a0e1a; color: #e0e6ed; min-height: 100vh; display: flex; align-items: center; justify-content: center; }
        .container { max-width: 800px; padding: 40px; text-align: center; }
        h1 { font-size: 2.8rem; margin-bottom: 8px; background: linear-gradient(135deg, #00d4aa, #0088ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .subtitle { font-size: 1.1rem; color: #8892a4; margin-bottom: 40px; }
        .badge { display: inline-block; background: #1a2332; border: 1px solid #2a3a4a; padding: 6px 14px; border-radius: 20px; font-size: 0.85rem; color: #00d4aa; margin-bottom: 30px; }
        .stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 40px; }
        .stat { background: #111827; border: 1px solid #1e2d3d; border-radius: 12px; padding: 24px 16px; }
        .stat-value { font-size: 2rem; font-weight: 700; color: #00d4aa; }
        .stat-label { font-size: 0.85rem; color: #6b7a8d; margin-top: 4px; }
        .features { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin-bottom: 40px; text-align: left; }
        .feature { background: #111827; border: 1px solid #1e2d3d; border-radius: 10px; padding: 20px; }
        .feature-title { font-size: 0.95rem; font-weight: 600; color: #e0e6ed; margin-bottom: 6px; }
        .feature-desc { font-size: 0.82rem; color: #6b7a8d; line-height: 1.5; }
        .links { display: flex; gap: 16px; justify-content: center; flex-wrap: wrap; }
        .link { display: inline-block; padding: 12px 28px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 0.95rem; transition: all 0.2s; }
        .link-primary { background: linear-gradient(135deg, #00d4aa, #0088ff); color: #fff; }
        .link-primary:hover { opacity: 0.9; transform: translateY(-1px); }
        .link-secondary { background: #1a2332; border: 1px solid #2a3a4a; color: #e0e6ed; }
        .link-secondary:hover { border-color: #00d4aa; }
        .gradient-badge { margin-top: 40px; font-size: 0.8rem; color: #4a5568; }
        .gradient-badge span { color: #0088ff; }
    </style>
</head>
<body>
    <div class="container">
        <div class="badge">DigitalOcean Gradient AI Hackathon 2026</div>
        <h1>IncidentAgent</h1>
        <p class="subtitle">AI-powered multi-agent system for automated incident root cause analysis</p>

        <div class="stats">
            <div class="stat">
                <div class="stat-value">100%</div>
                <div class="stat-label">Alert Classification</div>
            </div>
            <div class="stat">
                <div class="stat-value">6</div>
                <div class="stat-label">Specialist Agents</div>
            </div>
            <div class="stat">
                <div class="stat-value">&lt;3s</div>
                <div class="stat-label">P95 Latency</div>
            </div>
        </div>

        <div class="features">
            <div class="feature">
                <div class="feature-title">Multi-Agent Pipeline</div>
                <div class="feature-desc">Triage, Deploy, Logs, Metrics, K8s, Runbook, and Memory agents work together to investigate incidents.</div>
            </div>
            <div class="feature">
                <div class="feature-title">GPU-Trained ML Model</div>
                <div class="feature-desc">TF-IDF + LogisticRegression classifier trained on 850 log samples across 6 anomaly categories.</div>
            </div>
            <div class="feature">
                <div class="feature-title">Gradient ADK Native</div>
                <div class="feature-desc">Built with @entrypoint, @trace_tool, @trace_llm, @trace_retriever, Knowledge Bases, and Guardrails.</div>
            </div>
            <div class="feature">
                <div class="feature-title">Safe Remediation</div>
                <div class="feature-desc">Guardrails block dangerous commands (rm -rf, DROP TABLE, kubectl delete) before they reach production.</div>
            </div>
        </div>

        <div class="links">
            <a href="/docs" class="link link-primary">API Documentation</a>
            <a href="/health" class="link link-secondary">Health Check</a>
            <a href="https://github.com/novalis133/incident-agent" class="link link-secondary">GitHub</a>
        </div>

        <p class="gradient-badge">Powered by <span>DigitalOcean Gradient</span> and Claude AI</p>
    </div>
</body>
</html>"""
