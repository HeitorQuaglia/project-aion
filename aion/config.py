"""Top-level runtime configuration for an Aion evaluation run."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, Field, model_validator

from aion.executor.http_executor import HttpTargetConfig
from aion.providers.factory import ModelConfig


class AionConfig(BaseModel):
    """Runtime configuration for a single Aion evaluation session.

    Exactly one of ``llm`` or ``http_target`` must be provided.

    Args:
        llm: Provider and model configuration for Agno-based execution.
        http_target: HTTP endpoint configuration for HTTP-based execution.
        storage_path: Directory where the SQLite run database is written.
            Defaults to ``runs/`` relative to the working directory.
    """

    llm: Annotated[ModelConfig, Field(default=None)] = None  # type: ignore[assignment]
    http_target: HttpTargetConfig | None = None
    storage_path: Path = Field(default=Path("runs"))

    @model_validator(mode="after")
    def _require_one_executor(self) -> AionConfig:
        if self.llm is None and self.http_target is None:
            raise ValueError("Either 'llm' or 'http_target' must be set in AionConfig.")
        if self.llm is not None and self.http_target is not None:
            raise ValueError("Only one of 'llm' or 'http_target' may be set in AionConfig.")
        return self
