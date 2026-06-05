"""Project a raw graph into nodes with incoming/outgoing edges."""

from __future__ import annotations

from collections import defaultdict

from archunitpython.common.extraction.graph import Edge
from archunitpython.common.projection.types import ProjectedNode


def project_to_nodes(
    graph: list[Edge],
    *,
    include_externals: bool = False,
) -> list[ProjectedNode]:
    """Group edges into nodes with incoming and outgoing edge lists.

    Args:
        graph: Raw edge list.
        include_externals: If True, include nodes for external dependencies.

    Returns:
        List of ProjectedNode objects.
    """
    incoming: dict[str, list[Edge]] = defaultdict(list)
    outgoing: dict[str, list[Edge]] = defaultdict(list)
    all_labels: set[str] = set()

    for edge in graph:
        all_labels.add(edge.source)
        if edge.source != edge.target:  # Don't count self-edges as incoming
            outgoing[edge.source].append(edge)

        if (edge.external and include_externals) or not edge.external:
            # Record the target (external file)
            all_labels.add(edge.target)
            if edge.source != edge.target:  # Don't count self-edges as incoming
                incoming[edge.target].append(edge)

    return [
        ProjectedNode(
            label=label,
            incoming=incoming.get(label, []),
            outgoing=outgoing.get(label, []),
        )
        for label in sorted(all_labels)
    ]
