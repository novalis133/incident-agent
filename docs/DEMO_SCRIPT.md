# IncidentIQ Demo Script

## Video Structure (3 minutes)

### 0:00 - 0:30 | The Problem

**Narration:**
"It's 3am. PagerDuty fires. Your payment service is throwing 500 errors.
Enterprise downtime costs $5,600 per minute. An engineer wakes up, opens 5 different tools -
logs in Elasticsearch, metrics in Grafana, deployments in Kubernetes, runbooks in Confluence.
50 minutes later, they find the root cause: a bad deployment.

What if an AI agent could do that investigation in 2 minutes, before you even wake up?"

**Visual:** Show a PagerDuty alert screen, then montage of tools being switched between.

---

### 0:30 - 1:30 | Live Demo

**Narration:**
"This is IncidentIQ - an autonomous AI agent built on DigitalOcean Gradient."

**Actions:**
1. Open the Streamlit dashboard
2. Show the alert submission form
3. Enter: "High error rate on payment-service" / severity: critical / service: payment-service
4. Click "Investigate"
5. Show the real-time progress as agents work:
   - Triage Agent classifies the alert
   - Deploy Agent finds a recent deployment (v2.3.1)
   - Logs Agent finds ConnectionPoolExhaustedException across multiple pods
   - Metrics Agent shows connection pool at 100% capacity
   - K8s Agent reports pod restarts
   - Runbook Agent matches "Connection Pool Exhaustion" runbook
   - Memory Agent finds a similar past incident

**Key callout:** "Six specialist agents, working in sequence, each building on the previous one's findings."

---

### 1:30 - 2:30 | Results Walkthrough

**Narration:**
"In under 2 minutes, IncidentIQ has completed the investigation."

**Show each section:**
1. **Root Cause:** "Deployment of payment-service v2.3.1 introduced a connection pool configuration regression"
2. **Confidence:** 92%
3. **Timeline:** Chronological events from deployment to error spike
4. **Evidence Cards:** Deploy findings, log errors, metric anomalies
5. **Remediation:** Safe rollback steps with guardrails applied
6. **Past Incident Match:** Similar incident resolved by rollback

**Key callout:** "Notice the guardrails - dangerous commands are blocked, high-risk operations require approval."

---

### 2:30 - 3:00 | Gradient Features

**Narration:**
"Built entirely on DigitalOcean Gradient's AI platform."

**Show quickly:**
1. **ADK:** `@entrypoint`, `@trace_tool`, `@trace_llm`, `@trace_retriever` decorators in code
2. **Knowledge Bases:** Runbooks and past incidents stored and searched via Gradient KB
3. **Agent Routing:** Dynamic sub-agent selection based on triage results
4. **Function Calling:** Each agent declares tools (log search, metric queries, K8s events)
5. **Guardrails:** Blocked patterns and risk assessment on remediation
6. **GPU Training:** Custom log anomaly classifier trained on Gradient GPU
7. **Evaluation:** Automated benchmark suite with accuracy metrics

**Closing:** "IncidentIQ - because at 3am, you shouldn't have to be the one investigating."

---

## Recording Tips

- Use OBS Studio for screen recording
- Resolution: 1920x1080
- Highlight cursor movements
- Use dark mode on all tools
- Keep narration pace steady
- Total target: 2:30 - 3:00
