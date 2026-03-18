# IncidentAgent

> Autonomous AI Agent for DevOps Incident Investigation

[![DigitalOcean Gradient](https://img.shields.io/badge/Powered%20by-DigitalOcean%20Gradient-0080FF)](https://www.digitalocean.com/products/gradient)
[![Live](https://img.shields.io/badge/Live-incidentiq--a82rg.ondigitalocean.app-00FF9C)](https://incidentiq-a82rg.ondigitalocean.app)

When PagerDuty fires at 3am, IncidentAgent investigates before you wake up. It analyzes logs, correlates metrics, identifies root cause, and suggests fixes — all in under 2 minutes.

**Live Demo:** https://incidentiq-a82rg.ondigitalocean.app

## Problem

Enterprise downtime costs **$5,600 per minute**. When incidents occur:
- Engineers waste 30-60 minutes on initial investigation
- Context switching between 5+ tools (logs, metrics, traces, runbooks)
- Tribal knowledge locked in senior engineers' heads
- Same incidents repeat because learnings aren't captured

## Solution

IncidentAgent is an autonomous multi-agent system that:

1. **Triages** alerts automatically (severity, affected services)
2. **Investigates** using 6 specialist agents (Deploy, Logs, Metrics, K8s, Runbook, Memory)
3. **Identifies** root cause with confidence scores
4. **Suggests** safe remediation with guardrails blocking dangerous commands
5. **Learns** from resolved incidents via Knowledge Bases

## Architecture

```
                         IncidentAgent Pipeline

  Alert ──> [ Triage Agent ] ──> [ Investigator Master ]
                                        │
                    ┌───────────────────┼───────────────────┐
                    ▼                   ▼                   ▼
              [ DeployAgent ]    [ LogsAgent ]      [ MetricsAgent ]
              [ K8sAgent    ]    [ RunbookAgent ]   [ MemoryAgent  ]
                    │                   │                   │
                    └───────────────────┼───────────────────┘
                                        ▼
                              [ Root Cause Synthesis ]
                                        │
                                        ▼
                              [ Remediation Agent ]
                              (with Guardrails)
```

## Results

| Metric | Value |
|--------|-------|
| Alert Type Accuracy | **100%** (20/20 eval cases) |
| Confidence Pass Rate | **100%** |
| Avg Confidence Score | **0.912** |
| Avg Latency | **0.13s** |
| P95 Latency | **2.45s** |

## Quick Start

### 1. Clone and Install

```bash
git clone https://github.com/novalis133/incident-agent.git
cd incident-agent/incidentagent
pip install -r requirements.txt
```

### 2. Run the Streamlit Dashboard

```bash
cd incident-agent/incidentagent
streamlit run incidentagent/ui/dashboard.py
```

This opens the dashboard at **http://localhost:8501** where you can:
- Click **"Load Demo Alert"** to pre-fill a sample incident
- Click **"Investigate"** to watch 6 agents investigate in real-time
- View results across 5 tabs: Root Cause, Evidence, Timeline, Remediation, Metrics

### 3. Run the API Server

```bash
cd incident-agent/incidentagent
uvicorn incidentagent.api.app:app --host 0.0.0.0 --port 8000
```

API available at **http://localhost:8000** with docs at **/docs**.

### 4. Docker (both services)

```bash
cd incident-agent/incidentagent
cp .env.example .env
docker-compose up -d
# API:       http://localhost:8000
# Dashboard: http://localhost:8501
```

## Connecting Alerts

### Via API (POST)

Submit an alert to trigger an investigation:

```bash
curl -X POST http://localhost:8000/api/alerts \
  -H "Content-Type: application/json" \
  -d '{
    "id": "alert-001",
    "source": "prometheus",
    "title": "High error rate on payment-service",
    "description": "Error rate exceeded 5% threshold for 5 minutes",
    "severity": "critical",
    "service": "payment-service",
    "fired_at": "2026-03-18T03:15:00Z"
  }'
```

This returns an `investigation_id`. Poll for results:

```bash
curl http://localhost:8000/api/investigations/{investigation_id}
```

### Via Streamlit Dashboard

1. Open http://localhost:8501
2. Fill in the alert form (or click "Load Demo Alert")
3. Click "Investigate"
4. Watch agents work in real-time and review results in the tabbed panel

### Via Prometheus Alertmanager Webhook

Point your Alertmanager config to the API:

```yaml
# alertmanager.yml
receivers:
  - name: incidentagent
    webhook_configs:
      - url: http://your-host:8000/api/alerts
        send_resolved: false
```

### Via PagerDuty Webhook

Configure a PagerDuty webhook to POST to `/api/alerts`. The API accepts any JSON payload with `title`, `severity`, and `service` fields.

## Running Tests

```bash
cd incident-agent/incidentagent

# Unit tests (74 tests)
python -m pytest tests/ -v

# Evaluation benchmark (20 cases)
python -m tests.eval_runner
```

## Training the ML Model

```bash
cd incident-agent/incidentagent

# Generate training data (850 synthetic log lines)
python -m models.generate_training_data

# Train TF-IDF + LogisticRegression classifier
python -m models.train_classifier

# Train with GPU (if CUDA available)
python -m models.train_classifier --use-gpu
```

## Gradient Features Used

| Gradient Feature | Where It's Used | Code Location |
|---|---|---|
| **Agent Development Kit (ADK)** | `@entrypoint` on main, `@trace_tool`/`@trace_llm`/`@trace_retriever` on all agents | `main.py`, all agent files |
| **Knowledge Bases** | Runbook search + past incident lookup | `agents/sub_agents/runbook.py`, `memory.py` |
| **Agent Routing** | Dynamic sub-agent selection based on triage priority queue | `agents/investigator.py` |
| **Function Calling** | Each sub-agent declares tools via `get_tools()` | All sub-agent files |
| **Guardrails** | Blocks dangerous commands (rm -rf, DROP DATABASE, etc.) | `agents/remediation.py` |
| **GPU Training** | TF-IDF + LogisticRegression log classifier | `models/train_classifier.py` |
| **Evaluation** | 20-case benchmark with accuracy/confidence/latency metrics | `tests/eval_runner.py` |

## Project Structure

```
incident-agent/
├── README.md
├── Dockerfile
└── incidentagent/
    ├── incidentagent/
    │   ├── main.py              # Gradient ADK entrypoint
    │   ├── agents/
    │   │   ├── triage.py        # Alert classification
    │   │   ├── investigator.py  # Agent orchestrator
    │   │   ├── remediation.py   # Safe fix generation
    │   │   └── sub_agents/      # 6 specialist agents
    │   ├── schemas/             # Pydantic models
    │   ├── api/                 # FastAPI endpoints
    │   ├── ui/                  # Streamlit dashboard
    │   ├── llm/                 # LLM client
    │   └── knowledge/           # KB client
    ├── models/                  # ML classifier
    ├── tests/                   # Tests + eval benchmark
    ├── knowledge/               # Runbooks data
    ├── requirements.txt
    ├── Dockerfile
    └── docker-compose.yml
```

## Tech Stack

- **Agent Framework**: DigitalOcean Gradient ADK
- **LLM**: Gradient Serverless (Claude)
- **Knowledge Base**: Gradient Knowledge Bases
- **ML**: scikit-learn (TF-IDF + LogisticRegression)
- **API**: FastAPI
- **Dashboard**: Streamlit
- **Deployment**: DigitalOcean App Platform

## Hackathon

Built for the **DigitalOcean Gradient AI Hackathon** (March 2026)

---

**Built for the DigitalOcean Gradient AI Hackathon**
