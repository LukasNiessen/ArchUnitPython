"""Check that release metadata stays synchronized."""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
PACKAGE_INIT = ROOT / "src" / "archunitpython" / "__init__.py"
CHANGELOG = ROOT / "CHANGELOG.md"


def read_project_version() -> str:
    content = PYPROJECT.read_text(encoding="utf-8")
    match = re.search(r'^version = "([^"]+)"$', content, re.MULTILINE)
    if match is None:
        raise RuntimeError("Could not find project.version in pyproject.toml")
    return match.group(1)


def read_package_version() -> str:
    module = ast.parse(PACKAGE_INIT.read_text(encoding="utf-8"))
    for statement in module.body:
        if (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
            and statement.targets[0].id == "__version__"
            and isinstance(statement.value, ast.Constant)
            and isinstance(statement.value.value, str)
        ):
            return statement.value.value
    raise RuntimeError("Could not find __version__ in src/archunitpython/__init__.py")


def changelog_contains_version(version: str) -> bool:
    content = CHANGELOG.read_text(encoding="utf-8")
    heading_pattern = re.compile(
        rf"^#+\s+(?:\[)?{re.escape(version)}(?:\])?(?:\s|\(|$)",
        re.MULTILINE,
    )
    return heading_pattern.search(content) is not None


def main() -> int:
    project_version = read_project_version()
    package_version = read_package_version()

    errors = []
    if package_version != project_version:
        errors.append(
            f"Package __version__ ({package_version}) does not match "
            f"pyproject.toml version ({project_version})."
        )
    if not changelog_contains_version(project_version):
        errors.append(f"CHANGELOG.md does not contain a heading for version {project_version}.")

    if errors:
        print("Release metadata check failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"Release metadata is synchronized for version {project_version}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
