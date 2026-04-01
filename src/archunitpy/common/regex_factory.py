"""Factory for creating Filter objects from glob patterns or regex."""

from __future__ import annotations

import fnmatch
import re

from archunitpy.common.types import Filter, Pattern, PatternMatchingOptions


def _glob_to_regex(pattern: str) -> re.Pattern[str]:
    """Convert a glob pattern to a compiled regex.

    Uses fnmatch.translate() which converts shell-style wildcards to regex.
    """
    regex_str = fnmatch.translate(pattern)
    return re.compile(regex_str)


def _escape_regex(s: str) -> str:
    """Escape special regex characters in a string."""
    return re.escape(s)


def _pattern_to_regex(pattern: Pattern) -> re.Pattern[str]:
    """Convert a Pattern (str glob or compiled regex) to a compiled regex."""
    if isinstance(pattern, re.Pattern):
        return pattern
    return _glob_to_regex(pattern)


class RegexFactory:
    """Factory for creating Filter objects from patterns."""

    @staticmethod
    def filename_matcher(name: Pattern) -> Filter:
        """Create a filter that matches against the filename only (no directory)."""
        return Filter(
            regexp=_pattern_to_regex(name),
            options=PatternMatchingOptions(target="filename"),
        )

    @staticmethod
    def classname_matcher(name: Pattern) -> Filter:
        """Create a filter that matches against class names."""
        return Filter(
            regexp=_pattern_to_regex(name),
            options=PatternMatchingOptions(target="classname"),
        )

    @staticmethod
    def folder_matcher(folder: Pattern) -> Filter:
        """Create a filter that matches against the directory path (no filename)."""
        return Filter(
            regexp=_pattern_to_regex(folder),
            options=PatternMatchingOptions(target="path-no-filename"),
        )

    @staticmethod
    def path_matcher(path: Pattern) -> Filter:
        """Create a filter that matches against the full file path."""
        return Filter(
            regexp=_pattern_to_regex(path),
            options=PatternMatchingOptions(target="path"),
        )

    @staticmethod
    def exact_file_matcher(file_path: str) -> Filter:
        """Create a filter that matches an exact file path."""
        normalized = file_path.replace("\\", "/")
        escaped = _escape_regex(normalized)
        regexp = re.compile(f"^{escaped}$")
        return Filter(
            regexp=regexp,
            options=PatternMatchingOptions(target="path"),
        )
