"""Integration tests for the files fluent API."""

import os
import shutil
from pathlib import Path
from uuid import uuid4

from archunitpython.common.assertion.violation import EmptyTestViolation
from archunitpython.common.extraction.extract_graph import clear_graph_cache
from archunitpython.files.assertion.custom_file_logic import CustomFileViolation
from archunitpython.files.assertion.cycle_free import ViolatingCycle
from archunitpython.files.assertion.depend_on_external_modules import (
    ViolatingExternalModuleDependency,
)
from archunitpython.files.assertion.depend_on_files import ViolatingFileDependency
from archunitpython.files.fluentapi.files import project_files
from archunitpython.testing.assertion import format_violations

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


class TestDependOnExternalModules:
    def setup_method(self):
        clear_graph_cache()

    def test_should_not_depend_on_specific_external_module(self):
        rule = (
            project_files(FIXTURES_DIR)
            .in_folder("**/utils*")
            .should_not()
            .depend_on_external_modules()
            .matching("json")
        )
        violations = rule.check()
        dep_violations = [
            v
            for v in violations
            if isinstance(v, ViolatingExternalModuleDependency)
        ]
        assert len(dep_violations) == 1
        assert dep_violations[0].dependency.target_label == "json"

    def test_should_not_depend_on_unmatched_external_module(self):
        rule = (
            project_files(FIXTURES_DIR)
            .in_folder("**/utils*")
            .should_not()
            .depend_on_external_modules()
            .matching("requests")
        )
        violations = rule.check()
        dep_violations = [
            v
            for v in violations
            if isinstance(v, ViolatingExternalModuleDependency)
        ]
        assert len(dep_violations) == 0

    def test_matching_multiple_external_modules_uses_or_semantics(self):
        rule = (
            project_files(FIXTURES_DIR)
            .in_folder("**/utils*")
            .should_not()
            .depend_on_external_modules()
            .matching("json")
            .matching("typing")
        )
        violations = rule.check()
        dep_violations = [
            v
            for v in violations
            if isinstance(v, ViolatingExternalModuleDependency)
        ]
        assert {v.dependency.target_label for v in dep_violations} == {
            "json",
            "typing",
        }

    def test_positive_external_dependency_rule_acts_as_allowlist(self):
        rule = (
            project_files(FIXTURES_DIR)
            .in_folder("**/utils*")
            .should()
            .depend_on_external_modules()
            .matching("typing")
        )
        violations = rule.check()
        dep_violations = [
            v
            for v in violations
            if isinstance(v, ViolatingExternalModuleDependency)
        ]
        assert {v.dependency.target_label for v in dep_violations} == {
            "json",
            "os",
        }

    def test_external_dependency_violations_format_cleanly(self):
        rule = (
            project_files(FIXTURES_DIR)
            .in_folder("**/utils*")
            .should_not()
            .depend_on_external_modules()
            .matching("json")
        )
        violations = rule.check()
        result = format_violations(violations)
        assert "External module dependency violation" in result
        assert "external module 'json'" in result


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


class TestTypeCheckingImports:
    def setup_method(self):
        clear_graph_cache()

    def _build_type_checking_project(self) -> str:
        temp_root = Path(__file__).resolve().parent / ".tmp"
        temp_root.mkdir(exist_ok=True)
        project_root = temp_root / f"project_{uuid4().hex}"
        project_root.mkdir()

        services_dir = project_root / "sample_project" / "services"
        models_dir = project_root / "sample_project" / "models"
        services_dir.mkdir(parents=True, exist_ok=True)
        models_dir.mkdir(parents=True, exist_ok=True)

        for package_dir in (
            project_root / "sample_project",
            services_dir,
            models_dir,
        ):
            (package_dir / "__init__.py").write_text("", encoding="utf-8")

        (models_dir / "model.py").write_text(
            "class User:\n    pass\n",
            encoding="utf-8",
        )
        (services_dir / "service.py").write_text(
            "\n".join(
                [
                    "from typing import TYPE_CHECKING",
                    "",
                    "if TYPE_CHECKING:",
                    "    from sample_project.models.model import User",
                    "",
                    "def get_user() -> str:",
                    '    return "ok"',
                    "",
                ]
            ),
            encoding="utf-8",
        )
        self._temp_dir = project_root
        return str(project_root)

    def teardown_method(self):
        temp_dir = getattr(self, "_temp_dir", None)
        if temp_dir is not None:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_type_checking_imports_affect_rules_by_default(self):
        project_root = self._build_type_checking_project()
        rule = (
            project_files(project_root)
            .in_folder("**/services*")
            .should_not()
            .depend_on_files()
            .in_folder("**/models*")
        )
        violations = rule.check()
        dep_violations = [
            v for v in violations if isinstance(v, ViolatingFileDependency)
        ]
        assert len(dep_violations) == 1

    def test_type_checking_imports_can_be_ignored_for_rules(self):
        from archunitpython.common.fluentapi.checkable import CheckOptions

        project_root = self._build_type_checking_project()
        rule = (
            project_files(project_root)
            .in_folder("**/services*")
            .should_not()
            .depend_on_files()
            .in_folder("**/models*")
        )
        violations = rule.check(
            CheckOptions(ignore_type_checking_imports=True)
        )
        dep_violations = [
            v for v in violations if isinstance(v, ViolatingFileDependency)
        ]
        assert len(dep_violations) == 0
