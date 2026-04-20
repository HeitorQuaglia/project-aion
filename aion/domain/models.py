"""Pydantic domain models for Project Aion's core lifecycle objects."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class Probe(BaseModel):
    """A single evaluable property of an expected output.

    Args:
        id: Stable slug identifier (e.g. ``"tone-neutral"``).
        description: Human-readable question or rubric statement.
        probe_type: Whether evaluation is rule-based or model-judged.
    """

    id: str
    description: str
    probe_type: Literal["deterministic", "llm_judge"]


class Scenario(BaseModel):
    """Atomic unit of execution: an input paired with evaluation probes.

    Args:
        id: Stable identifier for this scenario.
        suite_id: Identifier of the suite this scenario belongs to.
        input: Raw prompt or instruction sent to the executor.
        probes: Ordered list of properties to evaluate on the output.
        tags: Arbitrary key-value metadata for filtering and grouping.
    """

    id: str
    suite_id: str
    input: str
    probes: list[Probe] = Field(default_factory=list)
    tags: dict[str, str] = Field(default_factory=dict)


class Observation(BaseModel):
    """Execution metadata captured during the execute lifecycle stage.

    Args:
        raw_response: The model's verbatim text output.
        wall_time_ms: Elapsed wall-clock time in milliseconds.
        input_tokens: Number of prompt tokens consumed, if reported.
        output_tokens: Number of completion tokens produced, if reported.
        error: Error message if execution failed; ``None`` on success.
    """

    raw_response: str
    wall_time_ms: float
    input_tokens: int | None = None
    output_tokens: int | None = None
    error: str | None = None


class RunStatus(StrEnum):
    """Execution lifecycle states for a Run."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"


class Run(BaseModel):
    """A single execution record for one Scenario.

    Immutable after creation — use ``model_copy(update={...})`` to produce
    updated versions as the run transitions through its lifecycle states.

    Args:
        id: UUID assigned at creation.
        scenario_id: The scenario that was executed.
        suite_id: The suite the scenario belongs to.
        session_id: Correlation ID linking this run to any external session.
        status: Current execution state.
        observation: Output and metrics captured during execution.
        started_at: UTC timestamp when execution began.
        finished_at: UTC timestamp when execution ended.
        model_id: Model identifier used (e.g. ``"gpt-4o"``).
        provider: Name of the model provider.
        metadata: Arbitrary extra data attached by the caller.
    """

    model_config = ConfigDict(frozen=True)

    id: str
    scenario_id: str
    suite_id: str
    session_id: str
    status: RunStatus = RunStatus.PENDING
    observation: Observation | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    model_id: str
    provider: Literal["bedrock", "openai"]
    metadata: dict[str, Any] = Field(default_factory=dict)
