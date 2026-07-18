"""Extract dependency graph from Python projects using AST analysis."""

from __future__ import annotations

import ast
import os
import re
from dataclasses import dataclass

from archunitpython.common.extraction.graph import Edge, Graph, ImportKind
from archunitpython.common.fluentapi.checkable import CheckOptions

GraphCacheKey = tuple[str, tuple[str, ...], bool]

_graph_cache: dict[GraphCacheKey, Graph] = {}

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

_ARCHIGNORE_FILE = ".archignore"

_IGNORE_DIRECTIVE_REGEX = re.compile(
    r"#\s*archunit(?::|-)\s*ignore"
    r"(?:\([^)]*\))?"
    r"(?P<modules>(?:\s+[\w.]+)*)\s*$"
)


@dataclass(frozen=True)
class _LocatedImport:
    module_name: str
    import_kind: ImportKind
    line_number: int
    resolution_kind: ImportKind | None = None


@dataclass(frozen=True)
class _IgnoreDirective:
    line_number: int
    modules: tuple[str, ...] = ()

    def matches(self, import_: _LocatedImport) -> bool:
        if not self.modules:
            return True
        return any(
            import_.module_name == module
            or import_.module_name.startswith(f"{module}.")
            for module in self.modules
        )


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
    excludes = _resolve_exclude_patterns(project_path, exclude_patterns)
    ignore_type_checking_imports = bool(options and options.ignore_type_checking_imports)
    cache_key = _build_cache_key(project_path, excludes, ignore_type_checking_imports)

    if options and options.clear_cache:
        _graph_cache.pop(cache_key, None)

    if cache_key in _graph_cache:
        return _graph_cache[cache_key]

    result = _extract_graph_uncached(
        project_path,
        excludes,
        ignore_type_checking_imports=ignore_type_checking_imports,
    )
    _graph_cache[cache_key] = result
    return result


def _build_cache_key(
    project_path: str,
    exclude_patterns: list[str],
    ignore_type_checking_imports: bool,
) -> GraphCacheKey:
    """Build a stable cache key for graph extraction options."""
    return (
        project_path,
        tuple(sorted(exclude_patterns)),
        ignore_type_checking_imports,
    )


def _resolve_exclude_patterns(
    project_path: str,
    exclude_patterns: list[str] | None,
) -> list[str]:
    """Resolve exclude patterns (explicit or defaults) plus any .archignore patterns."""
    excludes = list(exclude_patterns) if exclude_patterns is not None else list(_DEFAULT_EXCLUDE)
    excludes.extend(_load_archignore_patterns(project_path))
    return excludes


