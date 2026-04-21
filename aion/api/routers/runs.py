"""Runs router — trigger execution and query run records."""

import asyncio
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from aion.api.dependencies import get_run_store, get_runner, get_suites
from aion.api.schemas import TriggerResponse
from aion.domain.models import Run, Suite
from aion.runner import Runner
from aion.storage.run_store import RunStore

router = APIRouter(tags=["runs"])


async def _run_background(runner: Runner, suite: Suite) -> None:
    await asyncio.to_thread(runner.run_suite, suite)


@router.post("/suites/{suite_id}/runs", response_model=TriggerResponse, status_code=202)
async def trigger_run(
    suite_id: str,
    background_tasks: BackgroundTasks,
    runner: Annotated[Runner, Depends(get_runner)],
    suites: Annotated[dict[str, Suite], Depends(get_suites)],
) -> TriggerResponse:
    """Trigger execution of all scenarios in a suite.

    Args:
        suite_id: The suite to execute.
        background_tasks: FastAPI background task queue.
        runner: Injected ``Runner`` instance.
        suites: Injected in-memory suite registry.

    Raises:
        HTTPException: 404 if the suite does not exist.
        HTTPException: 422 if the suite has no scenarios.
    """
    suite = suites.get(suite_id)
    if suite is None:
        raise HTTPException(status_code=404, detail=f"Suite '{suite_id}' not found.")
    if not suite.scenarios:
        raise HTTPException(status_code=422, detail="Suite has no scenarios.")
    session_id = str(uuid4())
    background_tasks.add_task(_run_background, runner, suite)
    return TriggerResponse(
        session_id=session_id,
        suite_id=suite_id,
        scenario_count=len(suite.scenarios),
    )


@router.get("/runs/{run_id}", response_model=Run)
def get_run(
    run_id: str,
    run_store: Annotated[RunStore, Depends(get_run_store)],
) -> Run:
    """Return a single run by id.

    Raises:
        HTTPException: 404 if the run does not exist.
    """
    run = run_store.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")
    return run


@router.get("/runs", response_model=list[Run])
def list_runs(
    run_store: Annotated[RunStore, Depends(get_run_store)],
    suite_id: str | None = None,
    scenario_id: str | None = None,
) -> list[Run]:
    """Return runs filtered by suite or scenario.

    Args:
        run_store: Injected ``RunStore`` instance.
        suite_id: Filter by suite id.
        scenario_id: Filter by scenario id.

    Raises:
        HTTPException: 422 if neither ``suite_id`` nor ``scenario_id`` is provided.
    """
    if suite_id is not None:
        return run_store.list_by_suite(suite_id)
    if scenario_id is not None:
        return run_store.list_by_scenario(scenario_id)
    raise HTTPException(
        status_code=422,
        detail="Provide at least one query parameter: suite_id or scenario_id.",
    )
