"""Slicing projection functions that extract slice names from file paths."""

from __future__ import annotations

import re

from archunitpy.common.extraction.graph import Edge
from archunitpy.common.pattern_matching import normalize_path
from archunitpy.common.projection.types import MapFunction, MappedEdge


def identity() -> MapFunction:
    """No-op mapper - uses full paths as labels."""

    def mapper(edge: Edge) -> MappedEdge | None:
        if edge.source == edge.target:
            return None
        return MappedEdge(source_label=edge.source, target_label=edge.target)

    return mapper


def slice_by_pattern(pattern: str) -> MapFunction:
    """Create a mapper that extracts slice names from paths using a pattern.

    The pattern uses (**) as a placeholder for the slice name.
    Example: 'src/(**)/' with 'src/auth/service.py' extracts 'auth'.

    Args:
        pattern: A pattern string containing (**) as the slice capture group.
    """
    # Convert the pattern to regex:
    # - Escape special regex chars except (**)
    # - Replace (**) with a capture group
    escaped = _escape_for_regexp(pattern)
    regex_str = escaped.replace(r"\(\*\*\)", "([^/]+)")
    # Replace remaining ** with .* and * with [^/]*
    regex_str = regex_str.replace(r"\*\*", ".*").replace(r"\*", "[^/]*")
    regex = re.compile(regex_str)

    def mapper(edge: Edge) -> MappedEdge | None:
        if edge.external or edge.source == edge.target:
            return None

        source_label = _extract_slice(normalize_path(edge.source), regex)
        target_label = _extract_slice(normalize_path(edge.target), regex)

        if source_label is None or target_label is None:
            return None
        if source_label == target_label:
            return None

        return MappedEdge(source_label=source_label, target_label=target_label)

    return mapper


def slice_by_regex(regexp: re.Pattern[str]) -> MapFunction:
    """Create a mapper that extracts slice names using a regex with a capture group.

    The first capture group in the regex becomes the slice name.
    """

    def mapper(edge: Edge) -> MappedEdge | None:
        if edge.external or edge.source == edge.target:
            return None

        source_label = _extract_slice(normalize_path(edge.source), regexp)
        target_label = _extract_slice(normalize_path(edge.target), regexp)

        if source_label is None or target_label is None:
            return None
        if source_label == target_label:
            return None

        return MappedEdge(source_label=source_label, target_label=target_label)

    return mapper


def slice_by_file_suffix(labeling: dict[str, str]) -> MapFunction:
    """Create a mapper that assigns slices based on file name suffixes.

    Args:
        labeling: Mapping of suffix → slice name.
            Example: {'_controller': 'controllers', '_service': 'services'}
    """

    def mapper(edge: Edge) -> MappedEdge | None:
        if edge.external or edge.source == edge.target:
            return None

        source_label = _extract_suffix_label(edge.source, labeling)
        target_label = _extract_suffix_label(edge.target, labeling)

        if source_label is None or target_label is None:
            return None
        if source_label == target_label:
            return None

        return MappedEdge(source_label=source_label, target_label=target_label)

    return mapper


def _extract_slice(path: str, regex: re.Pattern[str]) -> str | None:
    """Extract slice name from path using regex first capture group."""
    match = regex.search(path)
    if match and match.groups():
        return match.group(1)
    return None


def _extract_suffix_label(path: str, labeling: dict[str, str]) -> str | None:
    """Extract label by matching file suffix."""
    normalized = normalize_path(path)
    # Remove extension
    base = normalized.rsplit(".", 1)[0] if "." in normalized else normalized

    for suffix, label in labeling.items():
        if base.endswith(suffix):
            return label
    return None


def _escape_for_regexp(pattern: str) -> str:
    """Escape special regex characters in a pattern string."""
    return re.escape(pattern)
