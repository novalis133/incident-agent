"""Alert ingestion and listing endpoints."""
import asyncio
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException

from incidentagent.api.store import store
from incidentagent.main import investigate_alert
from incidentagent.schemas.investigation import InvestigationResult
from incidentagent.schemas.alert import UnifiedAlert

router = APIRouter()


async def _run_investigation(investigation_id: str, alert: UnifiedAlert) -> None:
    """Background task: run investigation and update store on completion or failure."""
    try:
        result: InvestigationResult = await investigate_alert(alert)
        store.complete(investigation_id, result)
    except Exception as e:
        store.fail(investigation_id, str(e))


@router.post("/alerts")
async def create_alert(alert_data: dict[str, Any]):
    """Accept alert JSON, launch an investigation in the background, and return immediately.

    Returns the investigation_id so the caller can poll for results.
    """
    try:
        alert = UnifiedAlert(**alert_data)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Invalid alert payload: {e}") from e

    investigation_id = str(uuid.uuid4())
    store.create(investigation_id, alert_data)

    asyncio.create_task(_run_investigation(investigation_id, alert))

    return {"investigation_id": investigation_id, "status": "running"}


@router.get("/alerts")
async def list_alerts():
    """Return all investigations with their current status and results."""
    return store.list_all()
