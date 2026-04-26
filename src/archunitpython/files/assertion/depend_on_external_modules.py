"""Violation gathering for external module dependency rules."""

from __future__ import annotations

from dataclasses import dataclass

from archunitpython.common.assertion.violation import Violation
from archunitpython.common.pattern_matching import matches_pattern
from archunitpython.common.projection.types import ProjectedEdge
from archunitpython.common.types import Filter


@dataclass
class ViolatingExternalModuleDependency(Violation):
    """An external module dependency that violates a rule."""

    dependency: ProjectedEdge
    is_negated: bool = False


def gather_depend_on_external_module_violations(
    edges: list[ProjectedEdge],
    subject_filters: list[Filter],
    module_filters: list[Filter],
    is_negated: bool,
) -> list[Violation]:
    """Check if files depend on forbidden/allowed external modules.

    Subject filters use AND semantics. Module filters use OR semantics, which
    makes it possible to express useful allowlists or blocklists for external
    module names.
    """
    violations: list[Violation] = []

    for edge in edges:
        source_matches = all(
            matches_pattern(edge.source_label, filter_)
            for filter_ in subject_filters
        )
        if not source_matches:
            continue

        target_matches = (
            any(matches_pattern(edge.target_label, filter_) for filter_ in module_filters)
            if module_filters
            else False
        )

        if is_negated:
            if target_matches:
                violations.append(
                    ViolatingExternalModuleDependency(
                        dependency=edge, is_negated=True
                    )
                )
        else:
            if not target_matches:
                violations.append(
                    ViolatingExternalModuleDependency(
                        dependency=edge, is_negated=False
                    )
                )

    return violations
