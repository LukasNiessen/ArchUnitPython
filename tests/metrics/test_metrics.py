"""Tests for metrics: extraction, count, LCOM, distance."""

import os

from archunitpython.metrics.common.types import ClassInfo, FieldInfo, MethodInfo
from archunitpython.metrics.extraction.extract_class_info import (
    extract_class_info,
    extract_enhanced_class_info,
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
from archunitpython.metrics.calculation.distance import (
    calculate_distance_metrics_for_project,
    calculate_file_distance_metrics,
)
from archunitpython.metrics.assertion.metric_thresholds import check_threshold

FIXTURES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "fixtures", "metrics_project"
)
SERVICE_FILE = os.path.join(FIXTURES_DIR, "service.py")


# --- TICKET-14: Class Info Extraction ---

class TestExtractClassInfo:
    def test_extracts_classes(self):
        classes = extract_class_info(FIXTURES_DIR)
        names = {c.name for c in classes}
        assert "BaseService" in names
        assert "UserService" in names
        assert "DataClass" in names
        assert "Serializable" in names

    def test_extracts_methods(self):
        classes = extract_class_info(FIXTURES_DIR)
        user_service = next(c for c in classes if c.name == "UserService")
        method_names = {m.name for m in user_service.methods}
        assert "process" in method_names
        assert "get_user" in method_names
        assert "add_user" in method_names

    def test_extracts_fields(self):
        classes = extract_class_info(FIXTURES_DIR)
        user_service = next(c for c in classes if c.name == "UserService")
        field_names = {f.name for f in user_service.fields}
        assert "users" in field_names
        assert "active_count" in field_names

    def test_field_access_tracking(self):
        classes = extract_class_info(FIXTURES_DIR)
        data_class = next(c for c in classes if c.name == "DataClass")
        # to_dict should access name, value, category
        to_dict = next(m for m in data_class.methods if m.name == "to_dict")
        assert "name" in to_dict.accessed_fields
        assert "value" in to_dict.accessed_fields
        assert "category" in to_dict.accessed_fields

    def test_enhanced_extraction(self):
        results = extract_enhanced_class_info(FIXTURES_DIR)
        assert len(results) > 0
        all_classes = [c for r in results for c in r.classes]
        base = next(c for c in all_classes if c.name == "BaseService")
        assert base.is_abstract is True
        proto = next(c for c in all_classes if c.name == "Serializable")
        assert proto.is_protocol is True


# --- TICKET-15: Count Metrics ---

class TestCountMetrics:
    def test_method_count(self):
        ci = ClassInfo(
            name="Test",
            file_path="test.py",
            methods=[MethodInfo("a"), MethodInfo("b"), MethodInfo("c")],
        )
        assert MethodCountMetric().calculate(ci) == 3.0

    def test_field_count(self):
        ci = ClassInfo(
            name="Test",
            file_path="test.py",
            fields=[FieldInfo("x"), FieldInfo("y")],
        )
        assert FieldCountMetric().calculate(ci) == 2.0

    def test_lines_of_code(self):
        loc = LinesOfCodeMetric().calculate_from_file(SERVICE_FILE)
        assert loc > 20  # File has significant content

    def test_statement_count(self):
        count = StatementCountMetric().calculate_from_file(SERVICE_FILE)
        assert count > 10

    def test_import_count(self):
        count = ImportCountMetric().calculate_from_file(SERVICE_FILE)
        assert count >= 2  # abc and typing imports

    def test_class_count(self):
        count = ClassCountMetric().calculate_from_file(SERVICE_FILE)
        assert count == 4  # Serializable, BaseService, UserService, DataClass

    def test_function_count(self):
        count = FunctionCountMetric().calculate_from_file(SERVICE_FILE)
        assert count == 0  # No top-level functions (all in classes)


# --- TICKET-16: LCOM Metrics ---

def _make_perfect_cohesion():
    """All methods access all fields → perfect cohesion."""
    return ClassInfo(
        name="Perfect",
        file_path="test.py",
        methods=[
            MethodInfo("m1", ["f1", "f2"]),
            MethodInfo("m2", ["f1", "f2"]),
        ],
        fields=[
            FieldInfo("f1", ["m1", "m2"]),
            FieldInfo("f2", ["m1", "m2"]),
        ],
    )


