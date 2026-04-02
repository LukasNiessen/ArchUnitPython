"""Pattern matching functions for file paths and class names."""

from __future__ import annotations

from archunitpython.common.types import Filter


def normalize_path(path: str) -> str:
    """Normalize a file path by converting backslashes to forward slashes."""
    return path.replace("\\", "/")


def extract_filename(file_path: str) -> str:
    """Extract the filename from a file path."""
    normalized = normalize_path(file_path)
    parts = normalized.split("/")
    return parts[-1] if parts else file_path


def path_without_filename(file_path: str) -> str:
    """Extract the directory portion of a file path (without the filename)."""
    normalized = normalize_path(file_path)
    parts = normalized.split("/")
    if len(parts) > 1:
        parts.pop()
        return "/".join(parts)
    return ""


def matches_pattern(file_path: str, filter_: Filter) -> bool:
    """Check if a file path matches a single filter.

    The filter's target option determines which part of the path is tested:
    - 'filename': only the filename
    - 'path': the full normalized path
    - 'path-no-filename': the directory portion only
    - 'classname': not applicable for file paths (always uses full path)
    """
    target = filter_.options.target

    if target == "filename":
        target_string = extract_filename(file_path)
    elif target == "path":
        target_string = normalize_path(file_path)
    elif target == "path-no-filename":
        target_string = path_without_filename(file_path)
    else:
        target_string = normalize_path(file_path)

    return bool(filter_.regexp.search(target_string))


def matches_pattern_classname(
    class_name: str, file_path: str, filter_: Filter
) -> bool:
    """Check if a class/file matches a filter, supporting classname target."""
    target = filter_.options.target

    if target == "classname":
        target_string = class_name
    elif target == "filename":
        target_string = extract_filename(file_path)
    elif target == "path":
        target_string = normalize_path(file_path)
    elif target == "path-no-filename":
        target_string = path_without_filename(file_path)
    else:
        target_string = normalize_path(file_path)

    return bool(filter_.regexp.search(target_string))


def matches_all_patterns(file_path: str, filters: list[Filter]) -> bool:
    """Check if a file path matches ALL filters (AND logic)."""
    return all(matches_pattern(file_path, f) for f in filters)


def matches_any_pattern(file_path: str, filters: list[Filter]) -> bool:
    """Check if a file path matches ANY filter (OR logic)."""
    return any(matches_pattern(file_path, f) for f in filters)
