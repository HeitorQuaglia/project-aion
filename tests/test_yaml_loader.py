"""Tests for aion.yaml_loader."""

from pathlib import Path

import pytest

from aion.config import AionConfig
from aion.domain.models import Suite
from aion.executor.http_executor import HttpTargetConfig
from aion.providers.factory import BedrockConfig, OpenAIConfig
from aion.yaml_loader import load_run_config, load_suite


def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content)
    return p


MINIMAL_SUITE_YAML = """\
id: s1
name: Suite One
scenarios:
  - id: sc-1
    suite_id: s1
    input: Hello
"""

FULL_RUN_CONFIG_YAML = """\
executor:
  type: openai
  model_id: gpt-4o-mini

storage_path: /tmp/runs

suite:
  id: my-suite
  name: My Suite
  scenarios:
    - id: sc-1
      suite_id: my-suite
      input: "Tell me a joke"
      probes:
        - id: funny
          description: "Should be humorous"
          probe_type: llm_judge
"""


class TestLoadSuite:
    def test_parses_valid_suite(self, tmp_path: Path) -> None:
        path = _write(tmp_path, "suite.yaml", MINIMAL_SUITE_YAML)
        suite = load_suite(path)
        assert isinstance(suite, Suite)
        assert suite.id == "s1"
        assert len(suite.scenarios) == 1

    def test_raises_on_invalid_yaml(self, tmp_path: Path) -> None:
        path = _write(tmp_path, "bad.yaml", "key: [unclosed")
        with pytest.raises(ValueError, match="Invalid YAML"):
            load_suite(path)

    def test_raises_on_non_mapping_yaml(self, tmp_path: Path) -> None:
        path = _write(tmp_path, "bad.yaml", "- just a list\n")
        with pytest.raises(ValueError, match="must be a mapping"):
            load_suite(path)

    def test_raises_on_missing_required_field(self, tmp_path: Path) -> None:
        path = _write(tmp_path, "bad.yaml", "id: only-id\n")
        with pytest.raises(ValueError, match="Suite validation failed"):
            load_suite(path)


class TestLoadRunConfig:
    def test_parses_full_config(self, tmp_path: Path) -> None:
        path = _write(tmp_path, "aion.yaml", FULL_RUN_CONFIG_YAML)
        config, suite = load_run_config(path)
        assert isinstance(config, AionConfig)
        assert isinstance(suite, Suite)
        assert suite.id == "my-suite"
        assert len(suite.scenarios) == 1

    def test_openai_executor(self, tmp_path: Path) -> None:
        path = _write(tmp_path, "aion.yaml", FULL_RUN_CONFIG_YAML)
        config, _ = load_run_config(path)
        assert isinstance(config.llm, OpenAIConfig)
        assert config.llm.model_id == "gpt-4o-mini"

    def test_bedrock_executor(self, tmp_path: Path) -> None:
        yaml_content = """\
executor:
  type: bedrock
  model_id: anthropic.claude-3-5-sonnet-20241022-v2:0
  region: eu-west-1

suite:
  id: s1
  name: S1
  scenarios: []
"""
        path = _write(tmp_path, "aion.yaml", yaml_content)
        config, _ = load_run_config(path)
        assert isinstance(config.llm, BedrockConfig)
        assert config.llm.region == "eu-west-1"

    def test_http_executor(self, tmp_path: Path) -> None:
        yaml_content = """\
executor:
  type: http
  url: http://localhost:8080/chat
  provider_name: my-agent
  response_field: reply

suite:
  id: s1
  name: S1
  scenarios: []
"""
        path = _write(tmp_path, "aion.yaml", yaml_content)
        config, _ = load_run_config(path)
        assert isinstance(config.http_target, HttpTargetConfig)
        assert config.http_target.url == "http://localhost:8080/chat"
        assert config.http_target.response_field == "reply"

    def test_storage_path_override(self, tmp_path: Path) -> None:
        path = _write(tmp_path, "aion.yaml", FULL_RUN_CONFIG_YAML)
        config, _ = load_run_config(path)
        assert config.storage_path == Path("/tmp/runs")

    def test_default_storage_path(self, tmp_path: Path) -> None:
        yaml_content = """\
executor:
  type: openai
  model_id: gpt-4o

suite:
  id: s1
  name: S1
  scenarios: []
"""
        path = _write(tmp_path, "aion.yaml", yaml_content)
        config, _ = load_run_config(path)
        assert config.storage_path == Path("runs")

    def test_raises_on_missing_executor_key(self, tmp_path: Path) -> None:
        path = _write(tmp_path, "aion.yaml", "suite:\n  id: s1\n  name: S1\n")
        with pytest.raises(ValueError, match="'executor'"):
            load_run_config(path)

    def test_raises_on_missing_suite_key(self, tmp_path: Path) -> None:
        path = _write(tmp_path, "aion.yaml", "executor:\n  type: openai\n")
        with pytest.raises(ValueError, match="'suite'"):
            load_run_config(path)
