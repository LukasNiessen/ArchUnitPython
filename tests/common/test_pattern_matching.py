"""Tests for pattern matching and regex factory."""

import re

from archunitpy.common.pattern_matching import (
    extract_filename,
    matches_all_patterns,
    matches_any_pattern,
    matches_pattern,
    matches_pattern_classname,
    normalize_path,
    path_without_filename,
)
from archunitpy.common.regex_factory import RegexFactory


class TestNormalizePath:
    def test_forward_slashes_unchanged(self):
        assert normalize_path("src/models/user.py") == "src/models/user.py"

    def test_backslashes_converted(self):
        assert normalize_path("src\\models\\user.py") == "src/models/user.py"

    def test_mixed_slashes(self):
        assert normalize_path("src\\models/user.py") == "src/models/user.py"

    def test_empty_string(self):
        assert normalize_path("") == ""


class TestExtractFilename:
    def test_simple_path(self):
        assert extract_filename("src/models/user.py") == "user.py"

    def test_windows_path(self):
        assert extract_filename("src\\models\\user.py") == "user.py"

    def test_just_filename(self):
        assert extract_filename("user.py") == "user.py"

    def test_deep_path(self):
        assert extract_filename("a/b/c/d/e.py") == "e.py"


class TestPathWithoutFilename:
    def test_simple_path(self):
        assert path_without_filename("src/models/user.py") == "src/models"

    def test_windows_path(self):
        assert path_without_filename("src\\models\\user.py") == "src/models"

    def test_just_filename(self):
        assert path_without_filename("user.py") == ""

    def test_deep_path(self):
        assert path_without_filename("a/b/c/d/e.py") == "a/b/c/d"


class TestRegexFactory:
    def test_filename_matcher_glob(self):
        f = RegexFactory.filename_matcher("*.py")
        assert f.options.target == "filename"
        assert matches_pattern("src/service.py", f)
        assert not matches_pattern("src/service.ts", f)

    def test_filename_matcher_regex(self):
        f = RegexFactory.filename_matcher(re.compile(r".*Service.*\.py"))
        assert matches_pattern("src/UserService.py", f)
        assert not matches_pattern("src/user_model.py", f)

    def test_filename_matcher_service_pattern(self):
        f = RegexFactory.filename_matcher("*Service*")
        assert matches_pattern("src/UserService.py", f)
        assert matches_pattern("src/services/ServiceA.py", f)
        assert not matches_pattern("src/user_model.py", f)

    def test_classname_matcher(self):
        f = RegexFactory.classname_matcher("*Service*")
        assert f.options.target == "classname"

    def test_folder_matcher(self):
        f = RegexFactory.folder_matcher("src/models*")
        assert f.options.target == "path-no-filename"
        assert matches_pattern("src/models/user.py", f)
        assert not matches_pattern("src/controllers/user.py", f)

    def test_path_matcher(self):
        f = RegexFactory.path_matcher("src/*/user.py")
        assert f.options.target == "path"
        assert matches_pattern("src/models/user.py", f)
        assert not matches_pattern("src/models/product.py", f)

    def test_exact_file_matcher(self):
        f = RegexFactory.exact_file_matcher("src/models/user.py")
        assert matches_pattern("src/models/user.py", f)
        assert not matches_pattern("src/models/user.py/extra", f)
        assert not matches_pattern("prefix/src/models/user.py", f)

    def test_exact_file_matcher_windows_path(self):
        f = RegexFactory.exact_file_matcher("src\\models\\user.py")
        assert matches_pattern("src/models/user.py", f)

    def test_folder_matcher_wildcard(self):
        f = RegexFactory.folder_matcher("src/**/services")
        assert matches_pattern("src/app/services/service.py", f)

    def test_path_matcher_double_star(self):
        f = RegexFactory.path_matcher("src/**/*.py")
        assert matches_pattern("src/models/user.py", f)
        assert matches_pattern("src/deep/nested/file.py", f)


class TestMatchesPattern:
    def test_filename_target(self):
        f = RegexFactory.filename_matcher("*.py")
        assert matches_pattern("src/file.py", f)
        assert not matches_pattern("src/file.txt", f)

    def test_path_target(self):
        f = RegexFactory.path_matcher("src/*.py")
        assert matches_pattern("src/file.py", f)
        assert not matches_pattern("tests/file.py", f)

    def test_path_no_filename_target(self):
        f = RegexFactory.folder_matcher("src/models*")
        assert matches_pattern("src/models/file.py", f)
        assert not matches_pattern("src/controllers/file.py", f)


class TestMatchesPatternClassname:
    def test_classname_target(self):
        f = RegexFactory.classname_matcher("*Service*")
        assert matches_pattern_classname("UserService", "src/service.py", f)
        assert not matches_pattern_classname("UserModel", "src/model.py", f)

    def test_filename_target_for_class(self):
        f = RegexFactory.filename_matcher("*service*")
        assert matches_pattern_classname("Anything", "src/user_service.py", f)
        assert not matches_pattern_classname("Anything", "src/user_model.py", f)


class TestMatchesAllPatterns:
    def test_all_match(self):
        filters = [
            RegexFactory.path_matcher("src/*"),
            RegexFactory.filename_matcher("*.py"),
        ]
        assert matches_all_patterns("src/file.py", filters)

    def test_one_fails(self):
        filters = [
            RegexFactory.path_matcher("src/*"),
            RegexFactory.filename_matcher("*.ts"),
        ]
        assert not matches_all_patterns("src/file.py", filters)

    def test_empty_filters(self):
        assert matches_all_patterns("anything", [])


class TestMatchesAnyPattern:
    def test_one_matches(self):
        filters = [
            RegexFactory.path_matcher("tests/*"),
            RegexFactory.path_matcher("src/*"),
        ]
        assert matches_any_pattern("src/file.py", filters)

    def test_none_match(self):
        filters = [
            RegexFactory.path_matcher("tests/*"),
            RegexFactory.path_matcher("lib/*"),
        ]
        assert not matches_any_pattern("src/file.py", filters)

    def test_empty_filters(self):
        assert not matches_any_pattern("anything", [])
