"""Terminal color utilities for formatted output."""

from __future__ import annotations

import os
import sys


def _supports_color() -> bool:
    """Check if the terminal supports ANSI colors."""
    if "NO_COLOR" in os.environ or os.environ.get("CI", "").lower() == "true":
        return False
    if os.environ.get("TERM") == "dumb":
        return False
    if not hasattr(sys.stdout, "isatty"):
        return False
    return sys.stdout.isatty()


def _wrap(code: str, text: str) -> str:
    if not _supports_color():
        return text
    return f"\033[{code}m{text}\033[0m"


class ColorUtils:
    """ANSI color utilities for terminal output."""

    @staticmethod
    def style(text: str, code: str, enabled: bool | None = None) -> str:
        """Style text with automatic detection or an explicit color choice."""
        if enabled is False or "NO_COLOR" in os.environ:
            return text
        if enabled is None and not _supports_color():
            return text
        return f"\033[{code}m{text}\033[0m"

    @staticmethod
    def red(text: str) -> str:
        return _wrap("31", text)

    @staticmethod
    def green(text: str) -> str:
        return _wrap("32", text)

    @staticmethod
    def yellow(text: str) -> str:
        return _wrap("33", text)

    @staticmethod
    def blue(text: str) -> str:
        return _wrap("34", text)

    @staticmethod
    def magenta(text: str) -> str:
        return _wrap("35", text)

    @staticmethod
    def cyan(text: str) -> str:
        return _wrap("36", text)

    @staticmethod
    def bold(text: str) -> str:
        return _wrap("1", text)

    @staticmethod
    def dim(text: str) -> str:
        return _wrap("2", text)
