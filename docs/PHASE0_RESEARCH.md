# IncidentAgent - Phase 0: Research & Resource Ingestion

> **Project**: IncidentAgent  
> **Hackathon**: DigitalOcean Gradient AI Hackathon  
> **Deadline**: March 18, 2026  
> **Created**: February 21, 2026  
> **Status**: PHASE 0 - Research Complete

---

## 1. Project Overview

### 1.1 What We're Building

**IncidentAgent** is an autonomous AI agent for DevOps incident investigation that:
- Receives alerts from monitoring systems (PagerDuty, Prometheus, etc.)
- Automatically investigates root cause using logs, metrics, traces
- Suggests remediation based on runbooks and past incidents
- Learns from resolved incidents to improve over time

### 1.2 Elevator Pitch

> "When PagerDuty fires at 3am, IncidentAgent investigates before you wake up. It analyzes logs, correlates metrics, identifies root cause, and suggests fixes — all in under 2 minutes."

### 1.3 Key Differentiators

| Feature | IncidentAgent | Competitors |
|---------|---------------|-------------|
| Runs on Gradient AI | ✅ Full stack | ❌ External APIs |
| Custom trained models | ✅ GPU training | ❌ Generic LLMs |
| Multi-agent routing | ✅ Specialist agents | ❌ Single agent |
| Institutional memory | ✅ Learns from incidents | ❌ Stateless |
| Open source foundation | ✅ HolmesGPT base | ❌ Proprietary |

---

## 2. DigitalOcean Gradient AI Platform

### 2.1 Platform Overview

Gradient AI Platform provides:
- **Serverless Inference**: OpenAI, Anthropic, Google models via API
- **Agent Development Kit (ADK)**: Python toolkit for building agents
- **Knowledge Bases**: RAG with vector search for runbooks/docs
- **Agent Routing**: Route to specialist agents based on context
- **Guardrails**: Safety and content filtering
- **GPU Droplets**: For custom model training
- **Evaluation Framework**: Test and benchmark agents

### 2.2 Gradient ADK (Agent Development Kit)

**Repository**: https://github.com/digitalocean/gradient-adk  
**License**: Apache 2.0  
**Language**: Python  

#### Key Features

```python
# Core decorators
from gradient_adk import entrypoint, trace_llm, trace_tool, trace_retriever

@trace_retriever("search_logs")
async def search_logs(query: str):
    """Retriever spans capture search operations"""
    results = await log_store.search(query)
    return results

@trace_llm("analyze_incident")
async def analyze_incident(context: str):
    """LLM spans capture model calls"""
    response = await llm.generate(context)
    return response

@trace_tool("run_diagnostic")
async def run_diagnostic(command: str):
    """Tool spans capture function execution"""
    return execute_command(command)

@entrypoint
async def main(input: dict, context: dict):
    logs = await search_logs(input["query"])
    analysis = await analyze_incident(f"Context: {logs}")
    return analysis
```

#### CLI Commands

```bash
# Initialize new agent project
gradient agent init

# Run locally with hot-reload
gradient agent run --dev

# Deploy to DigitalOcean
export DIGITALOCEAN_API_TOKEN=your_token
gradient agent deploy

# View traces
gradient agent traces

# Run evaluations
gradient agent evaluate \
  --test-case-name "incident-investigation" \
  --dataset-file test_incidents.csv \
  --categories correctness,context_quality
```

#### Project Structure

```
incident-agent/
├── main.py              # Agent entrypoint with @entrypoint decorator
├── .gradient/agent.yml  # Agent configuration
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables
├── agents/              # Agent implementations
│   ├── triage_agent.py
│   ├── investigator_agent.py
│   ├── rootcause_agent.py
│   └── remediation_agent.py
└── tools/               # Custom tools
    ├── log_search.py
    ├── metric_query.py
    └── runbook_lookup.py
```

#### Framework Compatibility

- ✅ LangGraph (automatic trace capture)
- ✅ LangChain (use trace decorators)
- ✅ CrewAI (use trace decorators)
- ✅ Custom frameworks (use trace decorators)

### 2.3 Gradient Features We MUST Use

For hackathon judging, we need to demonstrate:

| Feature | How We'll Use It |
|---------|------------------|
| **Agent Development Kit** | Build all agents using ADK |
| **Knowledge Bases** | Store runbooks, past incidents, documentation |
| **Agent Routing** | Route to specialist agents (Triage → Investigator → RootCause) |
| **Function Calling** | Tools for log search, metric query, runbook lookup |
| **Guardrails** | Ensure safe remediation suggestions |
| **GPU Training** | Train custom log anomaly classifier |
| **Evaluation Framework** | Benchmark agent accuracy |
| **Serverless Inference** | Use Anthropic/OpenAI via Gradient |

---

## 3. HolmesGPT Analysis

### 3.1 Overview

**Repository**: https://github.com/HolmesGPT/holmesgpt  
**Stars**: 1.8k  
**License**: Apache 2.0  
**Status**: CNCF Sandbox Project  
**Language**: Python  

