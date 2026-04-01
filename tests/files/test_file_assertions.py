"""Tests for file-level assertion/violation gathering functions."""

import os

from archunitpy.common.extraction.graph import Edge
from archunitpy.common.projection.types import ProjectedEdge, ProjectedNode
from archunitpy.common.regex_factory import RegexFactory
from archunitpy.files.assertion.custom_file_logic import (
    CustomFileViolation,
    FileInfo,
    _build_file_info,
    gather_custom_file_violations,
)
from archunitpy.files.assertion.cycle_free import (
    ViolatingCycle,
    gather_cycle_violations,
)
from archunitpy.files.assertion.depend_on_files import (
    ViolatingFileDependency,
    gather_depend_on_file_violations,
)
from archunitpy.files.assertion.matching_files import (
    ViolatingNode,
    gather_regex_matching_violations,
)

FIXTURES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "fixtures", "sample_project"
)


def _node(label: str) -> ProjectedNode:
    return ProjectedNode(label=label)


def _edge(src: str, tgt: str) -> ProjectedEdge:
    return ProjectedEdge(source_label=src, target_label=tgt)


class TestMatchingFiles:
    def test_should_positive_no_violation(self):
        nodes = [_node("src/services/service.py")]
        filters = [RegexFactory.filename_matcher("*.py")]
        violations = gather_regex_matching_violations(nodes, filters, is_negated=False)
        assert len(violations) == 0

    def test_should_positive_violation(self):
        nodes = [_node("src/services/service.ts")]
        filters = [RegexFactory.filename_matcher("*.py")]
        violations = gather_regex_matching_violations(nodes, filters, is_negated=False)
        assert len(violations) == 1
        assert isinstance(violations[0], ViolatingNode)
        assert not violations[0].is_negated

    def test_should_not_negative_violation(self):
        nodes = [_node("src/services/service.py")]
        filters = [RegexFactory.filename_matcher("*.py")]
        violations = gather_regex_matching_violations(nodes, filters, is_negated=True)
        assert len(violations) == 1
        assert violations[0].is_negated

    def test_should_not_negative_no_violation(self):
        nodes = [_node("src/services/service.ts")]
        filters = [RegexFactory.filename_matcher("*.py")]
        violations = gather_regex_matching_violations(nodes, filters, is_negated=True)
        assert len(violations) == 0


class TestDependOnFiles:
    def test_should_not_violation(self):
        edges = [_edge("src/ui/view.py", "src/db/database.py")]
        subject = [RegexFactory.folder_matcher("src/ui*")]
        obj = [RegexFactory.folder_matcher("src/db*")]
        violations = gather_depend_on_file_violations(edges, subject, obj, is_negated=True)
        assert len(violations) == 1
        assert isinstance(violations[0], ViolatingFileDependency)

    def test_should_not_no_violation(self):
        edges = [_edge("src/ui/view.py", "src/services/service.py")]
        subject = [RegexFactory.folder_matcher("src/ui*")]
        obj = [RegexFactory.folder_matcher("src/db*")]
        violations = gather_depend_on_file_violations(edges, subject, obj, is_negated=True)
        assert len(violations) == 0

    def test_non_matching_subject_skipped(self):
        edges = [_edge("src/other/file.py", "src/db/database.py")]
        subject = [RegexFactory.folder_matcher("src/ui*")]
        obj = [RegexFactory.folder_matcher("src/db*")]
        violations = gather_depend_on_file_violations(edges, subject, obj, is_negated=True)
        assert len(violations) == 0


class TestCycleFree:
    def test_no_cycles_no_violations(self):
        violations = gather_cycle_violations([])
        assert len(violations) == 0

    def test_cycles_become_violations(self):
        cycle = [_edge("a.py", "b.py"), _edge("b.py", "a.py")]
        violations = gather_cycle_violations([cycle])
        assert len(violations) == 1
        assert isinstance(violations[0], ViolatingCycle)
        assert len(violations[0].cycle) == 2

    def test_multiple_cycles(self):
        cycle1 = [_edge("a.py", "b.py"), _edge("b.py", "a.py")]
        cycle2 = [_edge("c.py", "d.py"), _edge("d.py", "c.py")]
        violations = gather_cycle_violations([cycle1, cycle2])
        assert len(violations) == 2


class TestCustomFileLogic:
    def test_build_file_info(self):
        path = os.path.join(FIXTURES_DIR, "models", "model.py")
        info = _build_file_info(path)
        assert info.name == "model"
        assert info.extension == ".py"
        assert "class User" in info.content
        assert info.lines_of_code > 0

    def test_custom_condition_passes(self):
        path = os.path.join(FIXTURES_DIR, "models", "model.py")
        nodes = [_node(path)]
        violations = gather_custom_file_violations(
            nodes,
            condition=lambda f: f.lines_of_code < 1000,
            message="File too long",
            is_negated=False,
            pre_filters=[],
        )
        assert len(violations) == 0

    def test_custom_condition_fails(self):
        path = os.path.join(FIXTURES_DIR, "models", "model.py")
        nodes = [_node(path)]
        violations = gather_custom_file_violations(
            nodes,
            condition=lambda f: f.lines_of_code > 1000,
            message="File too short",
            is_negated=False,
            pre_filters=[],
        )
        assert len(violations) == 1
        assert isinstance(violations[0], CustomFileViolation)
        assert violations[0].message == "File too short"

    def test_custom_condition_with_filter(self):
        path_py = os.path.join(FIXTURES_DIR, "models", "model.py")
        path_init = os.path.join(FIXTURES_DIR, "models", "__init__.py")
        nodes = [_node(path_py), _node(path_init)]
        violations = gather_custom_file_violations(
            nodes,
            condition=lambda f: False,  # Always fails
            message="test",
            is_negated=False,
            pre_filters=[RegexFactory.filename_matcher("model.py")],
        )
        # Only model.py should be checked (not __init__.py)
        assert len(violations) == 1
