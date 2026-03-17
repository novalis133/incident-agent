"""In-memory investigation store."""
from datetime import datetime
from typing import Dict, Optional
from incidentagent.schemas.investigation import InvestigationResult


class InvestigationStore:
    """Thread-safe in-memory store for investigation results."""

    def __init__(self):
        self._investigations: Dict[str, dict] = {}

    def create(self, investigation_id: str, alert_data: dict) -> dict:
        """Create a new investigation entry."""
        entry = {
            "investigation_id": investigation_id,
            "status": "running",
            "alert": alert_data,
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": None,
            "result": None,
            "error": None,
        }
        self._investigations[investigation_id] = entry
        return entry

    def complete(self, investigation_id: str, result: InvestigationResult) -> None:
        """Mark an investigation as completed with its result."""
        if investigation_id in self._investigations:
            self._investigations[investigation_id]["status"] = "completed"
            self._investigations[investigation_id]["completed_at"] = datetime.utcnow().isoformat()
            self._investigations[investigation_id]["result"] = result.model_dump(mode="json")

    def fail(self, investigation_id: str, error: str) -> None:
        """Mark an investigation as failed with an error message."""
        if investigation_id in self._investigations:
            self._investigations[investigation_id]["status"] = "failed"
            self._investigations[investigation_id]["error"] = error

    def get(self, investigation_id: str) -> Optional[dict]:
        """Retrieve a single investigation by ID."""
        return self._investigations.get(investigation_id)

    def list_all(self) -> list:
        """Return all investigations as a list."""
        return list(self._investigations.values())


# Global store instance
store = InvestigationStore()
