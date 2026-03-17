"""Gradient Knowledge Base client."""
import json
from typing import Any, Dict, List, Optional
import httpx
import structlog

try:
    from gradient_adk import trace_retriever
except ImportError:
    def trace_retriever(name):
        def decorator(fn):
            return fn
        return decorator

from incidentagent.schemas.config import get_settings

logger = structlog.get_logger()


class KBClient:
    """Client for Gradient Knowledge Base queries."""

    def __init__(self):
        settings = get_settings()
        self.api_token = settings.gradient.api_token or settings.gradient.model_access_key
        self.runbooks_kb_id = settings.gradient.runbooks_kb_id
        self.incidents_kb_id = settings.gradient.incidents_kb_id
        self._available = self.api_token is not None
        self.logger = logger.bind(component="kb_client")

    @property
    def is_available(self) -> bool:
        return self._available

    @trace_retriever("gradient-kb-search")
    async def search_runbooks(self, query: str, top_k: int = 5) -> Optional[List[Dict[str, Any]]]:
        """Search runbooks knowledge base."""
        if not self._available:
            return None
        return await self._search(self.runbooks_kb_id, query, top_k)

    @trace_retriever("gradient-kb-incidents")
    async def search_incidents(self, query: str, top_k: int = 5) -> Optional[List[Dict[str, Any]]]:
        """Search past incidents knowledge base."""
        if not self._available:
            return None
        return await self._search(self.incidents_kb_id, query, top_k)

    async def _search(self, kb_id: str, query: str, top_k: int) -> Optional[List[Dict[str, Any]]]:
        """Execute a KB search."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"https://cluster-api.do-ai.run/v1/knowledge_bases/{kb_id}/search",
                    headers={
                        "Authorization": f"Bearer {self.api_token}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "query": query,
                        "top_k": top_k,
                    },
                )
                response.raise_for_status()
                data = response.json()
                return data.get("results", [])
        except Exception as e:
            self.logger.error("kb_search_failed", kb_id=kb_id, error=str(e))
            return None


_client: Optional[KBClient] = None


def get_kb_client() -> KBClient:
    global _client
    if _client is None:
        _client = KBClient()
    return _client
