"""Fluent API builder chain for slice-level architecture rules.

Usage:
    project_slices('src/')
        .defined_by('src/(**)/')
        .should()
        .adhere_to_diagram(puml_content)
        .check()
"""

from __future__ import annotations

import re

from archunitpython.common.assertion.violation import Violation
from archunitpython.common.extraction.extract_graph import extract_graph
from archunitpython.common.fluentapi.checkable import CheckOptions
from archunitpython.common.projection.project_edges import project_edges
from archunitpython.common.projection.types import MapFunction
from archunitpython.slices.assertion.admissible_edges import (
    CoherenceOptions,
    gather_positive_violations,
    gather_violations,
)
from archunitpython.slices.projection.slicing_projections import (
    slice_by_pattern,
    slice_by_regex,
)
from archunitpython.slices.uml.generate_rules import Rule, generate_rule


def project_slices(project_path: str | None = None) -> "SliceConditionBuilder":
    """Entry point for slice-level architecture rules.

    Args:
        project_path: Root directory of the project to analyze.
    """
    return SliceConditionBuilder(project_path)


class SliceConditionBuilder:
    """Initial builder - define how files are grouped into slices."""

    def __init__(self, project_path: str | None = None) -> None:
        self._project_path = project_path
        self._pattern: str | None = None
        self._regex: re.Pattern[str] | None = None

    def defined_by(self, pattern: str) -> "SliceConditionBuilder":
        """Define slices using a path pattern with (**) placeholder.

        Example: 'src/(**)/' groups files by the directory after src/.
        """
        self._pattern = pattern
        return self

    def defined_by_regex(self, regex: re.Pattern[str]) -> "SliceConditionBuilder":
        """Define slices using a regex with a capture group."""
        self._regex = regex
        return self

    def should(self) -> "PositiveConditionBuilder":
        """Begin positive assertion (slices SHOULD ...)."""
        return PositiveConditionBuilder(
            self._project_path, self._pattern, self._regex
        )

    def should_not(self) -> "NegativeConditionBuilder":
        """Begin negative assertion (slices SHOULD NOT ...)."""
        return NegativeConditionBuilder(
            self._project_path, self._pattern, self._regex
        )


class PositiveConditionBuilder:
    """Positive assertion builder for slices."""

    def __init__(
        self,
        project_path: str | None,
        pattern: str | None,
        regex: re.Pattern[str] | None,
    ) -> None:
        self._project_path = project_path
        self._pattern = pattern
        self._regex = regex
        self._coherence_options = CoherenceOptions()

    def ignoring_orphan_slices(self) -> "PositiveConditionBuilder":
        """Ignore slices not declared in the diagram."""
        self._coherence_options = CoherenceOptions(
            ignore_orphan_slices=True,
            ignore_external_slices=self._coherence_options.ignore_external_slices,
        )
        return self

    def ignoring_external_slices(self) -> "PositiveConditionBuilder":
        """Ignore external dependency slices."""
        self._coherence_options = CoherenceOptions(
            ignore_orphan_slices=self._coherence_options.ignore_orphan_slices,
            ignore_external_slices=True,
        )
        return self

    def adhere_to_diagram(self, puml_content: str) -> "PositiveSliceCondition":
        """Assert that slices adhere to a PlantUML diagram."""
        return PositiveSliceCondition(
            self._project_path,
            self._pattern,
            self._regex,
            puml_content,
            self._coherence_options,
        )

    def adhere_to_diagram_in_file(self, file_path: str) -> "PositiveSliceCondition":
        """Assert that slices adhere to a diagram loaded from a file."""
        with open(file_path, "r", encoding="utf-8") as f:
            puml_content = f.read()
        return self.adhere_to_diagram(puml_content)


class NegativeConditionBuilder:
    """Negative assertion builder for slices."""

    def __init__(
        self,
        project_path: str | None,
        pattern: str | None,
        regex: re.Pattern[str] | None,
    ) -> None:
        self._project_path = project_path
        self._pattern = pattern
        self._regex = regex
        self._forbidden_deps: list[tuple[str, str]] = []

    def contain_dependency(
        self, source: str, target: str
    ) -> "NegativeSliceCondition":
        """Assert that a specific dependency should NOT exist."""
        return NegativeSliceCondition(
            self._project_path,
            self._pattern,
            self._regex,
            source,
            target,
        )


class PositiveSliceCondition:
    """Checkable that verifies slices adhere to a diagram."""

    def __init__(
        self,
        project_path: str | None,
        pattern: str | None,
        regex: re.Pattern[str] | None,
        puml_content: str,
        coherence_options: CoherenceOptions,
    ) -> None:
        self._project_path = project_path
        self._pattern = pattern
        self._regex = regex
        self._puml_content = puml_content
        self._coherence_options = coherence_options

    def check(self, options: CheckOptions | None = None) -> list[Violation]:
        graph = extract_graph(self._project_path, options=options)
        rules, contained_nodes = generate_rule(self._puml_content)

        mapper = self._get_mapper()
        edges = project_edges(graph, mapper)

        return gather_positive_violations(
            edges, rules, contained_nodes, self._coherence_options
        )

    def _get_mapper(self) -> MapFunction:
        if self._pattern:
            return slice_by_pattern(self._pattern)
        elif self._regex:
            return slice_by_regex(self._regex)
        from archunitpython.slices.projection.slicing_projections import identity

        return identity()


class NegativeSliceCondition:
    """Checkable that verifies a specific dependency does NOT exist."""

    def __init__(
        self,
        project_path: str | None,
        pattern: str | None,
        regex: re.Pattern[str] | None,
        source: str,
        target: str,
    ) -> None:
        self._project_path = project_path
        self._pattern = pattern
        self._regex = regex
        self._source = source
        self._target = target

    def check(self, options: CheckOptions | None = None) -> list[Violation]:
        graph = extract_graph(self._project_path, options=options)

        mapper = self._get_mapper()
        edges = project_edges(graph, mapper)

        forbidden_rule = Rule(source=self._source, target=self._target)
        return gather_violations(edges, [forbidden_rule])

    def _get_mapper(self) -> MapFunction:
        if self._pattern:
            return slice_by_pattern(self._pattern)
        elif self._regex:
            return slice_by_regex(self._regex)
        from archunitpython.slices.projection.slicing_projections import identity

        return identity()
