"""Synchronize release version metadata for semantic-release."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
PACKAGE_INIT = ROOT / "src" / "archunitpython" / "__init__.py"


def replace_once(pattern: str, replacement: str, content: str, path: Path) -> str:
    updated, count = re.subn(pattern, replacement, content, count=1, flags=re.MULTILINE)
    if count != 1:
        raise RuntimeError(f"Could not update version in {path}")
    return updated


def bump_version(version: str) -> None:
    pyproject = PYPROJECT.read_text(encoding="utf-8")
    PYPROJECT.write_text(
        replace_once(r'^version = "[^"]+"$', f'version = "{version}"', pyproject, PYPROJECT),
        encoding="utf-8",
    )

    package_init = PACKAGE_INIT.read_text(encoding="utf-8")
    PACKAGE_INIT.write_text(
        replace_once(
            r'^__version__ = "[^"]+"$',
            f'__version__ = "{version}"',
            package_init,
            PACKAGE_INIT,
        ),
        encoding="utf-8",
    )


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/bump_release_version.py <version>", file=sys.stderr)
        return 2

    bump_version(sys.argv[1])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
