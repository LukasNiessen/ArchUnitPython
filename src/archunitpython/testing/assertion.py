"""Testing assertion helpers for architecture rules."""

from __future__ import annotations

from archunitpython.common.assertion.violation import Violation
from archunitpython.common.fluentapi.checkable import CheckOptions
from archunitpython.testing.common.violation_factory import ViolationFactory


def format_violations(violations: list[Violation]) -> str:
    """Format violations into a human-readable string.

    Args:
        violations: List of violations to format.

    Returns:
        Formatted string describing all violations.
    """
    if not violations:
        return "No violations found."

    lines = [f"Found {len(violations)} architecture violation(s):", ""]
    for i, violation in enumerate(violations, 1):
        tv = ViolationFactory.from_violation(violation)
        lines.append(f"  {i}. {tv.message}")
        lines.append(f"     {tv.details}")
        lines.append("")

    return "\n".join(lines)


def assert_passes(
    checkable: object,
    options: CheckOptions | None = None,
) -> None:
    """Assert that an architecture rule passes (no violations).

    Args:
        checkable: Any object with a check() method (implements Checkable).
        options: Optional check options.

    Raises:
        AssertionError: If the rule has violations.
    """
    violations = checkable.check(options)  # type: ignore[union-attr]
    if violations:
        raise AssertionError(format_violations(violations))
