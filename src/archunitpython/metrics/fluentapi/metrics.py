"""Fluent API builders for metrics rules.

Usage:
    metrics('src/').count().lines_of_code().should_be_below(500).check()
    metrics('src/').lcom().lcom96b().should_be_below(0.5).check()
    metrics('src/').distance().abstractness().should_be_below(0.8).check()
"""

from __future__ import annotations

from typing import Any, Callable

from archunitpython.common.assertion.violation import Violation
from archunitpython.common.fluentapi.checkable import CheckOptions
from archunitpython.common.pattern_matching import matches_pattern_classname
from archunitpython.common.regex_factory import RegexFactory
from archunitpython.common.types import Filter, Pattern
from archunitpython.metrics.assertion.metric_thresholds import (
    FileCountViolation,
    MetricViolation,
    check_threshold,
)
from archunitpython.metrics.calculation.count import (
    ClassCountMetric,
    FieldCountMetric,
    FunctionCountMetric,
    ImportCountMetric,
    LinesOfCodeMetric,
    MethodCountMetric,
    StatementCountMetric,
)
from archunitpython.metrics.calculation.distance import (
    calculate_file_distance_metrics,
)
from archunitpython.metrics.calculation.lcom import (
    LCOM1,
    LCOM2,
    LCOM3,
    LCOM4,
    LCOM5,
    LCOM96a,
    LCOM96b,
    LCOMStar,
)
from archunitpython.metrics.common.types import ClassInfo, MetricComparison
from archunitpython.metrics.extraction.extract_class_info import (
    extract_class_info,
    extract_enhanced_class_info,
)


def metrics(project_path: str | None = None) -> "MetricsBuilder":
    """Entry point for metrics rules."""
    return MetricsBuilder(project_path)


class MetricsBuilder:
    """Top-level metrics builder with filter methods."""

    def __init__(self, project_path: str | None = None) -> None:
        self._project_path = project_path
        self._filters: list[Filter] = []

    def with_name(self, name: Pattern) -> "MetricsBuilder":
        self._filters.append(RegexFactory.filename_matcher(name))
        return self

    def in_folder(self, folder: Pattern) -> "MetricsBuilder":
        self._filters.append(RegexFactory.folder_matcher(folder))
        return self

    def in_path(self, path: Pattern) -> "MetricsBuilder":
        self._filters.append(RegexFactory.path_matcher(path))
        return self

    def for_classes_matching(self, pattern: Pattern) -> "MetricsBuilder":
        self._filters.append(RegexFactory.classname_matcher(pattern))
        return self

    def count(self) -> "CountMetricsBuilder":
        return CountMetricsBuilder(self._project_path, list(self._filters))

    def lcom(self) -> "LCOMMetricsBuilder":
        return LCOMMetricsBuilder(self._project_path, list(self._filters))

    def distance(self) -> "DistanceMetricsBuilder":
        return DistanceMetricsBuilder(self._project_path, list(self._filters))

    def custom_metric(
        self,
        name: str,
        description: str,
        calculation: Callable[[ClassInfo], float],
    ) -> "CustomMetricsBuilder":
        return CustomMetricsBuilder(
            self._project_path, list(self._filters), name, description, calculation
        )


def _get_filtered_classes(
    project_path: str | None, filters: list[Filter]
) -> list[ClassInfo]:
    classes = extract_class_info(project_path)
    if not filters:
        return classes
    return [
        c
        for c in classes
        if all(matches_pattern_classname(c.name, c.file_path, f) for f in filters)
    ]


# --- Count Metrics ---


class CountMetricsBuilder:
    def __init__(self, project_path: str | None, filters: list[Filter]) -> None:
        self._project_path = project_path
        self._filters = filters

    def method_count(self) -> "ClassMetricThresholdBuilder":
        return ClassMetricThresholdBuilder(
            self._project_path, self._filters, MethodCountMetric()
        )

    def field_count(self) -> "ClassMetricThresholdBuilder":
        return ClassMetricThresholdBuilder(
            self._project_path, self._filters, FieldCountMetric()
        )

    def lines_of_code(self) -> "FileMetricThresholdBuilder":
        return FileMetricThresholdBuilder(
            self._project_path, self._filters, LinesOfCodeMetric()
        )

    def statements(self) -> "FileMetricThresholdBuilder":
        return FileMetricThresholdBuilder(
            self._project_path, self._filters, StatementCountMetric()
        )

    def imports(self) -> "FileMetricThresholdBuilder":
        return FileMetricThresholdBuilder(
            self._project_path, self._filters, ImportCountMetric()
        )

    def classes(self) -> "FileMetricThresholdBuilder":
        return FileMetricThresholdBuilder(
            self._project_path, self._filters, ClassCountMetric()
        )

    def functions(self) -> "FileMetricThresholdBuilder":
        return FileMetricThresholdBuilder(
            self._project_path, self._filters, FunctionCountMetric()
        )


