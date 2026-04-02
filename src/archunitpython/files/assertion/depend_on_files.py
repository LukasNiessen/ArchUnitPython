"""Violation gathering for file dependency rules."""

from __future__ import annotations

from dataclasses import dataclass

from archunitpython.common.assertion.violation import Violation
from archunitpython.common.pattern_matching import matches_pattern
from archunitpython.common.projection.types import ProjectedEdge
from archunitpython.common.types import Filter


@dataclass
class ViolatingFileDependency(Violation):
    """A file dependency that violates a rule."""

    dependency: ProjectedEdge
    is_negated: bool = False


def gather_depend_on_file_violations(
    edges: list[ProjectedEdge],
    subject_filters: list[Filter],
    object_filters: list[Filter],
    is_negated: bool,
) -> list[Violation]:
    """Check if files have/don't have certain dependencies.

    Args:
        edges: Projected dependency edges.
        subject_filters: Patterns for the source files (subject of the rule).
        object_filters: Patterns for the target files (dependency targets).
        is_negated: If False (should), files matching subject MUST depend on
                    files matching object.
                    If True (shouldNot), files matching subject must NOT
                    depend on files matching object.

    Returns:
        List of violations.
    """
    violations: list[Violation] = []

    for edge in edges:
        source_matches = all(
            matches_pattern(edge.source_label, f) for f in subject_filters
        )
        if not source_matches:
            continue

        target_matches = all(
            matches_pattern(edge.target_label, f) for f in object_filters
        )

        if is_negated:
            # shouldNot: violation if dependency EXISTS
            if target_matches:
                violations.append(
                    ViolatingFileDependency(dependency=edge, is_negated=True)
                )
        else:
            # should: violation if dependency does NOT match
            if not target_matches:
                violations.append(
                    ViolatingFileDependency(dependency=edge, is_negated=False)
                )

    return violations
