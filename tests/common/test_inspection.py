"""Diagnostics must describe execution without affecting its results."""

import importlib
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

import pytest

from archunitpython import CheckOptions, LoggingOptions, metrics, project_files
from archunitpython.common.fluentapi.inspection import inspect_check
from archunitpython.common.logging.inspection import current_session, debug


@pytest.fixture
def project(tmp_path):
    (tmp_path / "api.py").write_text("import storage\n", encoding="utf-8")
    (tmp_path / "storage.py").write_text(
        "class Storage:\n    def save(self): pass\n", encoding="utf-8"
    )
    return str(tmp_path)


def failing_rule(project):
    return (
        project_files(project)
        .with_name("api.py")
        .should_not()
        .depend_on_files()
        .with_name("storage.py")
    )


def test_default_and_explicit_disabled_are_silent(project, caplog, tmp_path):
    rule = failing_rule(project)
    options = CheckOptions(
        logging=LoggingOptions(
            enabled=False, log_file=True, log_path=str(tmp_path / "disabled.log")
        )
    )
    with caplog.at_level(logging.DEBUG, logger="archunitpython"):
        assert rule.check() == rule.check(options)
    assert not caplog.records
    assert not (tmp_path / "disabled.log").exists()


@pytest.mark.parametrize("level", ["debug", "info", "warn", "error"])
def test_levels_and_unchanged_results(project, caplog, level):
    rule = failing_rule(project)
    baseline = rule.check()
    with caplog.at_level(logging.DEBUG, logger="archunitpython"):
        result = rule.check(
            CheckOptions(clear_cache=True, logging=LoggingOptions(enabled=True, level=level))
        )
    assert result == baseline
    text = caplog.text
    assert ("Starting check" in text) == (level in ("debug", "info"))
    assert ("Violation:" in text) == (level != "error")
    assert ("Discovered file:" in text) == (level == "debug")
    if level == "debug":
        for detail in ("Processing file:", "Dependency:", "Selector ", "Projection:", "cache miss"):
            assert detail in text


def test_selected_source_debug_preserves_lazy_parsing_and_warm_cache(project, caplog, monkeypatch):
    extraction = importlib.import_module("archunitpython.common.extraction.extract_graph")
    original_extract = extraction._extract_located_imports
    parsed_files = []

    def record_parse(path):
        parsed_files.append(Path(path).name)
        return original_extract(path)

    monkeypatch.setattr(extraction, "_extract_located_imports", record_parse)
    rule = failing_rule(project)
    options = CheckOptions(logging=LoggingOptions(enabled=True, level="debug"))
    with caplog.at_level(logging.DEBUG, logger="archunitpython"):
        cold = rule.check(CheckOptions(clear_cache=True, logging=options.logging))
    assert len(cold) == 1
    assert parsed_files == ["api.py"]
    assert "Selected-source edge cache miss: 0/1 files cached" in caplog.text
    assert "Dependency:" in caplog.text

    caplog.clear()
    with caplog.at_level(logging.DEBUG, logger="archunitpython"):
        warm = rule.check(options)
    assert warm == cold
    assert parsed_files == ["api.py"]
    assert "Selected-source edge cache hit: 1/1 files cached" in caplog.text
    assert "Dependency:" in caplog.text


@pytest.mark.parametrize(
    ("source_pattern", "expected_cache_status"),
    [
        ("storage.py", "miss: 0/1 files cached"),
        ("*.py", "partial hit: 1/2 files cached"),
    ],
)
def test_existing_session_reports_uncached_selected_files(
    project, caplog, monkeypatch, source_pattern, expected_cache_status
):
    failing_rule(project).check()
    extraction = importlib.import_module("archunitpython.common.extraction.extract_graph")
    original_extract = extraction._extract_located_imports
    parsed_files = []

    def record_parse(path):
        parsed_files.append(Path(path).name)
        return original_extract(path)

    monkeypatch.setattr(extraction, "_extract_located_imports", record_parse)
    rule = (
        project_files(project)
        .with_name(source_pattern)
        .should_not()
        .depend_on_files()
        .with_name("storage.py")
    )
    with caplog.at_level(logging.DEBUG, logger="archunitpython"):
        rule.check(CheckOptions(logging=LoggingOptions(enabled=True, level="debug")))
    assert parsed_files == ["storage.py"]
    assert f"Selected-source edge cache {expected_cache_status}" in caplog.text
    assert "Selected-source edge cache hit:" not in caplog.text


def test_full_graph_warm_cache_still_describes_graph(project, caplog, monkeypatch):
    rule = project_files(project).should().have_no_cycles()
    baseline = rule.check()
    extraction = importlib.import_module("archunitpython.common.extraction.extract_graph")

    def unexpected_parse(path):
        raise AssertionError(f"Cached graph must not reparse {path}")

    monkeypatch.setattr(extraction, "_extract_located_imports", unexpected_parse)
    with caplog.at_level(logging.DEBUG, logger="archunitpython"):
        result = rule.check(CheckOptions(logging=LoggingOptions(enabled=True, level="debug")))
    assert result == baseline == []
    assert "Graph cache hit" in caplog.text
    assert "Dependency:" in caplog.text


