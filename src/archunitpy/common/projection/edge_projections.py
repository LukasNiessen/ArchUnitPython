"""Built-in MapFunction implementations for edge projection."""

from __future__ import annotations

from archunitpy.common.extraction.graph import Edge
from archunitpy.common.projection.types import MapFunction, MappedEdge


def per_internal_edge() -> MapFunction:
    """Create a mapper that only passes internal (non-external) edges.

    Self-referencing edges (source == target) are also filtered out.
    """

    def mapper(edge: Edge) -> MappedEdge | None:
        if edge.external:
            return None
        if edge.source == edge.target:
            return None
        return MappedEdge(source_label=edge.source, target_label=edge.target)

    return mapper


def per_edge() -> MapFunction:
    """Create a mapper that passes all edges (including external).

    Self-referencing edges are still filtered out.
    """

    def mapper(edge: Edge) -> MappedEdge | None:
        if edge.source == edge.target:
            return None
        return MappedEdge(source_label=edge.source, target_label=edge.target)

    return mapper
