"""LLM integration module for IncidentAgent."""
from incidentagent.llm.client import LLMClient, get_llm_client
from incidentagent.llm.prompts import TriagePrompt, SynthesisPrompt, RemediationPrompt

__all__ = [
    "LLMClient",
    "get_llm_client",
    "TriagePrompt",
    "SynthesisPrompt",
    "RemediationPrompt",
]
