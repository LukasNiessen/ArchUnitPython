"""Checkable protocol and CheckOptions for architecture rule execution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from archunitpy.common.assertion.violation import Violation
from archunitpy.common.logging.types import LoggingOptions


@dataclass(frozen=True)
class CheckOptions:
    """Options for controlling rule check execution."""

    allow_empty_tests: bool = False
    logging: LoggingOptions | None = None
    clear_cache: bool = False


class Checkable(Protocol):
    """Protocol for any architecture rule that can be checked.

    All fluent API chains ultimately produce a Checkable whose check()
    method executes the rule and returns a list of violations (empty = pass).
    """

    def check(self, options: CheckOptions | None = None) -> list[Violation]: ...
