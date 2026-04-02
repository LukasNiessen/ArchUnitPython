"""Integration tests for the files fluent API."""

import os

from archunitpython.common.assertion.violation import EmptyTestViolation
from archunitpython.common.extraction.extract_graph import clear_graph_cache
from archunitpython.files.assertion.custom_file_logic import CustomFileViolation
from archunitpython.files.assertion.cycle_free import ViolatingCycle
from archunitpython.files.assertion.depend_on_files import ViolatingFileDependency
from archunitpython.files.fluentapi.files import project_files

FIXTURES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "fixtures", "sample_project"
)


class TestCycleFree:
    def setup_method(self):
        clear_graph_cache()

    def test_no_cycles_in_sample_project(self):
        rule = project_files(FIXTURES_DIR).should().have_no_cycles()
        violations = rule.check()
        # Our sample project has no cycles
        cycle_violations = [v for v in violations if isinstance(v, ViolatingCycle)]
        assert len(cycle_violations) == 0

    def test_cycle_detection_with_filter(self):
        rule = (
            project_files(FIXTURES_DIR)
            .in_folder("**/services*")
            .should()
            .have_no_cycles()
        )
        violations = rule.check()
        cycle_violations = [v for v in violations if isinstance(v, ViolatingCycle)]
        assert len(cycle_violations) == 0


class TestDependOnFiles:
    def setup_method(self):
        clear_graph_cache()

    def test_should_not_depend(self):
        # controllers should not depend on utils
        rule = (
            project_files(FIXTURES_DIR)
            .in_folder("**/controllers*")
            .should_not()
            .depend_on_files()
            .in_folder("**/utils*")
        )
        violations = rule.check()
        dep_violations = [
            v for v in violations if isinstance(v, ViolatingFileDependency)
        ]
        assert len(dep_violations) == 0

    def test_should_not_depend_violation(self):
        # controllers should not depend on services (but they do!)
        rule = (
            project_files(FIXTURES_DIR)
            .in_folder("**/controllers*")
            .should_not()
            .depend_on_files()
            .in_folder("**/services*")
        )
        violations = rule.check()
        dep_violations = [
            v for v in violations if isinstance(v, ViolatingFileDependency)
        ]
        assert len(dep_violations) > 0


class TestCustomCondition:
    def setup_method(self):
        clear_graph_cache()

    def test_lines_of_code_limit(self):
        rule = (
            project_files(FIXTURES_DIR)
            .in_folder("**/services*")
            .should()
            .adhere_to(lambda f: f.lines_of_code < 1000, "File too long")
        )
        violations = rule.check()
        custom_violations = [
            v for v in violations if isinstance(v, CustomFileViolation)
        ]
        assert len(custom_violations) == 0

    def test_extension_check(self):
        rule = (
            project_files(FIXTURES_DIR)
            .should()
            .adhere_to(lambda f: f.extension == ".py", "Must be Python files")
        )
        violations = rule.check()
        custom_violations = [
            v for v in violations if isinstance(v, CustomFileViolation)
        ]
        assert len(custom_violations) == 0


class TestEmptyTestDetection:
    def setup_method(self):
        clear_graph_cache()

    def test_empty_test_violation(self):
        rule = (
            project_files(FIXTURES_DIR)
            .in_folder("**/nonexistent*")
            .should()
            .have_no_cycles()
        )
        violations = rule.check()
        empty_violations = [
            v for v in violations if isinstance(v, EmptyTestViolation)
        ]
        assert len(empty_violations) == 1

    def test_empty_test_allowed(self):
        from archunitpython.common.fluentapi.checkable import CheckOptions

        rule = (
            project_files(FIXTURES_DIR)
            .in_folder("**/nonexistent*")
            .should()
            .have_no_cycles()
        )
        violations = rule.check(CheckOptions(allow_empty_tests=True))
        assert len(violations) == 0


class TestMethodChaining:
    def setup_method(self):
        clear_graph_cache()

    def test_full_chain_no_cycles(self):
        violations = (
            project_files(FIXTURES_DIR)
            .in_folder("**/services*")
            .should()
            .have_no_cycles()
            .check()
        )
        cycle_violations = [v for v in violations if isinstance(v, ViolatingCycle)]
        assert len(cycle_violations) == 0

    def test_full_chain_depend_on(self):
        violations = (
            project_files(FIXTURES_DIR)
            .in_folder("**/controllers*")
            .should_not()
            .depend_on_files()
            .in_folder("**/utils*")
            .check()
        )
        dep_violations = [
            v for v in violations if isinstance(v, ViolatingFileDependency)
        ]
        assert len(dep_violations) == 0

    def test_builder_with_multiple_filters(self):
        violations = (
            project_files(FIXTURES_DIR)
            .in_folder("**/services*")
            .with_name("service*")
            .should()
            .have_no_cycles()
            .check()
        )
        cycle_violations = [v for v in violations if isinstance(v, ViolatingCycle)]
        assert len(cycle_violations) == 0
