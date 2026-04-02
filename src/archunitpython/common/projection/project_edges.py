"""Project a raw graph into labeled edges with edge aggregation."""

from __future__ import annotations

from collections import defaultdict

from archunitpython.common.extraction.graph import Edge
from archunitpython.common.projection.types import MapFunction, MappedEdge, ProjectedEdge


def project_edges(
    graph: list[Edge],
    mapper: MapFunction,
) -> list[ProjectedEdge]:
    """Apply a mapper to raw edges and group by (source_label, target_label).

    Edges that map to the same (source_label, target_label) are cumulated.
    Edges for which the mapper returns None are filtered out.

    Args:
        graph: Raw edge list.
        mapper: Function that maps Edge → MappedEdge or None.

    Returns:
        List of ProjectedEdge objects with cumulated raw edges.
    """
    groups: dict[tuple[str, str], list[Edge]] = defaultdict(list)

    for edge in graph:
        mapped = mapper(edge)
        if mapped is None:
            continue
        key = (mapped.source_label, mapped.target_label)
        groups[key].append(edge)

    return [
        ProjectedEdge(
            source_label=source_label,
            target_label=target_label,
            cumulated_edges=edges,
        )
        for (source_label, target_label), edges in groups.items()
    ]
