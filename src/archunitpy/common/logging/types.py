"""Logging configuration types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

LogLevel = Literal["debug", "info", "warn", "error"]


@dataclass(frozen=True)
class LoggingOptions:
    """Options for controlling logging during architecture checks."""

    enabled: bool = False
    level: LogLevel = "info"
    log_file: bool = False
    append_to_log_file: bool = False
