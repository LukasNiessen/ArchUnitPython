"""Count metrics: method count, field count, lines of code, etc."""

from __future__ import annotations

import ast

from archunitpy.metrics.common.types import ClassInfo


class MethodCountMetric:
    """Number of methods in a class."""

    name = "MethodCount"
    description = "Number of methods in a class"

    def calculate(self, class_info: ClassInfo) -> float:
        return float(len(class_info.methods))


class FieldCountMetric:
    """Number of fields in a class."""

    name = "FieldCount"
    description = "Number of fields in a class"

    def calculate(self, class_info: ClassInfo) -> float:
        return float(len(class_info.fields))


class LinesOfCodeMetric:
    """Number of non-blank, non-comment lines in a file."""

    name = "LinesOfCode"
    description = "Number of non-blank, non-comment lines"

    def calculate_from_file(self, file_path: str) -> float:
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
        except (OSError, IOError):
            return 0.0

        count = 0
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                count += 1
        return float(count)


class StatementCountMetric:
    """Number of AST statements in a file."""

    name = "StatementCount"
    description = "Number of statements in a file"

    def calculate_from_file(self, file_path: str) -> float:
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                source = f.read()
        except (OSError, IOError):
            return 0.0

        try:
            tree = ast.parse(source)
        except SyntaxError:
            return 0.0

        count = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.stmt):
                count += 1
        return float(count)


class ImportCountMetric:
    """Number of import statements in a file."""

    name = "ImportCount"
    description = "Number of import statements in a file"

    def calculate_from_file(self, file_path: str) -> float:
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                source = f.read()
        except (OSError, IOError):
            return 0.0

        try:
            tree = ast.parse(source)
        except SyntaxError:
            return 0.0

        count = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                count += 1
        return float(count)


class ClassCountMetric:
    """Number of class definitions in a file."""

    name = "ClassCount"
    description = "Number of class definitions in a file"

    def calculate_from_file(self, file_path: str) -> float:
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                source = f.read()
        except (OSError, IOError):
            return 0.0

        try:
            tree = ast.parse(source)
        except SyntaxError:
            return 0.0

        count = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                count += 1
        return float(count)


class FunctionCountMetric:
    """Number of top-level function definitions in a file."""

    name = "FunctionCount"
    description = "Number of top-level function definitions in a file"

    def calculate_from_file(self, file_path: str) -> float:
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                source = f.read()
        except (OSError, IOError):
            return 0.0

        try:
            tree = ast.parse(source)
        except SyntaxError:
            return 0.0

        count = 0
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                count += 1
        return float(count)
