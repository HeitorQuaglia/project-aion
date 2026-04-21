"""Health-check router."""

from fastapi import APIRouter

from aion.api.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    """Return a simple liveness signal."""
    return HealthResponse()
