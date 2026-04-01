"""Structured logging for architecture checks."""

from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path

from archunitpy.common.logging.types import LoggingOptions

_LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warn": logging.WARNING,
    "error": logging.ERROR,
}


class CheckLogger:
    """Logger specialized for architecture check operations."""

    def __init__(self) -> None:
        self._logger = logging.getLogger("archunitpy")
        self._file_handler: logging.FileHandler | None = None
        self._logger.setLevel(logging.DEBUG)

    def _should_log(self, options: LoggingOptions | None) -> bool:
        if options is None:
            return False
        return options.enabled

    def _ensure_file_handler(self, options: LoggingOptions) -> None:
        if not options.log_file:
            return
        if self._file_handler is not None:
            return

        log_dir = Path(os.getcwd()) / "logs"
        log_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_path = log_dir / f"archunit-{timestamp}.log"

        mode = "a" if options.append_to_log_file else "w"
        self._file_handler = logging.FileHandler(str(log_path), mode=mode)
        self._file_handler.setFormatter(
            logging.Formatter("[%(levelname)s] %(message)s")
        )
        self._logger.addHandler(self._file_handler)

    def _log(self, level: str, options: LoggingOptions | None, message: str) -> None:
        if not self._should_log(options):
            return
        assert options is not None
        log_level = _LOG_LEVELS.get(options.level, logging.INFO)
        msg_level = _LOG_LEVELS.get(level, logging.INFO)
        if msg_level < log_level:
            return
        self._ensure_file_handler(options)
        self._logger.log(msg_level, message)

    def debug(self, options: LoggingOptions | None, message: str) -> None:
        self._log("debug", options, message)

    def info(self, options: LoggingOptions | None, message: str) -> None:
        self._log("info", options, message)

    def warn(self, options: LoggingOptions | None, message: str) -> None:
        self._log("warn", options, message)

    def error(self, options: LoggingOptions | None, message: str) -> None:
        self._log("error", options, message)

    def start_check(self, rule_name: str, options: LoggingOptions | None) -> None:
        self.info(options, f"Starting check: {rule_name}")

    def end_check(
        self, rule_name: str, violation_count: int, options: LoggingOptions | None
    ) -> None:
        self.info(
            options,
            f"Finished check: {rule_name} - {violation_count} violation(s)",
        )

    def log_violation(self, violation: object, options: LoggingOptions | None) -> None:
        self.warn(options, f"Violation: {violation}")

    def log_progress(self, message: str, options: LoggingOptions | None) -> None:
        self.info(options, message)

    def close(self) -> None:
        """Remove file handler if present."""
        if self._file_handler is not None:
            self._logger.removeHandler(self._file_handler)
            self._file_handler.close()
            self._file_handler = None


shared_logger = CheckLogger()
