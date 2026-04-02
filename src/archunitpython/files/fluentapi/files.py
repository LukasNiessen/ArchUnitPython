"""Fluent API builder chain for file-level architecture rules.

Usage:
    project_files('src/')
        .in_folder('**/services/**')
        .should()
        .have_no_cycles()
        .check()
"""

from __future__ import annotations

from archunitpython.common.assertion.violation import EmptyTestViolation, Violation
from archunitpython.common.extraction.extract_graph import extract_graph
from archunitpython.common.fluentapi.checkable import CheckOptions
from archunitpython.common.pattern_matching import matches_all_patterns
from archunitpython.common.projection.edge_projections import per_internal_edge
from archunitpython.common.projection.project_cycles import project_cycles
from archunitpython.common.projection.project_edges import project_edges
from archunitpython.common.projection.project_nodes import project_to_nodes
from archunitpython.common.regex_factory import RegexFactory
from archunitpython.common.types import Filter, Pattern
from archunitpython.files.assertion.custom_file_logic import (
    CustomFileCondition,
    gather_custom_file_violations,
)
from archunitpython.files.assertion.cycle_free import gather_cycle_violations
from archunitpython.files.assertion.depend_on_files import gather_depend_on_file_violations
from archunitpython.files.assertion.matching_files import gather_regex_matching_violations


def project_files(project_path: str | None = None) -> "FileConditionBuilder":
    """Entry point for file-level architecture rules.

    Args:
        project_path: Root directory of the project to analyze.
            Defaults to current working directory.
    """
    return FileConditionBuilder(project_path)


# Alias
files = project_files


class FileConditionBuilder:
    """Initial builder for file rules - select files to apply rules to."""

    def __init__(self, project_path: str | None = None) -> None:
        self._project_path = project_path
        self._filters: list[Filter] = []

    def with_name(self, name: Pattern) -> "FilesShouldCondition":
        """Filter files by filename pattern."""
        self._filters.append(RegexFactory.filename_matcher(name))
        return FilesShouldCondition(self._project_path, list(self._filters))

    def in_folder(self, folder: Pattern) -> "FilesShouldCondition":
        """Filter files by folder pattern."""
        self._filters.append(RegexFactory.folder_matcher(folder))
        return FilesShouldCondition(self._project_path, list(self._filters))

    def in_path(self, path: Pattern) -> "FilesShouldCondition":
        """Filter files by full path pattern."""
        self._filters.append(RegexFactory.path_matcher(path))
        return FilesShouldCondition(self._project_path, list(self._filters))

    def should(self) -> "PositiveMatchPatternFileConditionBuilder":
        """Begin positive assertion (files SHOULD ...)."""
        return PositiveMatchPatternFileConditionBuilder(
            self._project_path, list(self._filters)
        )

    def should_not(self) -> "NegatedMatchPatternFileConditionBuilder":
        """Begin negative assertion (files SHOULD NOT ...)."""
        return NegatedMatchPatternFileConditionBuilder(
            self._project_path, list(self._filters)
        )


class FilesShouldCondition:
    """Intermediate builder that allows adding more filters or moving to assertions."""

    def __init__(self, project_path: str | None, filters: list[Filter]) -> None:
        self._project_path = project_path
        self._filters = filters

    def with_name(self, name: Pattern) -> "FilesShouldCondition":
        """Add a filename pattern filter."""
        self._filters.append(RegexFactory.filename_matcher(name))
        return self

    def in_folder(self, folder: Pattern) -> "FilesShouldCondition":
        """Add a folder pattern filter."""
        self._filters.append(RegexFactory.folder_matcher(folder))
        return self

    def in_path(self, path: Pattern) -> "FilesShouldCondition":
        """Add a full path pattern filter."""
        self._filters.append(RegexFactory.path_matcher(path))
        return self

    def should(self) -> "PositiveMatchPatternFileConditionBuilder":
        """Begin positive assertion (files SHOULD ...)."""
        return PositiveMatchPatternFileConditionBuilder(
            self._project_path, list(self._filters)
        )

    def should_not(self) -> "NegatedMatchPatternFileConditionBuilder":
        """Begin negative assertion (files SHOULD NOT ...)."""
        return NegatedMatchPatternFileConditionBuilder(
            self._project_path, list(self._filters)
        )


