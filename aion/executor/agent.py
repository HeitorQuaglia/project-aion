"""Executor agent for the execute lifecycle stage."""

from __future__ import annotations

import time
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from agno.agent import Agent
from agno.run.agent import RunOutput

from aion.domain.models import Observation, Run, RunStatus, Scenario
from aion.providers.factory import ModelConfig, build_model, provider_name
from aion.storage.run_store import RunStore

if TYPE_CHECKING:
    pass


def _extract_tokens(response: RunOutput) -> tuple[int | None, int | None]:
    """Return (input_tokens, output_tokens) from a RunOutput, or (None, None) if unavailable."""
    metrics = response.metrics
    if metrics is None:
        return None, None
    input_t = metrics.input_tokens or None
    output_t = metrics.output_tokens or None
    return input_t, output_t


class ExecutorAgent:
    """Executes a single Scenario against a configured LLM and returns a Run.

    Sits at the ``execute`` lifecycle stage. Each call to ``run()`` creates a
    fresh Agno agent with an isolated session — no context leaks between
    scenario executions. The resulting ``Run`` record is persisted via the
    injected ``RunStore`` before being returned.

    Args:
        model_config: Provider and model configuration.
        run_store: Persistence layer for ``Run`` records.
    """

    def __init__(self, model_config: ModelConfig, run_store: RunStore) -> None:
        """Initialise the executor.

        Args:
            model_config: Provider and model configuration.
            run_store: Persistence layer for ``Run`` records.
        """
        self._model_config = model_config
        self._run_store = run_store
        self._provider = provider_name(model_config)

    def run(self, scenario: Scenario) -> Run:
        """Execute a scenario and return a completed or failed Run.

        Args:
            scenario: The scenario to execute.

        Returns:
            A ``Run`` with ``status`` ``COMPLETE`` or ``FAILED`` and an
            ``Observation`` attached.
        """
        session_id = str(uuid.uuid4())
        run = Run(
            id=str(uuid.uuid4()),
            scenario_id=scenario.id,
            suite_id=scenario.suite_id,
            session_id=session_id,
            status=RunStatus.RUNNING,
            started_at=datetime.now(UTC),
            model_id=self._model_config.model_id,
            provider=self._provider,
        )
        self._run_store.save(run)

        agent = Agent(
            model=build_model(self._model_config),
            session_id=session_id,
            instructions=["Execute the following test instruction faithfully and completely."],
        )

        wall_start = time.perf_counter()
        try:
            response = agent.run(scenario.input)
            wall_ms = (time.perf_counter() - wall_start) * 1000.0

            input_tokens, output_tokens = _extract_tokens(response)
            observation = Observation(
                raw_response=response.content or "",
                wall_time_ms=wall_ms,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
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
