"""SQLite-backed persistence for Aion Run records."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from aion.domain.models import Run

_DEFAULT_RUNS_DIR = Path("runs")

_DDL = """
CREATE TABLE IF NOT EXISTS aion_runs (
    id          TEXT PRIMARY KEY,
    scenario_id TEXT NOT NULL,
    suite_id    TEXT NOT NULL,
    session_id  TEXT NOT NULL,
    status      TEXT NOT NULL,
    started_at  TEXT,
    finished_at TEXT,
    model_id    TEXT NOT NULL,
    provider    TEXT NOT NULL,
    payload     TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_runs_scenario ON aion_runs (scenario_id);
CREATE INDEX IF NOT EXISTS idx_runs_suite ON aion_runs (suite_id);
"""


class RunStore:
    """Persists and retrieves Run records in a local SQLite database.

    Each ``RunStore`` instance manages a single ``.db`` file. The file is
    created automatically; the parent directory must already exist (or
    default to ``runs/`` which is created on first use).

    Args:
        db_path: Explicit path to the ``.db`` file. Defaults to
            ``runs/aion.db`` relative to the working directory.
    """

    def __init__(self, db_path: Path | None = None) -> None:
        """Initialise the store and ensure the schema is present."""
        if db_path is None:
            _DEFAULT_RUNS_DIR.mkdir(exist_ok=True)
            db_path = _DEFAULT_RUNS_DIR / "aion.db"

        self._db_path = db_path
        with sqlite3.connect(str(self._db_path)) as conn:
            conn.executescript(_DDL)

    def save(self, run: Run) -> None:
        """Upsert a Run record.

        Args:
            run: The run to persist or update.
        """
        payload = run.model_dump_json()
        sql = """
        INSERT INTO aion_runs
            (id, scenario_id, suite_id, session_id, status,
             started_at, finished_at, model_id, provider, payload)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            status      = excluded.status,
            started_at  = excluded.started_at,
            finished_at = excluded.finished_at,
            payload     = excluded.payload
        """
        with sqlite3.connect(str(self._db_path)) as conn:
            conn.execute(
                sql,
                (
                    run.id,
                    run.scenario_id,
                    run.suite_id,
                    run.session_id,
                    run.status.value,
                    run.started_at.isoformat() if run.started_at else None,
                    run.finished_at.isoformat() if run.finished_at else None,
                    run.model_id,
                    run.provider,
                    payload,
                ),
            )

    def get(self, run_id: str) -> Run | None:
        """Retrieve a Run by its identifier.

        Args:
            run_id: The UUID of the run.

        Returns:
            The ``Run`` if found, ``None`` otherwise.
        """
        sql = "SELECT payload FROM aion_runs WHERE id = ?"
        with sqlite3.connect(str(self._db_path)) as conn:
            row = conn.execute(sql, (run_id,)).fetchone()
        return Run.model_validate_json(row[0]) if row else None

    def list_by_scenario(self, scenario_id: str) -> list[Run]:
        """Return all runs for a scenario, newest first.

        Args:
            scenario_id: The scenario to filter on.

        Returns:
            List of ``Run`` objects ordered by ``started_at`` descending.
        """
        sql = """
        SELECT payload FROM aion_runs
        WHERE scenario_id = ?
        ORDER BY started_at DESC
        """
        with sqlite3.connect(str(self._db_path)) as conn:
            rows = conn.execute(sql, (scenario_id,)).fetchall()
        return [Run.model_validate_json(row[0]) for row in rows]

    def list_by_suite(self, suite_id: str) -> list[Run]:
        """Return all runs for a suite, newest first.

        Args:
            suite_id: The suite to filter on.

        Returns:
            List of ``Run`` objects ordered by ``started_at`` descending.
        """
        sql = """
        SELECT payload FROM aion_runs
        WHERE suite_id = ?
        ORDER BY started_at DESC
        """
        with sqlite3.connect(str(self._db_path)) as conn:
            rows = conn.execute(sql, (suite_id,)).fetchall()
        return [Run.model_validate_json(row[0]) for row in rows]