class ClassMetricThresholdBuilder:
    def __init__(self, project_path: str | None, filters: list[Filter], metric: Any) -> None:
        self._project_path = project_path
        self._filters = filters
        self._metric = metric

    def should_be_below(self, threshold: float) -> "ClassMetricCondition":
        return ClassMetricCondition(
            self._project_path, self._filters, self._metric, threshold, "below"
        )

    def should_be_above(self, threshold: float) -> "ClassMetricCondition":
        return ClassMetricCondition(
            self._project_path, self._filters, self._metric, threshold, "above"
        )

    def should_be(self, threshold: float) -> "ClassMetricCondition":
        return ClassMetricCondition(
            self._project_path, self._filters, self._metric, threshold, "equal"
        )

    def should_be_below_or_equal(self, threshold: float) -> "ClassMetricCondition":
        return ClassMetricCondition(
            self._project_path, self._filters, self._metric, threshold, "below_equal"
        )

    def should_be_above_or_equal(self, threshold: float) -> "ClassMetricCondition":
        return ClassMetricCondition(
            self._project_path, self._filters, self._metric, threshold, "above_equal"
        )


class ClassMetricCondition:
    """Checkable that verifies a class-level metric threshold."""

    def __init__(
        self,
        project_path: str | None,
        filters: list[Filter],
        metric: Any,
        threshold: float,
        comparison: MetricComparison,
    ) -> None:
        self._project_path = project_path
        self._filters = filters
        self._metric = metric
        self._threshold = threshold
        self._comparison = comparison

    def check(self, options: CheckOptions | None = None) -> list[Violation]:
        classes = _get_filtered_classes(self._project_path, self._filters)
        violations: list[Violation] = []

        for cls in classes:
            value = self._metric.calculate(cls)
            if check_threshold(value, self._threshold, self._comparison):
                violations.append(
                    MetricViolation(
                        class_name=cls.name,
                        file_path=cls.file_path,
                        metric_name=self._metric.name,
                        metric_value=value,
                        threshold=self._threshold,
                        comparison=self._comparison,
                    )
                )

        return violations


class FileMetricThresholdBuilder:
    def __init__(self, project_path: str | None, filters: list[Filter], metric: Any) -> None:
        self._project_path = project_path
        self._filters = filters
        self._metric = metric

    def should_be_below(self, threshold: float) -> "FileMetricCondition":
        return FileMetricCondition(
            self._project_path, self._filters, self._metric, threshold, "below"
        )

    def should_be_above(self, threshold: float) -> "FileMetricCondition":
        return FileMetricCondition(
            self._project_path, self._filters, self._metric, threshold, "above"
        )

    def should_be_below_or_equal(self, threshold: float) -> "FileMetricCondition":
        return FileMetricCondition(
            self._project_path, self._filters, self._metric, threshold, "below_equal"
        )


class FileMetricCondition:
    """Checkable that verifies a file-level metric threshold."""

    def __init__(
        self,
        project_path: str | None,
        filters: list[Filter],
        metric: Any,
        threshold: float,
        comparison: MetricComparison,
    ) -> None:
        self._project_path = project_path
        self._filters = filters
        self._metric = metric
        self._threshold = threshold
        self._comparison: MetricComparison = comparison

    def check(self, options: CheckOptions | None = None) -> list[Violation]:
        import os

        from archunitpython.common.extraction.extract_graph import (
            _DEFAULT_EXCLUDE,
            _find_python_files,
        )

        project = self._project_path or os.getcwd()
        project = os.path.abspath(project)
        files = _find_python_files(project, _DEFAULT_EXCLUDE)
        violations: list[Violation] = []

        for file_path in files:
            norm = file_path.replace("\\", "/")
            if self._filters and not all(
                matches_pattern_classname("", norm, f) for f in self._filters
            ):
                continue

            value = self._metric.calculate_from_file(file_path)
            if check_threshold(value, self._threshold, self._comparison):
                violations.append(
                    FileCountViolation(
                        file_path=norm,
                        metric_name=self._metric.name,
                        metric_value=value,
                        threshold=self._threshold,
                        comparison=self._comparison,
                    )
                )

        return violations


