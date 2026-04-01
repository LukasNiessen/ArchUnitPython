"""Extract dependency graph from Python projects using AST analysis."""

from __future__ import annotations

import ast
import os
import sys
from pathlib import Path

from archunitpy.common.extraction.graph import Edge, Graph, ImportKind
from archunitpy.common.fluentapi.checkable import CheckOptions

_graph_cache: dict[str, Graph] = {}

_DEFAULT_EXCLUDE = [
    "__pycache__",
    ".venv",
    "venv",
    ".env",
    "node_modules",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "dist",
    "build",
    "*.egg-info",
]


def clear_graph_cache(options: CheckOptions | None = None) -> None:
    """Clear the cached dependency graphs."""
    _graph_cache.clear()


def extract_graph(
    project_path: str | None = None,
    *,
    exclude_patterns: list[str] | None = None,
    options: CheckOptions | None = None,
) -> Graph:
    """Extract a dependency graph from a Python project.

    Scans all .py files in the project directory, parses their imports,
    and resolves them to build a list of Edge objects.

    Args:
        project_path: Root directory of the project to analyze.
            Defaults to current working directory.
        exclude_patterns: Directory/file names to exclude.
            Defaults to common non-source directories.
        options: Check options (supports clear_cache).

    Returns:
        List of Edge objects representing import relationships.
    """
    if project_path is None:
        project_path = os.getcwd()

    project_path = os.path.abspath(project_path)
    cache_key = project_path

    if options and options.clear_cache:
        _graph_cache.pop(cache_key, None)

    if cache_key in _graph_cache:
        return _graph_cache[cache_key]

    result = _extract_graph_uncached(project_path, exclude_patterns)
    _graph_cache[cache_key] = result
    return result


def _extract_graph_uncached(
    project_path: str,
    exclude_patterns: list[str] | None = None,
) -> Graph:
    """Extract graph without caching."""
    excludes = exclude_patterns if exclude_patterns is not None else _DEFAULT_EXCLUDE
    py_files = _find_python_files(project_path, excludes)

    edges: list[Edge] = []
    py_files_set = set(py_files)

    for file_path in py_files:
        # Add self-referencing edge (ensures the file appears as a node)
        edges.append(
            Edge(
                source=_normalize(file_path),
                target=_normalize(file_path),
                external=False,
            )
        )

        # Extract and resolve imports
        imports = _extract_imports(file_path)
        for module_name, import_kind in imports:
            resolved, is_external = _resolve_import(
                module_name, file_path, project_path, import_kind
            )
            if resolved and resolved != _normalize(file_path):
                # Check if the resolved path is in our project
                if not is_external and resolved not in {
                    _normalize(f) for f in py_files_set
                }:
                    is_external = True

                edges.append(
                    Edge(
                        source=_normalize(file_path),
                        target=resolved,
                        external=is_external,
                        import_kinds=(import_kind,),
                    )
                )

    return _merge_edges(edges)


def _normalize(path: str) -> str:
    """Normalize a file path to use forward slashes."""
    return path.replace("\\", "/")


def _find_python_files(root: str, exclude: list[str]) -> list[str]:
    """Recursively find all .py files, excluding specified patterns."""
    py_files: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        # Filter out excluded directories in-place
        dirnames[:] = [
            d
            for d in dirnames
            if not _should_exclude(d, exclude)
        ]

        for filename in filenames:
            if filename.endswith(".py") and not _should_exclude(filename, exclude):
                full_path = os.path.join(dirpath, filename)
                py_files.append(os.path.abspath(full_path))

    return py_files


def _should_exclude(name: str, patterns: list[str]) -> bool:
    """Check if a name matches any exclude pattern."""
    import fnmatch

    for pattern in patterns:
        if fnmatch.fnmatch(name, pattern):
            return True
    return False


def _extract_imports(file_path: str) -> list[tuple[str, ImportKind]]:
    """Parse a Python file and extract all import statements.

    Returns list of (module_name, import_kind) tuples.
    """
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            source = f.read()
    except (OSError, IOError):
        return []

    try:
        tree = ast.parse(source, filename=file_path)
    except SyntaxError:
        return []

    imports: list[tuple[str, ImportKind]] = []
    type_checking_ranges = _find_type_checking_ranges(tree)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            is_type = _in_type_checking(node, type_checking_ranges)
            kind = ImportKind.TYPE_IMPORT if is_type else ImportKind.IMPORT
            for alias in node.names:
                imports.append((alias.name, kind))

        elif isinstance(node, ast.ImportFrom):
            is_type = _in_type_checking(node, type_checking_ranges)
            if node.level and node.level > 0:
                # Relative import
                kind = ImportKind.TYPE_IMPORT if is_type else ImportKind.RELATIVE_IMPORT
                module = node.module or ""
                dots = "." * node.level
                imports.append((f"{dots}{module}", kind))
            else:
                kind = ImportKind.TYPE_IMPORT if is_type else ImportKind.FROM_IMPORT
                if node.module:
                    imports.append((node.module, kind))

    return imports


