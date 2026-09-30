"""Observational instrumentation for the existing check contract."""

from __future__ import annotations

from functools import wraps
from time import perf_counter
from typing import Callable, TypeVar, cast

from archunitpython.common.assertion.violation import Violation
from archunitpython.common.fluentapi.checkable import CheckOptions
from archunitpython.common.logging.inspection import InspectionSession, current_session

F = TypeVar("F", bound=Callable[..., list[Violation]])


def inspect_check(check: F) -> F:
    """Trace a check while preserving its options, results, and exceptions."""

    @wraps(check)
    def inspected(self: object, options: CheckOptions | None = None) -> list[Violation]:
        logging_options = options.logging if options else None
        session = (
            InspectionSession(logging_options)
            if logging_options and logging_options.enabled
            else None
        )
        token = current_session.set(session)
        started = perf_counter() if session else 0.0
        rule_name = type(self).__name__
        try:
            if session:
                session.emit("info", "Starting check: %s", rule_name)
                # Describe only known rule configuration, never user callbacks.
                for name in (
                    "_project_path",
                    "_filters",
                    "_subject_filters",
                    "_object_filters",
                    "_module_filters",
                    "_pre_filters",
                    "_check_filters",
                    "_is_negated",
                    "_pattern",
                    "_regex",
                    "_source",
                    "_target",
                    "_layers",
                    "_allowed_dependencies",
                    "_forbidden_dependencies",
                    "_threshold",
                    "_comparison",
                    "_metric_attr",
                    "_name",
                    "_zone_type",
                ):
                    if session.options.level == "debug" and name in vars(self):
                        session.emit("debug", "%s: %s", name.removeprefix("_"), vars(self)[name])
            violations = check(self, options)
            if session:
                session.emit(
                    "warn" if violations else "info",
                    "Finished check: %s - %d violation(s) (%.3fs)",
                    rule_name,
                    len(violations),
                    perf_counter() - started,
                )
                for violation in violations:
                    session.emit("warn", "Violation: %s", violation)
            return violations
        except Exception as error:
            if session:
                session.emit("error", "Check failed: %s - %s", rule_name, error)
            raise
        finally:
            current_session.reset(token)
            if session:
                session.close()

    return cast(F, inspected)
