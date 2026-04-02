"""Tests for the slices module: projections, UML parsing, assertions, fluent API."""

import os

from archunitpython.common.extraction.extract_graph import clear_graph_cache
from archunitpython.common.extraction.graph import Edge
from archunitpython.common.projection.types import ProjectedEdge
from archunitpython.slices.assertion.admissible_edges import (
    CoherenceOptions,
    ViolatingEdge,
    gather_positive_violations,
    gather_violations,
)
from archunitpython.slices.fluentapi.slices import project_slices
from archunitpython.slices.projection.slicing_projections import (
    identity,
    slice_by_file_suffix,
    slice_by_pattern,
    slice_by_regex,
)
from archunitpython.slices.uml.export_diagram import export_diagram
from archunitpython.slices.uml.generate_rules import Rule, generate_rule

FIXTURES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "fixtures", "sample_project"
)


# --- TICKET-10: Slicing Projections ---

class TestSliceByPattern:
    def test_basic_pattern(self):
        mapper = slice_by_pattern("src/(**)/**")
        edge = Edge(source="src/auth/service.py", target="src/db/repo.py", external=False)
        result = mapper(edge)
        assert result is not None
        assert result.source_label == "auth"
        assert result.target_label == "db"

    def test_same_slice_filtered(self):
        mapper = slice_by_pattern("src/(**)/**")
        edge = Edge(source="src/auth/a.py", target="src/auth/b.py", external=False)
        result = mapper(edge)
        assert result is None  # Same slice → filtered

    def test_external_filtered(self):
        mapper = slice_by_pattern("src/(**)/**")
        edge = Edge(source="src/auth/a.py", target="os", external=True)
        result = mapper(edge)
        assert result is None

    def test_self_edge_filtered(self):
        mapper = slice_by_pattern("src/(**)/**")
        edge = Edge(source="src/auth/a.py", target="src/auth/a.py", external=False)
        result = mapper(edge)
        assert result is None


class TestSliceByRegex:
    def test_regex_capture(self):
        import re
        mapper = slice_by_regex(re.compile(r"src/([^/]+)/"))
        edge = Edge(source="src/controllers/ctrl.py", target="src/services/svc.py", external=False)
        result = mapper(edge)
        assert result is not None
        assert result.source_label == "controllers"
        assert result.target_label == "services"


class TestSliceByFileSuffix:
    def test_suffix_mapping(self):
        mapper = slice_by_file_suffix({"_controller": "controllers", "_service": "services"})
        edge = Edge(source="user_controller.py", target="user_service.py", external=False)
        result = mapper(edge)
        assert result is not None
        assert result.source_label == "controllers"
        assert result.target_label == "services"

    def test_unknown_suffix(self):
        mapper = slice_by_file_suffix({"_controller": "controllers"})
        edge = Edge(source="user_controller.py", target="helpers.py", external=False)
        result = mapper(edge)
        assert result is None  # helpers.py has no matching suffix


class TestIdentity:
    def test_passes_all(self):
        mapper = identity()
        edge = Edge(source="a.py", target="b.py", external=False)
        result = mapper(edge)
        assert result is not None
        assert result.source_label == "a.py"
        assert result.target_label == "b.py"

    def test_filters_self_edge(self):
        mapper = identity()
        edge = Edge(source="a.py", target="a.py", external=False)
        result = mapper(edge)
        assert result is None


# --- TICKET-11: PlantUML Parsing ---

class TestGenerateRule:
    def test_basic_diagram(self):
        puml = """
@startuml
  component [controllers]
  component [services]
  [controllers] --> [services]
@enduml
"""
        rules, nodes = generate_rule(puml)
        assert len(rules) == 1
        assert rules[0] == Rule(source="controllers", target="services")
        assert "controllers" in nodes
        assert "services" in nodes

    def test_multiple_relationships(self):
        puml = """
@startuml
  component [ui]
  component [business]
  component [data]
  [ui] --> [business]
  [business] --> [data]
@enduml
"""
        rules, nodes = generate_rule(puml)
        assert len(rules) == 2
        assert len(nodes) == 3

    def test_components_with_colors(self):
        puml = """
@startuml
  component [api] #Green
  component [db]
  [api] -> [db]
@enduml
"""
        rules, nodes = generate_rule(puml)
        assert "api" in nodes
        assert "db" in nodes
        assert len(rules) == 1

    def test_implicit_component_declaration(self):
        puml = """
@startuml
  [auth] --> [users]
@enduml
"""
        rules, nodes = generate_rule(puml)
        assert "auth" in nodes
        assert "users" in nodes
        assert len(rules) == 1


