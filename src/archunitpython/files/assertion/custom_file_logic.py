"""Custom file condition logic and FileInfo type."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Callable

from archunitpython.common.assertion.violation import Violation
from archunitpython.common.pattern_matching import matches_pattern
from archunitpython.common.projection.types import ProjectedNode
from archunitpython.common.types import Filter


@dataclass(frozen=True)
class FileInfo:
    """Information about a file, provided to custom conditions."""

    path: str
    name: str  # filename without extension
    extension: str
    directory: str
    content: str
    lines_of_code: int


CustomFileCondition = Callable[[FileInfo], bool]


@dataclass
class CustomFileViolation(Violation):
    """A file that violates a custom condition."""

    message: str
    file_info: FileInfo


def _build_file_info(file_path: str) -> FileInfo:
    """Build a FileInfo from a file path."""
    basename = os.path.basename(file_path)
    name, ext = os.path.splitext(basename)
    directory = os.path.dirname(file_path)

    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except (OSError, IOError):
        content = ""

    lines = [line for line in content.splitlines() if line.strip()]

    return FileInfo(
        path=file_path,
        name=name,
        extension=ext,
        directory=directory,
        content=content,
        lines_of_code=len(lines),
    )


def gather_custom_file_violations(
    nodes: list[ProjectedNode],
    condition: CustomFileCondition,
    message: str,
    is_negated: bool,
    pre_filters: list[Filter],
) -> list[Violation]:
    """Evaluate a custom condition on files matching pre_filters.

    Args:
        nodes: All projected nodes.
        condition: Custom function that returns True if the file passes.
        message: Message to include in violation.
        is_negated: If False (should adhere), violation when condition returns False.
                    If True (shouldNot adhere), violation when condition returns True.
        pre_filters: Filters to apply before checking the condition.

    Returns:
        List of CustomFileViolation violations.
    """
    violations: list[Violation] = []

    for node in nodes:
        # Check if node matches all pre-filters
        if pre_filters and not all(
            matches_pattern(node.label, f) for f in pre_filters
        ):
            continue

        file_info = _build_file_info(node.label)
        result = condition(file_info)

        if is_negated:
            # shouldNot: violation if condition IS True
            if result:
                violations.append(
                    CustomFileViolation(message=message, file_info=file_info)
                )
        else:
            # should: violation if condition is NOT True
            if not result:
                violations.append(
                    CustomFileViolation(message=message, file_info=file_info)
                )

    return violations
