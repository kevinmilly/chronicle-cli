"""Abstract sync backend interface."""

from __future__ import annotations

import abc


class SyncBackend(abc.ABC):
    """Pluggable backend for reading/writing encrypted sync data."""

    @abc.abstractmethod
    def read(self) -> str:
        """Fetch the full remote content. Returns empty string if nothing exists."""
        ...

    @abc.abstractmethod
    def write(self, content: str) -> None:
        """Overwrite the entire remote content."""
        ...

    @abc.abstractmethod
    def append(self, line: str) -> None:
        """Append a single line to the remote content."""
        ...
