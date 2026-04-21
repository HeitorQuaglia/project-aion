"""HTTP-based executor for testing agents that expose an HTTP endpoint."""

from __future__ import annotations

import time
import uuid
from datetime import UTC, datetime
from typing import Any

import httpx
from pydantic import BaseModel

from aion.domain.models import Observation, Run, RunStatus, Scenario
from aion.storage.run_store import RunStore


class HttpTargetConfig(BaseModel):
    """Configuration for an HTTP-based target agent.

    The agent endpoint must accept POST requests with a JSON body containing
    ``"message"`` (the scenario input) plus any extra fields from
    ``scenario.tags``, and return a JSON object with a string field named
    ``response_field``.

    Args:
        url: Full URL of the target endpoint.
        headers: Extra HTTP headers (e.g. auth tokens).
        timeout_seconds: Request timeout.
        provider_name: Logical name stored on the resulting Run.
        response_field: JSON key to extract as the raw response string.
    """

    url: str
    headers: dict[str, str] = {}
    timeout_seconds: float = 30.0
    provider_name: str = "http"
    response_field: str = "message"


class HttpExecutorAgent:
    """Executes a Scenario by POSTing to a configured HTTP endpoint.

    Satisfies the same ``run(scenario) -> Run`` interface as ``ExecutorAgent``,
    making it a drop-in replacement inside ``Runner``.

    Args:
        target_config: HTTP endpoint configuration.
        run_store: Persistence layer for ``Run`` records.
    """

    def __init__(self, target_config: HttpTargetConfig, run_store: RunStore) -> None:
        self._config = target_config
        self._run_store = run_store

    def run(self, scenario: Scenario) -> Run:
        """POST the scenario input to the target endpoint and return a Run.

        Args:
            scenario: The scenario to execute.

        Returns:
            A ``Run`` with ``status`` ``COMPLETE`` or ``FAILED``.
        """
        session_id = str(uuid.uuid4())
        run = Run(
            id=str(uuid.uuid4()),
            scenario_id=scenario.id,
            suite_id=scenario.suite_id,
            session_id=session_id,
            status=RunStatus.RUNNING,
            started_at=datetime.now(UTC),
            model_id=self._config.url,
            provider=self._config.provider_name,
        )
        self._run_store.save(run)

        body: dict[str, Any] = {"message": scenario.input, **scenario.tags}

        wall_start = time.perf_counter()
        try:
            with httpx.Client(
                headers=self._config.headers,
                timeout=self._config.timeout_seconds,
            ) as client:
                resp = client.post(self._config.url, json=body)
                resp.raise_for_status()

            wall_ms = (time.perf_counter() - wall_start) * 1000.0
            raw = resp.json().get(self._config.response_field, "")
            observation = Observation(
                raw_response=str(raw),
                wall_time_ms=wall_ms,
            )
            run = run.model_copy(
                update={
                    "status": RunStatus.COMPLETE,
                    "observation": observation,
                    "finished_at": datetime.now(UTC),
                }
            )
        except Exception as exc:
            wall_ms = (time.perf_counter() - wall_start) * 1000.0
            observation = Observation(
                raw_response="",
                wall_time_ms=wall_ms,
                error=str(exc),
            )
            run = run.model_copy(
                update={
                    "status": RunStatus.FAILED,
                    "observation": observation,
                    "finished_at": datetime.now(UTC),
                }
            )

        self._run_store.save(run)
        return run
