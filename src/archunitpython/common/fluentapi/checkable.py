"""Checkable protocol and CheckOptions for architecture rule execution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, TypeVar

from archunitpython.common.assertion.violation import Violation
from archunitpython.common.logging.types import LoggingOptions


@dataclass(frozen=True)
class CheckOptions:
    """Options for controlling rule check execution."""

    allow_empty_tests: bool = False
    logging: LoggingOptions | None = None
    clear_cache: bool = False
    ignore_type_checking_imports: bool = False


T = TypeVar("T", bound="RuleRationaleMixin")


class RuleRationaleMixin:
    """Mixin for checkable rules that can carry a human-readable rationale."""

    _because_reason: str | None = None

    def because(self: T, reason: str) -> T:
        """Attach a rationale explaining why the rule exists."""
        reason = reason.strip()
        if not reason:
            raise ValueError("Rule rationale must not be empty.")
        self._because_reason = reason
        return self

    @property
    def because_reason(self) -> str | None:
        """Return the rationale attached with because(), if any."""
        return self._because_reason


class Checkable(Protocol):
    """Protocol for any architecture rule that can be checked.

    All fluent API chains ultimately produce a Checkable whose check()
    method executes the rule and returns a list of violations (empty = pass).
    """

    def check(self, options: CheckOptions | None = None) -> list[Violation]: ...
