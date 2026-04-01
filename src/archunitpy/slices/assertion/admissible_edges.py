"""Violation gathering for slice-level architecture rules."""

from __future__ import annotations

from dataclasses import dataclass

from archunitpy.common.assertion.violation import Violation
from archunitpy.common.projection.types import ProjectedEdge
from archunitpy.slices.uml.generate_rules import Rule


@dataclass
class CoherenceOptions:
    """Options for architecture coherence checking."""

    ignore_orphan_slices: bool = False
    ignore_external_slices: bool = False


@dataclass
class ViolatingEdge(Violation):
    """A slice dependency that violates the architecture rules."""

    rule: Rule | None
    projected_edge: ProjectedEdge
    is_negated: bool = False


def gather_violations(
    edges: list[ProjectedEdge],
    rules: list[Rule],
) -> list[Violation]:
    """Check for forbidden dependencies (used with shouldNot).

    Args:
        edges: Projected dependency edges between slices.
        rules: Forbidden dependency rules.

    Returns:
        Violations for any edge that matches a forbidden rule.
    """
    violations: list[Violation] = []

    for edge in edges:
        for rule in rules:
            if edge.source_label == rule.source and edge.target_label == rule.target:
                violations.append(
                    ViolatingEdge(
                        rule=rule,
                        projected_edge=edge,
                        is_negated=True,
                    )
                )

    return violations


def gather_positive_violations(
    edges: list[ProjectedEdge],
    rules: list[Rule],
    contained_nodes: list[str],
    coherence_options: CoherenceOptions | None = None,
) -> list[Violation]:
    """Check that all dependencies are allowed by rules (used with should).

    Args:
        edges: Projected dependency edges between slices.
        rules: Allowed dependency rules from diagram.
        contained_nodes: All declared component names in the diagram.
        coherence_options: Options for handling orphan/external slices.

    Returns:
        Violations for any edge not covered by the rules.
    """
    violations: list[Violation] = []
    opts = coherence_options or CoherenceOptions()

    # Build set of allowed edges (including self-dependencies)
    allowed = {(r.source, r.target) for r in rules}

    for edge in edges:
        source = edge.source_label
        target = edge.target_label

        # Self-dependency is always allowed
        if source == target:
            continue

        # Check if source/target are known components
        source_known = source in contained_nodes
        target_known = target in contained_nodes

        if not source_known and opts.ignore_orphan_slices:
            continue
        if not target_known and opts.ignore_orphan_slices:
            continue

        # Check if the edge is allowed
        if (source, target) not in allowed:
            violations.append(
                ViolatingEdge(
                    rule=None,
                    projected_edge=edge,
                    is_negated=False,
                )
            )

    return violations
