"""ArchUnitPy - Architecture testing library for Python projects."""

__version__ = "0.1.0"

# Files API
from archunitpy.files import project_files, files

# Slices API
from archunitpy.slices import project_slices

# Metrics API
from archunitpy.metrics import metrics

# Testing
from archunitpy.testing import assert_passes, format_violations

# Common
from archunitpy.common import (
    Violation,
    EmptyTestViolation,
    CheckOptions,
    TechnicalError,
    UserError,
)
from archunitpy.common.extraction import extract_graph, clear_graph_cache

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
