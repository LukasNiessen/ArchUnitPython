"""Project a raw graph into labeled edges with edge aggregation."""

from __future__ import annotations

from collections import defaultdict

from archunitpython.common.extraction.graph import Edge
from archunitpython.common.logging.inspection import debug
from archunitpython.common.projection.types import MapFunction, ProjectedEdge


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
            debug("Projection omitted: %s -> %s", edge.source, edge.target)
            continue
        debug(
            "Projection: %s -> %s becomes %s -> %s",
            edge.source,
            edge.target,
            mapped.source_label,
            mapped.target_label,
        )
        key = (mapped.source_label, mapped.target_label)
        groups[key].append(edge)

    projected = [
        ProjectedEdge(
            source_label=source_label,
            target_label=target_label,
            cumulated_edges=edges,
        )
        for (source_label, target_label), edges in groups.items()
    ]
    debug("Projection complete: %d raw edges -> %d projected edges", len(graph), len(projected))
    return projected
