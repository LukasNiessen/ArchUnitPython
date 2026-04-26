"""Tests for graph extraction."""

import os
import shutil
from pathlib import Path
from uuid import uuid4

import pytest

from archunitpython.common.extraction.extract_graph import (
    _extract_imports,
    _find_python_files,
    _normalize,
    clear_graph_cache,
    extract_graph,
)
from archunitpython.common.extraction.graph import Edge, ImportKind
from archunitpython.common.fluentapi.checkable import CheckOptions

FIXTURES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fixtures")
SAMPLE_PROJECT = os.path.join(FIXTURES_DIR, "sample_project")


class TestFindPythonFiles:
    def test_finds_all_py_files(self):
        files = _find_python_files(SAMPLE_PROJECT, ["__pycache__"])
        filenames = {os.path.basename(f) for f in files}
        assert "__init__.py" in filenames
        assert "model.py" in filenames
        assert "service.py" in filenames
        assert "service_a.py" in filenames
        assert "service_b.py" in filenames
        assert "controller.py" in filenames
        assert "helpers.py" in filenames

    def test_excludes_pycache(self):
        files = _find_python_files(SAMPLE_PROJECT, ["__pycache__"])
        for f in files:
            assert "__pycache__" not in f


class TestExtractImports:
    def test_absolute_import(self):
        service_path = os.path.join(SAMPLE_PROJECT, "services", "service.py")
        imports = _extract_imports(service_path)
        modules = [m for m, _ in imports]
        assert "sample_project.models.model" in modules

    def test_relative_import(self):
        service_b_path = os.path.join(SAMPLE_PROJECT, "services", "service_b.py")
        imports = _extract_imports(service_b_path)
        kinds = {k for _, k in imports}
        assert ImportKind.RELATIVE_IMPORT in kinds

    def test_stdlib_import(self):
        helpers_path = os.path.join(SAMPLE_PROJECT, "utils", "helpers.py")
        imports = _extract_imports(helpers_path)
        modules = [m for m, _ in imports]
        assert "os" in modules
        assert "json" in modules

    def test_nonexistent_file(self):
        result = _extract_imports("/nonexistent/file.py")
        assert result == []


class TestExtractGraph:
    def setup_method(self):
        clear_graph_cache()

    def test_returns_edges(self):
        graph = extract_graph(SAMPLE_PROJECT)
        assert isinstance(graph, list)
        assert len(graph) > 0
        assert all(isinstance(e, Edge) for e in graph)

    def test_self_referencing_edges(self):
        graph = extract_graph(SAMPLE_PROJECT)
        self_edges = [e for e in graph if e.source == e.target and not e.external]
        # Each .py file should have a self-edge
        py_files = _find_python_files(SAMPLE_PROJECT, ["__pycache__"])
        assert len(self_edges) >= len(py_files)

    def test_internal_edges_detected(self):
        graph = extract_graph(SAMPLE_PROJECT)
        internal_non_self = [
            e
            for e in graph
            if not e.external and e.source != e.target
        ]
        assert len(internal_non_self) > 0

    def test_external_edges_detected(self):
        graph = extract_graph(SAMPLE_PROJECT)
        external = [e for e in graph if e.external]
        # helpers.py imports os, json, typing
        assert len(external) > 0

    def test_relative_import_resolved(self):
        graph = extract_graph(SAMPLE_PROJECT)
        service_b = _normalize(
            os.path.abspath(os.path.join(SAMPLE_PROJECT, "services", "service_b.py"))
        )
        service = _normalize(
            os.path.abspath(os.path.join(SAMPLE_PROJECT, "services", "service.py"))
        )
        # service_b imports from .service (relative)
        rel_edges = [
            e
            for e in graph
            if e.source == service_b
            and e.target == service
            and not e.external
        ]
        assert len(rel_edges) == 1

    def test_caching(self):
        graph1 = extract_graph(SAMPLE_PROJECT)
        graph2 = extract_graph(SAMPLE_PROJECT)
        assert graph1 is graph2  # Same object reference (cached)

    def test_cache_clear(self):
        graph1 = extract_graph(SAMPLE_PROJECT)
        graph2 = extract_graph(
            SAMPLE_PROJECT, options=CheckOptions(clear_cache=True)
        )
        assert graph1 is not graph2  # Different objects after cache clear

    def test_edge_has_import_kinds(self):
        graph = extract_graph(SAMPLE_PROJECT)
        edges_with_kinds = [e for e in graph if len(e.import_kinds) > 0]
        assert len(edges_with_kinds) > 0


