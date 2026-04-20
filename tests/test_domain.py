"""Tests for aion.domain.models."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from aion.domain.models import Observation, Probe, Run, RunStatus, Scenario, Suite


def _make_run(**overrides: object) -> Run:
    defaults: dict[str, object] = {
        "id": "run-1",
        "scenario_id": "scen-1",
        "suite_id": "suite-1",
        "session_id": "sess-1",
        "model_id": "gpt-4o",
        "provider": "openai",
    }
    defaults.update(overrides)
    return Run(**defaults)  # type: ignore[arg-type]


class TestProbe:
    def test_valid_deterministic(self) -> None:
        p = Probe(id="p1", description="check X", probe_type="deterministic")
        assert p.probe_type == "deterministic"

    def test_valid_llm_judge(self) -> None:
        p = Probe(id="p2", description="check Y", probe_type="llm_judge")
        assert p.probe_type == "llm_judge"

    def test_invalid_probe_type(self) -> None:
        with pytest.raises(ValidationError):
            Probe(id="p3", description="d", probe_type="unknown")  # type: ignore[arg-type]


class TestScenario:
    def test_requires_id_and_input(self) -> None:
        with pytest.raises(ValidationError):
            Scenario(suite_id="s1", input="hello")  # type: ignore[call-arg]

    def test_defaults(self) -> None:
        s = Scenario(id="s1", suite_id="suite-1", input="ping")
        assert s.probes == []
        assert s.tags == {}

    def test_with_probes(self) -> None:
        probe = Probe(id="p1", description="d", probe_type="deterministic")
        s = Scenario(id="s1", suite_id="suite-1", input="ping", probes=[probe])
        assert len(s.probes) == 1


class TestObservation:
    def test_error_field_optional(self) -> None:
        obs = Observation(raw_response="hello", wall_time_ms=42.0)
        assert obs.error is None
        assert obs.input_tokens is None

    def test_with_error(self) -> None:
        obs = Observation(raw_response="", wall_time_ms=10.0, error="timeout")
        assert obs.error == "timeout"


class TestRun:
    def test_defaults_to_pending(self) -> None:
        run = _make_run()
        assert run.status == RunStatus.PENDING

    def test_is_immutable(self) -> None:
        run = _make_run()
        with pytest.raises(ValidationError):
            run.status = RunStatus.COMPLETE  # noqa: E501

    def test_model_copy_update(self) -> None:
        run = _make_run()
        updated = run.model_copy(update={"status": RunStatus.COMPLETE})
        assert updated.status == RunStatus.COMPLETE
        assert run.status == RunStatus.PENDING  # original unchanged

    def test_json_roundtrip(self) -> None:
        obs = Observation(raw_response="ok", wall_time_ms=55.0, input_tokens=10, output_tokens=20)
        run = _make_run(
            status=RunStatus.COMPLETE,
            observation=obs,
            started_at=datetime.now(UTC),
            finished_at=datetime.now(UTC),
        )
        restored = Run.model_validate_json(run.model_dump_json())
        assert restored == run

    def test_missing_required_fields(self) -> None:
        with pytest.raises(ValidationError):
            Run(id="r1", scenario_id="s1")  # type: ignore[call-arg]


class TestSuite:
    def test_defaults(self) -> None:
        suite = Suite(id="s1", name="My Suite")
        assert suite.scenarios == []
        assert suite.description == ""

    def test_with_scenarios(self) -> None:
        scenario = Scenario(id="sc1", suite_id="s1", input="ping")
        suite = Suite(id="s1", name="My Suite", scenarios=[scenario])
        assert len(suite.scenarios) == 1
        assert suite.scenarios[0].id == "sc1"

    def test_json_roundtrip(self) -> None:
        scenario = Scenario(id="sc1", suite_id="s1", input="ping")
        suite = Suite(id="s1", name="My Suite", description="desc", scenarios=[scenario])
        restored = Suite.model_validate_json(suite.model_dump_json())
        assert restored == suite

    def test_suite_id_not_validated_against_scenarios(self) -> None:
        scenario = Scenario(id="sc1", suite_id="other-suite", input="ping")
        suite = Suite(id="s1", name="My Suite", scenarios=[scenario])
        assert suite.scenarios[0].suite_id == "other-suite"
