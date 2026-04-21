"""Tests for aion.runner."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from aion.config import AionConfig
from aion.domain.models import RunStatus, Scenario, Suite
from aion.providers.factory import OpenAIConfig
from aion.runner import Runner
from aion.storage.run_store import RunStore


@dataclass
class _FakeMetrics:
    input_tokens: int = 5
    output_tokens: int = 10


@dataclass
class _FakeRunOutput:
    content: str = "ok"
    metrics: Any = field(default_factory=_FakeMetrics)


def _make_config(tmp_path: Path) -> AionConfig:
    return AionConfig(llm=OpenAIConfig(model_id="gpt-4o"), storage_path=tmp_path)


def _make_suite(*inputs: str) -> Suite:
    scenarios = [
        Scenario(id=f"s{i}", suite_id="test-suite", input=inp) for i, inp in enumerate(inputs, 1)
    ]
    return Suite(id="test-suite", name="Test Suite", scenarios=scenarios)


@pytest.fixture
def config(tmp_path: Path) -> AionConfig:
    return _make_config(tmp_path)


class TestRunner:
    def test_run_suite_returns_one_run_per_scenario(self, config: AionConfig) -> None:
        suite = _make_suite("hello", "goodbye")
        runner = Runner(config)

        with patch("aion.executor.agent.Agent") as MockAgent:
            MockAgent.return_value.run.return_value = _FakeRunOutput()
            runs = runner.run_suite(suite)

        assert len(runs) == 2

    def test_run_suite_order_matches_scenarios(self, config: AionConfig) -> None:
        suite = _make_suite("first", "second")
        runner = Runner(config)

        with patch("aion.executor.agent.Agent") as MockAgent:
            MockAgent.return_value.run.return_value = _FakeRunOutput()
            runs = runner.run_suite(suite)

        assert runs[0].scenario_id == "s1"
        assert runs[1].scenario_id == "s2"

    def test_run_suite_continues_after_failed_scenario(self, config: AionConfig) -> None:
        suite = _make_suite("fail", "ok")
        runner = Runner(config)

        responses = [RuntimeError("boom"), _FakeRunOutput()]
        with patch("aion.executor.agent.Agent") as MockAgent:
            MockAgent.return_value.run.side_effect = responses
            runs = runner.run_suite(suite)

        assert runs[0].status == RunStatus.FAILED
        assert runs[1].status == RunStatus.COMPLETE

    def test_run_suite_empty_suite_returns_empty_list(self, config: AionConfig) -> None:
        suite = Suite(id="empty", name="Empty")
        runner = Runner(config)

        with patch("aion.executor.agent.Agent"):
            runs = runner.run_suite(suite)

        assert runs == []

    def test_run_suite_creates_db_at_storage_path(self, tmp_path: Path) -> None:
        config = _make_config(tmp_path)
        suite = _make_suite("ping")
        runner = Runner(config)

        with patch("aion.executor.agent.Agent") as MockAgent:
            MockAgent.return_value.run.return_value = _FakeRunOutput()
            runner.run_suite(suite)

        assert (tmp_path / "aion.db").exists()

    def test_run_suite_persists_runs(self, tmp_path: Path) -> None:
        config = _make_config(tmp_path)
        suite = _make_suite("ping")
        runner = Runner(config)

        with patch("aion.executor.agent.Agent") as MockAgent:
            MockAgent.return_value.run.return_value = _FakeRunOutput()
            runs = runner.run_suite(suite)

        store = RunStore(db_path=tmp_path / "aion.db")
        persisted = store.get(runs[0].id)
        assert persisted is not None
        assert persisted.id == runs[0].id
