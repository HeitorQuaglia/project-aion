"""Tests for /suites endpoints."""

from fastapi.testclient import TestClient

_SUITE_BODY = {"id": "suite-1", "name": "My Suite"}


class TestCreateSuite:
    def test_returns_201(self, client: TestClient) -> None:
        response = client.post("/suites", json=_SUITE_BODY)
        assert response.status_code == 201

    def test_response_contains_suite_fields(self, client: TestClient) -> None:
        response = client.post("/suites", json=_SUITE_BODY)
        data = response.json()
        assert data["id"] == "suite-1"
        assert data["name"] == "My Suite"
        assert data["scenarios"] == []

    def test_duplicate_id_returns_409(self, client: TestClient) -> None:
        client.post("/suites", json=_SUITE_BODY)
        response = client.post("/suites", json=_SUITE_BODY)
        assert response.status_code == 409


class TestListSuites:
    def test_empty_list_on_fresh_app(self, client: TestClient) -> None:
        response = client.get("/suites")
        assert response.status_code == 200
        assert response.json() == []

    def test_returns_created_suites(self, client: TestClient) -> None:
        client.post("/suites", json=_SUITE_BODY)
        response = client.get("/suites")
        assert len(response.json()) == 1


class TestGetSuite:
    def test_returns_suite(self, client: TestClient) -> None:
        client.post("/suites", json=_SUITE_BODY)
        response = client.get("/suites/suite-1")
        assert response.status_code == 200
        assert response.json()["id"] == "suite-1"

    def test_missing_suite_returns_404(self, client: TestClient) -> None:
        response = client.get("/suites/nonexistent")
        assert response.status_code == 404
