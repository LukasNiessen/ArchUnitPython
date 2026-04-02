"""Johnson's algorithm for finding all simple cycles in a directed graph."""

from __future__ import annotations

from dataclasses import dataclass

from archunitpython.common.projection.cycles.cycle_utils import CycleUtils
from archunitpython.common.projection.cycles.model import NumberEdge, NumberNode


@dataclass
class _BlockedBy:
    blocked: NumberNode
    by: NumberNode


class JohnsonsAPSP:
    """Johnson's algorithm for finding all simple (elementary) cycles."""

    def find_simple_cycles(self, edges: list[NumberEdge]) -> list[list[NumberEdge]]:
        """Find all simple cycles in the graph defined by edges.

        Should be called on a strongly connected component for efficiency.
        """
        self._blocked: list[NumberNode] = []
        self._stack: list[NumberNode] = []
        self._blocked_map: list[_BlockedBy] = []
        self._graph = CycleUtils.transform_edge_data(edges)
        self._start: NumberNode | None = None
        self._cycles: list[list[NumberEdge]] = []

        for node in list(self._graph):
            self._start = node
            self._stack.append(node)
            self._blocked.append(node)
            self._explore_neighbours(node)
            self._remove_from_graph(node)

        return self._cycles

    def _explore_neighbours(self, current_node: NumberNode) -> None:
        neighbours = CycleUtils.get_outgoing_neighbours(current_node, self._graph)
        for neighbour in neighbours:
            if self._found_cycle(neighbour):
                self._cycles.append(self._build_cycle())
            if not self._is_blocked(neighbour):
                self._stack.append(neighbour)
                self._blocked.append(neighbour)
                self._explore_neighbours(neighbour)

        self._stack.pop()

        if self._is_part_of_current_start_cycle(current_node):
            self._unblock(current_node)
        else:
            for neighbour in CycleUtils.get_outgoing_neighbours(
                current_node, self._graph
            ):
                if self._is_blocked(neighbour):
                    self._blocked_map.append(
                        _BlockedBy(blocked=current_node, by=neighbour)
                    )

    def _unblock(self, node: NumberNode) -> None:
        self._blocked = [n for n in self._blocked if n is not node]
        to_remove: list[_BlockedBy] = []
        for blocker in self._blocked_map:
            if blocker.by is node:
                self._unblock(blocker.blocked)
                to_remove.append(blocker)
        self._blocked_map = [b for b in self._blocked_map if b not in to_remove]

    def _is_part_of_current_start_cycle(self, current_node: NumberNode) -> bool:
        if self._start is None:
            return False
        for cycle in self._cycles:
            if (
                cycle[0].from_node == self._start.node
                and any(e.from_node == current_node.node for e in cycle)
            ):
                return True
        return False

    def _is_blocked(self, node: NumberNode) -> bool:
        return node in self._blocked

    def _remove_from_graph(self, to_remove: NumberNode) -> None:
        for node in self._graph:
            node.incoming = [
                e
                for e in node.incoming
                if e.from_node != to_remove.node and e.to_node != to_remove.node
            ]
            node.outgoing = [
                e
                for e in node.outgoing
                if e.from_node != to_remove.node and e.to_node != to_remove.node
            ]

    def _found_cycle(self, current_node: NumberNode) -> bool:
        return current_node is self._start

    def _build_cycle(self) -> list[NumberEdge]:
        node_ids = [n.node for n in self._stack]
        cycle_edges: list[NumberEdge] = []
        for i in range(len(node_ids)):
            from_id = node_ids[i]
            to_id = node_ids[i + 1] if i + 1 < len(node_ids) else self._start.node  # type: ignore[union-attr]
            cycle_edges.append(NumberEdge(from_node=from_id, to_node=to_id))
        return cycle_edges
