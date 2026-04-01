"""Violation gathering for cycle-free rules."""

from __future__ import annotations

from dataclasses import dataclass

from archunitpy.common.assertion.violation import Violation
from archunitpy.common.projection.types import ProjectedEdge


@dataclass
class ViolatingCycle(Violation):
    """A circular dependency detected between files."""

    cycle: list[ProjectedEdge]


def gather_cycle_violations(
    cycles: list[list[ProjectedEdge]],
) -> list[Violation]:
    """Convert detected cycles into violations.

    Args:
        cycles: List of cycles, each being a list of edges forming the cycle.

    Returns:
        List of ViolatingCycle violations.
    """
    return [ViolatingCycle(cycle=cycle) for cycle in cycles]