HolmesGPT is the closest existing project to what we're building. It provides:
- Agentic investigation loop
- 20+ data source integrations
- CLI and API interfaces
- Evaluation framework

### 3.2 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      HolmesGPT                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Alert Sources          Investigation Engine    Outputs     │
│  ┌──────────┐          ┌─────────────────┐    ┌─────────┐  │
│  │Prometheus│─────────▶│  Agentic Loop   │───▶│ Slack   │  │
│  │PagerDuty │          │  ┌───────────┐  │    │ Jira    │  │
│  │OpsGenie  │          │  │ LLM Call  │  │    │ CLI     │  │
│  │Jira      │          │  └─────┬─────┘  │    └─────────┘  │
│  └──────────┘          │        │        │                  │
│                        │  ┌─────▼─────┐  │                  │
│  Data Sources          │  │Tool Select│  │                  │
│  ┌──────────┐          │  └─────┬─────┘  │                  │
│  │Kubernetes│◀─────────│        │        │                  │
│  │Prometheus│          │  ┌─────▼─────┐  │                  │
│  │Loki      │          │  │ Execute   │  │                  │
│  │Datadog   │          │  └─────┬─────┘  │                  │
│  │AWS RDS   │          │        │        │                  │
│  │Confluence│          │  ┌─────▼─────┐  │                  │
│  └──────────┘          │  │Feed Back  │  │                  │
│                        │  └───────────┘  │                  │
│                        └─────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

### 3.3 Key Components to Study

| Component | Location | What to Learn |
|-----------|----------|---------------|
| Agentic Loop | `holmes/core/investigation.py` | How to iterate LLM → tool → result |
| Toolsets | `holmes/plugins/toolsets/` | How to define data source connectors |
| Runbooks | `holmes/core/runbooks.py` | How to inject domain knowledge |
| CLI | `holmes_cli.py` | User interface patterns |

### 3.4 HolmesGPT Gaps (Our Opportunities)

| Gap | IncidentAgent Solution |
|-----|------------------------|
| No custom trained models | Train on Gradient GPU |
| No multi-agent routing | Specialist agents via Gradient Routing |
| No institutional memory | Past incidents in Knowledge Base |
| Kubernetes-biased | Broader infrastructure support |
| No frontend dashboard | Streamlit UI |

---

## 4. Academic Research Summary

### 4.1 Key Papers

#### Paper 1: "Exploring LLM-based Agents for Root Cause Analysis"
- **Authors**: Microsoft Research (Roy et al.)
- **Venue**: FSE 2024
- **URL**: https://arxiv.org/abs/2403.04123
- **Key Finding**: ReAct agents achieve higher factual accuracy than RAG alone
- **Implication**: Use ReAct-style reasoning loop in IncidentAgent

#### Paper 2: "RCAgent: Cloud Root Cause Analysis by Autonomous Agents"
- **Authors**: Alibaba (Wang et al.)
- **Venue**: CIKM 2024
- **URL**: https://arxiv.org/abs/2310.16340
- **Key Finding**: Locally deployed LLMs work with proper stabilization
- **Implication**: Can run on Gradient without external API dependency

#### Paper 3: "Agentic AIOps Framework"
- **Authors**: MDPI Electronics
- **Venue**: April 2025
- **URL**: https://www.mdpi.com/2079-9292/14/9/1775
- **Key Finding**: 33% MTTR reduction, 25.7% resource utilization increase
- **Implication**: Strong ROI metrics to cite in demo

#### Paper 4: "AIOps Solutions for Incident Management" (Survey)
- **URL**: https://arxiv.org/abs/2404.01363
- **Key Finding**: Comprehensive taxonomy of AIOps approaches
- **Implication**: Use as reference for terminology and evaluation

### 4.2 Research Insights for Implementation

| Insight | Source | How to Apply |
|---------|--------|--------------|
| ReAct outperforms RAG | Microsoft FSE 2024 | Use tool-augmented reasoning loop |
| Discussion comments don't help | Microsoft FSE 2024 | Focus on tool access, not more text |
| Stabilization needed for local LLMs | Alibaba CIKM 2024 | Add retry logic and validation |
| Multi-modal analysis needed | OKESTRO 2026 | Support logs + metrics + traces |

---

## 5. Open Source Projects to Adapt

### 5.1 Tier 1: Direct Foundations

| Project | Stars | Use For |
|---------|-------|---------|
| **HolmesGPT** | 1.8k | Investigation loop, tool-use pattern |
| **Keep** | 11.4k | Alert ingestion, 100+ integrations |
| **k8sgpt** | 7.4k | Plugin architecture pattern |

### 5.2 Tier 2: Key Components

| Project | Stars | Use For |
|---------|-------|---------|
| **Drain3** | 753 | Log template mining |
| **AIOpsLab** | 800 | Evaluation harness |
| **Phoenix** | 7.8k | LLM observability |

### 5.3 Recommended Architecture

