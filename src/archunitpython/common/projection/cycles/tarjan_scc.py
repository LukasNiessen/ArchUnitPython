"""Tarjan's Strongly Connected Components algorithm."""

from __future__ import annotations

from archunitpython.common.projection.cycles.model import NumberEdge


class _Vertex:
    """Internal vertex representation for Tarjan's algorithm."""

    def __init__(self, node_id: int) -> None:
        self.id = node_id
        self.index = -1
        self.lowlink = -1
        self.neighbours: list[int] = []


class TarjanSCC:
    """Tarjan's algorithm for finding strongly connected components."""

    def find_strongly_connected_components(
        self, edges: list[NumberEdge]
    ) -> list[list[NumberEdge]]:
        """Find all strongly connected components in the graph.

        Returns a list of edge lists, where each inner list contains
        the edges belonging to one SCC. Only SCCs with edges are returned.
        """
        self._graph: dict[int, _Vertex] = {}
        self._index = 0
        self._stack: list[_Vertex] = []
        self._sccs: list[list[NumberEdge]] = []
        self._edges = edges

        self._init(edges)

        for vertex in self._graph.values():
            if vertex.index < 0:
                self._visit(vertex)

        return self._sccs

    def _init(self, edges: list[NumberEdge]) -> None:
        """Build adjacency representation from edges."""
        for edge in edges:
            if edge.from_node not in self._graph:
                self._graph[edge.from_node] = _Vertex(edge.from_node)
            if edge.to_node not in self._graph:
                self._graph[edge.to_node] = _Vertex(edge.to_node)

            v = self._graph[edge.from_node]
            if edge.to_node not in v.neighbours:
                v.neighbours.append(edge.to_node)

    def _visit(self, vertex: _Vertex) -> None:
        """DFS visit for Tarjan's algorithm."""
        vertex.index = self._index
        vertex.lowlink = self._index
        self._index += 1
        self._stack.append(vertex)

        for neighbour_id in vertex.neighbours:
            w = self._graph[neighbour_id]
            if w.index < 0:
                self._visit(w)
                vertex.lowlink = min(vertex.lowlink, w.lowlink)
            elif w in self._stack:
                vertex.lowlink = min(vertex.lowlink, w.index)

        if vertex.lowlink == vertex.index:
            scc_vertices: list[_Vertex] = []
            while True:
                w = self._stack.pop()
                scc_vertices.append(w)
                if w.id == vertex.id:
                    break

            if scc_vertices:
                scc_ids = {v.id for v in scc_vertices}
                scc_edges = [
                    e
                    for e in self._edges
                    if e.from_node in scc_ids and e.to_node in scc_ids
                ]
                if scc_edges:
                    self._sccs.append(scc_edges)
