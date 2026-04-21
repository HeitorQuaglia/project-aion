"""FastAPI dependency functions for injecting shared state."""

from typing import Annotated, cast

from fastapi import Depends, Request

from aion.api.state import AppState
from aion.domain.models import Suite
from aion.runner import Runner
from aion.storage.run_store import RunStore


def get_state(request: Request) -> AppState:
    """Extract the ``AppState`` from the FastAPI application instance."""
    return cast(AppState, request.app.state.aion)


def get_run_store(state: Annotated[AppState, Depends(get_state)]) -> RunStore:
    """Return the shared ``RunStore``."""
    return state.run_store


def get_runner(state: Annotated[AppState, Depends(get_state)]) -> Runner:
    """Return the shared ``Runner``."""
    return state.runner


def get_suites(state: Annotated[AppState, Depends(get_state)]) -> dict[str, Suite]:
    """Return the in-memory suite registry."""
    return state.suites
