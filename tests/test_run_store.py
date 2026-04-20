"""Tests for aion.storage.run_store."""

from datetime import UTC, datetime
from pathlib import Path

from aion.domain.models import Observation, Run, RunStatus
from aion.storage.run_store import RunStore


def _make_run(
    run_id: str = "run-1",
    scenario_id: str = "scen-1",
    started_at: datetime | None = None,
) -> Run:
    return Run(
        id=run_id,
        scenario_id=scenario_id,
        suite_id="suite-1",
        session_id="sess-1",
        model_id="gpt-4o",
        provider="openai",
        status=RunStatus.PENDING,
        started_at=started_at or datetime.now(UTC),
    )


class TestRunStore:
    def test_save_and_get_roundtrip(self, tmp_path: Path) -> None:
        store = RunStore(db_path=tmp_path / "test.db")
        run = _make_run()
        store.save(run)
        retrieved = store.get(run.id)
        assert retrieved == run

    def test_get_missing_returns_none(self, tmp_path: Path) -> None:
        store = RunStore(db_path=tmp_path / "test.db")
        assert store.get("nonexistent-id") is None

    def test_save_upserts(self, tmp_path: Path) -> None:
        store = RunStore(db_path=tmp_path / "test.db")
        run = _make_run()
        store.save(run)

        obs = Observation(raw_response="done", wall_time_ms=100.0)
        updated = run.model_copy(
            update={
                "status": RunStatus.COMPLETE,
                "observation": obs,
                "finished_at": datetime.now(UTC),
            }
        )
        store.save(updated)

        retrieved = store.get(run.id)
        assert retrieved is not None
        assert retrieved.status == RunStatus.COMPLETE
        assert retrieved.observation is not None

    def test_list_by_scenario_returns_newest_first(self, tmp_path: Path) -> None:
        store = RunStore(db_path=tmp_path / "test.db")
        older = _make_run("run-old", started_at=datetime(2024, 1, 1, tzinfo=UTC))
        newer = _make_run("run-new", started_at=datetime(2024, 6, 1, tzinfo=UTC))
        store.save(older)
        store.save(newer)

        results = store.list_by_scenario("scen-1")
        assert [r.id for r in results] == ["run-new", "run-old"]

    def test_list_by_scenario_empty(self, tmp_path: Path) -> None:
        store = RunStore(db_path=tmp_path / "test.db")
        assert store.list_by_scenario("nonexistent") == []

    def test_separate_db_files_are_independent(self, tmp_path: Path) -> None:
        store_a = RunStore(db_path=tmp_path / "a.db")
        store_b = RunStore(db_path=tmp_path / "b.db")
        run = _make_run()
        store_a.save(run)
        assert store_b.get(run.id) is None

    def test_list_by_suite_returns_runs_for_suite(self, tmp_path: Path) -> None:
        store = RunStore(db_path=tmp_path / "test.db")
        run_a = Run(
            id="r1",
            scenario_id="s1",
            suite_id="suite-A",
            session_id="sess",
            model_id="gpt-4o",
            provider="openai",
            started_at=datetime(2024, 1, 1, tzinfo=UTC),
        )
        run_b = Run(
            id="r2",
            scenario_id="s2",
            suite_id="suite-A",
            session_id="sess",
            model_id="gpt-4o",
            provider="openai",
            started_at=datetime(2024, 6, 1, tzinfo=UTC),
        )
        run_other = Run(
            id="r3",
            scenario_id="s3",
            suite_id="suite-B",
            session_id="sess",
            model_id="gpt-4o",
            provider="openai",
            started_at=datetime(2024, 3, 1, tzinfo=UTC),
        )
        store.save(run_a)
        store.save(run_b)
        store.save(run_other)

        results = store.list_by_suite("suite-A")
        assert [r.id for r in results] == ["r2", "r1"]

    def test_list_by_suite_empty(self, tmp_path: Path) -> None:
        store = RunStore(db_path=tmp_path / "test.db")
        assert store.list_by_suite("nonexistent") == []
