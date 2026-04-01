"""Convert violations to human-readable test messages."""

from __future__ import annotations

from dataclasses import dataclass

from archunitpy.common.assertion.violation import EmptyTestViolation, Violation
from archunitpy.files.assertion.custom_file_logic import CustomFileViolation
from archunitpy.files.assertion.cycle_free import ViolatingCycle
from archunitpy.files.assertion.depend_on_files import ViolatingFileDependency
from archunitpy.files.assertion.matching_files import ViolatingNode
from archunitpy.metrics.assertion.metric_thresholds import (
    FileCountViolation,
    MetricViolation,
)
from archunitpy.slices.assertion.admissible_edges import ViolatingEdge


@dataclass
class TestViolation:
    """A test-friendly violation representation."""

    message: str
    details: str


class ViolationFactory:
    """Convert violations to test-friendly format."""

    @staticmethod
    def from_violation(violation: Violation) -> TestViolation:
        if isinstance(violation, EmptyTestViolation):
            return TestViolation(
                message="No files matched",
                details=violation.message,
            )

        if isinstance(violation, ViolatingNode):
            return TestViolation(
                message=f"File pattern violation",
                details=f"File '{violation.projected_node.label}' "
                f"{'matches' if violation.is_negated else 'does not match'} "
                f"pattern '{violation.check_pattern.regexp.pattern}'",
            )

        if isinstance(violation, ViolatingFileDependency):
            edge = violation.dependency
            return TestViolation(
                message=f"File dependency violation",
                details=f"'{edge.source_label}' "
                f"{'depends on' if violation.is_negated else 'does not depend on'} "
                f"'{edge.target_label}'",
            )

        if isinstance(violation, ViolatingCycle):
            cycle_str = " -> ".join(
                e.source_label for e in violation.cycle
            )
            return TestViolation(
                message="Circular dependency detected",
                details=f"Cycle: {cycle_str}",
            )

        if isinstance(violation, CustomFileViolation):
            return TestViolation(
                message=violation.message,
                details=f"File: {violation.file_info.path}",
            )

        if isinstance(violation, MetricViolation):
            return TestViolation(
                message=f"Metric '{violation.metric_name}' violation",
                details=f"Class '{violation.class_name}' in '{violation.file_path}': "
                f"value={violation.metric_value:.2f}, "
                f"threshold={violation.threshold:.2f} ({violation.comparison})",
            )

        if isinstance(violation, FileCountViolation):
            return TestViolation(
                message=f"File metric '{violation.metric_name}' violation",
                details=f"File '{violation.file_path}': "
                f"value={violation.metric_value:.2f}, "
                f"threshold={violation.threshold:.2f} ({violation.comparison})",
            )

        if isinstance(violation, ViolatingEdge):
            edge = violation.projected_edge
            return TestViolation(
                message="Slice dependency violation",
                details=f"'{edge.source_label}' -> '{edge.target_label}' "
                f"is {'forbidden' if violation.is_negated else 'not allowed'}",
            )

        return TestViolation(
            message="Architecture violation",
            details=str(violation),
        )