def test_file_only_output_and_append(project, caplog, tmp_path):
    path = tmp_path / "inspection.log"
    path.write_text("old\n", encoding="utf-8")
    options = CheckOptions(
        logging=LoggingOptions(
            enabled=True,
            level="debug",
            console=False,
            log_file=True,
            log_path=str(path),
            append_to_log_file=True,
        )
    )
    rule = failing_rule(project)
    baseline = rule.check()
    assert rule.check(options) == baseline
    assert path.read_text(encoding="utf-8").startswith("old\n")
    assert "Finished check" in path.read_text(encoding="utf-8")
    assert "\x1b" not in path.read_text(encoding="utf-8")
    assert not caplog.records
    path.rename(tmp_path / "closed.log")  # Windows also verifies the handle is closed.


def test_unwritable_log_does_not_change_result(project, tmp_path):
    rule = failing_rule(project)
    baseline = rule.check()
    options = CheckOptions(
        logging=LoggingOptions(enabled=True, log_file=True, console=False, log_path=str(tmp_path))
    )
    assert rule.check(options) == baseline


def test_broken_handler_does_not_change_result(project):
    class BrokenHandler(logging.Handler):
        def emit(self, record):
            raise OSError("sink unavailable")

    logger = logging.getLogger("archunitpython")
    handler = BrokenHandler()
    baseline = failing_rule(project).check()
    logger.addHandler(handler)
    try:
        assert (
            failing_rule(project).check(CheckOptions(logging=LoggingOptions(enabled=True)))
            == baseline
        )
    finally:
        logger.removeHandler(handler)


def test_nested_silent_checks_restore_outer_session(caplog):
    class Rule:
        @inspect_check
        def check(self, options=None):
            debug("outer before")
            if options:
                Rule().check()
            debug("outer after")
            return []

    with caplog.at_level(logging.DEBUG, logger="archunitpython"):
        Rule().check(CheckOptions(logging=LoggingOptions(enabled=True, level="debug")))
    assert caplog.text.count("outer before") == 1
    assert caplog.text.count("outer after") == 1
    assert current_session.get() is None


def test_concurrent_sessions_do_not_mix_files(tmp_path):
    barrier = Barrier(2)

    class Rule:
        def __init__(self, label):
            self.label = label

        @inspect_check
        def check(self, options=None):
            barrier.wait(timeout=10)
            debug("private marker: %s", self.label)
            return []

    def run(label):
        path = tmp_path / f"{label}.log"
        Rule(label).check(
            CheckOptions(
                logging=LoggingOptions(
                    enabled=True, level="debug", console=False, log_file=True, log_path=str(path)
                )
            )
        )
        return path.read_text(encoding="utf-8")

    with ThreadPoolExecutor(max_workers=2) as executor:
        left, right = list(executor.map(run, ["left", "right"]))
    assert "private marker: left" in left and "private marker: right" not in left
    assert "private marker: right" in right and "private marker: left" not in right


def test_original_exception_is_preserved_and_session_closed(caplog):
    error = RuntimeError("analysis failed")

    class Rule:
        @inspect_check
        def check(self, options=None):
            raise error

    with caplog.at_level(logging.DEBUG, logger="archunitpython"):
        with pytest.raises(RuntimeError) as caught:
            Rule().check(CheckOptions(logging=LoggingOptions(enabled=True, level="error")))
    assert caught.value is error
    assert "Check failed" in caplog.text
    assert current_session.get() is None


def test_custom_metric_is_calculated_once_per_class(project, caplog):
    calls = []

    def calculate(cls):
        calls.append(cls.name)
        return 7

    rule = metrics(project).custom_metric("example", "example", calculate).should_be_below(2)
    with caplog.at_level(logging.DEBUG, logger="archunitpython"):
        violations = rule.check(CheckOptions(logging=LoggingOptions(enabled=True, level="debug")))
    assert calls == ["Storage"]
    assert len(violations) == 1
    assert "Custom metric example for Storage: value=7" in caplog.text


def test_debug_does_not_render_objects_at_info_level():
    class Unprintable:
        def __str__(self):
            raise AssertionError("must not stringify disabled debug payload")

    class Rule:
        @inspect_check
        def check(self, options=None):
            debug("payload %s", Unprintable())
            return []

    assert Rule().check(CheckOptions(logging=LoggingOptions(enabled=True, console=False))) == []


def test_inspection_does_not_read_rule_properties(caplog):
    class Rule:
        @property
        def _filters(self):
            raise AssertionError("inspection must not invoke descriptors")

        @inspect_check
        def check(self, options=None):
            return []

    with caplog.at_level(logging.DEBUG, logger="archunitpython"):
        assert Rule().check(CheckOptions(logging=LoggingOptions(enabled=True, level="debug"))) == []


def test_passing_metric_does_not_gain_a_name_requirement(project, caplog):
    from archunitpython.metrics.fluentapi.metrics import ClassMetricCondition

    class Metric:
        @property
        def name(self):
            raise RuntimeError("name unavailable")

        def calculate(self, cls):
            return 0.0

    rule = ClassMetricCondition(project, [], Metric(), 1, "below")
    assert rule.check() == []
    with caplog.at_level(logging.DEBUG, logger="archunitpython"):
        assert rule.check(CheckOptions(logging=LoggingOptions(enabled=True, level="debug"))) == []
    assert "Metric Metric for Storage" in caplog.text
