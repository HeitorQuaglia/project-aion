"""Aion CLI — headless CI entrypoint."""

from __future__ import annotations

import json
import sys
from enum import StrEnum
from pathlib import Path
from typing import Annotated

import typer

from aion.domain.models import Run, RunStatus
from aion.runner import Runner
from aion.yaml_loader import load_run_config

app = typer.Typer(name="aion", help="Aion QA/QC control plane — CI runner.")


class OutputFormat(StrEnum):
    """Supported output formats for the run command."""

    TEXT = "text"
    JSON = "json"


def _print_run_text(run: Run) -> None:
    status_label = "PASS" if run.status == RunStatus.COMPLETE else "FAIL"
    wall_ms = run.observation.wall_time_ms if run.observation else 0.0
    typer.echo(f"[{status_label}] {run.scenario_id} — {wall_ms:.0f}ms")


def _print_run_json(run: Run) -> None:
    typer.echo(run.model_dump_json())


@app.command()
def run(
    config_file: Annotated[Path, typer.Argument(help="Path to the run config YAML file.")],
    output: Annotated[
        OutputFormat,
        typer.Option("--output", "-o", help="Output format: text or json."),
    ] = OutputFormat.TEXT,
    storage_path: Annotated[
        Path | None,
        typer.Option("--storage-path", help="Override the storage path for the SQLite DB."),
    ] = None,
) -> None:
    """Execute a suite defined in CONFIG_FILE and report results."""
    if not config_file.exists():
        typer.echo(f"Error: config file not found: {config_file}", err=True)
        raise typer.Exit(code=1)

    try:
        aion_config, suite = load_run_config(config_file)
    except ValueError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    if storage_path is not None:
        aion_config = aion_config.model_copy(update={"storage_path": storage_path})

    aion_config.storage_path.mkdir(parents=True, exist_ok=True)

    runner = Runner(aion_config)
    runs = runner.run_suite(suite)

    for r in runs:
        if output == OutputFormat.JSON:
            _print_run_json(r)
        else:
            _print_run_text(r)

    passed = sum(1 for r in runs if r.status == RunStatus.COMPLETE)
    failed = len(runs) - passed

    if output == OutputFormat.TEXT:
        typer.echo(f"\n{passed} passed, {failed} failed")

    if output == OutputFormat.JSON:
        summary = {"passed": passed, "failed": failed, "total": len(runs)}
        typer.echo(json.dumps(summary))

    sys.exit(1 if failed > 0 else 0)
