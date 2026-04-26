"""Built-in MapFunction implementations for edge projection."""

from __future__ import annotations

from archunitpython.common.extraction.graph import Edge
from archunitpython.common.projection.types import MapFunction, MappedEdge


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


def per_external_edge() -> MapFunction:
    """Create a mapper that only passes external edges.

    Self-referencing edges are filtered out, though they are not expected for
    external imports.
    """

    def mapper(edge: Edge) -> MappedEdge | None:
        if not edge.external:
            return None
        if edge.source == edge.target:
            return None
        return MappedEdge(source_label=edge.source, target_label=edge.target)

    return mapper
