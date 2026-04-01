"""Sample utilities - imports external modules only."""

import os
import json
from typing import Any


def read_config(path: str) -> Any:
    with open(path) as f:
        return json.load(f)