class PositiveMatchPatternFileConditionBuilder:
    """Positive assertion builder - files SHOULD have certain properties."""

    def __init__(self, project_path: str | None, filters: list[Filter]) -> None:
        self._project_path = project_path
        self._filters = filters

    def have_no_cycles(self) -> "CycleFreeFileCondition":
        """Assert that files have no circular dependencies."""
        return CycleFreeFileCondition(self._project_path, self._filters)

    def depend_on_files(self) -> "DependOnFileConditionBuilder":
        """Begin dependency assertion - files SHOULD depend on ..."""
        return DependOnFileConditionBuilder(
            self._project_path, self._filters, is_negated=False
        )

    def be_in_folder(self, folder: Pattern) -> "MatchPatternFileCondition":
        """Assert that files are in a certain folder."""
        return MatchPatternFileCondition(
            self._project_path,
            self._filters,
            [RegexFactory.folder_matcher(folder)],
            is_negated=False,
        )

    def have_name(self, name: Pattern) -> "MatchPatternFileCondition":
        """Assert that files match a name pattern."""
        return MatchPatternFileCondition(
            self._project_path,
            self._filters,
            [RegexFactory.filename_matcher(name)],
            is_negated=False,
        )

    def be_in_path(self, path: Pattern) -> "MatchPatternFileCondition":
        """Assert that files match a path pattern."""
        return MatchPatternFileCondition(
            self._project_path,
            self._filters,
            [RegexFactory.path_matcher(path)],
            is_negated=False,
        )

    def adhere_to(
        self, condition: CustomFileCondition, message: str
    ) -> "CustomFileCheckableCondition":
        """Assert that files satisfy a custom condition."""
        return CustomFileCheckableCondition(
            self._project_path, self._filters, condition, message, is_negated=False
        )


class NegatedMatchPatternFileConditionBuilder:
    """Negative assertion builder - files SHOULD NOT have certain properties."""

    def __init__(self, project_path: str | None, filters: list[Filter]) -> None:
        self._project_path = project_path
        self._filters = filters

    def depend_on_files(self) -> "DependOnFileConditionBuilder":
        """Begin dependency assertion - files SHOULD NOT depend on ..."""
        return DependOnFileConditionBuilder(
            self._project_path, self._filters, is_negated=True
        )

    def be_in_folder(self, folder: Pattern) -> "MatchPatternFileCondition":
        """Assert that files are NOT in a certain folder."""
        return MatchPatternFileCondition(
            self._project_path,
            self._filters,
            [RegexFactory.folder_matcher(folder)],
            is_negated=True,
        )

    def have_name(self, name: Pattern) -> "MatchPatternFileCondition":
        """Assert that files do NOT match a name pattern."""
        return MatchPatternFileCondition(
            self._project_path,
            self._filters,
            [RegexFactory.filename_matcher(name)],
            is_negated=True,
        )

    def be_in_path(self, path: Pattern) -> "MatchPatternFileCondition":
        """Assert that files do NOT match a path pattern."""
        return MatchPatternFileCondition(
            self._project_path,
            self._filters,
            [RegexFactory.path_matcher(path)],
            is_negated=True,
        )

    def adhere_to(
        self, condition: CustomFileCondition, message: str
    ) -> "CustomFileCheckableCondition":
        """Assert that files do NOT satisfy a custom condition."""
        return CustomFileCheckableCondition(
            self._project_path, self._filters, condition, message, is_negated=True
        )


class DependOnFileConditionBuilder:
    """Configure dependency target patterns."""

    def __init__(
        self, project_path: str | None, filters: list[Filter], is_negated: bool
    ) -> None:
        self._project_path = project_path
        self._filters = filters
        self._is_negated = is_negated
        self._object_filters: list[Filter] = []

    def with_name(self, name: Pattern) -> "DependOnFileCondition":
        """Target files matching a name pattern."""
        self._object_filters.append(RegexFactory.filename_matcher(name))
        return DependOnFileCondition(
            self._project_path,
            self._filters,
            list(self._object_filters),
            self._is_negated,
        )

    def in_folder(self, folder: Pattern) -> "DependOnFileCondition":
        """Target files in a folder pattern."""
        self._object_filters.append(RegexFactory.folder_matcher(folder))
        return DependOnFileCondition(
            self._project_path,
            self._filters,
            list(self._object_filters),
            self._is_negated,
        )

    def in_path(self, path: Pattern) -> "DependOnFileCondition":
        """Target files matching a path pattern."""
        self._object_filters.append(RegexFactory.path_matcher(path))
        return DependOnFileCondition(
            self._project_path,
            self._filters,
            list(self._object_filters),
            self._is_negated,
        )


