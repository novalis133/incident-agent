"""
Base Agent Classes

Foundation for all agents in the system.
"""

import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Type

import structlog

from incidentagent.schemas.evidence import AgentEvidence, Finding

logger = structlog.get_logger()


class SubAgent(ABC):
    """
    Base class for all sub-agents.
    
    Sub-agents are specialized investigators that focus on specific
    data sources or investigation strategies.
    
    To create a new sub-agent:
    1. Inherit from SubAgent
    2. Set name and description
    3. Implement investigate() method
    4. Implement get_tools() method
    5. Register with AgentRegistry
    
    Example:
        class MyAgent(SubAgent):
            name = "MyAgent"
            description = "Does something useful"
            
            async def investigate(self, context: Dict) -> AgentEvidence:
                # Your investigation logic here
                pass
                
            def get_tools(self) -> List[Dict]:
                return [{"name": "my_tool", "description": "..."}]
    """
    
    # Override in subclass
    name: str = "BaseAgent"
    description: str = "Base agent class"
    
    def __init__(self):
        self.logger = logger.bind(agent=self.name)
    
    @abstractmethod
    async def investigate(self, context: Dict[str, Any]) -> AgentEvidence:
        """
        Run investigation and return evidence.
        
        Args:
            context: Investigation context containing:
                - alert: The original alert
                - triage: Triage results
                - previous_findings: Findings from prior agents
                - timeline_so_far: Current timeline
                - hypotheses_so_far: Current hypotheses
                - investigation_id: Unique investigation ID
        
        Returns:
            AgentEvidence with findings, confidence, and recommendations
        """
        pass
    
    @abstractmethod
    def get_tools(self) -> List[Dict[str, Any]]:
        """
        Return tools this agent can use.
        
        Returns:
            List of tool definitions for Gradient function calling
        """
        pass
    
    def _build_evidence(
        self,
        findings: List[Finding],
        context: Dict[str, Any],
        confidence: float,
        confidence_reasoning: str,
        started_at: datetime,
        suggests_next_agent: Optional[str] = None,
        next_agent_context: Optional[str] = None,
        errors: Optional[List[str]] = None,
    ) -> AgentEvidence:
        """
        Helper to build AgentEvidence from findings.
        
        Args:
            findings: List of findings
            context: Investigation context
            confidence: Overall confidence score
            confidence_reasoning: Explanation for confidence
            started_at: When investigation started
            suggests_next_agent: Recommended next agent
            next_agent_context: Context for next agent
            errors: Any errors encountered
        
        Returns:
            Complete AgentEvidence
        """
        completed_at = datetime.utcnow()
        duration_ms = int((completed_at - started_at).total_seconds() * 1000)
        
        return AgentEvidence(
            agent_name=self.name,
            agent_type=self.__class__.__name__,
            investigation_id=context.get("investigation_id", "unknown"),
            step_number=context.get("step_number", 0),
            started_at=started_at,
            completed_at=completed_at,
            duration_ms=duration_ms,
            findings=findings,
            finding_count=len(findings),
            confidence=confidence,
            confidence_reasoning=confidence_reasoning,
            suggests_next_agent=suggests_next_agent,
            next_agent_context=next_agent_context,
            is_high_confidence=confidence > 0.85,
            is_root_cause_candidate=any(f.confidence > 0.8 for f in findings),
            early_stop_recommended=False,
            errors=errors or [],
        )
    
    def _generate_finding_id(self) -> str:
        """Generate unique finding ID"""
        return f"finding-{uuid.uuid4().hex[:8]}"


class AgentRegistry:
    """
    Registry for sub-agents.
    
    Allows dynamic registration and lookup of agents.
    
    Usage:
        # Register an agent
        AgentRegistry.register(DeployAgent)
        
        # Get an agent instance
        agent = AgentRegistry.get("DeployAgent")
        
        # List all agents
        agents = AgentRegistry.list_agents()
    """
    
    _agents: Dict[str, Type[SubAgent]] = {}
    _instances: Dict[str, SubAgent] = {}
    
    @classmethod
    def register(cls, agent_class: Type[SubAgent]) -> None:
        """Register a sub-agent class"""
        cls._agents[agent_class.name] = agent_class
        logger.info("agent_registered", agent=agent_class.name)
    
    @classmethod
    def get(cls, name: str) -> SubAgent:
        """Get an agent instance by name (cached)"""
        if name not in cls._instances:
            if name not in cls._agents:
                raise ValueError(f"Unknown agent: {name}")
            cls._instances[name] = cls._agents[name]()
        return cls._instances[name]
    
    @classmethod
    def list_agents(cls) -> List[str]:
        """List all registered agent names"""
        return list(cls._agents.keys())
    
    @classmethod
    def get_all(cls) -> Dict[str, SubAgent]:
        """Get all agent instances"""
        return {name: cls.get(name) for name in cls._agents}
    
    @classmethod
    def clear(cls) -> None:
        """Clear registry (for testing)"""
        cls._agents.clear()
        cls._instances.clear()


def register_agent(cls: Type[SubAgent]) -> Type[SubAgent]:
    """
    Decorator to register an agent.
    
    Usage:
        @register_agent
        class MyAgent(SubAgent):
            name = "MyAgent"
            ...
    """
    AgentRegistry.register(cls)
    return cls
