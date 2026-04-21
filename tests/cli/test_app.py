"""Tests for aion.cli.app."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from unittest.mock import patch

from typer.testing import CliRunner

from aion.cli.app import app
from aion.domain.models import Observation, Run, RunStatus

runner = CliRunner()

_RUN_CONFIG_YAML = """\
executor:
  type: openai
  model_id: gpt-4o

suite:
  id: my-suite
  name: My Suite
  scenarios:
    - id: sc-1
      suite_id: my-suite
      input: Hello
"""


@dataclass
class _FakeMetrics:
    input_tokens: int = 5
    output_tokens: int = 10


@dataclass
class _FakeRunOutput:
    content: str = "hi"
    metrics: Any = field(default_factory=_FakeMetrics)


def _make_run(scenario_id: str, status: RunStatus = RunStatus.COMPLETE) -> Run:
    return Run(
        id="run-1",
        scenario_id=scenario_id,
        suite_id="my-suite",
        session_id="sess-1",
        status=status,
        model_id="gpt-4o",
        provider="openai",
        observation=Observation(raw_response="ok", wall_time_ms=42.0),
    )


def _write_config(tmp_path: Path, content: str = _RUN_CONFIG_YAML) -> Path:
    p = tmp_path / "aion.yaml"
    p.write_text(content)
    return p


class TestRunCommand:
    def test_missing_config_file_exits_1(self, tmp_path: Path) -> None:
        result = runner.invoke(app, [str(tmp_path / "missing.yaml")])
        assert result.exit_code == 1
        assert "not found" in result.output

    def test_all_pass_exits_0(self, tmp_path: Path) -> None:
        config_path = _write_config(tmp_path)
        fake_runs = [_make_run("sc-1", RunStatus.COMPLETE)]
        with (
            patch("aion.cli.app.Runner") as MockRunner,
            patch("aion.executor.agent.Agent"),
        ):
            MockRunner.return_value.run_suite.return_value = fake_runs
            result = runner.invoke(
                app, [str(config_path), "--storage-path", str(tmp_path)]
            )
        assert result.exit_code == 0
        assert "[PASS]" in result.output
        assert "1 passed, 0 failed" in result.output

    def test_any_fail_exits_1(self, tmp_path: Path) -> None:
        config_path = _write_config(tmp_path)
        fake_runs = [_make_run("sc-1", RunStatus.FAILED)]
        with patch("aion.cli.app.Runner") as MockRunner:
            MockRunner.return_value.run_suite.return_value = fake_runs
            result = runner.invoke(
                app, [str(config_path), "--storage-path", str(tmp_path)]
            )
        assert result.exit_code == 1
        assert "[FAIL]" in result.output
        assert "0 passed, 1 failed" in result.output

    def test_json_output_format(self, tmp_path: Path) -> None:
        config_path = _write_config(tmp_path)
        fake_runs = [_make_run("sc-1", RunStatus.COMPLETE)]
        with patch("aion.cli.app.Runner") as MockRunner:
            MockRunner.return_value.run_suite.return_value = fake_runs
            result = runner.invoke(
                app,
                [str(config_path), "--output", "json", "--storage-path", str(tmp_path)],
            )
        assert result.exit_code == 0
        lines = [ln for ln in result.output.strip().splitlines() if ln]
        import json

        run_data = json.loads(lines[0])
        assert run_data["scenario_id"] == "sc-1"
        summary = json.loads(lines[-1])
        assert summary["passed"] == 1
        assert summary["failed"] == 0

    def test_invalid_yaml_exits_1(self, tmp_path: Path) -> None:
        config_path = tmp_path / "bad.yaml"
        config_path.write_text("not: a: valid: config")
        result = runner.invoke(app, [str(config_path)])
        assert result.exit_code == 1

    def test_storage_path_override(self, tmp_path: Path) -> None:
        config_path = _write_config(tmp_path)
        custom_storage = tmp_path / "custom_db"
        fake_runs = [_make_run("sc-1")]
        with patch("aion.cli.app.Runner") as MockRunner:
            MockRunner.return_value.run_suite.return_value = fake_runs
            runner.invoke(
                app, [str(config_path), "--storage-path", str(custom_storage)]
            )
        call_config = MockRunner.call_args[0][0]
        assert call_config.storage_path == custom_storage
