"""Testing assertion helpers for architecture rules."""

from __future__ import annotations

from archunitpython.common.assertion.violation import Violation
from archunitpython.common.fluentapi.checkable import Checkable, CheckOptions
from archunitpython.testing.common.color_utils import ColorUtils
from archunitpython.testing.common.violation_factory import ViolationFactory


def format_violations(
    violations: list[Violation],
    *,
    because: str | None = None,
    color: bool | None = None,
) -> str:
    """Format violations into a human-readable string.

    Args:
        violations: List of violations to format.
        because: Optional rationale for the rule.
        color: None detects interactive terminals; False guarantees plain text.
            True explicitly enables ANSI colors, unless NO_COLOR is set.

    Returns:
        Formatted string describing all violations.
    """
    if not violations:
        return ColorUtils.style("No violations found.", "32", color)

    lines = [ColorUtils.style(f"Found {len(violations)} architecture violation(s):", "1;31", color)]
    if because:
        lines.extend(["", ColorUtils.style(f"Because: {because}", "33", color)])
    lines.append("")
    for i, violation in enumerate(violations, 1):
        tv = ViolationFactory.from_violation(violation)
        lines.append(f"  {i}. {ColorUtils.style(tv.message, '1;33', color)}")
        detail_color = "36" if "value=" in tv.details else "34"
        for detail in tv.details.split("\n"):
            lines.append(f"     {ColorUtils.style(detail, detail_color, color)}")
        lines.append("")

    return "\n".join(lines)


def assert_passes(
    checkable: Checkable,
    options: CheckOptions | None = None,
    *,
    color: bool | None = None,
) -> None:
    """Assert that an architecture rule passes (no violations).

    Args:
        checkable: Any object with a check() method (implements Checkable).
        options: Optional check options.
        color: Optional color override for failure output.

    Raises:
        AssertionError: If the rule has violations.
    """
    violations = checkable.check(options)
    if violations:
        because = getattr(checkable, "because_reason", None)
        raise AssertionError(format_violations(violations, because=because, color=color))
