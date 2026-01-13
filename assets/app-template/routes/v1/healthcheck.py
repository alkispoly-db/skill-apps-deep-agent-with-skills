"""
Health check endpoint for service availability monitoring.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()


class HealthCheckResponse(BaseModel):
    """Health check response model."""

    status: str
    timestamp: str
    service: str


@router.get("/healthcheck", response_model=HealthCheckResponse)
async def healthcheck():
    """
    Health check endpoint for monitoring service availability.

    Returns:
        HealthCheckResponse with status, timestamp, and service name
    """
    return HealthCheckResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        service="openai-compatible-api",
    )
