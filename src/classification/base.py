"""Classifier contract.

Two implementations live alongside: `ClaudeClassifier` for production and
`HeuristicClassifier` for local dev / tests. Both accept the same input
(raw HTML) and return the same `FormType`. The pipeline depends on this
abstract class, not either concrete one.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import FormType


class FormClassifier(ABC):
    @abstractmethod
    def classify(self, html: str, *, url: str) -> FormType:
        """Given the rendered HTML of a page, return the dominant form type."""
