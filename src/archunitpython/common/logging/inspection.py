"""Per-check diagnostic sessions, isolated from architecture evaluation."""

from __future__ import annotations

import logging
import sys
from contextvars import ContextVar
from datetime import datetime
from pathlib import Path
from typing import TextIO

from archunitpython.common.logging.types import LoggingOptions

_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warn": logging.WARNING,
    "error": logging.ERROR,
}


class InspectionSession:
    """Own a check's output without attaching process-wide logging handlers.

    Diagnostics are best effort: formatting and output errors must never replace
    a rule result or an exception raised by the analysis itself.
    """

    def __init__(self, options: LoggingOptions) -> None:
        self.options = options
        self._file: TextIO | None = None
        self._file_attempted = False

    def emit(self, level: str, message: str, *args: object) -> None:
        if _LEVELS[level] < _LEVELS.get(self.options.level, logging.INFO):
            return
        try:
            text = message % args if args else message
        except Exception:
            return
        if self.options.console:
            try:
                logger = logging.getLogger("archunitpython")
                if logger.hasHandlers():
                    logger.log(_LEVELS[level], text)
                else:
                    sys.stderr.write(f"[{level.upper()}] {text}\n")
            except Exception:
                pass
        if self.options.log_file:
            try:
                if not self._file_attempted:
                    self._file_attempted = True
                    path = (
                        Path(self.options.log_path)
                        if self.options.log_path
                        else Path("logs")
                        / datetime.now().strftime("archunit-%Y-%m-%d_%H-%M-%S-%f.log")
                    )
                    path.parent.mkdir(parents=True, exist_ok=True)
                    self._file = path.open(
                        "a" if self.options.append_to_log_file else "w", encoding="utf-8"
                    )
                if self._file is not None:
                    self._file.write(f"[{datetime.now().isoformat()}] [{level.upper()}] {text}\n")
                    self._file.flush()
            except Exception:
                self.close()

    def close(self) -> None:
        if self._file is not None:
            try:
                self._file.close()
            except Exception:
                pass
            self._file = None


current_session: ContextVar[InspectionSession | None] = ContextVar(
    "archunitpython_inspection", default=None
)


def debug(message: str, *args: object) -> None:
    """Lazily emit details only inside an enabled debug check."""
    session = current_session.get()
    if session is not None:
        session.emit("debug", message, *args)


def debug_enabled() -> bool:
    """Guard expensive diagnostic traversal before constructing its details."""
    session = current_session.get()
    return session is not None and session.options.level == "debug"
