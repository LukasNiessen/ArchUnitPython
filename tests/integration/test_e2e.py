"""End-to-end integration tests including self-testing."""

import os

import pytest

from archunitpython import (
    assert_passes,
    clear_graph_cache,
    format_violations,
    metrics,
    project_files,
    project_slices,
)
from archunitpython.common.assertion.violation import EmptyTestViolation
from archunitpython.files.assertion.cycle_free import ViolatingCycle

FIXTURES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "fixtures", "sample_project"
)
SRC_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "src", "archunitpython"
)


class TestTopLevelImports:
    """Verify all top-level imports work."""

    def test_import_project_files(self):
        from archunitpython import project_files

        assert callable(project_files)

    def test_import_project_slices(self):
        from archunitpython import project_slices

        assert callable(project_slices)

    def test_import_metrics(self):
        from archunitpython import metrics

        assert callable(metrics)

    def test_import_assert_passes(self):
        from archunitpython import assert_passes

        assert callable(assert_passes)

    def test_import_format_violations(self):
        from archunitpython import format_violations

        assert callable(format_violations)

    def test_version(self):
        import archunitpython

        assert archunitpython.__version__ == "1.0.0"


class TestAssertPasses:
    def setup_method(self):
        clear_graph_cache()

    def test_passing_rule(self):
        rule = project_files(FIXTURES_DIR).should().have_no_cycles()
        assert_passes(rule)

    def test_failing_rule_raises(self):
        # controllers should not depend on services (but they do)
        rule = (
            project_files(FIXTURES_DIR)
            .in_folder("**/controllers*")
            .should_not()
            .depend_on_files()
            .in_folder("**/services*")
        )
        with pytest.raises(AssertionError, match="architecture violation"):
            assert_passes(rule)


class TestFormatViolations:
    def test_no_violations(self):
        result = format_violations([])
        assert "No violations" in result

    def test_with_violations(self):
        from archunitpython.common.projection.types import ProjectedEdge

        violation = ViolatingCycle(
            cycle=[
                ProjectedEdge(source_label="a.py", target_label="b.py"),
                ProjectedEdge(source_label="b.py", target_label="a.py"),
            ]
        )
        result = format_violations([violation])
        assert "1 architecture violation" in result
        assert "Circular dependency" in result


class TestSelfTesting:
    """ArchUnitPython tests its own architecture."""

    def setup_method(self):
        clear_graph_cache()

    def test_no_cycles_in_library(self):
        """The library itself should have no circular dependencies."""
        if not os.path.isdir(SRC_DIR):
            pytest.skip("Source directory not found")
        rule = project_files(SRC_DIR).should().have_no_cycles()
        violations = rule.check()
        cycle_violations = [v for v in violations if isinstance(v, ViolatingCycle)]
        assert len(cycle_violations) == 0, format_violations(cycle_violations)

    def test_common_does_not_depend_on_files(self):
        """common/ should not import from files/."""
        if not os.path.isdir(SRC_DIR):
            pytest.skip("Source directory not found")
        rule = (
            project_files(SRC_DIR)
            .in_folder("**/archunitpython/common*")
            .should_not()
            .depend_on_files()
            .in_folder("**/archunitpython/files*")
        )
        violations = rule.check()
        from archunitpython.files.assertion.depend_on_files import ViolatingFileDependency
        dep_v = [v for v in violations if isinstance(v, ViolatingFileDependency)]
        assert len(dep_v) == 0, format_violations(dep_v)

    def test_common_does_not_depend_on_slices(self):
        """common/ should not import from slices/."""
        if not os.path.isdir(SRC_DIR):
            pytest.skip("Source directory not found")
        rule = (
            project_files(SRC_DIR)
            .in_folder("**/archunitpython/common*")
            .should_not()
            .depend_on_files()
            .in_folder("**/archunitpython/slices*")
        )
        violations = rule.check()
        from archunitpython.files.assertion.depend_on_files import ViolatingFileDependency
        dep_v = [v for v in violations if isinstance(v, ViolatingFileDependency)]
        assert len(dep_v) == 0, format_violations(dep_v)

    def test_common_does_not_depend_on_testing(self):
        """common/ should not import from testing/."""
        if not os.path.isdir(SRC_DIR):
            pytest.skip("Source directory not found")
        rule = (
            project_files(SRC_DIR)
            .in_folder("**/archunitpython/common*")
            .should_not()
            .depend_on_files()
            .in_folder("**/archunitpython/testing*")
        )
        violations = rule.check()
        from archunitpython.files.assertion.depend_on_files import ViolatingFileDependency
        dep_v = [v for v in violations if isinstance(v, ViolatingFileDependency)]
        assert len(dep_v) == 0, format_violations(dep_v)


class TestFullWorkflow:
    """Complete workflow tests combining multiple features."""

    def setup_method(self):
        clear_graph_cache()

    def test_layered_architecture_check(self):
        """Verify controllers → services → models pattern."""
        # controllers should NOT depend on models directly
        rule = (
            project_files(FIXTURES_DIR)
            .in_folder("**/controllers*")
            .should_not()
            .depend_on_files()
            .in_folder("**/models*")
        )
        violations = rule.check()
        from archunitpython.files.assertion.depend_on_files import ViolatingFileDependency
        dep_v = [v for v in violations if isinstance(v, ViolatingFileDependency)]
        assert len(dep_v) == 0

    def test_metrics_on_sample(self):
        rule = (
            metrics(FIXTURES_DIR)
            .count()
            .method_count()
            .should_be_below(100)
        )
        assert_passes(rule)

    def test_custom_condition(self):
        rule = (
            project_files(FIXTURES_DIR)
            .should()
            .adhere_to(
                lambda f: f.lines_of_code < 5000,
                "Files should be under 5000 lines",
            )
        )
        assert_passes(rule)
