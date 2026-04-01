"""Graph model for dependency analysis."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ImportKind(Enum):
    """Types of Python import statements."""

    IMPORT = "import"  # import foo
    FROM_IMPORT = "from_import"  # from foo import bar
    RELATIVE_IMPORT = "relative"  # from . import bar / from ..foo import bar
    DYNAMIC_IMPORT = "dynamic"  # __import__('foo') / importlib.import_module()
    TYPE_IMPORT = "type"  # inside TYPE_CHECKING block


@dataclass(frozen=True)
class Edge:
    """A dependency edge between two files.

    Represents an import relationship: source imports target.
    """

    source: str
    """Absolute path of the importing file."""

    target: str
    """Absolute path of the imported file (or module name if external)."""

    external: bool
    """True if the target is an external dependency (not part of the project)."""

    import_kinds: tuple[ImportKind, ...] = ()
    """The types of import statements creating this edge."""


Graph = list[Edge]