def _load_archignore_patterns(project_path: str) -> list[str]:
    """Load .archignore patterns from a project root, if present."""
    archignore_path = os.path.join(project_path, _ARCHIGNORE_FILE)
    try:
        with open(archignore_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except OSError:
        return []

    patterns: list[str] = []
    for line in lines:
        pattern = line.strip()
        if not pattern or pattern.startswith("#"):
            continue
        patterns.append(pattern)
    return patterns


def _extract_graph_uncached(
    project_path: str,
    exclude_patterns: list[str],
    *,
    ignore_type_checking_imports: bool = False,
) -> Graph:
    """Extract graph without caching."""
    py_files = _find_python_files(project_path, exclude_patterns)

    edges: list[Edge] = []
    py_files_set = set(py_files)
    normalized_py_file_set = {_normalize(f) for f in py_files_set}

    for file_path in py_files:
        # Add self-referencing edge (ensures the file appears as a node)
        edges.append(
            Edge(
                source=_normalize(file_path),
                target=_normalize(file_path),
                external=False,
            )
        )

        imports = _extract_located_imports(file_path)
        for located_import in imports:
            module_name = located_import.module_name
            import_kind = located_import.import_kind
            if (
                ignore_type_checking_imports
                and import_kind == ImportKind.TYPE_IMPORT
            ):
                continue
            resolution_kind = located_import.resolution_kind or import_kind
            resolved, is_external = _resolve_import(
                module_name, file_path, project_path, resolution_kind
            )
            if resolved and resolved != _normalize(file_path):
                # Check if the resolved path is in our project
                if not is_external and resolved not in normalized_py_file_set:
                    continue

                edges.append(
                    Edge(
                        source=_normalize(file_path),
                        target=resolved,
                        external=is_external,
                        import_kinds=_edge_import_kinds(located_import),
                    )
                )

    return _merge_edges(edges)


def _normalize(path: str) -> str:
    """Normalize a file path to use forward slashes."""
    return path.replace("\\", "/")


def _find_python_files(root: str, exclude: list[str]) -> list[str]:
    """Recursively find all .py files, excluding specified patterns."""
    py_files: list[str] = []
    root = os.path.abspath(root)
    for dirpath, dirnames, filenames in os.walk(root):
        # Filter out excluded directories in-place
        dirnames[:] = [
            d
            for d in dirnames
            if not _should_exclude_path(os.path.join(dirpath, d), root, exclude, is_dir=True)
        ]

        for filename in filenames:
            full_path = os.path.join(dirpath, filename)
            if filename.endswith(".py") and not _should_exclude_path(
                full_path, root, exclude, is_dir=False
            ):
                py_files.append(os.path.abspath(full_path))

    return py_files


def _should_exclude_path(
    path: str,
    root: str,
    patterns: list[str],
    *,
    is_dir: bool,
) -> bool:
    """Check if a path matches any exclude pattern."""
    import fnmatch

    rel_path = _normalize(os.path.relpath(path, root))
    name = os.path.basename(path)

    for raw_pattern in patterns:
        pattern = raw_pattern.strip().replace("\\", "/")
        if not pattern or pattern.startswith("#"):
            continue

        pattern = pattern.removeprefix("./")
        anchored = pattern.startswith("/")
        if anchored:
            pattern = pattern[1:]

        dir_only = pattern.endswith("/")
        if dir_only:
            pattern = pattern.rstrip("/")
            if not is_dir:
                continue

        if not pattern:
            continue

        if "/" in pattern or anchored:
            if fnmatch.fnmatch(rel_path, pattern):
                return True
            if is_dir and rel_path == pattern:
                return True
        elif fnmatch.fnmatch(name, pattern):
            return True

    return False


def _extract_imports(file_path: str) -> list[tuple[str, ImportKind]]:
    """Parse a Python file and extract all import statements.

    Returns list of (module_name, import_kind) tuples.
    """
    return [
        (import_.module_name, import_.import_kind)
        for import_ in _extract_located_imports(file_path)
    ]


def _extract_located_imports(file_path: str) -> list[_LocatedImport]:
    """Parse a Python file and extract imports with line numbers."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            source = f.read()
    except (OSError, IOError):
        return []

    try:
        tree = ast.parse(source, filename=file_path)
    except SyntaxError:
        return []

    imports: list[_LocatedImport] = []
    ignore_directives = _find_ignore_directives(source)
    type_checking_ranges = _find_type_checking_ranges(tree)
    conditional_import_ranges = _find_conditional_import_ranges(tree)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            syntax_kind = ImportKind.IMPORT
            kind = _classify_import(
                node,
                syntax_kind,
                type_checking_ranges,
                conditional_import_ranges,
            )
            for alias in node.names:
                imports.append(
                    _LocatedImport(alias.name, kind, node.lineno, syntax_kind)
                )

        elif isinstance(node, ast.ImportFrom):
            syntax_kind = (
                ImportKind.RELATIVE_IMPORT
                if node.level and node.level > 0
                else ImportKind.FROM_IMPORT
            )
            kind = _classify_import(
                node,
                syntax_kind,
                type_checking_ranges,
                conditional_import_ranges,
            )
            for module_name in _import_from_module_names(node):
                imports.append(
                    _LocatedImport(
                        module_name,
                        kind,
                        node.lineno,
                        syntax_kind,
                    )
                )

        elif isinstance(node, ast.Call):
            syntax_kind = ImportKind.DYNAMIC_IMPORT
            kind = _classify_import(
                node,
                syntax_kind,
                type_checking_ranges,
                conditional_import_ranges,
            )
            for module_name in _extract_dynamic_import_names(node):
                imports.append(
                    _LocatedImport(module_name, kind, node.lineno, syntax_kind)
                )

    return [
        import_
        for import_ in imports
        if not _is_ignored_import(import_, ignore_directives)
    ]


def _find_ignore_directives(source: str) -> dict[int, _IgnoreDirective]:
    """Find architecture-ignore directives.

    Supports inline directives on an import line and standalone directives that
    apply to the following line, for example:

    - from x import y  # archunit: ignore
    - # archunit: ignore
      from x import y
    """
    directives: dict[int, _IgnoreDirective] = {}
    for index, line in enumerate(source.splitlines(), start=1):
        match = _IGNORE_DIRECTIVE_REGEX.search(line)
        if match is None:
            continue

        modules = tuple(match.group("modules").split())
        target_line = index + 1 if line.strip().startswith("#") else index
        directives[target_line] = _IgnoreDirective(target_line, modules)
    return directives


def _is_ignored_import(
    import_: _LocatedImport,
    directives: dict[int, _IgnoreDirective],
) -> bool:
    directive = directives.get(import_.line_number)
    return directive is not None and directive.matches(import_)


def _extract_dynamic_import_names(node: ast.Call) -> list[str]:
    """Extract literal module names from common dynamic import calls."""
    if not node.args:
        return []

    first_arg = node.args[0]
    if not isinstance(first_arg, ast.Constant) or not isinstance(first_arg.value, str):
        return []

    if isinstance(node.func, ast.Name) and node.func.id in {
        "__import__",
        "import_module",
    }:
        return [first_arg.value]

    if (
        isinstance(node.func, ast.Attribute)
        and node.func.attr == "import_module"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "importlib"
    ):
        return [first_arg.value]

    return []


def _import_from_module_names(node: ast.ImportFrom) -> tuple[str, ...]:
    """Return resolvable module names for a from-import statement."""
    dots = "." * (node.level or 0)
    if node.module:
        return (f"{dots}{node.module}",)

    aliases = tuple(alias.name for alias in node.names if alias.name != "*")
    if dots and aliases:
        return tuple(f"{dots}{alias}" for alias in aliases)
    return (dots,) if dots else ()


def _edge_import_kinds(import_: _LocatedImport) -> tuple[ImportKind, ...]:
    """Return graph labels without losing syntax for conditional imports."""
    resolution_kind = import_.resolution_kind or import_.import_kind
    if (
        import_.import_kind == ImportKind.CONDITIONAL_IMPORT
        and resolution_kind != import_.import_kind
    ):
        return (resolution_kind, import_.import_kind)
    return (import_.import_kind,)


def _classify_import(
    node: ast.AST,
    default_kind: ImportKind,
    type_checking_ranges: list[tuple[int, int]],
    conditional_import_ranges: list[tuple[int, int]],
) -> ImportKind:
    """Classify an import node by special context before syntax kind."""
    if _in_type_checking(node, type_checking_ranges):
        return ImportKind.TYPE_IMPORT
    if _in_conditional_import(node, conditional_import_ranges):
        return ImportKind.CONDITIONAL_IMPORT
    return default_kind


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
                    getattr(n, "end_lineno", n.lineno) for n in node.body if hasattr(n, "lineno")
                )
                ranges.append((start, end))

    return sorted(ranges, key=lambda ele: ele[0])


def _find_conditional_import_ranges(tree: ast.Module) -> list[tuple[int, int]]:
    """Find try/except ImportError ranges that contain optional imports."""
    ranges: list[tuple[int, int]] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Try):
            continue
        if not any(_handles_import_error(handler.type) for handler in node.handlers):
            continue

        ranges.extend(_statement_ranges(node.body))
        for handler in node.handlers:
            if _handles_import_error(handler.type):
                ranges.extend(_statement_ranges(handler.body))

    return sorted(ranges, key=lambda ele: ele[0])


def _handles_import_error(node: ast.expr | None) -> bool:
    """Return True if an except handler catches import-related errors."""
    if node is None:
        return False
    if isinstance(node, ast.Name):
        return node.id in {"ImportError", "ModuleNotFoundError"}
    if isinstance(node, ast.Attribute):
        return node.attr in {"ImportError", "ModuleNotFoundError"}
    if isinstance(node, ast.Tuple):
        return any(_handles_import_error(elt) for elt in node.elts)
    return False


def _statement_ranges(statements: list[ast.stmt]) -> list[tuple[int, int]]:
    """Return line ranges covered by statement blocks."""
    if not statements:
        return []
    start = statements[0].lineno
    end = max(getattr(statement, "end_lineno", statement.lineno) for statement in statements)
    return [(start, end)]


def _in_type_checking(node: ast.AST, ranges: list[tuple[int, int]]) -> bool:
    """Check if a node is inside a TYPE_CHECKING block."""
    if not hasattr(node, "lineno"):
        return False
    lineno = node.lineno
    return any(start <= lineno <= end for start, end in ranges)


def _in_conditional_import(node: ast.AST, ranges: list[tuple[int, int]]) -> bool:
    """Check if a node is inside a try/except ImportError block."""
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
    if (
        kind
        in (
            ImportKind.RELATIVE_IMPORT,
            ImportKind.TYPE_IMPORT,
            ImportKind.CONDITIONAL_IMPORT,
        )
        and import_name.startswith(".")
    ):
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

    # Try resolving from the project root and also from parent directory
    # (the parent handles the case where project_root is itself a package
    # and imports use the package name as prefix)
    search_roots = [project_root]
    parent = os.path.dirname(project_root)
    if parent and parent != project_root:
        search_roots.append(parent)

    for root in search_roots:
        for i in range(len(parts), 0, -1):
            path_parts = parts[:i]
            candidate_base = os.path.join(root, *path_parts)

            # Try as a module file
            candidate_file = candidate_base + ".py"
            if os.path.isfile(candidate_file):
                resolved = _normalize(os.path.abspath(candidate_file))
                # Only count as internal if it's inside the project root
                is_internal = resolved.startswith(_normalize(os.path.abspath(project_root)))
                return resolved, not is_internal

            # Try as a package
            candidate_init = os.path.join(candidate_base, "__init__.py")
            if os.path.isfile(candidate_init):
                resolved = _normalize(os.path.abspath(candidate_init))
                is_internal = resolved.startswith(_normalize(os.path.abspath(project_root)))
                return resolved, not is_internal

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
