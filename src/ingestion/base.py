"""Abstract source — any provider that yields `Prospect` objects."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable

from ..models import Borough, Prospect


class ProspectSource(ABC):
    """Contract every prospect source implements."""

    @abstractmethod
    def fetch(
        self, vertical: str, borough: Borough, limit: int = 100
    ) -> Iterable[Prospect]:
        """Yield prospects matching the vertical + borough."""
