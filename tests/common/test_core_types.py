"""Tests for core types, violations, and errors."""

import re

from archunitpython.common.assertion.violation import EmptyTestViolation, Violation
from archunitpython.common.error.errors import TechnicalError, UserError
from archunitpython.common.fluentapi.checkable import CheckOptions
from archunitpython.common.logging.types import LoggingOptions
from archunitpython.common.types import Filter, PatternMatchingOptions


class TestViolation:
    def test_violation_is_base_class(self):
        v = Violation()
        assert isinstance(v, Violation)

    def test_empty_test_violation_is_violation(self):
        v = EmptyTestViolation(
            filters=["src/**"],
            message="No files found",
        )
        assert isinstance(v, Violation)
        assert v.message == "No files found"
        assert v.filters == ["src/**"]
        assert v.is_negated is False

    def test_empty_test_violation_negated(self):
        v = EmptyTestViolation(
            filters=[],
            message="test",
            is_negated=True,
        )
        assert v.is_negated is True


class TestErrors:
    def test_technical_error(self):
        err = TechnicalError("Config file not found")
        assert isinstance(err, Exception)
        assert str(err) == "Config file not found"

    def test_user_error(self):
        err = UserError("Invalid pattern")
        assert isinstance(err, Exception)
        assert str(err) == "Invalid pattern"

    def test_errors_are_catchable(self):
        try:
            raise TechnicalError("test")
        except TechnicalError as e:
            assert str(e) == "test"

        try:
            raise UserError("test")
        except UserError as e:
            assert str(e) == "test"


class TestTypes:
    def test_pattern_matching_options_defaults(self):
        opts = PatternMatchingOptions()
        assert opts.target == "path"
        assert opts.matching == "partial"

    def test_pattern_matching_options_custom(self):
        opts = PatternMatchingOptions(target="filename", matching="exact")
        assert opts.target == "filename"
        assert opts.matching == "exact"

    def test_pattern_matching_options_frozen(self):
        opts = PatternMatchingOptions()
        try:
            opts.target = "filename"  # type: ignore[misc]
            assert False, "Should raise"
        except AttributeError:
            pass

    def test_filter_creation(self):
        f = Filter(
            regexp=re.compile(r".*\.py$"),
            options=PatternMatchingOptions(target="filename"),
        )
        assert f.regexp.pattern == r".*\.py$"
        assert f.options.target == "filename"

    def test_filter_frozen(self):
        f = Filter(
            regexp=re.compile(r"test"),
            options=PatternMatchingOptions(),
        )
        try:
            f.regexp = re.compile(r"other")  # type: ignore[misc]
            assert False, "Should raise"
        except AttributeError:
            pass


class TestCheckOptions:
    def test_defaults(self):
        opts = CheckOptions()
        assert opts.allow_empty_tests is False
        assert opts.logging is None
        assert opts.clear_cache is False

    def test_custom(self):
        logging = LoggingOptions(enabled=True, level="debug")
        opts = CheckOptions(
            allow_empty_tests=True,
            logging=logging,
            clear_cache=True,
        )
        assert opts.allow_empty_tests is True
        assert opts.logging is not None
        assert opts.logging.enabled is True
        assert opts.logging.level == "debug"
        assert opts.clear_cache is True


class TestLoggingOptions:
    def test_defaults(self):
        opts = LoggingOptions()
        assert opts.enabled is False
        assert opts.level == "info"
        assert opts.log_file is False
        assert opts.append_to_log_file is False

    def test_custom(self):
        opts = LoggingOptions(
            enabled=True,
            level="error",
            log_file=True,
            append_to_log_file=True,
        )
        assert opts.enabled is True
        assert opts.level == "error"
        assert opts.log_file is True
        assert opts.append_to_log_file is True


class TestCheckable:
    def test_checkable_protocol(self):
        """Verify that any class with check() satisfies Checkable."""

        class MyRule:
            def check(self, options=None):
                return []

        rule = MyRule()
        result = rule.check()
        assert result == []