class TestTypeCheckingImportHandling:
    def setup_method(self):
        clear_graph_cache()

    def _build_type_checking_project(self) -> str:
        temp_root = Path(__file__).resolve().parent / ".tmp"
        temp_root.mkdir(exist_ok=True)
        project_root = temp_root / f"project_{uuid4().hex}"
        project_root.mkdir()

        package_dir = project_root / "sample_project"
        package_dir.mkdir(parents=True, exist_ok=True)

        (package_dir / "__init__.py").write_text("", encoding="utf-8")
        (package_dir / "models.py").write_text(
            "class User:\n    pass\n",
            encoding="utf-8",
        )
        (package_dir / "service.py").write_text(
            "\n".join(
                [
                    "from typing import TYPE_CHECKING",
                    "",
                    "if TYPE_CHECKING:",
                    "    from sample_project.models import User",
                    "",
                    "def get_user() -> str:",
                    '    return "ok"',
                    "",
                ]
            ),
            encoding="utf-8",
        )
        self._temp_dir = project_root
        return str(project_root)

    def teardown_method(self):
        temp_dir = getattr(self, "_temp_dir", None)
        if temp_dir is not None:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_type_checking_imports_included_by_default(self):
        project_root = self._build_type_checking_project()

        graph = extract_graph(project_root)
        models_path = os.path.abspath(
            os.path.join(project_root, "sample_project", "models.py")
        ).replace("\\", "/")
        service_path = os.path.abspath(
            os.path.join(project_root, "sample_project", "service.py")
        ).replace("\\", "/")

        edges = [
            edge
            for edge in graph
            if edge.source == service_path and edge.target == models_path
        ]
        assert len(edges) == 1
        assert ImportKind.TYPE_IMPORT in edges[0].import_kinds

    def test_type_checking_imports_can_be_ignored(self):
        project_root = self._build_type_checking_project()

        graph = extract_graph(
            project_root,
            options=CheckOptions(ignore_type_checking_imports=True),
        )
        models_path = os.path.abspath(
            os.path.join(project_root, "sample_project", "models.py")
        ).replace("\\", "/")
        service_path = os.path.abspath(
            os.path.join(project_root, "sample_project", "service.py")
        ).replace("\\", "/")

        edges = [
            edge
            for edge in graph
            if edge.source == service_path and edge.target == models_path
        ]
        assert edges == []

    def test_cache_key_includes_type_checking_option(self):
        project_root = self._build_type_checking_project()

        default_graph = extract_graph(project_root)
        filtered_graph = extract_graph(
            project_root,
            options=CheckOptions(ignore_type_checking_imports=True),
        )

        assert default_graph is not filtered_graph
        assert len(default_graph) > len(filtered_graph)


class TestEdgeModel:
    def test_edge_frozen(self):
        edge = Edge(source="a.py", target="b.py", external=False)
        with pytest.raises(AttributeError):
            edge.source = "c.py"  # type: ignore[misc]

    def test_edge_equality(self):
        e1 = Edge(source="a.py", target="b.py", external=False)
        e2 = Edge(source="a.py", target="b.py", external=False)
        assert e1 == e2

    def test_edge_with_import_kinds(self):
        edge = Edge(
            source="a.py",
            target="b.py",
            external=False,
            import_kinds=(ImportKind.IMPORT, ImportKind.FROM_IMPORT),
        )
        assert len(edge.import_kinds) == 2


class TestImportKind:
    def test_all_kinds_exist(self):
        assert ImportKind.IMPORT.value == "import"
        assert ImportKind.FROM_IMPORT.value == "from_import"
        assert ImportKind.RELATIVE_IMPORT.value == "relative"
        assert ImportKind.DYNAMIC_IMPORT.value == "dynamic"
        assert ImportKind.TYPE_IMPORT.value == "type"
