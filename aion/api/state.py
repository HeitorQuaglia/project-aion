"""Mutable application state shared across requests."""

from dataclasses import dataclass, field

from aion.domain.models import Suite
from aion.runner import Runner
from aion.storage.run_store import RunStore


@dataclass
class AppState:
    """Holds shared objects for the lifetime of a single FastAPI application instance."""

    run_store: RunStore
    runner: Runner
    suites: dict[str, Suite] = field(default_factory=dict)
