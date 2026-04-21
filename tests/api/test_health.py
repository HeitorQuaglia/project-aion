"""Tests for GET /health."""

from fastapi.testclient import TestClient


class TestHealth:
    def test_returns_200(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200

    def test_returns_ok_status(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.json() == {"status": "ok"}
