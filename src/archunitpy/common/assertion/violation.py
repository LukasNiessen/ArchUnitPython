"""Base violation types for architecture rule checks."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class Violation:
    """Base class for all architecture violations."""

    pass


@dataclass
class EmptyTestViolation(Violation):
    """Violation raised when no files match the specified filter patterns."""

    filters: list[Any]
    message: str
    is_negated: bool = False
