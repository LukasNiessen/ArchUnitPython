"""Utility functions for detecting Python declarations in AST."""

from __future__ import annotations

import ast
from dataclasses import dataclass


@dataclass
class DeclarationCounts:
    """Counts of different declaration types in a Python file."""

    total: int = 0
    protocols: int = 0
    abstract_classes: int = 0
    abstract_methods: int = 0
    concrete_classes: int = 0
    functions: int = 0
    variables: int = 0


def is_abstract_class(node: ast.ClassDef) -> bool:
    """Check if a class inherits from ABC or uses ABCMeta."""
    for base in node.bases:
        name = _get_name(base)
        if name in ("ABC", "ABCMeta"):
            return True
    for keyword in node.keywords:
        if keyword.arg == "metaclass":
            name = _get_name(keyword.value)
            if name == "ABCMeta":
                return True
    # Also detect by @abstractmethod presence
    for item in node.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for dec in item.decorator_list:
                if _get_name(dec) == "abstractmethod":
                    return True
    return False


def is_protocol_class(node: ast.ClassDef) -> bool:
    """Check if a class inherits from typing.Protocol."""
    for base in node.bases:
        name = _get_name(base)
        if name == "Protocol":
            return True
    return False


def is_abstract_method(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Check if a method has the @abstractmethod decorator."""
    for dec in node.decorator_list:
        if _get_name(dec) == "abstractmethod":
            return True
    return False


def count_declarations(source: str) -> DeclarationCounts:
    """Count all declaration types in a Python source string.

    Args:
        source: Python source code as a string.

    Returns:
        DeclarationCounts with totals for each declaration type.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return DeclarationCounts()

    counts = DeclarationCounts()

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            counts.total += 1
            if is_protocol_class(node):
                counts.protocols += 1
            elif is_abstract_class(node):
                counts.abstract_classes += 1
            else:
                counts.concrete_classes += 1

            # Count abstract methods
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if is_abstract_method(item):
                        counts.abstract_methods += 1

        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Only count module-level functions
            if _is_module_level(node, tree):
                counts.total += 1
                counts.functions += 1

        elif isinstance(node, ast.Assign) and _is_module_level(node, tree):
            counts.total += 1
            counts.variables += 1

    return counts


def _is_module_level(node: ast.AST, tree: ast.Module) -> bool:
    """Check if a node is directly in the module body."""
    return node in tree.body


def _get_name(node: ast.expr) -> str:
    """Extract a name from an AST node."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""
