"""Tests for loading architecture rules from JSON config files."""

import json
import shutil
from pathlib import Path
from uuid import uuid4

import pytest

from archunitpython.common.error.errors import UserError
from archunitpython.config import rules_from_config
from archunitpython.files.assertion.depend_on_external_modules import (
    ViolatingExternalModuleDependency,
)
from archunitpython.files.assertion.depend_on_files import ViolatingFileDependency


class TestRulesFromConfig:
    def setup_method(self):
        self._temp_dir = Path(__file__).resolve().parent / ".tmp" / f"project_{uuid4().hex}"
        self._temp_dir.mkdir(parents=True)

    def teardown_method(self):
        shutil.rmtree(self._temp_dir, ignore_errors=True)

    def _write(self, relative_path: str, content: str) -> None:
        path = self._temp_dir / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def _write_config(self, config: dict[str, object]) -> str:
        path = self._temp_dir / "archunitpython.json"
        path.write_text(json.dumps(config), encoding="utf-8")
        return str(path)

    def test_loads_no_cycles_rule(self):
        self._write("src/model.py", "class Model:\n    pass\n")
        self._write("src/service.py", "from model import Model\n")
        config_path = self._write_config(
            {
                "project_path": "src",
                "rules": [
                    {
                        "name": "source files have no cycles",
                        "type": "no_cycles",
                    }
                ],
            }
        )

        rules = rules_from_config(config_path)

        assert [rule.name for rule in rules] == ["source files have no cycles"]
        assert rules[0].check() == []

    def test_loads_forbidden_dependency_rule(self):
        self._write("src/controllers/controller.py", "from services.service import Service\n")
        self._write("src/services/service.py", "class Service:\n    pass\n")
        config_path = self._write_config(
            {
                "project_path": "src",
                "rules": [
                    {
                        "type": "forbidden_dependency",
                        "source": "**/controllers/**",
                        "target": "**/services/**",
                    }
                ],
            }
        )

        rules = rules_from_config(config_path)
        violations = rules[0].check()

        assert any(isinstance(v, ViolatingFileDependency) for v in violations)

    def test_loads_forbidden_external_dependency_rule(self):
        self._write("src/utils/helpers.py", "import json\n")
        config_path = self._write_config(
            {
                "project_path": "src",
                "rules": [
                    {
                        "type": "forbidden_external_dependency",
                        "source": "**/utils/**",
                        "module": "json",
                    }
                ],
            }
        )

        rules = rules_from_config(config_path)
        violations = rules[0].check()

        assert any(isinstance(v, ViolatingExternalModuleDependency) for v in violations)

    def test_rejects_missing_rules_list(self):
        config_path = self._write_config({"project_path": "src"})

        with pytest.raises(UserError, match="rules"):
            rules_from_config(config_path)

    def test_rejects_unknown_rule_type(self):
        config_path = self._write_config(
            {
                "rules": [
                    {
                        "type": "unknown",
                    }
                ]
            }
        )

        with pytest.raises(UserError, match="Unsupported rule type"):
            rules_from_config(config_path)
