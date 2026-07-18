"""Load common architecture rules from a JSON configuration file."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from archunitpython.common.assertion.violation import Violation
from archunitpython.common.error.errors import UserError
from archunitpython.common.fluentapi.checkable import Checkable, CheckOptions
from archunitpython.files.fluentapi.files import project_files


@dataclass(frozen=True)
class ConfiguredRule:
    """A named rule loaded from a configuration file."""

    name: str
    rule: Checkable

    def check(self, options: CheckOptions | None = None) -> list[Violation]:
        """Run the configured rule."""
        return self.rule.check(options)


def rules_from_config(config_path: str) -> list[ConfiguredRule]:
    """Load common architecture rules from a JSON config file.

    The fluent Python API remains the primary interface. Config files provide a
    lightweight way to share straightforward rules across projects or teams.
    """
    path = Path(config_path)
    try:
        raw_config = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise UserError(f"Could not read config file: {config_path}") from exc
    except json.JSONDecodeError as exc:
        raise UserError(f"Invalid JSON config file: {config_path}") from exc

    if not isinstance(raw_config, dict):
        raise UserError("Architecture config must be a JSON object.")

    project_path = _optional_string(raw_config, "project_path") or os.getcwd()
    rules = raw_config.get("rules")
    if not isinstance(rules, list):
        raise UserError("Architecture config must define a 'rules' list.")

    base_dir = str(path.parent if path.parent != Path("") else Path.cwd())
    resolved_project_path = _resolve_project_path(base_dir, project_path)

    return [_build_rule(resolved_project_path, item, index) for index, item in enumerate(rules, 1)]


def _build_rule(project_path: str, item: Any, index: int) -> ConfiguredRule:
    if not isinstance(item, dict):
        raise UserError(f"Rule #{index} must be a JSON object.")

    rule_type = _required_string(item, "type", index)
    name = _optional_string(item, "name") or f"{rule_type} rule #{index}"
    rule: Checkable
    if rule_type == "no_cycles":
        subject = _optional_string(item, "subject")
        builder = project_files(project_path)
        if subject is not None:
            rule = builder.in_path(subject).should().have_no_cycles()
        else:
            rule = builder.should().have_no_cycles()
    elif rule_type == "forbidden_dependency":
        source = _required_string(item, "source", index)
        target = _required_string(item, "target", index)
        rule = (
            project_files(project_path)
            .in_path(source)
            .should_not()
            .depend_on_files()
            .in_path(target)
        )
    elif rule_type == "forbidden_external_dependency":
        source = _required_string(item, "source", index)
        module = _required_string(item, "module", index)
        rule = (
            project_files(project_path)
            .in_path(source)
            .should_not()
            .depend_on_external_modules()
            .matching(module)
        )
    else:
        raise UserError(
            f"Unsupported rule type '{rule_type}'. Supported types: "
            "no_cycles, forbidden_dependency, forbidden_external_dependency."
        )

    return ConfiguredRule(name=name, rule=rule)


def _resolve_project_path(base_dir: str, project_path: str) -> str:
    if os.path.isabs(project_path):
        return project_path
    return os.path.abspath(os.path.join(base_dir, project_path))


def _required_string(rule: dict[str, Any], key: str, index: int) -> str:
    value = rule.get(key)
    if not isinstance(value, str) or not value.strip():
        raise UserError(f"Rule #{index} must define a non-empty string '{key}'.")
    return value


def _optional_string(rule: dict[str, Any], key: str) -> str | None:
    value = rule.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise UserError(f"Config value '{key}' must be a non-empty string.")
    return value
