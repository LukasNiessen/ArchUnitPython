"""Numeric graph model for cycle detection algorithms."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class NumberEdge:
    """An edge between two numerically-identified nodes."""

    from_node: int
    to_node: int


@dataclass
class NumberNode:
    """A node with incoming and outgoing edges."""

    node: int
    incoming: list[NumberEdge] = field(default_factory=list)
    outgoing: list[NumberEdge] = field(default_factory=list)
