"""Violation gathering for file pattern matching rules."""

from __future__ import annotations

from dataclasses import dataclass

from archunitpy.common.assertion.violation import Violation
from archunitpy.common.pattern_matching import matches_pattern
from archunitpy.common.projection.types import ProjectedNode
from archunitpy.common.types import Filter


@dataclass
class ViolatingNode(Violation):
    """A file that violates a pattern matching rule."""

    check_pattern: Filter
    projected_node: ProjectedNode
    is_negated: bool = False


def gather_regex_matching_violations(
    nodes: list[ProjectedNode],
    check_filters: list[Filter],
    is_negated: bool,
) -> list[Violation]:
    """Check if files match/don't match given patterns.

    Args:
        nodes: Files to check.
        check_filters: Patterns to match against.
        is_negated: If False (should), files MUST match all patterns.
                    If True (shouldNot), files must NOT match any pattern.

    Returns:
        List of violations.
    """
    violations: list[Violation] = []

    for node in nodes:
        for filter_ in check_filters:
            matched = matches_pattern(node.label, filter_)
            if is_negated:
                # shouldNot: violation if file DOES match
                if matched:
                    violations.append(
                        ViolatingNode(
                            check_pattern=filter_,
                            projected_node=node,
                            is_negated=True,
                        )
                    )
            else:
                # should: violation if file does NOT match
                if not matched:
                    violations.append(
                        ViolatingNode(
                            check_pattern=filter_,
                            projected_node=node,
                            is_negated=False,
                        )
                    )

    return violations
