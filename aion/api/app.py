"""FastAPI application factory."""

from fastapi import FastAPI

from aion.api.dependencies import get_run_store, get_runner, get_suites
from aion.api.routers.health import router as health_router
from aion.api.routers.runs import router as runs_router
from aion.api.routers.suites import router as suites_router
from aion.api.settings import ApiSettings
from aion.api.state import AppState
from aion.runner import Runner
from aion.storage.run_store import RunStore

__all__ = ["create_app"]

# Re-export dependency helpers so callers can import from aion.api.app if needed
__all__ += ["get_run_store", "get_runner", "get_suites"]


def create_app(settings: ApiSettings | None = None) -> FastAPI:
    """Create and configure the Aion FastAPI application.

    Args:
        settings: Optional settings override. Reads from environment when omitted.

    Returns:
        A configured ``FastAPI`` instance with all routers mounted.
    """
    if settings is None:
        settings = ApiSettings()

    config = settings.to_aion_config()
    config.storage_path.mkdir(parents=True, exist_ok=True)

    state = AppState(
        run_store=RunStore(db_path=config.storage_path / "aion.db"),
        runner=Runner(config),
    )

    app = FastAPI(title="Aion API", version="0.1.0")
    app.state.aion = state

    app.include_router(health_router)
    app.include_router(suites_router, prefix="/suites")
    app.include_router(runs_router)

    return app
