"""PlantUML diagram parsing and rule generation."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Rule:
    """An allowed dependency relationship between two components."""

    source: str
    target: str


def generate_rule(puml_content: str) -> tuple[list[Rule], list[str]]:
    """Parse a PlantUML diagram and extract component rules.

    Supports component diagrams with:
    - component [Name] declarations
    - [Source] --> [Target] relationships
    - package grouping (names extracted from components inside)

    Args:
        puml_content: PlantUML diagram content as a string.

    Returns:
        Tuple of (rules, contained_nodes):
        - rules: list of allowed dependency relationships
        - contained_nodes: list of all declared component names
    """
    rules: list[Rule] = []
    contained_nodes: list[str] = []

    lines = puml_content.strip().splitlines()

    for line in lines:
        stripped = line.strip()

        # Skip empty lines, comments, @startuml/@enduml
        if not stripped or stripped.startswith("@") or stripped.startswith("'"):
            continue

        # Match component declarations: component [Name] or component [Name] #Color
        comp_match = re.match(
            r"component\s+\[([^\]]+)\]", stripped
        )
        if comp_match:
            name = comp_match.group(1).strip()
            if name not in contained_nodes:
                contained_nodes.append(name)
            continue

        # Match relationships: [Source] --> [Target] or [Source] -> [Target]
        rel_match = re.match(
            r"\[([^\]]+)\]\s*-+>\s*\[([^\]]+)\]", stripped
        )
        if rel_match:
            source = rel_match.group(1).strip()
            target = rel_match.group(2).strip()
            rules.append(Rule(source=source, target=target))

            # Ensure both nodes are in contained_nodes
            if source not in contained_nodes:
                contained_nodes.append(source)
            if target not in contained_nodes:
                contained_nodes.append(target)
            continue

    return rules, contained_nodes
