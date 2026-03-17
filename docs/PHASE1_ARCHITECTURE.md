# IncidentAgent - Phase 1: System Architecture

> **Project**: IncidentAgent  
> **Version**: 1.0  
> **Created**: February 21, 2026  
> **Status**: PHASE 1 - Architecture Complete

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture Diagram](#2-architecture-diagram)
3. [Alert Router](#3-alert-router)
4. [Triage Agent](#4-triage-agent)
5. [Investigator Master Agent](#5-investigator-master-agent)
6. [Sub-Agents](#6-sub-agents)
7. [Remediation Agent](#7-remediation-agent)
8. [Output Layer](#8-output-layer)
9. [Memory & Learning](#9-memory--learning)
10. [Data Schemas](#10-data-schemas)
11. [Gradient Feature Mapping](#11-gradient-feature-mapping)
12. [Project Structure](#12-project-structure)
13. [Configuration](#13-configuration)

---

## 1. System Overview

### 1.1 What IncidentAgent Does

```
INPUT                    PROCESSING                      OUTPUT
─────                    ──────────                      ──────
Alert fires     →    AI investigates automatically   →   Root cause +
(3am)                (logs, metrics, deploys)            Remediation steps
                                                         (2 minutes)
```

### 1.2 Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Agent Framework | Gradient ADK | Hackathon requirement |
| Communication Pattern | Iterative Refinement (D) + Alert-Type Routing (B) | Research-backed, best accuracy |
| RCA + Remediation | Separate agents (Option C) | Safety isolation, guardrails |
| Memory Storage | Gradient Knowledge Bases | Platform alignment |
| Model Training | Continuous with benchmark gating | Quality control |

### 1.3 Core Principles

1. **Iterative Investigation**: Each step builds on previous findings
2. **Early Stopping**: Stop when confidence threshold reached (>0.85)
3. **Safety First**: Remediation has strict guardrails
4. **Learn Continuously**: Every resolved incident improves the system
5. **Explainable**: Clear reasoning chain for every conclusion

---

## 2. Architecture Diagram

### 2.1 Complete System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            INCIDENTAGENT                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ╔═══════════════════════════════════════════════════════════════════════╗ │
│  ║                         ALERT ROUTER                                   ║ │
│  ║  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐                 ║ │
│  ║  │Prometheus│ │PagerDuty │ │ Webhook  │ │  Manual  │                 ║ │
│  ║  │ Adapter  │ │ Adapter  │ │ Adapter  │ │  Input   │                 ║ │
│  ║  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘                 ║ │
│  ║       └───────────┬┴───────────┬┴────────────┘                       ║ │
│  ║                   ▼            ▼                                      ║ │
│  ║           ┌─────────────────────────────┐                            ║ │
│  ║           │    Unified Alert Schema     │                            ║ │
│  ║           └─────────────┬───────────────┘                            ║ │
│  ╚═════════════════════════╪═════════════════════════════════════════════╝ │
│                            │                                                │
│                            ▼                                                │
│  ╔═══════════════════════════════════════════════════════════════════════╗ │
│  ║                        TRIAGE AGENT                                    ║ │
│  ║  • Classify severity (critical/high/medium/low)                       ║ │
│  ║  • Identify affected services                                         ║ │
│  ║  • Determine alert type (error_rate/latency/crash/resource/unknown)  ║ │
│  ║  • Set investigation priority queue based on alert type               ║ │
│  ╚═════════════════════════╪═════════════════════════════════════════════╝ │
│                            │                                                │
│                            ▼                                                │
│  ╔═══════════════════════════════════════════════════════════════════════╗ │
│  ║                  INVESTIGATOR MASTER AGENT                             ║ │
│  ║                                                                        ║ │
│  ║  ┌─────────────────────────────────────────────────────────────────┐  ║ │
│  ║  │                    SUB-AGENT ORCHESTRATION                       │  ║ │
│  ║  │         (Iterative Refinement with Early Stopping)              │  ║ │
│  ║  │                                                                  │  ║ │
│  ║  │  Priority Queue: [DeployAgent, LogsAgent, MetricsAgent, ...]    │  ║ │
│  ║  │                                                                  │  ║ │
│  ║  │  Step 1: Call first agent → get findings                        │  ║ │
│  ║  │  Step 2: Analyze findings → decide next agent                   │  ║ │
│  ║  │  Step 3: Repeat until confidence > 0.85 or queue empty          │  ║ │
│  ║  └─────────────────────────────────────────────────────────────────┘  ║ │
│  ║                                                                        ║ │
│  ║  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌─────────┐ ║ │
│  ║  │  Deploy   │ │   Logs    │ │  Metrics  │ │    K8s    │ │ Runbook │ ║ │
│  ║  │   Agent   │ │   Agent   │ │   Agent   │ │   Agent   │ │  Agent  │ ║ │
│  ║  └─────┬─────┘ └─────┬─────┘ └─────┬─────┘ └─────┬─────┘ └────┬────┘ ║ │
│  ║        │             │             │             │            │       ║ │
│  ║        └─────────────┴──────┬──────┴─────────────┴────────────┘       ║ │
│  ║                             │                                          ║ │
│  ║                             ▼                                          ║ │
│  ║  ┌─────────────────────────────────────────────────────────────────┐  ║ │
│  ║  │                 EVIDENCE SYNTHESIS                               │  ║ │
│  ║  │  • Correlate findings across agents                              │  ║ │
│  ║  │  • Build incident timeline                                       │  ║ │
│  ║  │  • Calculate blast radius                                        │  ║ │
│  ║  │  • Generate ROOT CAUSE HYPOTHESIS                                │  ║ │
│  ║  └─────────────────────────────────────────────────────────────────┘  ║ │
│  ╚═════════════════════════╪═════════════════════════════════════════════╝ │
│                            │                                                │
│                            ▼                                                │
│  ╔═══════════════════════════════════════════════════════════════════════╗ │
│  ║                     MEMORY AGENT                                       ║ │
│  ║  • Search past incidents for similar patterns                         ║ │
│  ║  • Return: what worked, what didn't, resolution time                  ║ │
│  ║  • Feeds into Remediation Agent                                       ║ │
│  ╚═════════════════════════╪═════════════════════════════════════════════╝ │
│                            │                                                │
│                            ▼                                                │
│  ╔═══════════════════════════════════════════════════════════════════════╗ │
│  ║                    REMEDIATION AGENT                                   ║ │
│  ║                   (with Gradient Guardrails)                          ║ │
│  ║                                                                        ║ │
│  ║  ┌─────────────────────────────────────────────────────────────────┐  ║ │
│  ║  │  1. Receive root cause hypothesis                                │  ║ │
│  ║  │  2. Query runbooks for known solutions                           │  ║ │
│  ║  │  3. Check past incident success rates (from MemoryAgent)         │  ║ │
│  ║  │  4. Generate remediation steps                                   │  ║ │
│  ║  │  5. Apply GUARDRAILS (safety check)                              │  ║ │
│  ║  │  6. Calculate risk score                                         │  ║ │
│  ║  │  7. Require approval if high risk                                │  ║ │
│  ║  └─────────────────────────────────────────────────────────────────┘  ║ │
│  ║                                                                        ║ │
│  ║  GUARDRAILS:                                                          ║ │
│  ║  ✗ No destructive commands without approval                           ║ │
│  ║  ✗ No production database writes                                      ║ │
│  ║  ✗ Rollback plan required for high-risk actions                       ║ │
│  ║  ✗ Risk score must be calculated                                      ║ │
│  ╚═════════════════════════╪═════════════════════════════════════════════╝ │
│                            │                                                │
│                            ▼                                                │
│  ╔═══════════════════════════════════════════════════════════════════════╗ │
│  ║                       OUTPUT LAYER                                     ║ │
│  ║                                                                        ║ │
│  ║  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                ║ │
│  ║  │  Dashboard   │  │   Report     │  │ Integrations │                ║ │
│  ║  │  (Primary)   │  │  Generator   │  │  (Optional)  │                ║ │
│  ║  │              │  │              │  │              │                ║ │
│  ║  │  • Live view │  │  • Markdown  │  │  • PagerDuty │                ║ │
│  ║  │  • Timeline  │  │  • PDF       │  │  • Slack     │                ║ │
│  ║  │  • Evidence  │  │  • JSON      │  │  • Webhook   │                ║ │
│  ║  │  • Actions   │  │  • HTML      │  │              │                ║ │
│  ║  └──────────────┘  └──────────────┘  └──────────────┘                ║ │
│  ╚═══════════════════════════════════════════════════════════════════════╝ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘


                    ╔═══════════════════════════════════════╗
                    ║         GRADIENT KNOWLEDGE BASES       ║
                    ║                                        ║
                    ║  KB1: Runbooks (static)               ║
                    ║  KB2: Past Incidents (dynamic)        ║
                    ║                                        ║
                    ╚═══════════════════════════════════════╝
                                      │
                                      ▼
                    ╔═══════════════════════════════════════╗
                    ║         CUSTOM MODEL (GPU)             ║
                    ║                                        ║
                    ║  • Trained on causality + reasoning   ║
                    ║  • Versioned with benchmark gating    ║
                    ║  • Continuous improvement             ║
                    ╚═══════════════════════════════════════╝
```

---

## 3. Alert Router

### 3.1 Purpose

Normalize alerts from multiple sources into a unified schema.

### 3.2 Supported Sources

| Source | Priority | Implementation |
|--------|----------|----------------|
| Manual Input | P0 (Must) | Text input in UI |
| Generic Webhook | P0 (Must) | HTTP POST endpoint |
| Prometheus/AlertManager | P1 (Should) | REST API polling |
| PagerDuty | P2 (Nice) | REST API polling |

### 3.3 Unified Alert Schema

```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, List, Literal

class UnifiedAlert(BaseModel):
    """Normalized alert format from any source"""
    
    # Identity
    id: str                                    # Unique alert ID
    source: Literal["prometheus", "pagerduty", "webhook", "manual"]
    
    # Content
    title: str                                 # "High error rate on payment-service"
    description: str                           # Detailed description
    severity: Literal["critical", "high", "medium", "low"]
    
    # Context
    service: Optional[str] = None              # Affected service name
    environment: Optional[str] = None          # "production", "staging"
    labels: Dict[str, str] = {}                # Additional labels
    
    # Timing
    fired_at: datetime                         # When alert fired
    received_at: datetime                      # When we received it
    
    # Raw data
    raw_payload: Dict                          # Original alert for reference
```

### 3.4 Adapter Interface

```python
from abc import ABC, abstractmethod

class AlertAdapter(ABC):
    """Base class for alert source adapters"""
    
    @abstractmethod
    def parse(self, raw: dict) -> UnifiedAlert:
        """Convert raw alert to unified format"""
        pass
    
    @abstractmethod
    def validate(self, raw: dict) -> bool:
        """Check if raw data is valid for this adapter"""
        pass
```

### 3.5 File Location

```
incidentagent/
└── adapters/
    ├── __init__.py
    ├── base.py              # AlertAdapter ABC
    ├── prometheus.py        # PrometheusAdapter
    ├── pagerduty.py         # PagerDutyAdapter
    ├── webhook.py           # WebhookAdapter
    └── manual.py            # ManualInputAdapter
```

---

## 4. Triage Agent

### 4.1 Purpose

- Classify alert severity
- Identify affected services
- Determine alert type
- Set investigation priority queue

### 4.2 Alert Type Classification

```python
class AlertType(str, Enum):
    ERROR_RATE = "error_rate"          # High error percentage
    LATENCY = "latency"                # Slow response times
    CRASH = "crash"                    # Pod/service crashes
    RESOURCE = "resource"              # CPU/memory/disk issues
    DEPENDENCY = "dependency"          # External service failures
    CONFIG = "config"                  # Configuration issues
    UNKNOWN = "unknown"                # Cannot classify
```

### 4.3 Investigation Priority Mapping

```python
# Based on research: 80% of incidents follow changes
INVESTIGATION_PRIORITY = {
    AlertType.ERROR_RATE: ["DeployAgent", "LogsAgent", "MetricsAgent", "K8sAgent"],
    AlertType.LATENCY: ["MetricsAgent", "LogsAgent", "DeployAgent", "K8sAgent"],
    AlertType.CRASH: ["K8sAgent", "LogsAgent", "MetricsAgent", "DeployAgent"],
    AlertType.RESOURCE: ["MetricsAgent", "K8sAgent", "LogsAgent", "DeployAgent"],
    AlertType.DEPENDENCY: ["LogsAgent", "MetricsAgent", "DeployAgent", "K8sAgent"],
    AlertType.CONFIG: ["DeployAgent", "K8sAgent", "LogsAgent", "MetricsAgent"],
    AlertType.UNKNOWN: ["DeployAgent", "LogsAgent", "MetricsAgent", "K8sAgent"],
}
```

### 4.4 Triage Output

```python
class TriageResult(BaseModel):
    """Output from Triage Agent"""
    
    alert_id: str
    
    # Classification
    severity: Literal["critical", "high", "medium", "low"]
    alert_type: AlertType
    
    # Context
    affected_services: List[str]
    affected_environment: str
    
    # Investigation plan
    priority_queue: List[str]          # Ordered list of agents to call
    
    # Metadata
    classification_confidence: float    # 0.0 - 1.0
    classification_reasoning: str       # Why this classification
```

### 4.5 Gradient Implementation

```python
from gradient_adk import entrypoint, trace_llm

@trace_llm("triage_classification")
async def classify_alert(alert: UnifiedAlert) -> TriageResult:
    """Classify alert and determine investigation strategy"""
    
    # Use LLM to classify alert type
    prompt = f"""
    Analyze this alert and classify it:
    
    Title: {alert.title}
    Description: {alert.description}
    Service: {alert.service}
    Severity: {alert.severity}
    
    Determine:
    1. Alert type (error_rate, latency, crash, resource, dependency, config, unknown)
    2. Affected services
    3. Classification confidence (0-1)
    
    Respond in JSON format.
    """
    
    # LLM call handled by Gradient
    response = await llm.generate(prompt)
    
    # Parse and build priority queue
    alert_type = AlertType(response["alert_type"])
    priority_queue = INVESTIGATION_PRIORITY[alert_type]
    
    return TriageResult(
        alert_id=alert.id,
        severity=alert.severity,
        alert_type=alert_type,
        affected_services=response["affected_services"],
        affected_environment=alert.environment or "production",
        priority_queue=priority_queue,
        classification_confidence=response["confidence"],
        classification_reasoning=response["reasoning"]
    )
```

---

## 5. Investigator Master Agent

### 5.1 Purpose

- Orchestrate sub-agents in iterative refinement pattern
- Build context from findings
- Decide which agent to call next
- Synthesize evidence into root cause hypothesis
- Stop early when confidence threshold reached

### 5.2 Investigation State

```python
class InvestigationState(BaseModel):
    """Running state of investigation"""
    
    # Identity
    investigation_id: str
    alert: UnifiedAlert
    triage: TriageResult
    
    # Progress
    current_step: int = 0
    agents_called: List[str] = []
    agents_remaining: List[str]
    current_agent: Optional[str] = None
    
    # Evidence accumulation
    all_evidence: List["AgentEvidence"] = []
    combined_confidence: float = 0.0
    
    # Synthesis (updated after each step)
    timeline: List[Dict] = []
    blast_radius: Dict = {}
    root_cause_hypotheses: List["RootCauseHypothesis"] = []
    
    # Control
    should_continue: bool = True
    stop_reason: Optional[str] = None
    confidence_threshold: float = 0.85
```

### 5.3 Iterative Refinement Loop

```python
from gradient_adk import entrypoint, trace_llm, trace_tool

class InvestigatorMaster:
    """Master agent that orchestrates sub-agents"""
    
    def __init__(self):
        self.sub_agents = {
            "DeployAgent": DeployAgent(),
            "LogsAgent": LogsAgent(),
            "MetricsAgent": MetricsAgent(),
            "K8sAgent": K8sAgent(),
            "RunbookAgent": RunbookAgent(),
            "MemoryAgent": MemoryAgent(),
        }
        
    @trace_tool("investigation_loop")
    async def investigate(
        self, 
        alert: UnifiedAlert, 
        triage: TriageResult
    ) -> "InvestigationResult":
        """Run iterative investigation"""
        
        # Initialize state
        state = InvestigationState(
            investigation_id=generate_id(),
            alert=alert,
            triage=triage,
            agents_remaining=triage.priority_queue.copy()
        )
        
        # Iterative refinement loop
        while state.should_continue and state.agents_remaining:
            
            # Step 1: Select next agent
            next_agent = await self._select_next_agent(state)
            state.current_agent = next_agent
            state.current_step += 1
            
            # Step 2: Call agent with context
            context = self._build_context(state)
            evidence = await self._call_agent(next_agent, context)
            
            # Step 3: Update state
            state.all_evidence.append(evidence)
            state.agents_called.append(next_agent)
            state.agents_remaining.remove(next_agent)
            
            # Step 4: Synthesize findings
            synthesis = await self._synthesize(state)
            state.combined_confidence = synthesis.confidence
            state.root_cause_hypotheses = synthesis.hypotheses
            state.timeline = synthesis.timeline
            state.blast_radius = synthesis.blast_radius
            
            # Step 5: Check stopping conditions
            if state.combined_confidence >= state.confidence_threshold:
                state.should_continue = False
                state.stop_reason = "confidence_threshold_reached"
            elif evidence.early_stop_recommended:
                state.should_continue = False
                state.stop_reason = "agent_recommended_stop"
        
        # Final synthesis
        return await self._finalize(state)
    
    @trace_llm("select_next_agent")
    async def _select_next_agent(self, state: InvestigationState) -> str:
        """Decide which agent to call next based on current findings"""
        
        if not state.all_evidence:
            # First call: use priority queue
            return state.agents_remaining[0]
        
        # LLM decides based on context
        prompt = f"""
        Current investigation state:
        - Alert: {state.alert.title}
        - Findings so far: {self._summarize_findings(state)}
        - Agents remaining: {state.agents_remaining}
        
        Based on the findings, which agent should we call next?
        Consider what evidence we still need to identify root cause.
        
        Respond with just the agent name.
        """
        
        response = await llm.generate(prompt)
        return response.strip()
    
    def _build_context(self, state: InvestigationState) -> Dict:
        """Build context for sub-agent call"""
        
        return {
            "alert": state.alert.model_dump(),
            "triage": state.triage.model_dump(),
            "previous_findings": [e.model_dump() for e in state.all_evidence],
            "timeline_so_far": state.timeline,
            "hypotheses_so_far": [h.model_dump() for h in state.root_cause_hypotheses],
        }
    
    @trace_llm("synthesize_findings")
    async def _synthesize(self, state: InvestigationState) -> "Synthesis":
        """Synthesize all findings into hypotheses"""
        
        prompt = f"""
        Synthesize these investigation findings:
        
        Alert: {state.alert.title}
        
        Evidence collected:
        {self._format_evidence(state.all_evidence)}
        
        Generate:
        1. Root cause hypotheses (ranked by confidence)
        2. Incident timeline
        3. Blast radius (affected services, users)
        4. Overall confidence score
        
        Respond in JSON format.
        """
        
        return await llm.generate(prompt, response_model=Synthesis)
```

---

## 6. Sub-Agents

### 6.1 Sub-Agent Interface

```python
from abc import ABC, abstractmethod

class SubAgent(ABC):
    """Base class for all sub-agents"""
    
    name: str
    description: str
    
    @abstractmethod
    async def investigate(self, context: Dict) -> "AgentEvidence":
        """Run investigation and return evidence"""
        pass
    
    @abstractmethod
    def get_tools(self) -> List[Dict]:
        """Return tools this agent can use"""
        pass
```

### 6.2 Agent Evidence Schema

```python
class FindingType(str, Enum):
    DEPLOYMENT = "deployment"
    ERROR_SIGNATURE = "error_signature"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    DEPENDENCY_FAILURE = "dependency_failure"
    ANOMALY = "anomaly"
    CORRELATION = "correlation"
    HISTORICAL_MATCH = "historical_match"
    CONFIG_CHANGE = "config_change"

class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class Finding(BaseModel):
    """Single piece of evidence"""
    
    # Identity
    id: str
    type: FindingType
    
    # Content
    title: str
    description: str
    severity: Severity
    confidence: float                   # 0.0 - 1.0
    
    # Timeline
    timestamp: datetime
    time_delta_from_incident: str       # "-2h 15m"
    
    # Blast Radius
    affected_services: List[str]
    affected_users_estimate: Optional[int]
    
    # Evidence
    evidence_source: str                # "elasticsearch", "prometheus"
    evidence_query: str                 # Actual query used
    raw_evidence: str                   # Log line, metric value
    
    # Correlation
    related_findings: List[str] = []
    correlation_strength: Optional[float]
    
    # Actionability
    is_actionable: bool
    suggested_action: Optional[str]

class AgentEvidence(BaseModel):
    """Complete evidence from a sub-agent"""
    
    # Identity
    agent_name: str
    agent_type: str
    
    # Timing
    investigation_id: str
    started_at: datetime
    completed_at: datetime
    duration_ms: int
    
    # Findings
    findings: List[Finding]
    finding_count: int
    
    # Confidence
    confidence: float
    confidence_reasoning: str
    
    # Iteration hints
    suggests_next_agent: Optional[str]
    next_agent_context: Optional[str]
    
    # Early stopping
    is_high_confidence: bool
    is_root_cause_candidate: bool
    early_stop_recommended: bool
```

### 6.3 DeployAgent

```python
class DeployAgent(SubAgent):
    """Investigates recent deployments and changes"""
    
    name = "DeployAgent"
    description = "Checks recent deployments, config changes, and releases"
    
    @trace_tool("deploy_investigation")
    async def investigate(self, context: Dict) -> AgentEvidence:
        """Find recent deployments that may correlate with incident"""
        
        alert = context["alert"]
        service = alert.get("service")
        incident_time = alert.get("fired_at")
        
        findings = []
        
        # Check Kubernetes deployments
        k8s_deploys = await self._check_k8s_deployments(service, incident_time)
        findings.extend(k8s_deploys)
        
        # Check Git commits (if configured)
        git_changes = await self._check_git_changes(service, incident_time)
        findings.extend(git_changes)
        
        # Check ConfigMap changes
        config_changes = await self._check_config_changes(service, incident_time)
        findings.extend(config_changes)
        
        # Calculate confidence
        confidence = self._calculate_confidence(findings, incident_time)
        
        return AgentEvidence(
            agent_name=self.name,
            agent_type="deployment_checker",
            investigation_id=context.get("investigation_id"),
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            duration_ms=0,  # Will be calculated
            findings=findings,
            finding_count=len(findings),
            confidence=confidence,
            confidence_reasoning=self._explain_confidence(findings),
            suggests_next_agent="LogsAgent" if findings else "MetricsAgent",
            next_agent_context=f"Check logs around {findings[0].timestamp}" if findings else None,
            is_high_confidence=confidence > 0.85,
            is_root_cause_candidate=any(f.confidence > 0.8 for f in findings),
            early_stop_recommended=False
        )
    
    @trace_tool("check_k8s_deployments")
    async def _check_k8s_deployments(
        self, 
        service: str, 
        incident_time: datetime
    ) -> List[Finding]:
        """Query Kubernetes for recent deployments"""
        
        # Implementation will use kubernetes API
        pass
```

### 6.4 LogsAgent

```python
class LogsAgent(SubAgent):
    """Searches logs for errors and anomalies"""
    
    name = "LogsAgent"
    description = "Searches application logs for errors, exceptions, patterns"
    
    @trace_retriever("log_search")
    async def investigate(self, context: Dict) -> AgentEvidence:
        """Search logs for relevant errors"""
        
        alert = context["alert"]
        previous_findings = context.get("previous_findings", [])
        
        # Build time window from context
        time_window = self._determine_time_window(alert, previous_findings)
        
        findings = []
        
        # Search for errors
        errors = await self._search_errors(
            service=alert.get("service"),
            time_window=time_window
        )
        findings.extend(errors)
        
        # Search for exceptions
        exceptions = await self._search_exceptions(
            service=alert.get("service"),
            time_window=time_window
        )
        findings.extend(exceptions)
        
        # Look for patterns
        patterns = await self._find_patterns(errors + exceptions)
        findings.extend(patterns)
        
        return self._build_evidence(findings, context)
    
    @trace_retriever("elasticsearch_query")
    async def _search_errors(
        self, 
        service: str, 
        time_window: Tuple[datetime, datetime]
    ) -> List[Finding]:
        """Query Elasticsearch for error logs"""
        
        query = {
            "bool": {
                "must": [
                    {"match": {"service": service}},
                    {"match": {"level": "error"}},
                    {"range": {"@timestamp": {
                        "gte": time_window[0].isoformat(),
                        "lte": time_window[1].isoformat()
                    }}}
                ]
            }
        }
        
        # Execute search
        results = await self.es_client.search(index="logs-*", query=query)
        
        # Convert to findings
        return self._results_to_findings(results)
```

### 6.5 MetricsAgent

```python
class MetricsAgent(SubAgent):
    """Queries metrics for anomalies and resource issues"""
    
    name = "MetricsAgent"
    description = "Analyzes metrics for resource exhaustion, latency spikes, anomalies"
    
    @trace_tool("metrics_investigation")
    async def investigate(self, context: Dict) -> AgentEvidence:
        """Analyze metrics around incident time"""
        
        alert = context["alert"]
        service = alert.get("service")
        
        findings = []
        
        # Check resource metrics
        resource_findings = await self._check_resources(service)
        findings.extend(resource_findings)
        
        # Check error rate metrics
        error_rate = await self._check_error_rate(service)
        findings.extend(error_rate)
        
        # Check latency metrics
        latency = await self._check_latency(service)
        findings.extend(latency)
        
        # Detect anomalies
        anomalies = await self._detect_anomalies(service)
        findings.extend(anomalies)
        
        return self._build_evidence(findings, context)
    
    @trace_tool("prometheus_query")
    async def _check_resources(self, service: str) -> List[Finding]:
        """Query Prometheus for resource metrics"""
        
        queries = [
            f'container_cpu_usage_seconds_total{{service="{service}"}}',
            f'container_memory_usage_bytes{{service="{service}"}}',
            f'container_network_receive_bytes_total{{service="{service}"}}',
        ]
        
        findings = []
        for query in queries:
            result = await self.prom_client.query(query)
            if self._is_anomalous(result):
                findings.append(self._create_finding(result))
        
        return findings
```

### 6.6 K8sAgent

```python
class K8sAgent(SubAgent):
    """Checks Kubernetes events and pod status"""
    
    name = "K8sAgent"
    description = "Analyzes Kubernetes events, pod status, restarts, OOM kills"
    
    @trace_tool("k8s_investigation")
    async def investigate(self, context: Dict) -> AgentEvidence:
        """Check Kubernetes for relevant events"""
        
        alert = context["alert"]
        service = alert.get("service")
        
        findings = []
        
        # Check pod status
        pod_findings = await self._check_pods(service)
        findings.extend(pod_findings)
        
        # Check events
        event_findings = await self._check_events(service)
        findings.extend(event_findings)
        
        # Check for OOM kills
        oom_findings = await self._check_oom(service)
        findings.extend(oom_findings)
        
        # Check restarts
        restart_findings = await self._check_restarts(service)
        findings.extend(restart_findings)
        
        return self._build_evidence(findings, context)
```

### 6.7 RunbookAgent

```python
class RunbookAgent(SubAgent):
    """Searches runbooks for relevant solutions"""
    
    name = "RunbookAgent"
    description = "Searches knowledge base for runbooks and known solutions"
    
    @trace_retriever("runbook_search")
    async def investigate(self, context: Dict) -> AgentEvidence:
        """Search runbooks for relevant procedures"""
        
        alert = context["alert"]
        hypotheses = context.get("hypotheses_so_far", [])
        
        # Search by alert
        alert_runbooks = await self._search_by_alert(alert)
        
        # Search by hypotheses
        hypothesis_runbooks = await self._search_by_hypotheses(hypotheses)
        
        # Combine and rank
        all_runbooks = self._rank_runbooks(alert_runbooks + hypothesis_runbooks)
        
        findings = [self._runbook_to_finding(r) for r in all_runbooks[:5]]
        
        return self._build_evidence(findings, context)
    
    @trace_retriever("knowledge_base_query")
    async def _search_by_alert(self, alert: Dict) -> List[Dict]:
        """Query Gradient Knowledge Base for relevant runbooks"""
        
        # Use Gradient KB API
        results = await self.kb_client.search(
            knowledge_base_id="runbooks",
            query=f"{alert['title']} {alert['description']}",
            top_k=10
        )
        
        return results
```

### 6.8 MemoryAgent

```python
class MemoryAgent(SubAgent):
    """Searches past incidents for similar patterns"""
    
    name = "MemoryAgent"
    description = "Finds similar past incidents and what worked"
    
    @trace_retriever("memory_search")
    async def investigate(self, context: Dict) -> AgentEvidence:
        """Find similar past incidents"""
        
        alert = context["alert"]
        findings_so_far = context.get("previous_findings", [])
        hypotheses = context.get("hypotheses_so_far", [])
        
        # Build search query from context
        search_query = self._build_search_query(alert, findings_so_far, hypotheses)
        
        # Search past incidents
        similar_incidents = await self._search_incidents(search_query)
        
        # Extract learnings
        findings = []
        for incident in similar_incidents[:5]:
            findings.append(Finding(
                id=generate_id(),
                type=FindingType.HISTORICAL_MATCH,
                title=f"Similar incident: {incident['title']}",
                description=f"Root cause was: {incident['root_cause']}",
                severity=Severity.INFO,
                confidence=incident['similarity_score'],
                timestamp=incident['created_at'],
                time_delta_from_incident="historical",
                affected_services=incident['affected_services'],
                affected_users_estimate=None,
                evidence_source="incident_memory",
                evidence_query=search_query,
                raw_evidence=json.dumps(incident),
                is_actionable=True,
                suggested_action=incident.get('remediation_that_worked', {}).get('summary')
            ))
        
        return self._build_evidence(findings, context)
    
    @trace_retriever("incident_kb_query")
    async def _search_incidents(self, query: str) -> List[Dict]:
        """Query Gradient Knowledge Base for past incidents"""
        
        results = await self.kb_client.search(
            knowledge_base_id="past_incidents",
            query=query,
            top_k=10
        )
        
        return results
```

### 6.9 Sub-Agent File Structure

```
incidentagent/
└── agents/
    ├── __init__.py
    ├── base.py              # SubAgent ABC
    ├── triage.py            # TriageAgent
    ├── investigator.py      # InvestigatorMaster
    ├── remediation.py       # RemediationAgent
    └── sub_agents/
        ├── __init__.py
        ├── deploy.py        # DeployAgent
        ├── logs.py          # LogsAgent
        ├── metrics.py       # MetricsAgent
        ├── k8s.py           # K8sAgent
        ├── runbook.py       # RunbookAgent
        └── memory.py        # MemoryAgent
```

---

## 7. Remediation Agent

### 7.1 Purpose

- Generate safe remediation steps
- Apply guardrails
- Calculate risk scores
- Require approval for high-risk actions

### 7.2 Remediation Schema

```python
class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class RemediationStep(BaseModel):
    """Single remediation action"""
    
    step_number: int
    action: str                         # "Rollback deployment"
    command: Optional[str]              # "kubectl rollout undo..."
    risk_level: RiskLevel
    requires_approval: bool
    rollback_plan: Optional[str]
    estimated_time: str                 # "2-5 minutes"
    
class Remediation(BaseModel):
    """Complete remediation plan"""
    
    summary: str
    steps: List[RemediationStep]
    total_risk_score: float             # 0.0 - 1.0
    requires_human_approval: bool
    estimated_resolution_time: str
    
    # From memory
    based_on_runbook: Optional[str]
    similar_past_incident: Optional[str]
    past_success_rate: Optional[float]
```

### 7.3 Guardrails

```python
class RemediationGuardrails:
    """Safety checks for remediation suggestions"""
    
    BLOCKED_PATTERNS = [
        r"rm\s+-rf",
        r"DROP\s+DATABASE",
        r"DELETE\s+FROM.*WHERE\s+1=1",
        r"kubectl\s+delete\s+namespace",
        r"terraform\s+destroy",
    ]
    
    HIGH_RISK_PATTERNS = [
        r"kubectl\s+delete",
        r"kubectl\s+scale.*replicas=0",
        r"ALTER\s+TABLE",
        r"UPDATE.*SET.*WHERE",
    ]
    
    def check(self, remediation: Remediation) -> Remediation:
        """Apply guardrails to remediation plan"""
        
        for step in remediation.steps:
            if step.command:
                # Block dangerous commands
                for pattern in self.BLOCKED_PATTERNS:
                    if re.search(pattern, step.command, re.IGNORECASE):
                        raise GuardrailViolation(
                            f"Blocked dangerous command: {step.command}"
                        )
                
                # Flag high-risk commands
                for pattern in self.HIGH_RISK_PATTERNS:
                    if re.search(pattern, step.command, re.IGNORECASE):
                        step.risk_level = RiskLevel.HIGH
                        step.requires_approval = True
        
        # Require approval if any step is high risk
        if any(s.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL] 
               for s in remediation.steps):
            remediation.requires_human_approval = True
        
        # Require rollback plan for high-risk steps
        for step in remediation.steps:
            if step.risk_level == RiskLevel.HIGH and not step.rollback_plan:
                raise GuardrailViolation(
                    f"High-risk step requires rollback plan: {step.action}"
                )
        
        return remediation
```

### 7.4 Remediation Agent Implementation

```python
class RemediationAgent:
    """Generates safe remediation plans"""
    
    def __init__(self):
        self.guardrails = RemediationGuardrails()
        self.runbook_agent = RunbookAgent()
        self.memory_agent = MemoryAgent()
    
    @trace_llm("generate_remediation")
    async def generate(
        self,
        root_cause: "RootCauseHypothesis",
        evidence: List[AgentEvidence],
        memory_findings: Optional[AgentEvidence] = None
    ) -> Remediation:
        """Generate remediation plan for root cause"""
        
        # Get relevant runbooks
        runbook_context = await self._get_runbook_context(root_cause)
        
        # Get past incident learnings
        if memory_findings:
            past_learnings = self._extract_learnings(memory_findings)
        else:
            past_learnings = None
        
        # Generate remediation with LLM
        prompt = f"""
        Generate a remediation plan for this root cause:
        
        Root Cause: {root_cause.hypothesis}
        Confidence: {root_cause.confidence}
        
        Evidence:
        {self._format_evidence(evidence)}
        
        Relevant Runbooks:
        {runbook_context}
        
        Past Incident Learnings:
        {past_learnings}
        
        Generate:
        1. Summary of remediation approach
        2. Step-by-step actions with commands
        3. Risk level for each step
        4. Rollback plan for high-risk steps
        5. Estimated time for each step
        
        Be conservative - prefer safe actions over aggressive ones.
        """
        
        raw_remediation = await llm.generate(prompt, response_model=Remediation)
        
        # Apply guardrails
        safe_remediation = self.guardrails.check(raw_remediation)
        
        # Add past success rate if available
        if past_learnings and past_learnings.get("success_rate"):
            safe_remediation.past_success_rate = past_learnings["success_rate"]
        
        return safe_remediation
```

---

## 8. Output Layer

### 8.1 Investigation Result Schema

```python
class RootCauseHypothesis(BaseModel):
    """Root cause analysis result"""
    
    hypothesis: str
    confidence: float
    category: str                       # "deployment", "resource", "config"
    
    supporting_evidence: List[str]      # Finding IDs
    evidence_summary: str
    
    probable_trigger_time: datetime
    probable_trigger_event: str

class InvestigationResult(BaseModel):
    """Complete investigation output"""
    
    # Metadata
    investigation_id: str
    alert_id: str
    started_at: datetime
    completed_at: datetime
    duration_seconds: int
    
    # Alert
    alert_title: str
    alert_severity: str
    affected_services: List[str]
    
    # Investigation
    status: Literal["completed", "partial", "failed"]
    agents_used: List[str]
    total_findings: int
    
    # Root Cause
    root_cause: RootCauseHypothesis
    alternative_hypotheses: List[RootCauseHypothesis]
    
    # Timeline
    incident_timeline: List[Dict]
    
    # Blast Radius
    blast_radius: Dict
    
    # Remediation
    remediation: Remediation
    
    # Evidence
    evidence_summary: List[Dict]
    full_evidence: List[AgentEvidence]
    
    # Metrics
    time_saved_estimate: str
    confidence_score: float
```

### 8.2 Dashboard (Streamlit)

```python
# ui/dashboard.py

import streamlit as st

def render_dashboard():
    """Main dashboard view"""
    
    st.set_page_config(
        page_title="IncidentAgent",
        page_icon="🚨",
        layout="wide"
    )
    
    st.title("🚨 IncidentAgent Dashboard")
    
    # Sidebar: Configuration
    with st.sidebar:
        st.header("⚙️ Settings")
        render_settings()
    
    # Main content
    tab1, tab2, tab3 = st.tabs([
        "🔴 Active Investigation",
        "📊 History",
        "📚 Knowledge Base"
    ])
    
    with tab1:
        render_active_investigation()
    
    with tab2:
        render_history()
    
    with tab3:
        render_knowledge_base()

def render_active_investigation():
    """Render live investigation view"""
    
    investigation = get_active_investigation()
    
    if not investigation:
        st.info("No active investigation. Submit an alert to start.")
        render_alert_input()
        return
    
    # Progress bar
    progress = calculate_progress(investigation)
    st.progress(progress, text=f"Investigating... ({investigation.current_agent})")
    
    # Two columns: Findings and Timeline
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Findings")
        render_findings(investigation.all_evidence)
    
    with col2:
        st.subheader("🕐 Timeline")
        render_timeline(investigation.timeline)
    
    # Root Cause (if available)
    if investigation.root_cause_hypotheses:
        st.subheader("🎯 Root Cause Hypothesis")
        render_root_cause(investigation.root_cause_hypotheses[0])
    
    # Remediation (if complete)
    if investigation.status == "completed":
        st.subheader("🔧 Recommended Remediation")
        render_remediation(investigation.remediation)
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📋 Copy Commands"):
                copy_commands(investigation.remediation)
        with col2:
            if st.button("📄 Generate Report"):
                generate_report(investigation)
        with col3:
            if st.button("✅ Mark Resolved"):
                mark_resolved(investigation)
```

### 8.3 Report Generator

```python
class ReportFormat(str, Enum):
    MARKDOWN = "markdown"
    PDF = "pdf"
    JSON = "json"
    HTML = "html"

class ReportGenerator:
    """Generate investigation reports"""
    
    def generate(
        self,
        result: InvestigationResult,
        format: ReportFormat
    ) -> bytes:
        """Generate report in specified format"""
        
        if format == ReportFormat.MARKDOWN:
            return self._generate_markdown(result)
        elif format == ReportFormat.PDF:
            return self._generate_pdf(result)
        elif format == ReportFormat.JSON:
            return result.model_dump_json(indent=2).encode()
        elif format == ReportFormat.HTML:
            return self._generate_html(result)
    
    def _generate_markdown(self, result: InvestigationResult) -> bytes:
        """Generate Markdown report"""
        
        md = f"""# Incident Investigation Report

## Summary

| Field | Value |
|-------|-------|
| **Alert** | {result.alert_title} |
| **Severity** | {result.alert_severity} |
| **Status** | {result.status} |
| **Duration** | {result.duration_seconds}s |
| **Confidence** | {result.confidence_score:.0%} |

## Root Cause

**{result.root_cause.hypothesis}**

Category: {result.root_cause.category}  
Confidence: {result.root_cause.confidence:.0%}

### Evidence Summary

{result.root_cause.evidence_summary}

## Timeline

{self._format_timeline(result.incident_timeline)}

## Blast Radius

- **Services affected**: {', '.join(result.blast_radius.get('services', []))}
- **Users affected**: ~{result.blast_radius.get('users_affected', 'Unknown')}

## Remediation

### Summary

{result.remediation.summary}

### Steps

{self._format_steps(result.remediation.steps)}

### Risk Assessment

- **Total Risk Score**: {result.remediation.total_risk_score:.0%}
- **Requires Approval**: {'Yes' if result.remediation.requires_human_approval else 'No'}
- **Estimated Time**: {result.remediation.estimated_resolution_time}

## Metrics

- **Time Saved**: {result.time_saved_estimate}
- **Agents Used**: {', '.join(result.agents_used)}
- **Total Findings**: {result.total_findings}

---

*Generated by IncidentAgent at {datetime.utcnow().isoformat()}*
"""
        return md.encode()
```

### 8.4 Integration Webhooks

```python
class IntegrationManager:
    """Manages output integrations"""
    
    async def send_to_pagerduty(
        self,
        result: InvestigationResult,
        incident_id: str
    ):
        """Post investigation results to PagerDuty incident"""
        
        note = f"""
🤖 IncidentAgent Investigation Complete

**Root Cause**: {result.root_cause.hypothesis}
**Confidence**: {result.root_cause.confidence:.0%}

**Remediation**:
{result.remediation.summary}

**Time Saved**: {result.time_saved_estimate}
"""
        
        await self.pagerduty_client.add_incident_note(
            incident_id=incident_id,
            note=note
        )
    
    async def send_to_slack(
        self,
        result: InvestigationResult,
        channel: str
    ):
        """Post investigation results to Slack"""
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🚨 Investigation Complete: {result.alert_title}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Root Cause:*\n{result.root_cause.hypothesis}"},
                    {"type": "mrkdwn", "text": f"*Confidence:*\n{result.root_cause.confidence:.0%}"}
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Remediation:*\n{result.remediation.summary}"
                }
            }
        ]
        
        await self.slack_client.post_message(
            channel=channel,
            blocks=blocks
        )
```

---

## 9. Memory & Learning

### 9.1 Storage Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    GRADIENT STORAGE                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  KNOWLEDGE BASE: Runbooks                                               │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  ID: kb_runbooks                                                 │   │
│  │  Type: Static documents                                          │   │
│  │  Content: Troubleshooting guides, SOPs, best practices           │   │
│  │  Updated: Manually                                               │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  KNOWLEDGE BASE: Past Incidents                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  ID: kb_incidents                                                │   │
│  │  Type: Dynamic (grows over time)                                 │   │
│  │  Content: StoredIncident records                                 │   │
│  │  Updated: After each resolved incident                           │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 9.2 Stored Incident Schema

```python
class StoredIncident(BaseModel):
    """Complete incident record for memory + training"""
    
    # Identity
    incident_id: str
    created_at: datetime
    resolved_at: Optional[datetime]
    
    # Alert
    alert: Dict
    alert_type: str
    severity: str
    affected_services: List[str]
    
    # Investigation
    investigation_duration_seconds: int
    agents_used: List[str]
    findings: List[Dict]
    
    # Root Cause
    root_cause: Dict
    root_cause_category: str
    root_cause_confidence: float
    
    # Reasoning Chain (for training)
    reasoning_chain: List[Dict]
    
    # Remediation
    remediation_attempted: List[Dict]
    remediation_successful: bool
    remediation_that_worked: Optional[Dict]
    resolution_time_seconds: Optional[int]
    
    # Feedback
    human_verified: bool
    human_correction: Optional[str]
    feedback_score: Optional[int]
    
    # Embeddings (for similarity search)
    alert_embedding: List[float]
    root_cause_embedding: List[float]
```

### 9.3 Model Training Pipeline

```python
class ModelVersionManager:
    """Manages model training and promotion"""
    
    def __init__(self):
        self.production_model: str = "v1.0"
        self.candidate_model: Optional[str] = None
        self.benchmark_threshold: float = 0.02  # Must be 2% better
    
    async def train_new_version(self, incidents: List[StoredIncident]):
        """Train candidate model on new incidents"""
        
        # 1. Copy current model
        new_version = self._increment_version(self.production_model)
        base = await self._copy_model(self.production_model)
        
        # 2. Prepare training data
        training_data = self._prepare_data(incidents)
        
        # 3. Fine-tune on Gradient GPU
        candidate = await self._fine_tune(base, training_data, new_version)
        
        self.candidate_model = new_version
        return candidate
    
    async def evaluate_and_promote(self) -> bool:
        """Evaluate candidate and promote if better"""
        
        # Run benchmark
        candidate_score = await self._benchmark(self.candidate_model)
        current_score = await self._benchmark(self.production_model)
        
        # Promote if better
        if candidate_score > current_score + self.benchmark_threshold:
            old = self.production_model
            self.production_model = self.candidate_model
            self.candidate_model = None
            await self._archive(old)
            return True
        
        return False

class TrainingPipeline:
    """Continuous training pipeline"""
    
    def __init__(self):
        self.model_manager = ModelVersionManager()
        self.incident_buffer: List[StoredIncident] = []
        self.training_threshold: int = 100
    
    async def on_incident_resolved(self, incident: StoredIncident):
        """Called when incident is resolved and verified"""
        
        if not incident.human_verified:
            return
        
        self.incident_buffer.append(incident)
        
        if len(self.incident_buffer) >= self.training_threshold:
            await self._trigger_training()
    
    async def _trigger_training(self):
        """Train and evaluate new model"""
        
        await self.model_manager.train_new_version(self.incident_buffer)
        promoted = await self.model_manager.evaluate_and_promote()
        
        if promoted:
            self.incident_buffer = []
```

---

## 10. Data Schemas

All data schemas are defined in `incidentagent/schemas/`:

```
incidentagent/
└── schemas/
    ├── __init__.py
    ├── alert.py             # UnifiedAlert
    ├── triage.py            # TriageResult, AlertType
    ├── evidence.py          # Finding, AgentEvidence
    ├── investigation.py     # InvestigationState, InvestigationResult
    ├── remediation.py       # Remediation, RemediationStep, RiskLevel
    ├── root_cause.py        # RootCauseHypothesis
    ├── memory.py            # StoredIncident
    └── config.py            # Configuration schemas
```

---

## 11. Gradient Feature Mapping

| Feature | Component | Usage |
|---------|-----------|-------|
| **Agent Development Kit** | All agents | `@entrypoint`, `@trace_*` decorators |
| **Knowledge Bases** | RunbookAgent, MemoryAgent | Store runbooks + past incidents |
| **Agent Routing** | Triage Agent | Route to investigation queue |
| **Function Calling** | All sub-agents | Tools for data retrieval |
| **Guardrails** | Remediation Agent | Safety checks on suggestions |
| **GPU Droplets** | Training Pipeline | Fine-tune custom model |
| **Evaluation** | Benchmark | Test model accuracy |
| **Serverless Inference** | LLM calls | Anthropic Claude via Gradient |

---

## 12. Project Structure

```
incidentagent/
├── README.md
├── requirements.txt
├── pyproject.toml
├── .env.example
├── .gradient/
│   └── agent.yml
│
├── main.py                      # Gradient entrypoint
│
├── adapters/
│   ├── __init__.py
│   ├── base.py
│   ├── prometheus.py
│   ├── pagerduty.py
│   ├── webhook.py
│   └── manual.py
│
├── agents/
│   ├── __init__.py
│   ├── base.py
│   ├── triage.py
│   ├── investigator.py
│   ├── remediation.py
│   └── sub_agents/
│       ├── __init__.py
│       ├── deploy.py
│       ├── logs.py
│       ├── metrics.py
│       ├── k8s.py
│       ├── runbook.py
│       └── memory.py
│
├── schemas/
│   ├── __init__.py
│   ├── alert.py
│   ├── triage.py
│   ├── evidence.py
│   ├── investigation.py
│   ├── remediation.py
│   ├── root_cause.py
│   ├── memory.py
│   └── config.py
│
├── tools/
│   ├── __init__.py
│   ├── elasticsearch.py
│   ├── prometheus.py
│   ├── kubernetes.py
│   └── git.py
│
├── guardrails/
│   ├── __init__.py
│   └── remediation.py
│
├── training/
│   ├── __init__.py
│   ├── pipeline.py
│   └── version_manager.py
│
├── output/
│   ├── __init__.py
│   ├── report.py
│   └── integrations.py
│
├── ui/
│   └── dashboard.py
│
├── knowledge/
│   ├── runbooks/
│   │   └── *.md
│   └── sample_incidents/
│       └── *.json
│
├── tests/
│   ├── __init__.py
│   ├── test_agents.py
│   ├── test_guardrails.py
│   └── eval_dataset.csv
│
└── docs/
    ├── PHASE0_RESEARCH.md
    ├── PHASE1_ARCHITECTURE.md
    └── CLAUDE_INSTRUCTIONS.md
```

---

## 13. Configuration

### 13.1 Environment Variables

```bash
# .env.example

# DigitalOcean Gradient
DIGITALOCEAN_API_TOKEN=your_token
GRADIENT_MODEL_ACCESS_KEY=your_key

# Data Sources
ELASTICSEARCH_URL=http://localhost:9200
PROMETHEUS_URL=http://localhost:9090
KUBERNETES_CONFIG=~/.kube/config

# Optional Integrations
PAGERDUTY_API_KEY=
SLACK_WEBHOOK_URL=

# Model Training
TRAINING_THRESHOLD=100
BENCHMARK_THRESHOLD=0.02
```

### 13.2 Application Config

```yaml
# config.yaml

app:
  name: incidentagent
  version: "1.0.0"
  
investigation:
  confidence_threshold: 0.85
  max_agents_per_investigation: 6
  timeout_seconds: 300

alert_sources:
  manual:
    enabled: true
  webhook:
    enabled: true
    endpoint: /api/alerts
  prometheus:
    enabled: false
    url: ${PROMETHEUS_URL}
  pagerduty:
    enabled: false
    api_key: ${PAGERDUTY_API_KEY}

knowledge_bases:
  runbooks:
    id: kb_runbooks
    path: ./knowledge/runbooks
  incidents:
    id: kb_incidents
    
output:
  dashboard:
    enabled: true
    port: 8501
  reports:
    enabled: true
    formats: [markdown, pdf, json]
  integrations:
    pagerduty:
      enabled: false
    slack:
      enabled: false

training:
  enabled: true
  threshold: 100
  benchmark_improvement: 0.02
```

### 13.3 Gradient Agent Config

```yaml
# .gradient/agent.yml

name: incidentagent
runtime: python3.11
entrypoint: main:main

environment:
  - DIGITALOCEAN_API_TOKEN
  - GRADIENT_MODEL_ACCESS_KEY
  - ELASTICSEARCH_URL
  
knowledge_bases:
  - kb_runbooks
  - kb_incidents

guardrails:
  enabled: true
  
evaluation:
  enabled: true
  dataset: tests/eval_dataset.csv
```

---

## Summary

This architecture document defines:

1. ✅ **Alert Router**: Normalize alerts from multiple sources
2. ✅ **Triage Agent**: Classify and route alerts
3. ✅ **Investigator Master**: Orchestrate sub-agents with iterative refinement
4. ✅ **6 Sub-Agents**: Deploy, Logs, Metrics, K8s, Runbook, Memory
5. ✅ **Remediation Agent**: Safe suggestions with guardrails
6. ✅ **Output Layer**: Dashboard, reports, integrations
7. ✅ **Memory System**: Learn from past incidents
8. ✅ **Training Pipeline**: Continuous improvement with benchmark gating
9. ✅ **All Schemas**: Complete data models
10. ✅ **Gradient Mapping**: How each feature is used
11. ✅ **Project Structure**: File organization
12. ✅ **Configuration**: Environment and app config

---

## Next Steps for Claude Code

1. Create project directory structure
2. Implement schemas first (foundation)
3. Build adapters (alert ingestion)
4. Implement agents one by one
5. Build dashboard
6. Set up Gradient deployment
7. Create demo data
8. Record demo video

**Start with**: Create the project structure and implement schemas.
