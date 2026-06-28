"""Tests for layer-level architecture rules."""

import os

from archunitpython.layers.assertion.layer_dependencies import LayerDependencyViolation
from archunitpython.layers.fluentapi.layers import project_layers
from archunitpython.testing.assertion import format_violations

FIXTURES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "fixtures", "sample_project"
)


def _sample_layers():
    return (
        project_layers(FIXTURES_DIR)
        .layer("controllers")
        .defined_by_folder("**/controllers*")
        .layer("services")
        .defined_by_folder("**/services*")
        .layer("models")
        .defined_by_folder("**/models*")
    )


class TestLayeredArchitecture:
    def test_layer_allowlist_passes_for_sample_project(self):
        violations = (
            _sample_layers()
            .where_layer("controllers")
            .may_only_depend_on_layers("services")
            .where_layer("services")
            .may_only_depend_on_layers("models")
            .where_layer("models")
            .may_only_depend_on_layers()
            .check()
        )

        assert violations == []

    def test_layer_allowlist_reports_disallowed_dependency(self):
        violations = (
            _sample_layers()
            .where_layer("controllers")
            .may_only_depend_on_layers("models")
            .check()
        )

        layer_violations = [
            violation
            for violation in violations
            if isinstance(violation, LayerDependencyViolation)
        ]
        assert len(layer_violations) == 1
        assert layer_violations[0].source_layer == "controllers"
        assert layer_violations[0].target_layer == "services"

    def test_layer_blocklist_reports_forbidden_dependency(self):
        violations = (
            _sample_layers()
            .where_layer("services")
            .may_not_depend_on_layers("models")
            .check()
        )

        layer_violations = [
            violation
            for violation in violations
            if isinstance(violation, LayerDependencyViolation)
        ]
        assert len(layer_violations) == 1
        assert layer_violations[0].source_layer == "services"
        assert layer_violations[0].target_layer == "models"

    def test_layer_violations_format_cleanly(self):
        violations = (
            _sample_layers()
            .where_layer("controllers")
            .may_only_depend_on_layers("models")
            .check()
        )

        result = format_violations(violations)
        assert "Layer dependency violation" in result
        assert "controllers" in result
        assert "services" in result
