"""Verify project setup is correct."""

import re
from pathlib import Path


def test_import():
    import archunitpython

    assert archunitpython.__version__ == "1.1.0"


def test_project_version_matches_package_version():
    import archunitpython

    project_root = Path(__file__).resolve().parents[1]
    pyproject = (project_root / "pyproject.toml").read_text()
    match = re.search(r'^version = "([^"]+)"$', pyproject, re.MULTILINE)

    assert match is not None
    assert archunitpython.__version__ == match.group(1)
