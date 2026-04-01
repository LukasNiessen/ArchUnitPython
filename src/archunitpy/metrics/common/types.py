"""Common types for the metrics module."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Protocol


@dataclass
class MethodInfo:
    """Information about a class method."""

    name: str
    accessed_fields: list[str] = field(default_factory=list)


@dataclass
class FieldInfo:
    """Information about a class field."""

    name: str
    accessed_by: list[str] = field(default_factory=list)


@dataclass
class ClassInfo:
    """Information about a class extracted from source code."""

    name: str
    file_path: str
    methods: list[MethodInfo] = field(default_factory=list)
    fields: list[FieldInfo] = field(default_factory=list)


@dataclass
class EnhancedClassInfo(ClassInfo):
    """Extended class info with abstractness and dependency data."""

    is_abstract: bool = False
    is_protocol: bool = False
    abstract_methods: list[str] = field(default_factory=list)
    efferent_coupling: int = 0  # Ce: outgoing dependencies
    afferent_coupling: int = 0  # Ca: incoming dependencies


@dataclass
class FileAnalysisResult:
    """Analysis result for a single Python file."""

    file_path: str
    classes: list[EnhancedClassInfo] = field(default_factory=list)
    protocols: int = 0
    abstract_classes: int = 0
    concrete_classes: int = 0
    total_types: int = 0


MetricComparison = Literal["below", "above", "equal", "above_equal", "below_equal"]


class Metric(Protocol):
    """Protocol for class-level metrics."""

    name: str
    description: str

    def calculate(self, class_info: ClassInfo) -> float: ...
