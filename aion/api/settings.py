"""Environment-based configuration for the Aion REST API."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from aion.config import AionConfig
from aion.providers.factory import BedrockConfig, OpenAIConfig


class ApiSettings(BaseSettings):
    """Runtime settings read from environment variables (prefix: ``AION_``).

    Example env vars::

        AION_LLM_PROVIDER=openai
        AION_LLM_MODEL_ID=gpt-4o
        AION_STORAGE_PATH=/data/runs
    """

    model_config = SettingsConfigDict(env_prefix="AION_")

    llm_provider: str = "openai"
    llm_model_id: str = "gpt-4o"
    llm_openai_api_key: str | None = None
    llm_openai_base_url: str | None = None
    llm_bedrock_region: str = "us-east-1"
    storage_path: Path = Path("runs")

    def to_aion_config(self) -> AionConfig:
        """Build an ``AionConfig`` from the current settings.

        Returns:
            An ``AionConfig`` instance wired with the configured LLM provider.
        """
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
