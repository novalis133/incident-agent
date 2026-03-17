# CLAUDE CODE INSTRUCTIONS

> **IMPORTANT**: Read this file FIRST before doing any work on IncidentAgent.

---

## Project Context

**Project Name**: IncidentAgent  
**Hackathon**: DigitalOcean Gradient AI Hackathon  
**Deadline**: March 18, 2026  
**Prize**: $20,000  

**What we're building**: An autonomous AI agent that investigates DevOps incidents, finds root cause, and suggests remediation — all running on DigitalOcean Gradient AI Platform.

---

## Document Reading Order

Read these documents in order before writing code:

1. `PHASE0_RESEARCH.md` - Research and resource summary
2. `PHASE1_ARCHITECTURE.md` - System architecture (when created)
3. `PHASE2_AGENTS.md` - Agent definitions (when created)
4. `PHASE3_GRADIENT.md` - Gradient feature mapping (when created)

---

## Hard Requirements

### 1. MUST Use Gradient ADK

All agents MUST be built using DigitalOcean Gradient ADK:

```python
from gradient_adk import entrypoint, trace_llm, trace_tool, trace_retriever

@entrypoint
async def main(input: dict, context: dict):
    # Agent logic here
    pass
```

### 2. MUST Use These Gradient Features

| Feature | Required Usage |
|---------|----------------|
| Agent Development Kit (ADK) | ✅ All agents |
| Knowledge Bases | ✅ Runbooks, past incidents |
| Agent Routing | ✅ Multi-agent workflow |
| Function Calling | ✅ Tools (log search, metrics) |
| Guardrails | ✅ Safe remediation |
| GPU Training | ✅ At least 1 custom model |
| Evaluation | ✅ Benchmark tests |

### 3. Project Structure

```
incidentiq/
├── README.md
├── requirements.txt
├── pyproject.toml
├── .env.example
├── .gradient/
│   └── agent.yml
├── main.py                 # Gradient entrypoint
├── agents/
│   ├── __init__.py
│   ├── triage.py           # Triage Agent
│   ├── investigator.py     # Investigator Agent
│   ├── rootcause.py        # Root Cause Agent
│   └── remediation.py      # Remediation Agent
├── tools/
│   ├── __init__.py
│   ├── log_search.py       # Log search tool
│   ├── metric_query.py     # Metrics query tool
│   ├── runbook_lookup.py   # Runbook lookup tool
│   └── incident_memory.py  # Past incident search
├── models/
│   ├── __init__.py
│   └── log_classifier.py   # Custom trained model
├── knowledge/
│   ├── runbooks/           # Runbook documents
│   └── incidents/          # Past incident data
├── ui/
│   └── streamlit_app.py    # Dashboard
├── tests/
│   └── eval_dataset.csv    # Evaluation data
└── docs/
    ├── PHASE0_RESEARCH.md
    ├── PHASE1_ARCHITECTURE.md
    ├── PHASE2_AGENTS.md
    └── PHASE3_GRADIENT.md
```

### 4. Code Style

- Python 3.11+
- Type hints required
- Async/await for all I/O operations
- Docstrings for all public functions
- Use `logging` module, not print statements

### 5. Dependencies

Core dependencies (add to requirements.txt):

```
gradient-adk>=0.1.4
fastapi>=0.100.0
streamlit>=1.28.0
elasticsearch>=8.0.0
langchain>=0.1.0
pydantic>=2.0.0
httpx>=0.25.0
python-dotenv>=1.0.0
```

---

## Agent Specifications

### Agent 1: Triage Agent

**Purpose**: Classify incident severity and route to appropriate specialist

**Input**: Raw alert from monitoring system
**Output**: Severity level, affected services, recommended specialist agent

**Gradient Features**:
- `@trace_tool` for classification
- Agent Routing to select next agent

### Agent 2: Investigator Agent

**Purpose**: Gather evidence from logs, metrics, traces

**Input**: Triage results + alert context
**Output**: Collected evidence, timeline of events

**Gradient Features**:
- `@trace_retriever` for log search
- Knowledge Base for runbooks
- Function Calling for metric queries

### Agent 3: Root Cause Agent

**Purpose**: Analyze evidence to identify probable root cause

**Input**: Evidence from Investigator
**Output**: Root cause hypothesis with confidence score

**Gradient Features**:
- `@trace_llm` for analysis
- Knowledge Base for past incidents
- Custom trained classifier (GPU)

### Agent 4: Remediation Agent

**Purpose**: Suggest fixes based on root cause

**Input**: Root cause analysis
**Output**: Remediation steps with safety assessment

**Gradient Features**:
- Guardrails for safe suggestions
- Knowledge Base for runbooks
- `@trace_tool` for validation

---

## Workflow

```
Alert Received
      │
      ▼
┌─────────────┐
│ Triage Agent│ ─── Classify severity, identify services
└──────┬──────┘
       │
       ▼
┌──────────────────┐
│ Investigator Agent│ ─── Search logs, query metrics, check traces
└────────┬─────────┘
         │
         ▼
┌─────────────────┐
│ Root Cause Agent│ ─── Analyze evidence, identify cause
└────────┬────────┘
         │
         ▼
┌───────────────────┐
│ Remediation Agent │ ─── Suggest fixes, assess safety
└─────────┬─────────┘
          │
          ▼
    Investigation
      Complete
```

---

## DO NOT

❌ Do NOT use external LLM APIs directly (use Gradient Serverless)
❌ Do NOT skip Gradient ADK decorators
❌ Do NOT hardcode API keys (use environment variables)
❌ Do NOT write synchronous I/O code
❌ Do NOT skip type hints
❌ Do NOT create agents without trace decorators

---

## DO

✅ Use Gradient ADK for all agents
✅ Use Knowledge Bases for runbooks and past incidents
✅ Use Agent Routing for multi-agent workflow
✅ Use Function Calling for tools
✅ Use Guardrails for remediation safety
✅ Train at least one custom model on GPU
✅ Write evaluation tests
✅ Create Streamlit dashboard
✅ Document everything

---

## Questions?

If you need clarification on any requirement, ask before implementing. The hackathon deadline is firm - we need to get this right the first time.

---

## Current Phase

**PHASE 0 COMPLETE** ✅

Next: Create PHASE1_ARCHITECTURE.md with detailed system design.
