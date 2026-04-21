"""Tests for aion.executor.agent."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from unittest.mock import patch

from aion.domain.models import RunStatus, Scenario
from aion.executor.agent import ExecutorAgent
from aion.providers.factory import OpenAIConfig
from aion.storage.run_store import RunStore


def _make_scenario() -> Scenario:
    return Scenario(id="scen-1", suite_id="suite-1", input="Say hello.")


def _make_executor(tmp_path: Path) -> ExecutorAgent:
    config = OpenAIConfig(model_id="gpt-4o")
    store = RunStore(db_path=tmp_path / "test.db")
    return ExecutorAgent(model_config=config, run_store=store)


@dataclass
class _FakeMetrics:
    input_tokens: int = 10
    output_tokens: int = 20


@dataclass
class _FakeRunOutput:
    content: str = "Hello!"
    metrics: Any = field(default_factory=_FakeMetrics)


class TestExecutorAgent:
    def test_run_returns_complete_on_success(self, tmp_path: Path) -> None:
        executor = _make_executor(tmp_path)
        scenario = _make_scenario()

        with patch("aion.executor.agent.Agent") as MockAgent:
            instance = MockAgent.return_value
            instance.run.return_value = _FakeRunOutput()
            result = executor.run(scenario)

        assert result.status == RunStatus.COMPLETE
        assert result.observation is not None
        assert result.observation.raw_response == "Hello!"
        assert result.observation.error is None

    def test_run_returns_failed_on_exception(self, tmp_path: Path) -> None:
        executor = _make_executor(tmp_path)
        scenario = _make_scenario()

        with patch("aion.executor.agent.Agent") as MockAgent:
            instance = MockAgent.return_value
            instance.run.side_effect = RuntimeError("connection refused")
            result = executor.run(scenario)

        assert result.status == RunStatus.FAILED
        assert result.observation is not None
        assert result.observation.error == "connection refused"
        assert result.observation.raw_response == ""

    def test_run_persists_twice(self, tmp_path: Path) -> None:
        store = RunStore(db_path=tmp_path / "test.db")
        executor = ExecutorAgent(model_config=OpenAIConfig(model_id="gpt-4o"), run_store=store)
        scenario = _make_scenario()

        save_calls: list[str] = []
        original_save = store.save

        def tracking_save(run: Any) -> None:
            save_calls.append(run.status.value)
            original_save(run)

        store.save = tracking_save  # type: ignore[method-assign]

        with patch("aion.executor.agent.Agent") as MockAgent:
            instance = MockAgent.return_value
            instance.run.return_value = _FakeRunOutput()
            executor.run(scenario)

        assert save_calls == ["running", "complete"]

    def test_run_assigns_unique_session_ids(self, tmp_path: Path) -> None:
        executor = _make_executor(tmp_path)
        scenario = _make_scenario()

        with patch("aion.executor.agent.Agent") as MockAgent:
            instance = MockAgent.return_value
            instance.run.return_value = _FakeRunOutput()
            run1 = executor.run(scenario)
            run2 = executor.run(scenario)

        assert run1.session_id != run2.session_id

    def test_run_populates_wall_time(self, tmp_path: Path) -> None:
        executor = _make_executor(tmp_path)

        with patch("aion.executor.agent.Agent") as MockAgent:
            instance = MockAgent.return_value
            instance.run.return_value = _FakeRunOutput()
            result = executor.run(_make_scenario())

        assert result.observation is not None
        assert result.observation.wall_time_ms >= 0.0

    def test_run_sets_started_and_finished_at(self, tmp_path: Path) -> None:
        executor = _make_executor(tmp_path)

        with patch("aion.executor.agent.Agent") as MockAgent:
            instance = MockAgent.return_value
            instance.run.return_value = _FakeRunOutput()
            result = executor.run(_make_scenario())

        assert result.started_at is not None
        assert result.finished_at is not None

    def test_run_populates_token_counts(self, tmp_path: Path) -> None:
        executor = _make_executor(tmp_path)

        with patch("aion.executor.agent.Agent") as MockAgent:
            instance = MockAgent.return_value
            instance.run.return_value = _FakeRunOutput(content="ok", metrics=_FakeMetrics(10, 20))
            result = executor.run(_make_scenario())

        assert result.observation is not None
        assert result.observation.input_tokens == 10
        assert result.observation.output_tokens == 20
