"""Shared fixtures for API tests."""

from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from aion.api.app import create_app
from aion.api.settings import ApiSettings


@pytest.fixture
def client(tmp_path: Path) -> Generator[TestClient]:
    settings = ApiSettings(
        llm_provider="openai",
        llm_model_id="gpt-4o",
        storage_path=tmp_path,
    )
    app = create_app(settings)
    with TestClient(app) as c:
        yield c
