"""Tests for aion.providers.factory."""

import pytest
from agno.models.aws import AwsBedrock
from agno.models.openai import OpenAIChat

from aion.providers.factory import BedrockConfig, OpenAIConfig, build_model, provider_name


class TestBuildModel:
    def test_bedrock_returns_aws_bedrock(self) -> None:
        config = BedrockConfig(model_id="anthropic.claude-3-5-sonnet-20241022-v2:0")
        model = build_model(config)
        assert isinstance(model, AwsBedrock)

    def test_bedrock_model_id(self) -> None:
        config = BedrockConfig(model_id="amazon.nova-pro-v1:0", region="eu-west-1")
        model = build_model(config)
        assert isinstance(model, AwsBedrock)
        assert model.id == "amazon.nova-pro-v1:0"

    def test_openai_returns_openai_chat(self) -> None:
        config = OpenAIConfig(model_id="gpt-4o")
        model = build_model(config)
        assert isinstance(model, OpenAIChat)

    def test_openai_model_id(self) -> None:
        config = OpenAIConfig(model_id="gpt-4o-mini")
        model = build_model(config)
        assert model.id == "gpt-4o-mini"

    def test_openai_base_url_passthrough(self) -> None:
        config = OpenAIConfig(model_id="my-model", base_url="http://localhost:11434/v1")
        model = build_model(config)
        assert isinstance(model, OpenAIChat)
        assert str(model.base_url) == "http://localhost:11434/v1"

    def test_unknown_config_raises_type_error(self) -> None:
        with pytest.raises(TypeError, match="Unknown model config type"):
            build_model("not-a-config")  # type: ignore[arg-type]


class TestProviderName:
    def test_bedrock(self) -> None:
        assert provider_name(BedrockConfig(model_id="x")) == "bedrock"

    def test_openai(self) -> None:
        assert provider_name(OpenAIConfig(model_id="gpt-4o")) == "openai"

    def test_unknown_raises_type_error(self) -> None:
        with pytest.raises(TypeError):
            provider_name(object())  # type: ignore[arg-type]
