"""YAML-based loaders for Suite definitions and full CLI run configurations."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from aion.config import AionConfig
from aion.domain.models import Suite
from aion.executor.http_executor import HttpTargetConfig
from aion.providers.factory import BedrockConfig, OpenAIConfig


def load_suite(path: Path) -> Suite:
    """Load a Suite from a YAML file whose root matches the Suite schema.

    Args:
        path: Path to a YAML file containing a suite definition.

    Returns:
        A validated ``Suite`` instance.

    Raises:
        ValueError: If the file cannot be parsed or fails Suite validation.
    """
    try:
        raw = yaml.safe_load(path.read_text())
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ValueError(f"Suite YAML must be a mapping, got {type(raw).__name__}")
    try:
        return Suite.model_validate(raw)
    except Exception as exc:
        raise ValueError(f"Suite validation failed for {path}: {exc}") from exc


def load_run_config(path: Path) -> tuple[AionConfig, Suite]:
    """Load a full run configuration from a YAML file.

    The YAML must contain an ``executor`` block and a ``suite`` block.
    An optional ``storage_path`` key overrides the default.

    Args:
        path: Path to the run config YAML file.

    Returns:
        A tuple of ``(AionConfig, Suite)``.

    Raises:
        ValueError: If the file is missing required keys or fails validation.
    """
    try:
        raw = yaml.safe_load(path.read_text())
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ValueError(f"Run config YAML must be a mapping, got {type(raw).__name__}")

    if "executor" not in raw:
        raise ValueError("Run config YAML must contain an 'executor' key")
    if "suite" not in raw:
        raise ValueError("Run config YAML must contain a 'suite' key")

    storage_path = Path(raw.get("storage_path", "runs"))
    aion_config = _build_aion_config(raw["executor"], storage_path)

    suite_data: dict[str, Any] = raw["suite"]
    try:
        suite = Suite.model_validate(suite_data)
    except Exception as exc:
        raise ValueError(f"Suite validation failed: {exc}") from exc

    return aion_config, suite


def _build_aion_config(executor: dict[str, Any], storage_path: Path) -> AionConfig:
    executor_type = executor.get("type", "openai")

    if executor_type == "http":
        headers: dict[str, str] = executor.get("headers", {})
        http_target = HttpTargetConfig(
            url=executor["url"],
            headers=headers,
            provider_name=executor.get("provider_name", "http"),
            response_field=executor.get("response_field", "message"),
            timeout_seconds=float(executor.get("timeout_seconds", 30.0)),
        )
        return AionConfig(http_target=http_target, storage_path=storage_path)

    llm: BedrockConfig | OpenAIConfig
    if executor_type == "bedrock":
        llm = BedrockConfig(
            model_id=executor["model_id"],
            region=executor.get("region", "us-east-1"),
        )
    else:
        llm = OpenAIConfig(
            model_id=executor.get("model_id", "gpt-4o"),
            base_url=executor.get("base_url") or None,
            api_key=executor.get("api_key") or None,
        )

    return AionConfig(llm=llm, storage_path=storage_path)
