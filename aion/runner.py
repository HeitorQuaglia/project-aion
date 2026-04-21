"""Orchestrates a full evaluation run: config + suite → Run results."""

from __future__ import annotations

from aion.config import AionConfig
from aion.domain.models import Run, Suite
from aion.executor.agent import ExecutorAgent
from aion.executor.http_executor import HttpExecutorAgent
from aion.storage.run_store import RunStore


class Runner:
    """Drives execution of all scenarios in a Suite under a given AionConfig.

    Args:
        config: Runtime configuration specifying the executor and storage location.
    """

    def __init__(self, config: AionConfig) -> None:
        """Initialise the runner, wiring storage and executor from config.

        The SQLite database file is placed at ``config.storage_path / "aion.db"``.
        """
        store = RunStore(db_path=config.storage_path / "aion.db")
        if config.http_target is not None:
            self._executor: ExecutorAgent | HttpExecutorAgent = HttpExecutorAgent(
                target_config=config.http_target,
                run_store=store,
            )
        else:
            assert config.llm is not None
            self._executor = ExecutorAgent(model_config=config.llm, run_store=store)

    def run_suite(self, suite: Suite) -> list[Run]:
        """Execute every scenario in the suite and return all Run records.

        Scenarios are executed sequentially. If a scenario fails, its Run is
        recorded with ``status=FAILED`` and execution continues with the next
        scenario — a single failure does not abort the suite.

        Args:
            suite: The suite whose scenarios will be executed.

        Returns:
            A list of ``Run`` objects in scenario order, one per scenario.
        """
        return [self._executor.run(scenario) for scenario in suite.scenarios]
