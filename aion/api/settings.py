"""Environment-based configuration for the Aion REST API."""

import json
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from aion.config import AionConfig
from aion.executor.http_executor import HttpTargetConfig
from aion.providers.factory import BedrockConfig, OpenAIConfig


class ApiSettings(BaseSettings):
    """Runtime settings read from environment variables (prefix: ``AION_``).

    Example env vars for Agno-based execution::

        AION_EXECUTOR_TYPE=agno
        AION_LLM_PROVIDER=openai
        AION_LLM_MODEL_ID=gpt-4o
        AION_STORAGE_PATH=/data/runs

    Example env vars for HTTP-based execution::

        AION_EXECUTOR_TYPE=http
        AION_HTTP_TARGET_URL=http://localhost:8001/api/v1/aion/chat
        AION_HTTP_TARGET_HEADERS={"Authorization": "Bearer my-key"}
        AION_HTTP_TARGET_PROVIDER_NAME=my-agent
        AION_HTTP_TARGET_RESPONSE_FIELD=message
    """

    model_config = SettingsConfigDict(env_prefix="AION_")

    executor_type: str = "agno"

    # Agno executor settings
    llm_provider: str = "openai"
    llm_model_id: str = "gpt-4o"
    llm_openai_api_key: str | None = None
    llm_openai_base_url: str | None = None
    llm_bedrock_region: str = "us-east-1"

    # HTTP executor settings
    http_target_url: str = ""
    http_target_headers: str = "{}"
    http_target_provider_name: str = "http"
    http_target_response_field: str = "message"
    http_target_timeout_seconds: float = 30.0

    storage_path: Path = Path("runs")

    def to_aion_config(self) -> AionConfig:
        """Build an ``AionConfig`` from the current settings.

        Returns:
            An ``AionConfig`` wired with either an Agno LLM or an HTTP target.
        """
        if self.executor_type == "http":
            headers: dict[str, str] = json.loads(self.http_target_headers)
            return AionConfig(
                http_target=HttpTargetConfig(
                    url=self.http_target_url,
                    headers=headers,
                    provider_name=self.http_target_provider_name,
                    response_field=self.http_target_response_field,
                    timeout_seconds=self.http_target_timeout_seconds,
                ),
                storage_path=self.storage_path,
            )

        match self.llm_provider:
            case "bedrock":
                llm: BedrockConfig | OpenAIConfig = BedrockConfig(
                    model_id=self.llm_model_id,
                    region=self.llm_bedrock_region,
                )
            case _:
                llm = OpenAIConfig(
                    model_id=self.llm_model_id,
                    base_url=self.llm_openai_base_url,
                    api_key=self.llm_openai_api_key,
                )
        return AionConfig(llm=llm, storage_path=self.storage_path)