def _make_no_cohesion():
    """Each method accesses separate field → no cohesion."""
    return ClassInfo(
        name="NoCohesion",
        file_path="test.py",
        methods=[
            MethodInfo("m1", ["f1"]),
            MethodInfo("m2", ["f2"]),
        ],
        fields=[
            FieldInfo("f1", ["m1"]),
            FieldInfo("f2", ["m2"]),
        ],
    )


class TestLCOM96b:
    def test_perfect_cohesion(self):
        ci = _make_perfect_cohesion()
        result = LCOM96b().calculate(ci)
        assert result == 0.0

    def test_no_cohesion(self):
        ci = _make_no_cohesion()
        result = LCOM96b().calculate(ci)
        assert result == 0.5

    def test_single_method(self):
        ci = ClassInfo(
            name="One",
            file_path="test.py",
            methods=[MethodInfo("m1", ["f1"])],
            fields=[FieldInfo("f1", ["m1"])],
        )
        result = LCOM96b().calculate(ci)
        assert result == 0.0

    def test_no_fields(self):
        ci = ClassInfo(name="Empty", file_path="test.py", methods=[MethodInfo("m1")])
        assert LCOM96b().calculate(ci) == 0.0

    def test_no_methods(self):
        ci = ClassInfo(name="Empty", file_path="test.py", fields=[FieldInfo("f1")])
        assert LCOM96b().calculate(ci) == 0.0


class TestLCOM1:
    def test_perfect_cohesion(self):
        ci = _make_perfect_cohesion()
        assert LCOM1().calculate(ci) == 0.0

    def test_no_cohesion(self):
        ci = _make_no_cohesion()
        result = LCOM1().calculate(ci)
        assert result == 1.0  # 1 non-sharing pair - 0 sharing pairs


class TestLCOM4:
    def test_perfect_cohesion(self):
        ci = _make_perfect_cohesion()
        assert LCOM4().calculate(ci) == 1.0  # 1 connected component

    def test_no_cohesion(self):
        ci = _make_no_cohesion()
        assert LCOM4().calculate(ci) == 2.0  # 2 connected components


class TestAllLCOMVariants:
    def test_all_defined(self):
        ci = _make_perfect_cohesion()
        for metric_class in [LCOM96a, LCOM96b, LCOM1, LCOM2, LCOM3, LCOM4, LCOM5, LCOMStar]:
            metric = metric_class()
            result = metric.calculate(ci)
            assert isinstance(result, float), f"{metric.name} returned non-float"


# --- TICKET-17: Distance Metrics ---

class TestDistanceMetrics:
    def test_project_summary(self):
        results = extract_enhanced_class_info(FIXTURES_DIR)
        summary = calculate_distance_metrics_for_project(results)
        assert summary.total_files > 0
        assert 0 <= summary.average_abstractness <= 1
        assert 0 <= summary.average_instability <= 1

    def test_empty_project(self):
        summary = calculate_distance_metrics_for_project([])
        assert summary.total_files == 0


# --- Threshold Checking ---

class TestCheckThreshold:
    def test_below(self):
        assert check_threshold(10, 5, "below") is True  # 10 >= 5 → violation
        assert check_threshold(3, 5, "below") is False  # 3 < 5 → ok

    def test_above(self):
        assert check_threshold(3, 5, "above") is True  # 3 <= 5 → violation
        assert check_threshold(10, 5, "above") is False  # 10 > 5 → ok

    def test_equal(self):
        assert check_threshold(5, 5, "equal") is False  # 5 == 5 → ok
        assert check_threshold(6, 5, "equal") is True  # 6 != 5 → violation

    def test_below_equal(self):
        assert check_threshold(5, 5, "below_equal") is False  # 5 <= 5 → ok
        assert check_threshold(6, 5, "below_equal") is True  # 6 > 5 → violation

    def test_above_equal(self):
        assert check_threshold(5, 5, "above_equal") is False  # 5 >= 5 → ok
        assert check_threshold(4, 5, "above_equal") is True  # 4 < 5 → violation
