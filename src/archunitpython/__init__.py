"""ArchUnitPython - Architecture testing library for Python projects."""

__version__ = "1.0.0"

# Files API
# Common
from archunitpython.common import (
    CheckOptions,
    EmptyTestViolation,
    TechnicalError,
    UserError,
    Violation,
)
from archunitpython.common.extraction import clear_graph_cache, extract_graph
from archunitpython.files import files, project_files

# Metrics API
from archunitpython.metrics import metrics

# Slices API
from archunitpython.slices import project_slices

# Testing
from archunitpython.testing import assert_passes, format_violations

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
