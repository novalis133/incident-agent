"""
Investigation Sub-Agents

Specialized agents for different data sources and investigation strategies.
"""

from incidentagent.agents.sub_agents.deploy import DeployAgent
from incidentagent.agents.sub_agents.logs import LogsAgent
from incidentagent.agents.sub_agents.metrics import MetricsAgent
from incidentagent.agents.sub_agents.k8s import K8sAgent
from incidentagent.agents.sub_agents.runbook import RunbookAgent
from incidentagent.agents.sub_agents.memory import MemoryAgent

__all__ = [
    "DeployAgent",
    "LogsAgent",
    "MetricsAgent",
    "K8sAgent",
    "RunbookAgent",
    "MemoryAgent",
]

# Register all agents
def register_all_agents():
    """Register all sub-agents with the registry."""
    from incidentagent.agents.base import AgentRegistry
    
    AgentRegistry.register(DeployAgent)
    AgentRegistry.register(LogsAgent)
    AgentRegistry.register(MetricsAgent)
    AgentRegistry.register(K8sAgent)
    AgentRegistry.register(RunbookAgent)
    AgentRegistry.register(MemoryAgent)
