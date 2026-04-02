"""Types for graph projections."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from archunitpython.common.extraction.graph import Edge


@dataclass
class ProjectedNode:
    """A node in a projected graph with its incoming/outgoing edges."""

    label: str
    incoming: list[Edge] = field(default_factory=list)
    outgoing: list[Edge] = field(default_factory=list)


@dataclass
class MappedEdge:
    """An edge after label mapping."""

    source_label: str
    target_label: str


@dataclass
class ProjectedEdge:
    """An edge between two labeled nodes, aggregating underlying raw edges."""

    source_label: str
    target_label: str
    cumulated_edges: list[Edge] = field(default_factory=list)


MapFunction = Callable[[Edge], MappedEdge | None]
"""A function that maps a raw Edge to a MappedEdge (or None to filter it out)."""

ProjectedGraph = list[ProjectedEdge]
