"""Tests for aion.executor.http_executor."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from aion.domain.models import RunStatus, Scenario
from aion.executor.http_executor import HttpExecutorAgent, HttpTargetConfig
from aion.storage.run_store import RunStore


def _make_scenario(**kwargs) -> Scenario:  # type: ignore[no-untyped-def]
    defaults = dict(id="scen-1", suite_id="suite-1", input="Hello agent.")
    return Scenario(**{**defaults, **kwargs})


def _make_executor(tmp_path: Path, **config_kwargs) -> HttpExecutorAgent:  # type: ignore[no-untyped-def]
    config = HttpTargetConfig(url="http://localhost:9999/chat", **config_kwargs)
    store = RunStore(db_path=tmp_path / "test.db")
    return HttpExecutorAgent(target_config=config, run_store=store)


def _mock_response(body: dict, status_code: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = body
    resp.raise_for_status = MagicMock()
    if status_code >= 400:
        resp.raise_for_status.side_effect = Exception(f"HTTP {status_code}")
    return resp


class TestHttpExecutorAgent:
    def test_run_returns_complete_on_success(self, tmp_path: Path) -> None:
        executor = _make_executor(tmp_path)

        with patch("aion.executor.http_executor.httpx.Client") as MockClient:
            MockClient.return_value.__enter__.return_value.post.return_value = _mock_response(
                {"message": "Here are some great hotels!"}
            )
            result = executor.run(_make_scenario())

        assert result.status == RunStatus.COMPLETE
        assert result.observation is not None
        assert result.observation.raw_response == "Here are some great hotels!"
        assert result.observation.error is None

    def test_run_returns_failed_on_http_error(self, tmp_path: Path) -> None:
        executor = _make_executor(tmp_path)

        with patch("aion.executor.http_executor.httpx.Client") as MockClient:
            MockClient.return_value.__enter__.return_value.post.return_value = _mock_response(
                {}, status_code=500
            )
            result = executor.run(_make_scenario())

        assert result.status == RunStatus.FAILED
        assert result.observation is not None
        assert result.observation.error is not None
        assert result.observation.raw_response == ""

    def test_run_returns_failed_on_connection_error(self, tmp_path: Path) -> None:
        executor = _make_executor(tmp_path)

        with patch("aion.executor.http_executor.httpx.Client") as MockClient:
            MockClient.return_value.__enter__.return_value.post.side_effect = ConnectionError(
                "refused"
            )
            result = executor.run(_make_scenario())

        assert result.status == RunStatus.FAILED
        assert result.observation is not None
        assert "refused" in (result.observation.error or "")

    def test_run_merges_tags_into_request_body(self, tmp_path: Path) -> None:
        executor = _make_executor(tmp_path)
        scenario = _make_scenario(
            input="Suggest hotels",
            tags={"aspect_type": "accommodation", "destination": "Paris"},
        )

        with patch("aion.executor.http_executor.httpx.Client") as MockClient:
            mock_post = MockClient.return_value.__enter__.return_value.post
            mock_post.return_value = _mock_response({"message": "ok"})
            executor.run(scenario)

        _, kwargs = mock_post.call_args
        body = kwargs["json"]
        assert body["message"] == "Suggest hotels"
        assert body["aspect_type"] == "accommodation"
        assert body["destination"] == "Paris"

    def test_run_uses_custom_response_field(self, tmp_path: Path) -> None:
        executor = _make_executor(tmp_path, response_field="output")

        with patch("aion.executor.http_executor.httpx.Client") as MockClient:
            MockClient.return_value.__enter__.return_value.post.return_value = _mock_response(
                {"output": "Custom field response"}
            )
            result = executor.run(_make_scenario())

        assert result.observation is not None
        assert result.observation.raw_response == "Custom field response"

    def test_run_sends_configured_headers(self, tmp_path: Path) -> None:
        executor = _make_executor(
            tmp_path, headers={"Authorization": "Bearer test-key"}
        )

        with patch("aion.executor.http_executor.httpx.Client") as MockClient:
            mock_post = MockClient.return_value.__enter__.return_value.post
            mock_post.return_value = _mock_response({"message": "ok"})
            executor.run(_make_scenario())

        init_kwargs = MockClient.call_args.kwargs
        assert init_kwargs["headers"] == {"Authorization": "Bearer test-key"}

    def test_run_stores_provider_name_on_run(self, tmp_path: Path) -> None:
        executor = _make_executor(tmp_path, provider_name="explorai")

        with patch("aion.executor.http_executor.httpx.Client") as MockClient:
            MockClient.return_value.__enter__.return_value.post.return_value = _mock_response(
                {"message": "ok"}
            )
            result = executor.run(_make_scenario())

        assert result.provider == "explorai"

    def test_run_persists_running_then_final(self, tmp_path: Path) -> None:
        store = RunStore(db_path=tmp_path / "test.db")
        config = HttpTargetConfig(url="http://localhost:9999/chat")
        executor = HttpExecutorAgent(target_config=config, run_store=store)

        saved_statuses: list[str] = []
        original_save = store.save

        def tracking_save(run):  # type: ignore[no-untyped-def]
            saved_statuses.append(run.status.value)
            original_save(run)

        store.save = tracking_save  # type: ignore[method-assign]

        with patch("aion.executor.http_executor.httpx.Client") as MockClient:
            MockClient.return_value.__enter__.return_value.post.return_value = _mock_response(
                {"message": "ok"}
            )
            executor.run(_make_scenario())

        assert saved_statuses == ["running", "complete"]

    def test_run_token_counts_are_none(self, tmp_path: Path) -> None:
        executor = _make_executor(tmp_path)

        with patch("aion.executor.http_executor.httpx.Client") as MockClient:
            MockClient.return_value.__enter__.return_value.post.return_value = _mock_response(
                {"message": "ok"}
            )
            result = executor.run(_make_scenario())

        assert result.observation is not None
        assert result.observation.input_tokens is None
        assert result.observation.output_tokens is None

    def test_run_populates_wall_time(self, tmp_path: Path) -> None:
        executor = _make_executor(tmp_path)

        with patch("aion.executor.http_executor.httpx.Client") as MockClient:
            MockClient.return_value.__enter__.return_value.post.return_value = _mock_response(
                {"message": "ok"}
            )
            result = executor.run(_make_scenario())

        assert result.observation is not None
        assert result.observation.wall_time_ms >= 0.0


class TestHttpTargetConfig:
    def test_defaults(self) -> None:
        config = HttpTargetConfig(url="http://example.com")
        assert config.headers == {}
        assert config.timeout_seconds == 30.0
        assert config.provider_name == "http"
        assert config.response_field == "message"

    def test_custom_values(self) -> None:
        config = HttpTargetConfig(
            url="http://example.com",
            headers={"X-Key": "val"},
            timeout_seconds=10.0,
            provider_name="my-agent",
            response_field="answer",
        )
        assert config.headers == {"X-Key": "val"}
        assert config.timeout_seconds == 10.0
        assert config.provider_name == "my-agent"
        assert config.response_field == "answer"
