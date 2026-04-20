"""Top-level runtime configuration for an Aion evaluation run."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from aion.providers.factory import ModelConfig


class AionConfig(BaseModel):
    """Runtime configuration for a single Aion evaluation session.

    Args:
        llm: Provider and model configuration for the executor agent.
        storage_path: Directory where the SQLite run database is written.
            Defaults to ``runs/`` relative to the working directory.
    """

    llm: ModelConfig
    storage_path: Path = Field(default=Path("runs"))
