"""Sample utilities - imports external modules only."""

import json
import os
from typing import Any


def read_config(path: str) -> Any:
    with open(path) as f:
        return json.load(f)


def platform_name() -> str:
    return os.name