# --- LCOM Metrics ---


class LCOMMetricsBuilder:
    def __init__(self, project_path: str | None, filters: list[Filter]) -> None:
        self._project_path = project_path
        self._filters = filters

    def lcom96a(self) -> "ClassMetricThresholdBuilder":
        return ClassMetricThresholdBuilder(self._project_path, self._filters, LCOM96a())

    def lcom96b(self) -> "ClassMetricThresholdBuilder":
        return ClassMetricThresholdBuilder(self._project_path, self._filters, LCOM96b())

    def lcom1(self) -> "ClassMetricThresholdBuilder":
        return ClassMetricThresholdBuilder(self._project_path, self._filters, LCOM1())

    def lcom2(self) -> "ClassMetricThresholdBuilder":
        return ClassMetricThresholdBuilder(self._project_path, self._filters, LCOM2())

    def lcom3(self) -> "ClassMetricThresholdBuilder":
        return ClassMetricThresholdBuilder(self._project_path, self._filters, LCOM3())

    def lcom4(self) -> "ClassMetricThresholdBuilder":
        return ClassMetricThresholdBuilder(self._project_path, self._filters, LCOM4())

    def lcom5(self) -> "ClassMetricThresholdBuilder":
        return ClassMetricThresholdBuilder(self._project_path, self._filters, LCOM5())

    def lcomstar(self) -> "ClassMetricThresholdBuilder":
        return ClassMetricThresholdBuilder(self._project_path, self._filters, LCOMStar())


# --- Distance Metrics ---


class DistanceMetricsBuilder:
    def __init__(self, project_path: str | None, filters: list[Filter]) -> None:
        self._project_path = project_path
        self._filters = filters

    def abstractness(self) -> "DistanceThresholdBuilder":
        return DistanceThresholdBuilder(
            self._project_path, self._filters, "abstractness"
        )

    def instability(self) -> "DistanceThresholdBuilder":
        return DistanceThresholdBuilder(
            self._project_path, self._filters, "instability"
        )

    def distance_from_main_sequence(self) -> "DistanceThresholdBuilder":
        return DistanceThresholdBuilder(
            self._project_path, self._filters, "distance"
        )

    def not_in_zone_of_pain(self) -> "ZoneCondition":
        return ZoneCondition(self._project_path, self._filters, "pain")

    def not_in_zone_of_uselessness(self) -> "ZoneCondition":
        return ZoneCondition(self._project_path, self._filters, "uselessness")


class DistanceThresholdBuilder:
    def __init__(self, project_path: str | None, filters: list[Filter], metric_attr: str) -> None:
        self._project_path = project_path
        self._filters = filters
        self._metric_attr = metric_attr

    def should_be_below(self, threshold: float) -> "DistanceCondition":
        return DistanceCondition(
            self._project_path,
            self._filters,
            self._metric_attr,
            threshold,
            "below",
        )

    def should_be_above(self, threshold: float) -> "DistanceCondition":
        return DistanceCondition(
            self._project_path,
            self._filters,
            self._metric_attr,
            threshold,
            "above",
        )


class DistanceCondition:
    """Checkable for distance metric thresholds."""

    def __init__(
        self,
        project_path: str | None,
        filters: list[Filter],
        metric_attr: str,
        threshold: float,
        comparison: MetricComparison,
    ) -> None:
        self._project_path = project_path
        self._filters = filters
        self._metric_attr = metric_attr
        self._threshold = threshold
        self._comparison: MetricComparison = comparison

    def check(self, options: CheckOptions | None = None) -> list[Violation]:
        files = extract_enhanced_class_info(self._project_path)
        violations: list[Violation] = []

        for file_result in files:
            dm = calculate_file_distance_metrics(file_result, files)
            value = getattr(dm, self._metric_attr)

            if check_threshold(value, self._threshold, self._comparison):
                violations.append(
                    MetricViolation(
                        class_name="",
                        file_path=file_result.file_path,
                        metric_name=self._metric_attr,
                        metric_value=value,
                        threshold=self._threshold,
                        comparison=self._comparison,
                    )
                )

        return violations


