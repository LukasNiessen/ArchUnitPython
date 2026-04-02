"""ArchUnitPython - Architecture testing library for Python projects."""

__version__ = "0.1.0"

# Files API
from archunitpython.files import project_files, files

# Slices API
from archunitpython.slices import project_slices

# Metrics API
from archunitpython.metrics import metrics

# Testing
from archunitpython.testing import assert_passes, format_violations

# Common
from archunitpython.common import (
    Violation,
    EmptyTestViolation,
    CheckOptions,
    TechnicalError,
    UserError,
)
from archunitpython.common.extraction import extract_graph, clear_graph_cache

__all__ = [
    # Files
    "project_files",
    "files",
    # Slices
    "project_slices",
    # Metrics
    "metrics",
    # Testing
    "assert_passes",
    "format_violations",
    # Common
    "Violation",
    "EmptyTestViolation",
    "CheckOptions",
    "TechnicalError",
    "UserError",
    "extract_graph",
    "clear_graph_cache",
]