```
ALERT SOURCES (Keep pattern)
    └── Alert ingestion, dedup, correlation
          │
          ▼
INCIDENTAGENT (rebuilt on Gradient)
    ├── Triage Agent (Gradient Agent + Routing)
    ├── Investigator Agent (Gradient Knowledge Bases)
    ├── Root Cause Agent (Gradient Function Calling)
    └── Remediation Agent (Gradient Guardrails)
          │
          ▼
CUSTOM MODELS (trained on Gradient GPU)
    ├── Log anomaly classifier
    ├── Root cause category predictor
    └── Severity estimator
          │
          ▼
STREAMLIT DASHBOARD (reuse from DocOps)
```

---

## 6. Technical Requirements

### 6.1 Must Have (Hackathon Requirements)

- [ ] Public GitHub repository with Apache 2.0 license
- [ ] ~3 minute demo video on YouTube
- [ ] Deployed on DigitalOcean infrastructure
- [ ] Uses Gradient AI Platform features
- [ ] DevPost submission with documentation

### 6.2 Technology Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | Streamlit |
| **Backend** | FastAPI + Python |
| **Agent Framework** | Gradient ADK |
| **LLM** | Gradient Serverless (Anthropic Claude) |
| **Knowledge Base** | Gradient Knowledge Bases |
| **Search** | Elasticsearch (reuse from DocOps) |
| **Training** | Gradient GPU Droplets |
| **Deployment** | DigitalOcean App Platform |

### 6.3 Environment Setup

```bash
# DigitalOcean credentials
export DIGITALOCEAN_API_TOKEN=your_token
export GRADIENT_MODEL_ACCESS_KEY=your_key

# Install Gradient ADK
pip install gradient-adk

# Initialize project
gradient agent init
```

---

## 7. Demo Scenario

### 7.1 Demo Flow (3 minutes)

1. **0:00-0:30** - Problem statement: 3am alert, $5,600/min downtime
2. **0:30-1:30** - Live demo: Alert fires → IncidentAgent investigates
3. **1:30-2:30** - Show investigation trace: logs → metrics → root cause
4. **2:30-3:00** - Remediation suggestion + confidence score

### 7.2 Demo Data

Create synthetic incident scenario:
- **Alert**: "High error rate on payment-service"
- **Root Cause**: Database connection pool exhausted
- **Evidence**: Error logs, connection metrics, recent deployment
- **Remediation**: Increase pool size, restart pods

---

## 8. Success Metrics

### 8.1 Hackathon Judging Criteria

| Criteria | Weight | Our Approach |
|----------|--------|--------------|
| Technological Implementation | 25% | Use ALL Gradient features |
| Design / UX | 25% | Polished Streamlit dashboard |
| Potential Impact | 25% | "$5,600/min saved" story |
| Quality / Creativity | 25% | Multi-agent + custom models |

### 8.2 Demo Metrics to Show

- Investigation time: <2 minutes
- Root cause accuracy: 85%+ confidence
- Time saved: 50 hours → 2 minutes (99.9%)

---

## 9. Next Steps (Phase 1)

After Phase 0 (this document), proceed to:

1. **Phase 1**: Theoretical Foundation
   - Define agent responsibilities
   - Design workflow diagrams
   - Specify tool interfaces

2. **Phase 2**: System Design
   - Component specifications
   - Data flow diagrams
   - API contracts

3. **Phase 3**: Gradient Mapping
   - Map each component to Gradient feature
   - Define Knowledge Base schema
   - Design evaluation datasets

4. **Phase 4**: Implementation
   - Code agents
   - Train custom models
   - Build UI

5. **Phase 5**: Demo & Submission
   - Record video
   - Write DevPost
   - Submit

---

## 10. References

### Documentation
- Gradient AI Platform: https://docs.digitalocean.com/products/gradient-ai-platform/
- Gradient ADK: https://github.com/digitalocean/gradient-adk
- HolmesGPT: https://holmesgpt.dev/

### Papers
- LLM Agents for RCA: https://arxiv.org/abs/2403.04123
- RCAgent: https://arxiv.org/abs/2310.16340
- AIOps Survey: https://arxiv.org/abs/2404.01363

### GitHub
- HolmesGPT: https://github.com/HolmesGPT/holmesgpt
- Keep: https://github.com/keephq/keep
- Gradient ADK: https://github.com/digitalocean/gradient-adk

---

## INSTRUCTIONS FOR CLAUDE CODE

**READ THIS DOCUMENT FIRST** before writing any code.

Key constraints:
1. All agents MUST use Gradient ADK decorators (`@entrypoint`, `@trace_llm`, `@trace_tool`, `@trace_retriever`)
2. Project structure MUST follow Gradient ADK conventions
3. Use HolmesGPT patterns for investigation loop
4. Reuse DocOps patterns for Streamlit UI and Elasticsearch
5. All code must be deployable on DigitalOcean App Platform

Next document to read: `PHASE1_ARCHITECTURE.md`
