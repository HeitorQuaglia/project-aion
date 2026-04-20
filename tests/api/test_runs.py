"""Tests for /suites/{suite_id}/runs and /runs endpoints."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from aion.api.app import create_app
from aion.api.settings import ApiSettings


@dataclass
class _FakeMetrics:
    input_tokens: int = 5
    output_tokens: int = 10


@dataclass
class _FakeRunOutput:
    content: str = "ok"
    metrics: Any = field(default_factory=_FakeMetrics)


_SUITE_WITH_SCENARIO = {
    "id": "suite-1",
    "name": "Test Suite",
    "scenarios": [{"id": "s1", "suite_id": "suite-1", "input": "hello", "probes": [], "tags": {}}],
}

_EMPTY_SUITE = {"id": "empty-suite", "name": "Empty"}


@pytest.fixture
def client_with_suite(tmp_path: Path) -> TestClient:
    settings = ApiSettings(llm_provider="openai", llm_model_id="gpt-4o", storage_path=tmp_path)
    app = create_app(settings)
    client = TestClient(app)
    client.post("/suites", json=_SUITE_WITH_SCENARIO)
    return client


@pytest.fixture
def client_empty_suite(tmp_path: Path) -> TestClient:
    settings = ApiSettings(llm_provider="openai", llm_model_id="gpt-4o", storage_path=tmp_path)
    app = create_app(settings)
    client = TestClient(app)
    client.post("/suites", json=_EMPTY_SUITE)
    return client


class TestTriggerRun:
    def test_returns_202(self, client_with_suite: TestClient) -> None:
        with patch("aion.executor.agent.Agent") as MockAgent:
            MockAgent.return_value.run.return_value = _FakeRunOutput()
            response = client_with_suite.post("/suites/suite-1/runs")
        assert response.status_code == 202

    def test_response_contains_session_and_count(self, client_with_suite: TestClient) -> None:
        with patch("aion.executor.agent.Agent") as MockAgent:
            MockAgent.return_value.run.return_value = _FakeRunOutput()
            response = client_with_suite.post("/suites/suite-1/runs")
        data = response.json()
        assert data["suite_id"] == "suite-1"
        assert data["scenario_count"] == 1
        assert "session_id" in data

    def test_unknown_suite_returns_404(self, client_with_suite: TestClient) -> None:
        response = client_with_suite.post("/suites/nonexistent/runs")
        assert response.status_code == 404

    def test_empty_suite_returns_422(self, client_empty_suite: TestClient) -> None:
        response = client_empty_suite.post("/suites/empty-suite/runs")
        assert response.status_code == 422


class TestGetRun:
    def test_returns_run_after_execution(self, client_with_suite: TestClient) -> None:
        with patch("aion.executor.agent.Agent") as MockAgent:
            MockAgent.return_value.run.return_value = _FakeRunOutput()
            client_with_suite.post("/suites/suite-1/runs")

        # Retrieve run ids via suite query
        runs = client_with_suite.get("/runs?suite_id=suite-1").json()
        assert len(runs) >= 1
        run_id = runs[0]["id"]

        response = client_with_suite.get(f"/runs/{run_id}")
        assert response.status_code == 200
        assert response.json()["id"] == run_id

    def test_missing_run_returns_404(self, client_with_suite: TestClient) -> None:
        response = client_with_suite.get("/runs/nonexistent-id")
        assert response.status_code == 404


class TestListRuns:
    def test_query_by_suite_id(self, client_with_suite: TestClient) -> None:
        with patch("aion.executor.agent.Agent") as MockAgent:
            MockAgent.return_value.run.return_value = _FakeRunOutput()
            client_with_suite.post("/suites/suite-1/runs")

        response = client_with_suite.get("/runs?suite_id=suite-1")
        assert response.status_code == 200
        runs = response.json()
        assert len(runs) == 1
        assert runs[0]["suite_id"] == "suite-1"

    def test_query_by_scenario_id(self, client_with_suite: TestClient) -> None:
        with patch("aion.executor.agent.Agent") as MockAgent:
            MockAgent.return_value.run.return_value = _FakeRunOutput()
            client_with_suite.post("/suites/suite-1/runs")

        response = client_with_suite.get("/runs?scenario_id=s1")
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_no_query_params_returns_422(self, client_with_suite: TestClient) -> None:
        response = client_with_suite.get("/runs")
        assert response.status_code == 422
