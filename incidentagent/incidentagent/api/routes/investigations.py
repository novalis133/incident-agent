"""Investigation status and result retrieval endpoint."""
from fastapi import APIRouter, HTTPException

from incidentagent.api.store import store

router = APIRouter()


@router.get("/investigations/{investigation_id}")
async def get_investigation(investigation_id: str):
    """Return the status and result for a specific investigation.

    Raises 404 if the investigation_id is not found in the store.
    """
    investigation = store.get(investigation_id)
    if investigation is None:
        raise HTTPException(
            status_code=404,
            detail=f"Investigation '{investigation_id}' not found.",
        )
    return investigation
