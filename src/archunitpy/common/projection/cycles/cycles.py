"""Orchestrate cycle detection: Tarjan SCC -> Johnson per SCC."""

from __future__ import annotations

from archunitpy.common.projection.cycles.johnsons_apsp import JohnsonsAPSP
from archunitpy.common.projection.cycles.model import NumberEdge
from archunitpy.common.projection.cycles.tarjan_scc import TarjanSCC


def calculate_cycles(edges: list[NumberEdge]) -> list[list[NumberEdge]]:
    """Find all simple cycles using Tarjan SCC + Johnson's algorithm.

    1. Find strongly connected components using Tarjan's algorithm
    2. For each SCC with >1 edge, find all simple cycles using Johnson's
    """
    cycles: list[list[NumberEdge]] = []

    tarjan = TarjanSCC()
    sccs = tarjan.find_strongly_connected_components(edges)

    for scc in sccs:
        if len(scc) > 1:
            johnson = JohnsonsAPSP()
            cycles.extend(johnson.find_simple_cycles(scc))

    return cycles
