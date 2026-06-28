"""Fluent API builder chain for layer-level architecture rules."""

from __future__ import annotations

from archunitpython.common.assertion.violation import Violation
from archunitpython.common.extraction.extract_graph import extract_graph
from archunitpython.common.fluentapi.checkable import CheckOptions
from archunitpython.common.projection.edge_projections import per_internal_edge
from archunitpython.common.projection.project_edges import project_edges
from archunitpython.common.regex_factory import RegexFactory
from archunitpython.common.types import Filter, Pattern
from archunitpython.layers.assertion.layer_dependencies import (
    LayerDefinition,
    gather_layer_dependency_violations,
)


def project_layers(project_path: str | None = None) -> "LayeredArchitecture":
    """Entry point for layer-level architecture rules."""
    return LayeredArchitecture(project_path)


layers = project_layers


class LayeredArchitecture:
    """Builder and checkable for named layer dependency policies."""

    def __init__(self, project_path: str | None = None) -> None:
        self._project_path = project_path
        self._layers: dict[str, list[Filter]] = {}
        self._allowed_dependencies: dict[str, set[str]] = {}
        self._forbidden_dependencies: dict[str, set[str]] = {}

    def layer(self, name: str) -> "LayerDefinitionBuilder":
        """Start defining a named layer."""
        self._layers.setdefault(name, [])
        return LayerDefinitionBuilder(self, name)

    def where_layer(self, name: str) -> "LayerDependencyRuleBuilder":
        """Start defining dependency rules for a named layer."""
        self._layers.setdefault(name, [])
        return LayerDependencyRuleBuilder(self, name)

    def check(self, options: CheckOptions | None = None) -> list[Violation]:
        graph = extract_graph(self._project_path, options=options)
        edges = project_edges(graph, per_internal_edge())
        layer_definitions = [
            LayerDefinition(name=name, filters=tuple(filters))
            for name, filters in self._layers.items()
            if filters
        ]

        return gather_layer_dependency_violations(
            edges,
            layer_definitions,
            self._allowed_dependencies,
            self._forbidden_dependencies,
        )

    def _add_layer_filter(self, name: str, filter_: Filter) -> None:
        self._layers.setdefault(name, []).append(filter_)

    def _allow_only(self, source_layer: str, target_layers: tuple[str, ...]) -> None:
        self._allowed_dependencies[source_layer] = set(target_layers)

    def _forbid(self, source_layer: str, target_layers: tuple[str, ...]) -> None:
        self._forbidden_dependencies.setdefault(source_layer, set()).update(target_layers)


class LayerDefinitionBuilder:
    """Configure the file patterns that make up one layer."""

    def __init__(self, architecture: LayeredArchitecture, layer_name: str) -> None:
        self._architecture = architecture
        self._layer_name = layer_name

    def defined_by(self, path: Pattern) -> LayeredArchitecture:
        """Define this layer by a full path pattern."""
        self._architecture._add_layer_filter(
            self._layer_name,
            RegexFactory.path_matcher(path),
        )
        return self._architecture

    def defined_by_folder(self, folder: Pattern) -> LayeredArchitecture:
        """Define this layer by a folder pattern."""
        self._architecture._add_layer_filter(
            self._layer_name,
            RegexFactory.folder_matcher(folder),
        )
        return self._architecture


class LayerDependencyRuleBuilder:
    """Configure allowed or forbidden dependencies for one layer."""

    def __init__(self, architecture: LayeredArchitecture, layer_name: str) -> None:
        self._architecture = architecture
        self._layer_name = layer_name

    def may_only_depend_on_layers(
        self,
        *layer_names: str,
    ) -> LayeredArchitecture:
        """Allow this layer to depend only on the listed other layers."""
        self._architecture._allow_only(self._layer_name, layer_names)
        return self._architecture

    def may_not_depend_on_layers(
        self,
        *layer_names: str,
    ) -> LayeredArchitecture:
        """Forbid this layer from depending on the listed other layers."""
        self._architecture._forbid(self._layer_name, layer_names)
        return self._architecture
