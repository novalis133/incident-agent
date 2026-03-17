"""Seed Knowledge Base with runbooks and incident data."""
import os
from pathlib import Path
from typing import List
import httpx
import structlog

from incidentagent.schemas.config import get_settings

logger = structlog.get_logger()

RUNBOOKS_DIR = Path(__file__).parent.parent.parent / "knowledge" / "runbooks"


async def seed_runbooks() -> int:
    """Upload runbooks to Gradient KB."""
    settings = get_settings()
    api_token = settings.gradient.api_token or settings.gradient.model_access_key

    if not api_token:
        logger.warning("seed_skipped", reason="no API token")
        return 0

    kb_id = settings.gradient.runbooks_kb_id
    count = 0

    if not RUNBOOKS_DIR.exists():
        logger.warning("runbooks_dir_missing", path=str(RUNBOOKS_DIR))
        return 0

    async with httpx.AsyncClient(timeout=60.0) as client:
        for md_file in RUNBOOKS_DIR.glob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                response = await client.post(
                    f"https://cluster-api.do-ai.run/v1/knowledge_bases/{kb_id}/documents",
                    headers={
                        "Authorization": f"Bearer {api_token}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "title": md_file.stem.replace("-", " ").replace("_", " ").title(),
                        "content": content,
                        "metadata": {"type": "runbook", "filename": md_file.name},
                    },
                )
                response.raise_for_status()
                count += 1
                logger.info("runbook_uploaded", filename=md_file.name)
            except Exception as e:
                logger.error("runbook_upload_failed", filename=md_file.name, error=str(e))

    return count


SAMPLE_INCIDENTS = [
    {
        "title": "Payment Service Connection Pool Exhaustion",
        "content": (
            "Root cause: Connection leak in PaymentProcessor.java introduced in v2.3.1. "
            "The new code path failed to close database connections in the error handling branch, "
            "causing gradual pool exhaustion over ~2 hours. "
            "Resolution: Rollback to v2.3.0, then fix connection handling in v2.3.2. "
            "Time to resolve: 45 minutes."
        ),
        "metadata": {
            "incident_id": "INC-2024-0892",
            "category": "deployment",
            "service": "payment-service",
        },
    },
    {
        "title": "Checkout Service OOM Kills",
        "content": (
            "Root cause: Memory leak in cart serialization module after upgrading Jackson library. "
            "Each cart operation leaked ~2MB. Under normal load, pods would OOM after ~4 hours. "
            "Resolution: Pin Jackson to previous version, increase memory limits temporarily. "
            "Time to resolve: 2 hours."
        ),
        "metadata": {
            "incident_id": "INC-2024-1156",
            "category": "resource",
            "service": "checkout-service",
        },
    },
    {
        "title": "API Gateway Latency Spike",
        "content": (
            "Root cause: DNS resolution timeout caused by upstream DNS provider degradation. "
            "All external API calls experienced 5s+ latency. "
            "Resolution: Switch to backup DNS resolver, implement DNS caching. "
            "Time to resolve: 30 minutes."
        ),
        "metadata": {
            "incident_id": "INC-2025-0034",
            "category": "dependency",
            "service": "api-gateway",
        },
    },
    {
        "title": "Order Service Config Rollback Failure",
        "content": (
            "Root cause: ConfigMap update with invalid JSON in feature flags caused "
            "order-service pods to crash-loop. The invalid JSON was not caught by CI because "
            "config validation was only run against staging format. "
            "Resolution: Revert ConfigMap, add JSON schema validation to CI. "
            "Time to resolve: 1 hour."
        ),
        "metadata": {
            "incident_id": "INC-2025-0089",
            "category": "config",
            "service": "order-service",
        },
    },
]


async def seed_incidents() -> int:
    """Upload sample incidents to Gradient KB."""
    settings = get_settings()
    api_token = settings.gradient.api_token or settings.gradient.model_access_key

    if not api_token:
        logger.warning("seed_skipped", reason="no API token")
        return 0

    kb_id = settings.gradient.incidents_kb_id
    count = 0

    async with httpx.AsyncClient(timeout=60.0) as client:
        for incident in SAMPLE_INCIDENTS:
            try:
                response = await client.post(
                    f"https://cluster-api.do-ai.run/v1/knowledge_bases/{kb_id}/documents",
                    headers={
                        "Authorization": f"Bearer {api_token}",
                        "Content-Type": "application/json",
                    },
                    json=incident,
                )
                response.raise_for_status()
                count += 1
                logger.info("incident_uploaded", title=incident["title"])
            except Exception as e:
                logger.error("incident_upload_failed", title=incident["title"], error=str(e))

    return count
