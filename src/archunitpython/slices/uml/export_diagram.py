"""Export a projected graph as a PlantUML diagram."""

from __future__ import annotations

from archunitpython.common.projection.types import ProjectedEdge


def export_diagram(graph: list[ProjectedEdge]) -> str:
    """Generate a PlantUML component diagram from projected edges.

    Args:
        graph: List of projected edges.

    Returns:
        PlantUML diagram as a string.
    """
    components: set[str] = set()
    lines: list[str] = ["@startuml"]

    for edge in graph:
        components.add(edge.source_label)
        components.add(edge.target_label)

    for component in sorted(components):
        lines.append(f"  component [{component}]")

    for edge in graph:
        lines.append(f"  [{edge.source_label}] --> [{edge.target_label}]")

    lines.append("@enduml")
    return "\n".join(lines)
