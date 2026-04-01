"""Architecture tests for the AI RAG Demo using ArchUnitPy.

Demonstrates how ArchUnitPy catches real architecture violations.
Tests marked with @pytest.mark.xfail are INTENTIONAL violations
baked into the demo code to show "hey, it works!".
"""

import os
import re

import pytest

from archunitpy import (
    assert_passes,
    clear_graph_cache,
    format_violations,
    metrics,
    project_files,
    project_slices,
)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUML_PATH = os.path.join(PROJECT_ROOT, "architecture.puml")


@pytest.fixture(autouse=True)
def _clear_cache():
    clear_graph_cache()


# =============================================================================
# PASSING TESTS - These verify the correct parts of the architecture
# =============================================================================


class TestLayeredArchitecturePassing:
    """Tests that PASS - the happy path of our layered architecture."""

    def test_no_circular_dependencies(self):
        """The project should have no circular dependency chains."""
        rule = project_files(PROJECT_ROOT).should().have_no_cycles()
        assert_passes(rule)

    def test_services_do_not_depend_on_api(self):
        """Services layer should never import from the API layer."""
        rule = (
            project_files(PROJECT_ROOT)
            .in_folder("**/services*")
            .should_not()
            .depend_on_files()
            .in_folder("**/api*")
        )
        assert_passes(rule)

    def test_models_do_not_depend_on_services(self):
        """Models layer should never import from services."""
        rule = (
            project_files(PROJECT_ROOT)
            .in_folder("**/models*")
            .should_not()
            .depend_on_files()
            .in_folder("**/services*")
        )
        assert_passes(rule)

    def test_retrieval_does_not_depend_on_api(self):
        """Retrieval layer should never import from API."""
        rule = (
            project_files(PROJECT_ROOT)
            .in_folder("**/retrieval*")
            .should_not()
            .depend_on_files()
            .in_folder("**/api*")
        )
        assert_passes(rule)

    def test_llm_does_not_depend_on_api(self):
        """LLM layer should never import from API."""
        rule = (
            project_files(PROJECT_ROOT)
            .in_folder("**/llm*")
            .should_not()
            .depend_on_files()
            .in_folder("**/api*")
        )
        assert_passes(rule)

    def test_all_files_under_200_lines(self):
        """No file should exceed 200 lines of code."""
        rule = (
            project_files(PROJECT_ROOT)
            .should()
            .adhere_to(
                lambda f: f.lines_of_code < 200,
                "Files should be under 200 lines",
            )
        )
        assert_passes(rule)


class TestMetricsPassing:
    """Metrics tests that PASS."""

    def test_no_god_classes(self):
        """No class should have more than 15 methods."""
        rule = metrics(PROJECT_ROOT).count().method_count().should_be_below(15)
        assert_passes(rule)

    def test_no_data_dumps(self):
        """No class should have more than 10 fields."""
        rule = metrics(PROJECT_ROOT).count().field_count().should_be_below(10)
        assert_passes(rule)


# =============================================================================
# FAILING TESTS - Intentional violations that demonstrate ArchUnitPy detection
# =============================================================================


class TestIntentionalViolations:
    """Tests that FAIL on purpose to demonstrate ArchUnitPy catching violations.

    Each test is marked with xfail so the test suite stays green,
    but the violation messages show exactly what went wrong.
    """

    @pytest.mark.xfail(reason="DEMO: api/bad_shortcut.py bypasses the service layer", strict=True)
    def test_api_should_not_depend_on_retrieval(self):
        """API layer should NOT directly access the retrieval layer.

        VIOLATION: api/bad_shortcut.py imports from retrieval/
        instead of going through services/.
        """
        rule = (
            project_files(PROJECT_ROOT)
            .in_folder("**/api*")
            .should_not()
            .depend_on_files()
            .in_folder("**/retrieval*")
        )
        assert_passes(rule)

    @pytest.mark.xfail(reason="DEMO: shared/leaky.py imports from services", strict=True)
    def test_shared_should_not_depend_on_services(self):
        """Shared/utility layer should NEVER depend on higher layers.

        VIOLATION: shared/leaky.py imports RAGService from services/,
        creating an upward dependency from the lowest layer.
        """
        rule = (
            project_files(PROJECT_ROOT)
            .in_folder("**/shared*")
            .should_not()
            .depend_on_files()
            .in_folder("**/services*")
        )
        assert_passes(rule)

    @pytest.mark.xfail(reason="DEMO: threshold intentionally too strict", strict=True)
    def test_overly_strict_method_count(self):
        """Intentionally too-strict threshold to show metric violations.

        Setting max methods to 2 is unrealistic - RAGService alone has 3.
        """
        rule = metrics(PROJECT_ROOT).count().method_count().should_be_below(2)
        assert_passes(rule)

    @pytest.mark.xfail(reason="DEMO: bad_shortcut.py and leaky.py break the diagram", strict=True)
    def test_slices_adhere_to_diagram(self):
        """All slice dependencies should match the PlantUML diagram.

        VIOLATION: The diagram says api -> services only, but
        bad_shortcut.py creates api -> retrieval. Also shared -> services
        from leaky.py is not in the diagram.
        """
        rule = (
            project_slices(PROJECT_ROOT)
            .defined_by_regex(re.compile(r"/([^/]+)/[^/]+\.py$"))
            .should()
            .adhere_to_diagram_in_file(PUML_PATH)
        )
        assert_passes(rule)


# =============================================================================
# BONUS: Show the actual violation messages
# =============================================================================


class TestShowViolationMessages:
    """These tests print the violation messages so you can see the output."""

    def test_print_api_retrieval_violations(self):
        """Show what ArchUnitPy reports for the API->retrieval violation."""
        rule = (
            project_files(PROJECT_ROOT)
            .in_folder("**/api*")
            .should_not()
            .depend_on_files()
            .in_folder("**/retrieval*")
        )
        violations = rule.check()
        assert len(violations) > 0, "Expected violations but found none"
        print("\n" + format_violations(violations))

    def test_print_shared_services_violations(self):
        """Show what ArchUnitPy reports for the shared->services violation."""
        rule = (
            project_files(PROJECT_ROOT)
            .in_folder("**/shared*")
            .should_not()
            .depend_on_files()
            .in_folder("**/services*")
        )
        violations = rule.check()
        assert len(violations) > 0, "Expected violations but found none"
        print("\n" + format_violations(violations))
