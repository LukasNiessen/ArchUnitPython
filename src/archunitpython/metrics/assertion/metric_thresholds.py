"""Metric threshold violations."""

from __future__ import annotations

from dataclasses import dataclass

from archunitpython.common.assertion.violation import Violation
from archunitpython.metrics.common.types import MetricComparison


@dataclass
class MetricViolation(Violation):
    """A class metric that exceeds its threshold."""

    class_name: str
    file_path: str
    metric_name: str
    metric_value: float
    threshold: float
    comparison: MetricComparison


@dataclass
class FileCountViolation(Violation):
    """A file-level metric that exceeds its threshold."""

    file_path: str
    metric_name: str
    metric_value: float
    threshold: float
    comparison: MetricComparison


def check_threshold(
    value: float, threshold: float, comparison: MetricComparison
) -> bool:
    """Check if a value violates a threshold.

    Returns True if the value is a VIOLATION.
    """
    if comparison == "below":
        return value >= threshold
    elif comparison == "above":
        return value <= threshold
    elif comparison == "equal":
        return abs(value - threshold) > 1e-9
    elif comparison == "below_equal":
        return value > threshold
    elif comparison == "above_equal":
        return value < threshold
    return False
