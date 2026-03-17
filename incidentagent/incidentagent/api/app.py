"""FastAPI application for IncidentAgent API."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from incidentagent.api.routes import alerts, investigations, health

app = FastAPI(
    title="IncidentAgent API",
    description="AI-powered incident investigation API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["health"])
app.include_router(alerts.router, prefix="/api", tags=["alerts"])
app.include_router(investigations.router, prefix="/api", tags=["investigations"])
