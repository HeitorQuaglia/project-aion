"""Model provider factory for Agno-backed executor agents."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from agno.models.aws import AwsBedrock
from agno.models.openai import OpenAIChat

ProviderName = Literal["bedrock", "openai"]


@dataclass(frozen=True)
class BedrockConfig:
    """Configuration for an AWS Bedrock-hosted model.

    Attributes:
        model_id: Bedrock model ARN or ID (e.g. ``"anthropic.claude-3-5-sonnet-20241022-v2:0"``).
        region: AWS region where the model endpoint is available.
    """

    model_id: str
    region: str = "us-east-1"


@dataclass(frozen=True)
class OpenAIConfig:
    """Configuration for an OpenAI or OpenAI-compatible model endpoint.

    Attributes:
        model_id: Model name (e.g. ``"gpt-4o"``).
        base_url: Override the API base URL for compatible endpoints (e.g. opencode).
        api_key: Explicit API key; falls back to ``OPENAI_API_KEY`` env var if ``None``.
    """

    model_id: str
    base_url: str | None = None
    api_key: str | None = None


ModelConfig = BedrockConfig | OpenAIConfig


def build_model(config: ModelConfig) -> AwsBedrock | OpenAIChat:
    """Construct an Agno model instance from a provider config.

    Args:
        config: A ``BedrockConfig`` or ``OpenAIConfig`` value object.

    Returns:
        An Agno model object ready to be passed to ``Agent(model=...)``.

    Raises:
        TypeError: If ``config`` is not a recognised ``ModelConfig`` type.
    """
    match config:
        case BedrockConfig():
            return AwsBedrock(id=config.model_id, aws_region=config.region)
        case OpenAIConfig():
            kwargs: dict[str, Any] = {"id": config.model_id}
            if config.base_url is not None:
                kwargs["base_url"] = config.base_url
            if config.api_key is not None:
                kwargs["api_key"] = config.api_key
            return OpenAIChat(**kwargs)
        case _:
            raise TypeError(f"Unknown model config type: {type(config)!r}")


def provider_name(config: ModelConfig) -> ProviderName:
    """Return the canonical provider name for a given config.

    Args:
        config: A ``BedrockConfig`` or ``OpenAIConfig`` value object.

    Returns:
        ``"bedrock"`` or ``"openai"``.

    Raises:
        TypeError: If ``config`` is not a recognised ``ModelConfig`` type.
    """
    match config:
        case BedrockConfig():
            return "bedrock"
        case OpenAIConfig():
            return "openai"
        case _:
            raise TypeError(f"Unknown model config type: {type(config)!r}")
