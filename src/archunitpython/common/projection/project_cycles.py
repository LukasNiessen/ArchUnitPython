"""High-level cycle detection on projected graphs."""

from __future__ import annotations

from archunitpython.common.extraction.graph import Edge
from archunitpython.common.projection.cycles.cycles import calculate_cycles
from archunitpython.common.projection.cycles.model import NumberEdge
from archunitpython.common.projection.edge_projections import per_internal_edge
from archunitpython.common.projection.project_edges import project_edges
from archunitpython.common.projection.types import ProjectedEdge

ProjectedCycles = list[list[ProjectedEdge]]


def project_internal_cycles(graph: list[Edge]) -> ProjectedCycles:
    """Find cycles among internal edges of a raw graph."""
    edges = project_edges(graph, per_internal_edge())
    return project_cycles(edges)


def project_cycles(edges: list[ProjectedEdge]) -> ProjectedCycles:
    """Find cycles in a list of projected edges."""
    return _CycleProcessor().find_cycles(edges)


class _CycleProcessor:
    """Converts between string labels and numeric IDs for cycle detection."""

    def __init__(self) -> None:
        self._label_to_id: dict[str, int] = {}
        self._id_to_label: dict[int, str] = {}
        self._source_edges: list[ProjectedEdge] = []

    def find_cycles(self, edges: list[ProjectedEdge]) -> ProjectedCycles:
        domain_edges = self._to_domain(edges)
        cycles = calculate_cycles(domain_edges)
        return self._from_domain(cycles)

    def _to_domain(self, edges: list[ProjectedEdge]) -> list[NumberEdge]:
        self._source_edges = edges
        self._label_to_id = {}
        self._id_to_label = {}
        index = 0

        for e in edges:
            if e.source_label not in self._label_to_id:
                self._label_to_id[e.source_label] = index
                self._id_to_label[index] = e.source_label
                index += 1
            if e.target_label not in self._label_to_id:
                self._label_to_id[e.target_label] = index
                self._id_to_label[index] = e.target_label
                index += 1

        return [
            NumberEdge(
                from_node=self._label_to_id[e.source_label],
                to_node=self._label_to_id[e.target_label],
            )
            for e in edges
        ]

    def _from_domain(self, cycles: list[list[NumberEdge]]) -> ProjectedCycles:
        result: ProjectedCycles = []

        for cycle in cycles:
            projected_cycle: list[ProjectedEdge] = []
            for e in cycle:
                source_label = self._id_to_label[e.from_node]
                target_label = self._id_to_label[e.to_node]
                found = next(
                    (
                        se
                        for se in self._source_edges
                        if se.source_label == source_label
                        and se.target_label == target_label
                    ),
                    None,
                )
                if found:
                    projected_cycle.append(found)
            if projected_cycle:
                result.append(projected_cycle)

        return result
