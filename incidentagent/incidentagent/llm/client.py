"""Gradient LLM client with tracing."""
import json
from typing import Any, Dict, Optional

import httpx
import structlog

try:
    from gradient_adk import trace_llm
except ImportError:
    def trace_llm(name):
        def decorator(fn):
            return fn
        return decorator

from incidentagent.schemas.config import get_settings

logger = structlog.get_logger()


class LLMClient:
    """Client for Gradient LLM API calls."""

    def __init__(self):
        settings = get_settings()
        self.api_token = settings.gradient.api_token or settings.gradient.model_access_key
        self.model = settings.llm.model
        self.temperature = settings.llm.temperature
        self.max_tokens = settings.llm.max_tokens
        self._available = self.api_token is not None
        self.logger = logger.bind(component="llm_client")

        if self._available:
            self.logger.info("llm_client_initialized", model=self.model)
        else:
            self.logger.warning(
                "llm_client_unavailable",
                reason="no API token configured",
            )

    @property
    def is_available(self) -> bool:
        return self._available

    @trace_llm("gradient-completion")
    async def complete(
        self,
        prompt: str,
        system_prompt: str = "You are an expert SRE assistant.",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Optional[str]:
        """Send a completion request to the LLM.

        Args:
            prompt: The user prompt to send.
            system_prompt: The system prompt context.
            temperature: Override the default temperature.
            max_tokens: Override the default max token limit.

        Returns:
            The model's text response, or None if unavailable or failed.
        """
        if not self._available:
            return None

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://cluster-api.do-ai.run/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_token}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": temperature if temperature is not None else self.temperature,
                        "max_tokens": max_tokens if max_tokens is not None else self.max_tokens,
                    },
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            self.logger.error("llm_completion_failed", error=str(e))
            return None

    @trace_llm("gradient-json-completion")
    async def complete_json(
        self,
        prompt: str,
        system_prompt: str = "You are an expert SRE assistant. Respond only with valid JSON.",
    ) -> Optional[Dict[str, Any]]:
        """Send a completion request expecting a JSON response.

        Strips markdown code fences if the model wraps its JSON output in them.

        Args:
            prompt: The user prompt to send.
            system_prompt: The system prompt context.

        Returns:
            Parsed JSON dict, or None if unavailable, failed, or parse error.
        """
        result = await self.complete(prompt, system_prompt)
        if result is None:
            return None

        try:
            text = result.strip()
            if text.startswith("```"):
                lines = text.split("\n")
                text = "\n".join(lines[1:-1])
            return json.loads(text)
        except json.JSONDecodeError:
            self.logger.warning("llm_json_parse_failed", response=result[:200])
            return None


_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Return a cached singleton LLMClient instance."""
    global _client
    if _client is None:
        _client = LLMClient()
    return _client
