"""Tests for graph projection functions."""

from archunitpy.common.extraction.graph import Edge, ImportKind
from archunitpy.common.projection.edge_projections import per_edge, per_internal_edge
from archunitpy.common.projection.project_edges import project_edges
from archunitpy.common.projection.project_nodes import project_to_nodes
from archunitpy.common.projection.types import MappedEdge


def _make_edge(src: str, tgt: str, external: bool = False) -> Edge:
    return Edge(source=src, target=tgt, external=external)


class TestProjectToNodes:
    def test_simple_graph(self):
        graph = [
            _make_edge("a.py", "a.py"),  # self-edge
            _make_edge("b.py", "b.py"),
            _make_edge("a.py", "b.py"),
        ]
        nodes = project_to_nodes(graph)
        labels = {n.label for n in nodes}
        assert labels == {"a.py", "b.py"}

        a_node = next(n for n in nodes if n.label == "a.py")
        assert len(a_node.outgoing) == 1  # a → b
        assert a_node.outgoing[0].target == "b.py"
        assert len(a_node.incoming) == 0

        b_node = next(n for n in nodes if n.label == "b.py")
        assert len(b_node.incoming) == 1  # a → b
        assert len(b_node.outgoing) == 0

    def test_excludes_externals_by_default(self):
        graph = [
            _make_edge("a.py", "a.py"),
            _make_edge("a.py", "os", external=True),
        ]
        nodes = project_to_nodes(graph)
        labels = {n.label for n in nodes}
        assert "os" not in labels
        assert "a.py" in labels

    def test_includes_externals_when_requested(self):
        graph = [
            _make_edge("a.py", "a.py"),
            _make_edge("a.py", "os", external=True),
        ]
        nodes = project_to_nodes(graph, include_externals=True)
        labels = {n.label for n in nodes}
        assert "os" in labels

    def test_empty_graph(self):
        nodes = project_to_nodes([])
        assert nodes == []


class TestProjectEdges:
    def test_with_per_internal_edge(self):
        graph = [
            _make_edge("a.py", "a.py"),
            _make_edge("a.py", "b.py"),
            _make_edge("a.py", "os", external=True),
        ]
        projected = project_edges(graph, per_internal_edge())
        assert len(projected) == 1
        assert projected[0].source_label == "a.py"
        assert projected[0].target_label == "b.py"
        assert len(projected[0].cumulated_edges) == 1

    def test_with_per_edge(self):
        graph = [
            _make_edge("a.py", "a.py"),
            _make_edge("a.py", "b.py"),
            _make_edge("a.py", "os", external=True),
        ]
        projected = project_edges(graph, per_edge())
        assert len(projected) == 2  # a→b and a→os (self-edge filtered)

    def test_cumulation(self):
        graph = [
            Edge(
                source="a.py",
                target="b.py",
                external=False,
                import_kinds=(ImportKind.IMPORT,),
            ),
            Edge(
                source="a.py",
                target="b.py",
                external=False,
                import_kinds=(ImportKind.FROM_IMPORT,),
            ),
        ]
        projected = project_edges(graph, per_internal_edge())
        assert len(projected) == 1
        assert len(projected[0].cumulated_edges) == 2

    def test_custom_mapper(self):
        graph = [
            _make_edge("src/a/file.py", "src/b/file.py"),
        ]

        def folder_mapper(edge: Edge) -> MappedEdge | None:
            src_parts = edge.source.split("/")
            tgt_parts = edge.target.split("/")
            if len(src_parts) >= 2 and len(tgt_parts) >= 2:
                return MappedEdge(source_label=src_parts[1], target_label=tgt_parts[1])
            return None

        projected = project_edges(graph, folder_mapper)
        assert len(projected) == 1
        assert projected[0].source_label == "a"
        assert projected[0].target_label == "b"

    def test_empty_graph(self):
        projected = project_edges([], per_internal_edge())
        assert projected == []


class TestPerInternalEdge:
    def test_filters_external(self):
        mapper = per_internal_edge()
        assert mapper(_make_edge("a", "ext", external=True)) is None

    def test_filters_self_edge(self):
        mapper = per_internal_edge()
        assert mapper(_make_edge("a", "a")) is None

    def test_passes_internal(self):
        mapper = per_internal_edge()
        result = mapper(_make_edge("a", "b"))
        assert result is not None
        assert result.source_label == "a"
        assert result.target_label == "b"


class TestPerEdge:
    def test_passes_external(self):
        mapper = per_edge()
        result = mapper(_make_edge("a", "ext", external=True))
        assert result is not None

    def test_filters_self_edge(self):
        mapper = per_edge()
        assert mapper(_make_edge("a", "a")) is None

    def test_passes_internal(self):
        mapper = per_edge()
        result = mapper(_make_edge("a", "b"))
        assert result is not None