class ZoneCondition:
    """Checkable for zone detection (pain/uselessness)."""

    def __init__(self, project_path: str | None, filters: list[Filter], zone_type: str) -> None:
        self._project_path = project_path
        self._filters = filters
        self._zone_type = zone_type

    def check(self, options: CheckOptions | None = None) -> list[Violation]:
        files = extract_enhanced_class_info(self._project_path)
        violations: list[Violation] = []

        for file_result in files:
            dm = calculate_file_distance_metrics(file_result, files)
            in_zone = (
                dm.in_zone_of_pain
                if self._zone_type == "pain"
                else dm.in_zone_of_uselessness
            )

            if in_zone:
                violations.append(
                    MetricViolation(
                        class_name="",
                        file_path=file_result.file_path,
                        metric_name=f"zone_of_{self._zone_type}",
                        metric_value=1.0,
                        threshold=0.0,
                        comparison="equal",
                    )
                )

        return violations


# --- Custom Metrics ---


class CustomMetricsBuilder:
    def __init__(
        self,
        project_path: str | None,
        filters: list[Filter],
        name: str,
        description: str,
        calculation: Callable[[ClassInfo], float],
    ) -> None:
        self._project_path = project_path
        self._filters = filters
        self._name = name
        self._description = description
        self._calculation = calculation

    def should_be_below(self, threshold: float) -> "CustomMetricCondition":
        return CustomMetricCondition(
            self._project_path,
            self._filters,
            self._name,
            self._calculation,
            threshold,
            "below",
        )

    def should_be_above(self, threshold: float) -> "CustomMetricCondition":
        return CustomMetricCondition(
            self._project_path,
            self._filters,
            self._name,
            self._calculation,
            threshold,
            "above",
        )

    def should_satisfy(
        self, assertion: Callable[[float, ClassInfo], bool]
    ) -> "CustomAssertionCondition":
        return CustomAssertionCondition(
            self._project_path,
            self._filters,
            self._name,
            self._calculation,
            assertion,
        )


class CustomMetricCondition:
    """Checkable for custom metric thresholds."""

    def __init__(
        self,
        project_path: str | None,
        filters: list[Filter],
        name: str,
        calculation: Callable[[ClassInfo], float],
        threshold: float,
        comparison: MetricComparison,
    ) -> None:
        self._project_path = project_path
        self._filters = filters
        self._name = name
        self._calculation = calculation
        self._threshold = threshold
        self._comparison = comparison

    def check(self, options: CheckOptions | None = None) -> list[Violation]:
        classes = _get_filtered_classes(self._project_path, self._filters)
        violations: list[Violation] = []

        for cls in classes:
            value = self._calculation(cls)
            if check_threshold(value, self._threshold, self._comparison):
                violations.append(
                    MetricViolation(
                        class_name=cls.name,
                        file_path=cls.file_path,
                        metric_name=self._name,
                        metric_value=value,
                        threshold=self._threshold,
                        comparison=self._comparison,
                    )
                )

        return violations


class CustomAssertionCondition:
    """Checkable for custom metric assertions."""

    def __init__(
        self,
        project_path: str | None,
        filters: list[Filter],
        name: str,
        calculation: Callable[[ClassInfo], float],
        assertion: Callable[[float, ClassInfo], bool],
    ) -> None:
        self._project_path = project_path
        self._filters = filters
        self._name = name
        self._calculation = calculation
        self._assertion = assertion

    def check(self, options: CheckOptions | None = None) -> list[Violation]:
        classes = _get_filtered_classes(self._project_path, self._filters)
        violations: list[Violation] = []

        for cls in classes:
            value = self._calculation(cls)
            if not self._assertion(value, cls):
                violations.append(
                    MetricViolation(
                        class_name=cls.name,
                        file_path=cls.file_path,
                        metric_name=self._name,
                        metric_value=value,
                        threshold=0,
                        comparison="equal",
                    )
                )

        return violations
