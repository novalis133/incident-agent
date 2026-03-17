# IncidentIQ Demo Script (3 minutes)

> Record with OBS Studio, 1920x1080, dark mode everywhere, highlight cursor.

---

## Scene 1 — The Problem (0:00 - 0:30)

**Show on screen:** A blank dark slide or text overlay with these words as you speak them.

**Say:**
"It's 3am. PagerDuty fires. Your payment service is throwing 500 errors.
Enterprise downtime costs $5,600 per minute. An engineer opens 5 tools —
logs, metrics, Kubernetes, runbooks, past incidents. 50 minutes later they
find the root cause: a bad deployment.
What if an AI agent could do that in under 2 minutes?"

---

## Scene 2 — Landing Page (0:30 - 0:50)

**Open in browser:**
```
https://incidentiq-a82rg.ondigitalocean.app/
```

**Say:**
"This is IncidentAgent — an autonomous AI investigation system running live on DigitalOcean.
Six specialist agents, a GPU-trained ML model, 100% alert classification accuracy, all under 3 seconds."

**Show on screen:** Scroll the landing page slowly — point out the 3 stats (100%, 6 agents, <3s) and the 4 feature cards.

---

## Scene 3 — API Docs (0:50 - 1:10)

**Open in browser:**
```
https://incidentiq-a82rg.ondigitalocean.app/docs
```

**Say:**
"The API is built with FastAPI. We can submit alerts, track investigations, and check health — all through REST endpoints."

**Show on screen:** Expand the `POST /api/alerts` endpoint to show the schema. Expand `GET /api/investigations/{id}` briefly.

---

## Scene 4 — Live Investigation (1:10 - 2:00)

**In the Swagger UI, click "Try it out" on `POST /api/alerts` and paste:**
```json
{
  "id": "demo-001",
  "source": "pagerduty",
  "title": "High error rate on payment-service",
  "description": "Error rate exceeded 5% threshold for 5 minutes with 5xx responses after v2.3.1 deploy",
  "severity": "critical",
  "service": "payment-service",
  "fired_at": "2026-03-17T21:00:00Z"
}
```

**Click Execute.**

**Say:**
"We submit a critical alert — high error rate on payment-service. The system kicks off an investigation instantly."

**Show on screen:** The response with `investigation_id` and `status: running`.

**Now open the investigation result — paste the investigation_id into `GET /api/investigations/{id}` and execute.**

**Say:**
"In seconds, six agents investigated the incident. The Triage Agent classified it as an error_rate alert. The Deploy Agent found a recent v2.3.1 deployment. The Logs Agent detected ConnectionPoolExhausted exceptions. The Metrics Agent found connection pools at 100%. The K8s Agent spotted pod restarts. And the Runbook Agent matched a known runbook."

**Show on screen:** Scroll through the JSON result — pause on:
- `root_cause` → `hypothesis` and `category`
- `confidence_score`
- `agents_used` list
- `total_findings`
- `remediation` → `summary` and `steps`
- `time_saved_estimate`

---

## Scene 5 — Health Check (2:00 - 2:10)

**Open in browser:**
```
https://incidentiq-a82rg.ondigitalocean.app/health
```

**Say:**
"The service is live and healthy on DigitalOcean App Platform."

---

## Scene 6 — Code Walkthrough (2:10 - 2:40)

**Open in browser:**
```
https://github.com/novalis133/incident-agent
```

**Say:**
"Let me show the Gradient ADK integration in the code."

**Show on screen:** Navigate to these files and briefly highlight the decorated functions:

1. **Main entrypoint** — click `incidentagent/incidentagent/main.py`
   - Show `@entrypoint` on `main()` (line 64)
   - Show `@trace_tool("investigation-pipeline")` on `investigate_alert()` (line 129)

2. **Triage agent** — click `incidentagent/incidentagent/agents/triage.py`
   - Show `@trace_tool("triage-classify")` and `@trace_llm("triage-llm-classify")`

3. **Sub-agents** — click `incidentagent/incidentagent/agents/sub_agents/logs.py`
   - Show `@trace_retriever("logs-error-search")`
   - Show ML classifier integration (`_classify_findings`)

4. **GPU model** — click `incidentagent/models/train_classifier.py`
   - Show TF-IDF + LogisticRegression pipeline and GPU training option

5. **Tests** — click `incidentagent/tests/`
   - Show `test_triage.py` (27 tests), `test_guardrails.py` (30 tests), `eval_dataset.csv` (20 benchmarks)

**Say:**
"We use all 7 Gradient features: ADK entrypoint, trace_tool, trace_llm, trace_retriever, Knowledge Bases, Guardrails, and a GPU-trained custom model."

---

## Scene 7 — Closing (2:40 - 3:00)

**Show on screen:** Go back to the landing page:
```
https://incidentiq-a82rg.ondigitalocean.app/
```

**Say:**
"IncidentAgent. Six AI agents. One root cause. Under 3 seconds.
Because at 3am, you shouldn't have to be the one investigating.
Built on DigitalOcean Gradient."

---

## All Links for Demo

| What | URL |
|------|-----|
| Landing Page | https://incidentiq-a82rg.ondigitalocean.app/ |
| API Docs (Swagger) | https://incidentiq-a82rg.ondigitalocean.app/docs |
| Health Check | https://incidentiq-a82rg.ondigitalocean.app/health |
| Submit Alert | https://incidentiq-a82rg.ondigitalocean.app/docs#/alerts/create_alert_api_alerts_post |
| Get Investigation | https://incidentiq-a82rg.ondigitalocean.app/docs#/investigations/get_investigation_api_investigations__investigation_id__get |
| GitHub Repo | https://github.com/novalis133/incident-agent |
| Main entrypoint | https://github.com/novalis133/incident-agent/blob/main/incidentagent/incidentagent/main.py |
| Triage agent | https://github.com/novalis133/incident-agent/blob/main/incidentagent/incidentagent/agents/triage.py |
| Sub-agents (logs) | https://github.com/novalis133/incident-agent/blob/main/incidentagent/incidentagent/agents/sub_agents/logs.py |
| GPU model trainer | https://github.com/novalis133/incident-agent/blob/main/incidentagent/models/train_classifier.py |
| Tests | https://github.com/novalis133/incident-agent/tree/main/incidentagent/tests |
| Eval dataset | https://github.com/novalis133/incident-agent/blob/main/incidentagent/tests/eval_dataset.csv |

## Alert Payload to Copy-Paste

```json
{
  "id": "demo-001",
  "source": "pagerduty",
  "title": "High error rate on payment-service",
  "description": "Error rate exceeded 5% threshold for 5 minutes with 5xx responses after v2.3.1 deploy",
  "severity": "critical",
  "service": "payment-service",
  "fired_at": "2026-03-17T21:00:00Z"
}
```

## Recording Tips

- OBS Studio, 1920x1080, 30fps
- Dark mode on browser and VS Code
- Zoom browser to 125% so text is readable
- Highlight cursor movements
- Speak slowly and clearly
- Total target: 2:30 - 3:00