def _find_type_checking_ranges(tree: ast.Module) -> list[tuple[int, int]]:
    """Find line ranges of TYPE_CHECKING blocks."""
    ranges: list[tuple[int, int]] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            # Check for `if TYPE_CHECKING:` pattern
            test = node.test
            is_type_checking = False

            if isinstance(test, ast.Name) and test.id == "TYPE_CHECKING":
                is_type_checking = True
            elif isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING":
                is_type_checking = True

            if is_type_checking and node.body:
                start = node.body[0].lineno
                end = max(
                    getattr(n, "end_lineno", n.lineno)
                    for n in node.body
                    if hasattr(n, "lineno")
                )
                ranges.append((start, end))

    return ranges


def _in_type_checking(
    node: ast.AST, ranges: list[tuple[int, int]]
) -> bool:
    """Check if a node is inside a TYPE_CHECKING block."""
    if not hasattr(node, "lineno"):
        return False
    lineno = node.lineno
    return any(start <= lineno <= end for start, end in ranges)


def _resolve_import(
    import_name: str,
    source_file: str,
    project_root: str,
    kind: ImportKind,
) -> tuple[str, bool]:
    """Resolve an import name to an absolute file path.

    Returns (resolved_path, is_external).
    The path is normalized with forward slashes.
    """
    if kind in (ImportKind.RELATIVE_IMPORT, ImportKind.TYPE_IMPORT) and import_name.startswith("."):
        # Relative import
        return _resolve_relative_import(import_name, source_file, project_root)

    # Absolute import: try to resolve within the project
    return _resolve_absolute_import(import_name, project_root)


def _resolve_relative_import(
    import_name: str,
    source_file: str,
    project_root: str,
) -> tuple[str, bool]:
    """Resolve a relative import (starts with dots)."""
    # Count dots
    dots = 0
    for ch in import_name:
        if ch == ".":
            dots += 1
        else:
            break

    module_part = import_name[dots:]

    # Navigate up from the source file's directory
    source_dir = os.path.dirname(os.path.abspath(source_file))
    for _ in range(dots - 1):  # -1 because first dot = current package
        source_dir = os.path.dirname(source_dir)

    if module_part:
        parts = module_part.split(".")
        candidate_base = os.path.join(source_dir, *parts)
    else:
        candidate_base = source_dir

    # Try file.py first, then package/__init__.py
    for candidate in [
        candidate_base + ".py",
        os.path.join(candidate_base, "__init__.py"),
    ]:
        if os.path.isfile(candidate):
            return _normalize(os.path.abspath(candidate)), False

    return _normalize(candidate_base + ".py"), True


def _resolve_absolute_import(
    import_name: str,
    project_root: str,
) -> tuple[str, bool]:
    """Resolve an absolute import within the project."""
    parts = import_name.split(".")

    # Try progressively longer paths within the project
    # e.g., for 'foo.bar.baz', try:
    #   foo/bar/baz.py, foo/bar/baz/__init__.py
    #   foo/bar.py (baz might be an attribute)
    #   foo/__init__.py (bar.baz might be attributes)

    for i in range(len(parts), 0, -1):
        path_parts = parts[:i]
        candidate_base = os.path.join(project_root, *path_parts)

        # Try as a module file
        candidate_file = candidate_base + ".py"
        if os.path.isfile(candidate_file):
            return _normalize(os.path.abspath(candidate_file)), False

        # Try as a package
        candidate_init = os.path.join(candidate_base, "__init__.py")
        if os.path.isfile(candidate_init):
            return _normalize(os.path.abspath(candidate_init)), False

    # Not found in project → external
    return import_name, True


def _merge_edges(edges: list[Edge]) -> list[Edge]:
    """Merge edges with same source and target, combining import kinds."""
    edge_map: dict[tuple[str, str], Edge] = {}

    for edge in edges:
        key = (edge.source, edge.target)
        if key in edge_map:
            existing = edge_map[key]
            combined_kinds = set(existing.import_kinds) | set(edge.import_kinds)
            edge_map[key] = Edge(
                source=edge.source,
                target=edge.target,
                external=edge.external,
                import_kinds=tuple(sorted(combined_kinds, key=lambda k: k.value)),
            )
        else:
            edge_map[key] = edge

    return list(edge_map.values())