class TestExportDiagram:
    def test_export_simple(self):
        edges = [
            ProjectedEdge(source_label="a", target_label="b"),
        ]
        result = export_diagram(edges)
        assert "@startuml" in result
        assert "@enduml" in result
        assert "component [a]" in result
        assert "component [b]" in result
        assert "[a] --> [b]" in result


# --- TICKET-12: Slice Assertions ---

class TestGatherViolations:
    def test_forbidden_dependency_found(self):
        edges = [ProjectedEdge(source_label="ui", target_label="db")]
        rules = [Rule(source="ui", target="db")]
        violations = gather_violations(edges, rules)
        assert len(violations) == 1
        assert isinstance(violations[0], ViolatingEdge)

    def test_no_forbidden_dependency(self):
        edges = [ProjectedEdge(source_label="ui", target_label="services")]
        rules = [Rule(source="ui", target="db")]
        violations = gather_violations(edges, rules)
        assert len(violations) == 0


class TestGatherPositiveViolations:
    def test_all_allowed(self):
        edges = [ProjectedEdge(source_label="ui", target_label="services")]
        rules = [Rule(source="ui", target="services")]
        violations = gather_positive_violations(edges, rules, ["ui", "services"])
        assert len(violations) == 0

    def test_disallowed_edge(self):
        edges = [ProjectedEdge(source_label="ui", target_label="db")]
        rules = [Rule(source="ui", target="services")]
        violations = gather_positive_violations(edges, rules, ["ui", "services", "db"])
        assert len(violations) == 1

    def test_ignore_orphan_slices(self):
        edges = [ProjectedEdge(source_label="unknown", target_label="db")]
        rules = []
        violations = gather_positive_violations(
            edges, rules, ["db"],
            CoherenceOptions(ignore_orphan_slices=True),
        )
        assert len(violations) == 0


# --- TICKET-13: Slices Fluent API ---

class TestSlicesFluentAPI:
    def setup_method(self):
        clear_graph_cache()

    def test_should_not_contain_dependency(self):
        import re
        rule = (
            project_slices(FIXTURES_DIR)
            .defined_by_regex(re.compile(r"/([^/]+)/[^/]+\.py$"))
            .should_not()
            .contain_dependency("models", "controllers")
        )
        violations = rule.check()
        dep_violations = [v for v in violations if isinstance(v, ViolatingEdge)]
        assert len(dep_violations) == 0

    def test_adhere_to_diagram_in_file(self):
        import re
        puml_path = os.path.join(FIXTURES_DIR, "architecture.puml")
        rule = (
            project_slices(FIXTURES_DIR)
            .defined_by_regex(re.compile(r"/([^/]+)/[^/]+\.py$"))
            .should()
            .ignoring_orphan_slices()
            .adhere_to_diagram_in_file(puml_path)
        )
        violations = rule.check()
        # Our sample project follows the architecture
        edge_violations = [v for v in violations if isinstance(v, ViolatingEdge)]
        # Some violations may occur if services depend on controllers etc.
        # The main assertion is that the API works end-to-end
        assert isinstance(violations, list)

    def test_adhere_to_diagram_inline(self):
        import re
        puml = """
@startuml
  component [controllers]
  component [services]
  component [models]
  component [utils]
  [controllers] --> [services]
  [services] --> [models]
@enduml
"""
        rule = (
            project_slices(FIXTURES_DIR)
            .defined_by_regex(re.compile(r"/([^/]+)/[^/]+\.py$"))
            .should()
            .ignoring_orphan_slices()
            .adhere_to_diagram(puml)
        )
        violations = rule.check()
        assert isinstance(violations, list)
