"""Request and response schemas for the Aion REST API."""

from typing import Literal

from pydantic import BaseModel, Field

from aion.domain.models import Scenario


class SuiteCreate(BaseModel):
    """Payload for creating a new suite."""

    id: str
    name: str
    description: str = ""
    scenarios: list[Scenario] = Field(default_factory=list)


class TriggerResponse(BaseModel):
    """Response returned when a suite execution is triggered."""

    session_id: str
    suite_id: str
    scenario_count: int


class HealthResponse(BaseModel):
    """Response for the health-check endpoint."""

    status: Literal["ok"] = "ok"
