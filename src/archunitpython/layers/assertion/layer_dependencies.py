"""Violation gathering for layer dependency rules."""

from __future__ import annotations

from dataclasses import dataclass

from archunitpython.common.assertion.violation import Violation
from archunitpython.common.pattern_matching import matches_pattern
from archunitpython.common.projection.types import ProjectedEdge
from archunitpython.common.types import Filter


@dataclass
class LayerDependencyViolation(Violation):
    """A dependency from one named layer to a disallowed named layer."""

    dependency: ProjectedEdge
    source_layer: str
    target_layer: str
    rule: str


@dataclass(frozen=True)
class LayerDefinition:
    """A named architectural layer with one or more file filters."""

    name: str
    filters: tuple[Filter, ...]

    def matches(self, file_path: str) -> bool:
        return any(matches_pattern(file_path, filter_) for filter_ in self.filters)


def gather_layer_dependency_violations(
    edges: list[ProjectedEdge],
    layers: list[LayerDefinition],
    allowed_dependencies: dict[str, set[str]],
    forbidden_dependencies: dict[str, set[str]],
) -> list[Violation]:
    """Check cross-layer dependencies against allowlist/blocklist rules."""
    violations: list[Violation] = []

    for edge in edges:
        source_layer = _find_layer(edge.source_label, layers)
        target_layer = _find_layer(edge.target_label, layers)

        if source_layer is None or target_layer is None:
            continue
        if source_layer == target_layer:
            continue

        forbidden_targets = forbidden_dependencies.get(source_layer, set())
        if target_layer in forbidden_targets:
            violations.append(
                LayerDependencyViolation(
                    dependency=edge,
                    source_layer=source_layer,
                    target_layer=target_layer,
                    rule="may_not_depend_on_layers",
                )
            )
            continue

        if source_layer in allowed_dependencies:
            allowed_targets = allowed_dependencies[source_layer]
            if target_layer not in allowed_targets:
                violations.append(
                    LayerDependencyViolation(
                        dependency=edge,
                        source_layer=source_layer,
                        target_layer=target_layer,
                        rule="may_only_depend_on_layers",
                    )
                )

    return violations


def _find_layer(file_path: str, layers: list[LayerDefinition]) -> str | None:
    for layer in layers:
        if layer.matches(file_path):
            return layer.name
    return None
