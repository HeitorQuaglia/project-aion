"""Tests for aion.loader."""

from aion.domain.models import Scenario, Suite
from aion.loader import SuiteLoader


class _FakeLoader:
    def load(self, source: str) -> Suite:
        return Suite(
            id="fake",
            name="Fake Suite",
            scenarios=[Scenario(id="s1", suite_id="fake", input=source)],
        )


class TestSuiteLoader:
    def test_fake_loader_satisfies_protocol(self) -> None:
        loader: SuiteLoader = _FakeLoader()
        suite = loader.load("ping")
        assert suite.id == "fake"
        assert suite.scenarios[0].input == "ping"

    def test_fake_loader_returns_suite_type(self) -> None:
        loader: SuiteLoader = _FakeLoader()
        result = loader.load("any")
        assert isinstance(result, Suite)
