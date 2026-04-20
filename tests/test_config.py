"""Tests for aion.config."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from aion.config import AionConfig
from aion.providers.factory import BedrockConfig, OpenAIConfig


class TestAionConfig:
    def test_requires_llm(self) -> None:
        with pytest.raises(ValidationError):
            AionConfig()  # type: ignore[call-arg]

    def test_storage_path_defaults_to_runs(self) -> None:
        config = AionConfig(llm=OpenAIConfig(model_id="gpt-4o"))
        assert config.storage_path == Path("runs")

    def test_storage_path_accepts_custom_path(self) -> None:
        config = AionConfig(llm=OpenAIConfig(model_id="gpt-4o"), storage_path=Path("/tmp/mydir"))
        assert config.storage_path == Path("/tmp/mydir")

    def test_llm_accepts_bedrock_config(self) -> None:
        config = AionConfig(llm=BedrockConfig(model_id="anthropic.claude-3-5-sonnet-20241022-v2:0"))
        assert isinstance(config.llm, BedrockConfig)

    def test_llm_accepts_openai_config(self) -> None:
        config = AionConfig(llm=OpenAIConfig(model_id="gpt-4o"))
        assert isinstance(config.llm, OpenAIConfig)

    def test_json_roundtrip_with_bedrock(self) -> None:
        config = AionConfig(llm=BedrockConfig(model_id="x", region="eu-west-1"))
        restored = AionConfig.model_validate_json(config.model_dump_json())
        assert restored == config
        assert isinstance(restored.llm, BedrockConfig)

    def test_json_roundtrip_with_openai(self) -> None:
        config = AionConfig(llm=OpenAIConfig(model_id="gpt-4o", base_url="http://localhost/v1"))
        restored = AionConfig.model_validate_json(config.model_dump_json())
        assert restored == config
        assert isinstance(restored.llm, OpenAIConfig)
