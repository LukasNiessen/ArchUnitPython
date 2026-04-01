"""Core type definitions for pattern matching and filtering."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal, Union

Pattern = Union[str, re.Pattern[str]]
"""A pattern can be a glob string or a compiled regex."""

MatchTarget = Literal["filename", "path", "path-no-filename", "classname"]
MatchType = Literal["exact", "partial"]


@dataclass(frozen=True)
class PatternMatchingOptions:
    """Options controlling how a pattern is matched against file paths."""

    target: MatchTarget = "path"
    matching: MatchType = "partial"


@dataclass(frozen=True)
class Filter:
    """A compiled regex filter with matching options."""

    regexp: re.Pattern[str]
    options: PatternMatchingOptions
