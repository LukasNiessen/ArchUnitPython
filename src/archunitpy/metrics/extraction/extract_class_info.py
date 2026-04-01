"""Extract class information from Python source files using AST."""

from __future__ import annotations

import ast
import os

from archunitpy.common.extraction.extract_graph import _find_python_files, _DEFAULT_EXCLUDE
from archunitpy.metrics.common.types import (
    ClassInfo,
    EnhancedClassInfo,
    FieldInfo,
    FileAnalysisResult,
    MethodInfo,
)


def extract_class_info(
    project_path: str | None = None,
    *,
    exclude_patterns: list[str] | None = None,
) -> list[ClassInfo]:
    """Extract class metadata from all Python files in a project.

    Args:
        project_path: Root directory to scan.
        exclude_patterns: Directory/file names to exclude.

    Returns:
        List of ClassInfo for every class found.
    """
    if project_path is None:
        project_path = os.getcwd()

    project_path = os.path.abspath(project_path)
    excludes = exclude_patterns if exclude_patterns is not None else _DEFAULT_EXCLUDE
    py_files = _find_python_files(project_path, excludes)

    classes: list[ClassInfo] = []
    for file_path in py_files:
        classes.extend(_process_source_file(file_path))

    return classes


def extract_enhanced_class_info(
    project_path: str | None = None,
    *,
    exclude_patterns: list[str] | None = None,
) -> list[FileAnalysisResult]:
    """Enhanced extraction with abstractness and dependency information."""
    if project_path is None:
        project_path = os.getcwd()

    project_path = os.path.abspath(project_path)
    excludes = exclude_patterns if exclude_patterns is not None else _DEFAULT_EXCLUDE
    py_files = _find_python_files(project_path, excludes)

    results: list[FileAnalysisResult] = []
    for file_path in py_files:
        result = _process_source_file_enhanced(file_path)
        if result.classes:
            results.append(result)

    return results


def _process_source_file(file_path: str) -> list[ClassInfo]:
    """Extract ClassInfo from a single Python file."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            source = f.read()
    except (OSError, IOError):
        return []

    try:
        tree = ast.parse(source, filename=file_path)
    except SyntaxError:
        return []

    classes: list[ClassInfo] = []
    norm_path = file_path.replace("\\", "/")

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            class_info = _extract_class(node, norm_path)
            classes.append(class_info)

    return classes


def _process_source_file_enhanced(file_path: str) -> FileAnalysisResult:
    """Extract enhanced class info from a single Python file."""
    norm_path = file_path.replace("\\", "/")
    result = FileAnalysisResult(file_path=norm_path)

    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            source = f.read()
    except (OSError, IOError):
        return result

    try:
        tree = ast.parse(source, filename=file_path)
    except SyntaxError:
        return result

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            enhanced = _extract_enhanced_class(node, norm_path)
            result.classes.append(enhanced)
            result.total_types += 1
            if enhanced.is_protocol:
                result.protocols += 1
            elif enhanced.is_abstract:
                result.abstract_classes += 1
            else:
                result.concrete_classes += 1

    return result


def _extract_class(node: ast.ClassDef, file_path: str) -> ClassInfo:
    """Extract ClassInfo from a ClassDef AST node."""
    methods: list[MethodInfo] = []
    fields: dict[str, FieldInfo] = {}

    # Find fields from __init__ and class body
    for item in ast.walk(node):
        if isinstance(item, ast.Assign):
            for target in item.targets:
                if isinstance(target, ast.Attribute) and isinstance(
                    target.value, ast.Name
                ):
                    if target.value.id == "self":
                        field_name = target.attr
                        if field_name not in fields:
                            fields[field_name] = FieldInfo(name=field_name)

    # Extract methods and track field accesses
    for item in node.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            method_name = item.name
            accessed = _find_field_accesses(item, set(fields.keys()))
            methods.append(
                MethodInfo(name=method_name, accessed_fields=accessed)
            )
            # Update field access tracking
            for field_name in accessed:
                if field_name in fields:
                    if method_name not in fields[field_name].accessed_by:
                        fields[field_name].accessed_by.append(method_name)

    return ClassInfo(
        name=node.name,
        file_path=file_path,
        methods=methods,
        fields=list(fields.values()),
    )


def _extract_enhanced_class(
    node: ast.ClassDef, file_path: str
) -> EnhancedClassInfo:
    """Extract EnhancedClassInfo from a ClassDef AST node."""
    base = _extract_class(node, file_path)

    is_abstract = _is_abstract_class(node)
    is_protocol = _is_protocol_class(node)
    abstract_methods = _find_abstract_methods(node)

    return EnhancedClassInfo(
        name=base.name,
        file_path=base.file_path,
        methods=base.methods,
        fields=base.fields,
        is_abstract=is_abstract,
        is_protocol=is_protocol,
        abstract_methods=abstract_methods,
    )


def _find_field_accesses(
    func_node: ast.FunctionDef | ast.AsyncFunctionDef,
    known_fields: set[str],
) -> list[str]:
    """Find all self.field accesses within a method."""
    accessed: list[str] = []
    for node in ast.walk(func_node):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            if node.value.id == "self" and node.attr in known_fields:
                if node.attr not in accessed:
                    accessed.append(node.attr)
    return accessed


def _is_abstract_class(node: ast.ClassDef) -> bool:
    """Check if a class inherits from ABC or ABCMeta."""
    for base in node.bases:
        name = _get_name(base)
        if name in ("ABC", "ABCMeta"):
            return True
    for keyword in node.keywords:
        if keyword.arg == "metaclass":
            name = _get_name(keyword.value)
            if name == "ABCMeta":
                return True
    # Also check for @abstractmethod decorators
    for item in node.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for decorator in item.decorator_list:
                name = _get_name(decorator)
                if name == "abstractmethod":
                    return True
    return False


def _is_protocol_class(node: ast.ClassDef) -> bool:
    """Check if a class inherits from Protocol."""
    for base in node.bases:
        name = _get_name(base)
        if name == "Protocol":
            return True
    return False


def _find_abstract_methods(node: ast.ClassDef) -> list[str]:
    """Find all methods with @abstractmethod decorator."""
    abstract: list[str] = []
    for item in node.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for decorator in item.decorator_list:
                name = _get_name(decorator)
                if name == "abstractmethod":
                    abstract.append(item.name)
                    break
    return abstract


def _get_name(node: ast.expr) -> str:
    """Extract a name from an AST node (handles Name and Attribute)."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""
