import re

import pytest

from archunitpython import format_violations
from archunitpython.common.projection.types import ProjectedEdge
from archunitpython.files.assertion.cycle_free import ViolatingCycle


@pytest.fixture
def violations():
    return [
        ViolatingCycle(
            cycle=[
                ProjectedEdge(source_label="api.py", target_label="db.py"),
                ProjectedEdge(source_label="db.py", target_label="api.py"),
            ]
        )
    ]


def test_colored_output_preserves_plain_text(violations, monkeypatch):
    monkeypatch.delenv("NO_COLOR", raising=False)
    plain = format_violations(violations, because="keep boundaries clear", color=False)
    colored = format_violations(violations, because="keep boundaries clear", color=True)
    assert "\x1b[1;31m" in colored
    assert "\x1b[34m" in colored
    assert re.sub(r"\x1b\[[0-9;]*m", "", colored) == plain
    assert "1. Circular dependency detected" in plain
    assert "Cycle: api.py -> db.py" in plain


@pytest.mark.parametrize("environment", [{"NO_COLOR": ""}, {"CI": "true"}, {"TERM": "dumb"}])
def test_environment_disables_auto_color(violations, monkeypatch, environment):
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    for key, value in environment.items():
        monkeypatch.setenv(key, value)
    assert "\x1b[" not in format_violations(violations)


def test_redirected_output_is_plain(violations, monkeypatch):
    monkeypatch.setattr("sys.stdout.isatty", lambda: False)
    assert "\x1b[" not in format_violations(violations)


def test_success_color_and_explicit_no_color(monkeypatch):
    monkeypatch.delenv("NO_COLOR", raising=False)
    assert "\x1b[32m" in format_violations([], color=True)
    assert format_violations([], color=False) == "No violations found."
    monkeypatch.setenv("NO_COLOR", "")
    assert format_violations([], color=True) == "No violations found."
