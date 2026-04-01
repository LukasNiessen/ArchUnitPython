"""Utility functions for cycle detection."""

from __future__ import annotations

from archunitpy.common.projection.cycles.model import NumberEdge, NumberNode


class CycleUtils:
    @staticmethod
    def get_outgoing_neighbours(
        current_node: NumberNode, graph: list[NumberNode]
    ) -> list[NumberNode]:
        """Get all nodes that current_node has outgoing edges to."""
        node_map = {n.node: n for n in graph}
        result = []
        for edge in current_node.outgoing:
            neighbour = node_map.get(edge.to_node)
            if neighbour is not None:
                result.append(neighbour)
        return result

    @staticmethod
    def transform_edge_data(edges: list[NumberEdge]) -> list[NumberNode]:
        """Convert a list of edges into a list of nodes with in/out edges."""
        unique_ids = CycleUtils.find_unique_nodes(edges)
        nodes = []
        for node_id in unique_ids:
            nodes.append(
                NumberNode(
                    node=node_id,
                    incoming=[e for e in edges if e.to_node == node_id],
                    outgoing=[e for e in edges if e.from_node == node_id],
                )
            )
        return nodes

    @staticmethod
    def find_unique_nodes(edges: list[NumberEdge]) -> list[int]:
        """Find all unique node IDs in a list of edges, preserving order."""
        seen: set[int] = set()
        result: list[int] = []
        for edge in edges:
            if edge.from_node not in seen:
                seen.add(edge.from_node)
                result.append(edge.from_node)
            if edge.to_node not in seen:
                seen.add(edge.to_node)
                result.append(edge.to_node)
        return result