def _get_filtered_nodes(project_path, filters, options):
    """Extract graph and get nodes matching filters."""
    graph = extract_graph(project_path, options=options)
    nodes = project_to_nodes(graph)
    if not filters:
        return nodes
    return [n for n in nodes if matches_all_patterns(n.label, filters)]


def _check_empty_test(filtered_items, filters, is_negated, options):
    """Check for empty test condition."""
    if not filtered_items and not (options and options.allow_empty_tests):
        return [
            EmptyTestViolation(
                filters=filters,
                message="No files found matching the specified patterns",
                is_negated=is_negated,
            )
        ]
    return None


class CycleFreeFileCondition:
    """Checkable that verifies no cycles exist among filtered files."""

    def __init__(self, project_path: str | None, filters: list[Filter]) -> None:
        self._project_path = project_path
        self._filters = filters

    def check(self, options: CheckOptions | None = None) -> list[Violation]:
        graph = extract_graph(self._project_path, options=options)
        edges = project_edges(graph, per_internal_edge())

        # Filter edges to only those involving our filtered files
        if self._filters:
            edges = [
                e
                for e in edges
                if matches_all_patterns(e.source_label, self._filters)
                and matches_all_patterns(e.target_label, self._filters)
            ]

        empty = _check_empty_test(edges, self._filters, False, options)
        if empty is not None:
            return empty

        cycles = project_cycles(edges)
        return gather_cycle_violations(cycles)


class DependOnFileCondition:
    """Checkable that verifies file dependency rules."""

    def __init__(
        self,
        project_path: str | None,
        subject_filters: list[Filter],
        object_filters: list[Filter],
        is_negated: bool,
    ) -> None:
        self._project_path = project_path
        self._subject_filters = subject_filters
        self._object_filters = object_filters
        self._is_negated = is_negated

    def check(self, options: CheckOptions | None = None) -> list[Violation]:
        graph = extract_graph(self._project_path, options=options)
        edges = project_edges(graph, per_internal_edge())

        return gather_depend_on_file_violations(
            edges,
            self._subject_filters,
            self._object_filters,
            self._is_negated,
        )


class MatchPatternFileCondition:
    """Checkable that verifies files match/don't match patterns."""

    def __init__(
        self,
        project_path: str | None,
        pre_filters: list[Filter],
        check_filters: list[Filter],
        is_negated: bool,
    ) -> None:
        self._project_path = project_path
        self._pre_filters = pre_filters
        self._check_filters = check_filters
        self._is_negated = is_negated

    def check(self, options: CheckOptions | None = None) -> list[Violation]:
        nodes = _get_filtered_nodes(self._project_path, self._pre_filters, options)

        empty = _check_empty_test(nodes, self._pre_filters, self._is_negated, options)
        if empty is not None:
            return empty

        return gather_regex_matching_violations(
            nodes, self._check_filters, self._is_negated
        )


class CustomFileCheckableCondition:
    """Checkable that evaluates a custom condition on files."""

    def __init__(
        self,
        project_path: str | None,
        filters: list[Filter],
        condition: CustomFileCondition,
        message: str,
        is_negated: bool,
    ) -> None:
        self._project_path = project_path
        self._filters = filters
        self._condition = condition
        self._message = message
        self._is_negated = is_negated

    def check(self, options: CheckOptions | None = None) -> list[Violation]:
        graph = extract_graph(self._project_path, options=options)
        nodes = project_to_nodes(graph)

        return gather_custom_file_violations(
            nodes,
            self._condition,
            self._message,
            self._is_negated,
            self._filters,
        )
