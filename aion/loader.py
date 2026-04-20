"""Abstract loading interface for Suite definitions."""

from __future__ import annotations

from typing import Protocol

from aion.domain.models import Suite


class SuiteLoader(Protocol):
    """Contract for objects that load a Suite from an external source.

    Concrete implementations (YAML, TOML, in-memory) satisfy this protocol
    without inheriting from it — structural subtyping is intentional.
    """

    def load(self, source: str) -> Suite:
        """Load and return a Suite from the given source identifier.

        Args:
            source: An opaque identifier for the suite source — typically a
                file path, but the protocol does not constrain the format.

        Returns:
            A fully-constructed and validated ``Suite``.

        Raises:
            ValueError: If the source cannot be parsed as a valid ``Suite``.
        """
        ...
