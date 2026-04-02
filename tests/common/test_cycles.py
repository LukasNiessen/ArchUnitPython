"""Tests for cycle detection algorithms."""

from archunitpython.common.extraction.graph import Edge
from archunitpython.common.projection.cycles.cycles import calculate_cycles
from archunitpython.common.projection.cycles.johnsons_apsp import JohnsonsAPSP
from archunitpython.common.projection.cycles.model import NumberEdge
from archunitpython.common.projection.cycles.tarjan_scc import TarjanSCC
from archunitpython.common.projection.project_cycles import (
    project_cycles,
    project_internal_cycles,
)
from archunitpython.common.projection.types import ProjectedEdge


class TestTarjanSCC:
    def test_no_cycles(self):
        # A → B → C (no cycle)
        edges = [NumberEdge(0, 1), NumberEdge(1, 2)]
        tarjan = TarjanSCC()
        sccs = tarjan.find_strongly_connected_components(edges)
        assert len(sccs) == 0

    def test_simple_cycle(self):
        # A → B → A
        edges = [NumberEdge(0, 1), NumberEdge(1, 0)]
        tarjan = TarjanSCC()
        sccs = tarjan.find_strongly_connected_components(edges)
        assert len(sccs) == 1
        assert len(sccs[0]) == 2

    def test_triangle_cycle(self):
        # A → B → C → A
        edges = [NumberEdge(0, 1), NumberEdge(1, 2), NumberEdge(2, 0)]
        tarjan = TarjanSCC()
        sccs = tarjan.find_strongly_connected_components(edges)
        assert len(sccs) == 1
        assert len(sccs[0]) == 3

    def test_two_separate_cycles(self):
        # A → B → A and C → D → C (disconnected)
        edges = [
            NumberEdge(0, 1),
            NumberEdge(1, 0),
            NumberEdge(2, 3),
            NumberEdge(3, 2),
        ]
        tarjan = TarjanSCC()
        sccs = tarjan.find_strongly_connected_components(edges)
        assert len(sccs) == 2

    def test_complex_graph(self):
        # A → B → C → A, C → D (D is not in cycle)
        edges = [
            NumberEdge(0, 1),
            NumberEdge(1, 2),
            NumberEdge(2, 0),
            NumberEdge(2, 3),
        ]
        tarjan = TarjanSCC()
        sccs = tarjan.find_strongly_connected_components(edges)
        assert len(sccs) == 1  # Only the A-B-C cycle


class TestJohnsonsAPSP:
    def test_simple_cycle(self):
        # A ↔ B
        edges = [NumberEdge(0, 1), NumberEdge(1, 0)]
        johnson = JohnsonsAPSP()
        cycles = johnson.find_simple_cycles(edges)
        assert len(cycles) == 1
        cycle_nodes = {e.from_node for e in cycles[0]}
        assert cycle_nodes == {0, 1}

    def test_triangle_finds_one_cycle(self):
        # A → B → C → A
        edges = [NumberEdge(0, 1), NumberEdge(1, 2), NumberEdge(2, 0)]
        johnson = JohnsonsAPSP()
        cycles = johnson.find_simple_cycles(edges)
        assert len(cycles) == 1
        assert len(cycles[0]) == 3

    def test_complete_graph_finds_all_cycles(self):
        # Complete graph on 3 nodes: A↔B, B↔C, A↔C
        edges = [
            NumberEdge(0, 1),
            NumberEdge(1, 0),
            NumberEdge(1, 2),
            NumberEdge(2, 1),
            NumberEdge(0, 2),
            NumberEdge(2, 0),
        ]
        johnson = JohnsonsAPSP()
        cycles = johnson.find_simple_cycles(edges)
        # Should find multiple cycles: AB, BC, AC, ABC, ACB
        assert len(cycles) >= 3


class TestCalculateCycles:
    def test_acyclic(self):
        edges = [NumberEdge(0, 1), NumberEdge(1, 2)]
        cycles = calculate_cycles(edges)
        assert len(cycles) == 0

    def test_single_cycle(self):
        edges = [NumberEdge(0, 1), NumberEdge(1, 0)]
        cycles = calculate_cycles(edges)
        assert len(cycles) == 1

    def test_multiple_overlapping_cycles(self):
        # A → B → C → A, B → A
        edges = [
            NumberEdge(0, 1),
            NumberEdge(1, 2),
            NumberEdge(2, 0),
            NumberEdge(1, 0),
        ]
        cycles = calculate_cycles(edges)
        assert len(cycles) >= 2  # A→B→A and A→B→C→A


class TestProjectCycles:
    def test_no_cycles(self):
        edges = [
            ProjectedEdge(source_label="a", target_label="b"),
        ]
        cycles = project_cycles(edges)
        assert len(cycles) == 0

    def test_simple_cycle(self):
        edges = [
            ProjectedEdge(source_label="a", target_label="b"),
            ProjectedEdge(source_label="b", target_label="a"),
        ]
        cycles = project_cycles(edges)
        assert len(cycles) == 1
        labels = {e.source_label for e in cycles[0]}
        assert labels == {"a", "b"}

    def test_preserves_cumulated_edges(self):
        raw_edge = Edge(source="x.py", target="y.py", external=False)
        edges = [
            ProjectedEdge(
                source_label="a",
                target_label="b",
                cumulated_edges=[raw_edge],
            ),
            ProjectedEdge(
                source_label="b",
                target_label="a",
                cumulated_edges=[raw_edge],
            ),
        ]
        cycles = project_cycles(edges)
        assert len(cycles) == 1
        for edge in cycles[0]:
            assert len(edge.cumulated_edges) == 1


class TestProjectInternalCycles:
    def test_no_cycles_in_acyclic_graph(self):
        graph = [
            Edge(source="a.py", target="a.py", external=False),
            Edge(source="b.py", target="b.py", external=False),
            Edge(source="a.py", target="b.py", external=False),
        ]
        cycles = project_internal_cycles(graph)
        assert len(cycles) == 0

    def test_detects_cycle(self):
        graph = [
            Edge(source="a.py", target="a.py", external=False),
            Edge(source="b.py", target="b.py", external=False),
            Edge(source="a.py", target="b.py", external=False),
            Edge(source="b.py", target="a.py", external=False),
        ]
        cycles = project_internal_cycles(graph)
        assert len(cycles) == 1

    def test_ignores_external_edges(self):
        graph = [
            Edge(source="a.py", target="a.py", external=False),
            Edge(source="a.py", target="os", external=True),
            Edge(source="os", target="a.py", external=True),
        ]
        cycles = project_internal_cycles(graph)
        assert len(cycles) == 0
