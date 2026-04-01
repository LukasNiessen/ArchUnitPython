"""Tests for the metrics fluent API."""

import os

from archunitpy.metrics.assertion.metric_thresholds import (
    FileCountViolation,
    MetricViolation,
)
from archunitpy.metrics.fluentapi.metrics import metrics

FIXTURES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "fixtures", "metrics_project"
)


class TestCountMetricsFluentAPI:
    def test_method_count_below(self):
        violations = (
            metrics(FIXTURES_DIR).count().method_count().should_be_below(50).check()
        )
        metric_violations = [v for v in violations if isinstance(v, MetricViolation)]
        assert len(metric_violations) == 0

    def test_method_count_violation(self):
        violations = (
            metrics(FIXTURES_DIR).count().method_count().should_be_below(2).check()
        )
        metric_violations = [v for v in violations if isinstance(v, MetricViolation)]
        assert len(metric_violations) > 0

    def test_field_count_below(self):
        violations = (
            metrics(FIXTURES_DIR).count().field_count().should_be_below(20).check()
        )
        metric_violations = [v for v in violations if isinstance(v, MetricViolation)]
        assert len(metric_violations) == 0

    def test_lines_of_code_below(self):
        violations = (
            metrics(FIXTURES_DIR)
            .count()
            .lines_of_code()
            .should_be_below(5000)
            .check()
        )
        file_violations = [v for v in violations if isinstance(v, FileCountViolation)]
        assert len(file_violations) == 0

    def test_lines_of_code_violation(self):
        violations = (
            metrics(FIXTURES_DIR)
            .count()
            .lines_of_code()
            .should_be_below(5)
            .check()
        )
        file_violations = [v for v in violations if isinstance(v, FileCountViolation)]
        assert len(file_violations) > 0


class TestLCOMMetricsFluentAPI:
    def test_lcom96b_below(self):
        violations = (
            metrics(FIXTURES_DIR).lcom().lcom96b().should_be_below(1.0).check()
        )
        metric_violations = [v for v in violations if isinstance(v, MetricViolation)]
        assert len(metric_violations) == 0

    def test_lcom4_below(self):
        violations = (
            metrics(FIXTURES_DIR).lcom().lcom4().should_be_below(10).check()
        )
        metric_violations = [v for v in violations if isinstance(v, MetricViolation)]
        assert len(metric_violations) == 0


class TestDistanceMetricsFluentAPI:
    def test_abstractness_below(self):
        violations = (
            metrics(FIXTURES_DIR)
            .distance()
            .abstractness()
            .should_be_below(1.0)
            .check()
        )
        assert isinstance(violations, list)

    def test_not_in_zone_of_uselessness(self):
        violations = (
            metrics(FIXTURES_DIR)
            .distance()
            .not_in_zone_of_uselessness()
            .check()
        )
        assert isinstance(violations, list)


class TestCustomMetrics:
    def test_custom_metric_below(self):
        violations = (
            metrics(FIXTURES_DIR)
            .custom_metric(
                "MethodFieldRatio",
                "Ratio of methods to fields",
                lambda ci: len(ci.methods) / max(len(ci.fields), 1),
            )
            .should_be_below(100)
            .check()
        )
        assert len(violations) == 0

    def test_custom_metric_satisfy(self):
        violations = (
            metrics(FIXTURES_DIR)
            .custom_metric(
                "HasMethods",
                "Class should have methods",
                lambda ci: float(len(ci.methods)),
            )
            .should_satisfy(lambda value, ci: value >= 0)
            .check()
        )
        assert len(violations) == 0


class TestMetricsFiltering:
    def test_filter_by_class_name(self):
        violations = (
            metrics(FIXTURES_DIR)
            .for_classes_matching("*Service*")
            .count()
            .method_count()
            .should_be_below(50)
            .check()
        )
        metric_violations = [v for v in violations if isinstance(v, MetricViolation)]
        assert len(metric_violations) == 0
