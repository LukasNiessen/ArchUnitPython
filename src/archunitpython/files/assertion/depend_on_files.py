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
        is_negated: If False (`should()`), files matching subject MUST depend on
                    files matching object.
                    If True (`should_not()`), files matching subject must NOT
                    depend on files matching object.

    Returns:
        List of violations.
    """
    violations: list[Violation] = []
    subject_matches_by_label: dict[str, bool] = {}
    target_matches_by_label: dict[str, bool] = {}

    for edge in edges:
        source_label = edge.source_label
        if source_label not in subject_matches_by_label:
            subject_matches_by_label[source_label] = all(
                matches_pattern(source_label, filter_) for filter_ in subject_filters
            )
        if not subject_matches_by_label[source_label]:
            continue

        target_label = edge.target_label
        if target_label not in target_matches_by_label:
            target_matches_by_label[target_label] = all(
                matches_pattern(target_label, filter_) for filter_ in object_filters
            )
        target_matches = target_matches_by_label[target_label]

        if is_negated:
            # should_not(): violation if dependency EXISTS
            if target_matches:
                violations.append(ViolatingFileDependency(dependency=edge, is_negated=True))
        else:
            # should: violation if dependency does NOT match
            if not target_matches:
                violations.append(ViolatingFileDependency(dependency=edge, is_negated=False))

    return violations
