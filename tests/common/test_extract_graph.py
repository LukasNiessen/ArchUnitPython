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
    _resolve_exclude_patterns,
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

    def test_dynamic_import(self):
        temp_root = Path(__file__).resolve().parent / ".tmp"
        temp_root.mkdir(exist_ok=True)
        project_root = temp_root / f"project_{uuid4().hex}"
        project_root.mkdir()
        file_path = project_root / "loader.py"
        file_path.write_text(
            'def load():\n    return __import__("sample_project.models")\n',
            encoding="utf-8",
        )

        try:
            imports = _extract_imports(str(file_path))
            assert ("sample_project.models", ImportKind.DYNAMIC_IMPORT) in imports
        finally:
            shutil.rmtree(project_root, ignore_errors=True)

    def test_importlib_import_module(self):
        temp_root = Path(__file__).resolve().parent / ".tmp"
        temp_root.mkdir(exist_ok=True)
        project_root = temp_root / f"project_{uuid4().hex}"
        project_root.mkdir()
        file_path = project_root / "loader.py"
        file_path.write_text(
            "\n".join(
                [
                    "import importlib",
                    "",
                    "def load():",
                    '    return importlib.import_module("sample_project.models")',
                    "",
                ]
            ),
            encoding="utf-8",
        )

        try:
            imports = _extract_imports(str(file_path))
            assert ("sample_project.models", ImportKind.DYNAMIC_IMPORT) in imports
        finally:
            shutil.rmtree(project_root, ignore_errors=True)

    def test_conditional_import(self):
        temp_root = Path(__file__).resolve().parent / ".tmp"
        temp_root.mkdir(exist_ok=True)
        project_root = temp_root / f"project_{uuid4().hex}"
        project_root.mkdir()
        file_path = project_root / "loader.py"
        file_path.write_text(
            "\n".join(
                [
                    "try:",
                    "    import orjson",
                    "except ImportError:",
                    "    import json",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        try:
            imports = _extract_imports(str(file_path))
            assert ("orjson", ImportKind.CONDITIONAL_IMPORT) in imports
            assert ("json", ImportKind.CONDITIONAL_IMPORT) in imports
        finally:
            shutil.rmtree(project_root, ignore_errors=True)


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
        internal_non_self = [e for e in graph if not e.external and e.source != e.target]
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
            e for e in graph if e.source == service_b and e.target == service and not e.external
        ]
        assert len(rel_edges) == 1

    def test_caching(self):
        graph1 = extract_graph(SAMPLE_PROJECT)
        graph2 = extract_graph(SAMPLE_PROJECT)
        assert graph1 is graph2  # Same object reference (cached)

    def test_cache_clear(self):
        graph1 = extract_graph(SAMPLE_PROJECT)
        graph2 = extract_graph(SAMPLE_PROJECT, options=CheckOptions(clear_cache=True))
        assert graph1 is not graph2  # Different objects after cache clear

    def test_edge_has_import_kinds(self):
        graph = extract_graph(SAMPLE_PROJECT)
        edges_with_kinds = [e for e in graph if len(e.import_kinds) > 0]
        assert len(edges_with_kinds) > 0


class TestArchignore:
    def setup_method(self):
        clear_graph_cache()
        self._temp_dir = Path(__file__).resolve().parent / ".tmp" / f"project_{uuid4().hex}"
        self._temp_dir.mkdir(parents=True)

    def teardown_method(self):
        shutil.rmtree(self._temp_dir, ignore_errors=True)

    def _write(self, relative_path: str, content: str = "") -> None:
        path = self._temp_dir / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def test_archignore_excludes_files_and_directories(self):
        self._write(
            ".archignore",
            "\n".join(
                [
                    "# Ignore generated architecture-test inputs",
                    "ignored.py",
                    "generated/",
                    "nested/*.py",
                    "/root_ignored.py",
                ]
            ),
        )
        self._write("keep.py")
        self._write("ignored.py")
        self._write("root_ignored.py")
        self._write("generated/generated.py")
        self._write("nested/ignored_nested.py")

        excludes = _resolve_exclude_patterns(str(self._temp_dir), ["__pycache__"])
        files = _find_python_files(str(self._temp_dir), excludes)
        relative_files = {
            Path(file_path).relative_to(self._temp_dir).as_posix()
            for file_path in files
        }

        assert relative_files == {"keep.py"}

    def test_archignore_ignored_files_are_not_dependency_targets(self):
        self._write(".archignore", "ignored.py\n")
        self._write("keep.py", "import ignored\n")
        self._write("ignored.py", "VALUE = 1\n")

        graph = extract_graph(str(self._temp_dir))
        targets = {edge.target for edge in graph}

        ignored_path = _normalize(str((self._temp_dir / "ignored.py").resolve()))
        assert ignored_path not in targets

    def test_archignore_with_invalid_utf8_bytes_does_not_abort_extraction(self):
        (self._temp_dir / ".archignore").write_bytes(b"ignored.py\n\xff\n")
        self._write("keep.py")
        self._write("ignored.py")

        graph = extract_graph(str(self._temp_dir))
        sources = {edge.source for edge in graph}

        keep_path = _normalize(str((self._temp_dir / "keep.py").resolve()))
        ignored_path = _normalize(str((self._temp_dir / "ignored.py").resolve()))
        assert keep_path in sources
        assert ignored_path not in sources


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
            edge for edge in graph if edge.source == service_path and edge.target == models_path
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
            edge for edge in graph if edge.source == service_path and edge.target == models_path
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


class TestDynamicImportGraphHandling:
    def setup_method(self):
        clear_graph_cache()

    def _build_dynamic_project(self) -> str:
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
        (package_dir / "loader.py").write_text(
            "\n".join(
                [
                    "def load_model():",
                    '    return __import__("sample_project.models")',
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

    def test_dynamic_import_resolves_to_internal_edge(self):
        project_root = self._build_dynamic_project()

        graph = extract_graph(project_root)
        models_path = os.path.abspath(
            os.path.join(project_root, "sample_project", "models.py")
        ).replace("\\", "/")
        loader_path = os.path.abspath(
            os.path.join(project_root, "sample_project", "loader.py")
        ).replace("\\", "/")

        edges = [
            edge
            for edge in graph
            if edge.source == loader_path and edge.target == models_path
        ]
        assert len(edges) == 1
        assert ImportKind.DYNAMIC_IMPORT in edges[0].import_kinds


class TestConditionalImportGraphHandling:
    def setup_method(self):
        clear_graph_cache()

    def _build_conditional_project(
        self,
        service_source: str | None = None,
        *,
        service_subdirectory: str | None = None,
    ) -> str:
        temp_root = Path(__file__).resolve().parent / ".tmp"
        temp_root.mkdir(exist_ok=True)
        project_root = temp_root / f"project_{uuid4().hex}"
        project_root.mkdir()

        package_dir = project_root / "sample_project"
        package_dir.mkdir(parents=True, exist_ok=True)

        (package_dir / "__init__.py").write_text("", encoding="utf-8")
        (package_dir / "fast_model.py").write_text(
            "class FastUser:\n    pass\n",
            encoding="utf-8",
        )
        (package_dir / "fallback_model.py").write_text(
            "class FallbackUser:\n    pass\n",
            encoding="utf-8",
        )
        if service_source is None:
            service_source = "\n".join(
                [
                    "try:",
                    "    from sample_project.fast_model import FastUser",
                    "except ImportError:",
                    "    from sample_project.fallback_model import FallbackUser",
                    "",
                ]
            )

        service_dir = package_dir
        if service_subdirectory is not None:
            service_dir = package_dir / service_subdirectory
            service_dir.mkdir()
            (service_dir / "__init__.py").write_text("", encoding="utf-8")
        (service_dir / "service.py").write_text(service_source, encoding="utf-8")
        self._service_subdirectory = service_subdirectory
        self._temp_dir = project_root
        return str(project_root)

    def teardown_method(self):
        temp_dir = getattr(self, "_temp_dir", None)
        if temp_dir is not None:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_import_error_fallback_imports_are_marked_conditional(self):
        project_root = self._build_conditional_project()

        graph = extract_graph(project_root)
        service_path = os.path.abspath(
            os.path.join(project_root, "sample_project", "service.py")
        ).replace("\\", "/")
        target_paths = {
            os.path.abspath(
                os.path.join(project_root, "sample_project", "fast_model.py")
            ).replace("\\", "/"),
            os.path.abspath(
                os.path.join(project_root, "sample_project", "fallback_model.py")
            ).replace("\\", "/"),
        }

        edges = [
            edge
            for edge in graph
            if edge.source == service_path and edge.target in target_paths
        ]

        assert len(edges) == 2
        assert all(edge.external is False for edge in edges)
        assert all(ImportKind.CONDITIONAL_IMPORT in edge.import_kinds for edge in edges)
        assert all(ImportKind.FROM_IMPORT in edge.import_kinds for edge in edges)

    def _conditional_edges(self, project_root: str) -> list[Edge]:
        service_parts = [project_root, "sample_project"]
        service_subdirectory = getattr(self, "_service_subdirectory", None)
        if service_subdirectory is not None:
            service_parts.append(service_subdirectory)
        service_parts.append("service.py")
        service_path = os.path.abspath(os.path.join(*service_parts)).replace("\\", "/")
        return [
            edge
            for edge in extract_graph(project_root)
            if edge.source == service_path and edge.target != service_path
        ]

    def test_relative_fallback_imports_resolve_sibling_modules(self):
        project_root = self._build_conditional_project(
            "\n".join(
                [
                    "try:",
                    "    from . import fast_model",
                    "except ImportError:",
                    "    from . import fallback_model",
                    "",
                ]
            )
        )

        edges = self._conditional_edges(project_root)
        target_paths = {
            os.path.abspath(
                os.path.join(project_root, "sample_project", module)
            ).replace("\\", "/")
            for module in ("fast_model.py", "fallback_model.py")
        }

        assert {edge.target for edge in edges if not edge.external} == target_paths
        assert all(ImportKind.RELATIVE_IMPORT in edge.import_kinds for edge in edges)
        assert all(ImportKind.CONDITIONAL_IMPORT in edge.import_kinds for edge in edges)
        assert not any(edge.target.endswith("/__init__.py") for edge in edges)

    def test_conditional_relative_import_resolves_multiple_aliased_modules(self):
        project_root = self._build_conditional_project(
            "\n".join(
                [
                    "try:",
                    "    from . import fast_model as selected, fallback_model",
                    "except ImportError:",
                    "    pass",
                    "",
                ]
            )
        )

        edges = self._conditional_edges(project_root)
        target_paths = {
            os.path.abspath(
                os.path.join(project_root, "sample_project", module)
            ).replace("\\", "/")
            for module in ("fast_model.py", "fallback_model.py")
        }

        assert {edge.target for edge in edges if not edge.external} == target_paths
        assert all(ImportKind.RELATIVE_IMPORT in edge.import_kinds for edge in edges)
        assert all(ImportKind.CONDITIONAL_IMPORT in edge.import_kinds for edge in edges)

    def test_regular_relative_import_resolves_without_conditional_kind(self):
        project_root = self._build_conditional_project("from . import fast_model\n")

        model_edges = [
            edge
            for edge in self._conditional_edges(project_root)
            if edge.target.endswith("/fast_model.py")
        ]

        assert len(model_edges) == 1
        assert ImportKind.RELATIVE_IMPORT in model_edges[0].import_kinds
        assert ImportKind.CONDITIONAL_IMPORT not in model_edges[0].import_kinds

    def test_parent_relative_fallback_imports_resolve_modules(self):
        project_root = self._build_conditional_project(
            "\n".join(
                [
                    "try:",
                    "    from .. import fast_model",
                    "except ImportError:",
                    "    from .. import fallback_model",
                    "",
                ]
            ),
            service_subdirectory="feature",
        )

        edges = self._conditional_edges(project_root)
        target_paths = {
            os.path.abspath(
                os.path.join(project_root, "sample_project", module)
            ).replace("\\", "/")
            for module in ("fast_model.py", "fallback_model.py")
        }

        assert {edge.target for edge in edges if not edge.external} == target_paths
        assert all(ImportKind.RELATIVE_IMPORT in edge.import_kinds for edge in edges)
        assert all(ImportKind.CONDITIONAL_IMPORT in edge.import_kinds for edge in edges)

    def test_module_not_found_error_marks_fallback_conditional(self):
        project_root = self._build_conditional_project(
            "\n".join(
                [
                    "try:",
                    "    from . import fast_model",
                    "except ModuleNotFoundError:",
                    "    from . import fallback_model",
                    "",
                ]
            )
        )

        edges = self._conditional_edges(project_root)

        assert len(edges) == 2
        assert all(ImportKind.CONDITIONAL_IMPORT in edge.import_kinds for edge in edges)

    def test_tuple_handler_marks_import_fallback_conditional(self):
        project_root = self._build_conditional_project(
            "\n".join(
                [
                    "try:",
                    "    from . import fast_model",
                    "except (ImportError, OSError):",
                    "    from . import fallback_model",
                    "",
                ]
            )
        )

        edges = self._conditional_edges(project_root)

        assert len(edges) == 2
        assert all(ImportKind.CONDITIONAL_IMPORT in edge.import_kinds for edge in edges)

    def test_non_import_error_handler_does_not_mark_imports_conditional(self):
        project_root = self._build_conditional_project(
            "\n".join(
                [
                    "try:",
                    "    from sample_project.fast_model import FastUser",
                    "except OSError:",
                    "    from sample_project.fallback_model import FallbackUser",
                    "",
                ]
            )
        )

        edges = self._conditional_edges(project_root)

        assert len(edges) == 2
        assert all(ImportKind.FROM_IMPORT in edge.import_kinds for edge in edges)
        assert all(
            ImportKind.CONDITIONAL_IMPORT not in edge.import_kinds for edge in edges
        )

    def test_conditional_dynamic_import_retains_dynamic_kind(self):
        project_root = self._build_conditional_project(
            "\n".join(
                [
                    "import importlib",
                    "",
                    "try:",
                    '    importlib.import_module("sample_project.fast_model")',
                    "except ImportError:",
                    '    importlib.import_module("sample_project.fallback_model")',
                    "",
                ]
            )
        )

        internal_edges = [
            edge for edge in self._conditional_edges(project_root) if not edge.external
        ]

        assert len(internal_edges) == 2
        assert all(
            ImportKind.CONDITIONAL_IMPORT in edge.import_kinds
            for edge in internal_edges
        )
        assert all(ImportKind.DYNAMIC_IMPORT in edge.import_kinds for edge in internal_edges)

    def test_type_checking_import_takes_precedence_over_conditional_context(self):
        project_root = self._build_conditional_project(
            "\n".join(
                [
                    "from typing import TYPE_CHECKING",
                    "",
                    "try:",
                    "    if TYPE_CHECKING:",
                    "        from . import fast_model",
                    "except ImportError:",
                    "    pass",
                    "",
                ]
            )
        )

        edges = self._conditional_edges(project_root)
        model_edges = [edge for edge in edges if edge.target.endswith("/fast_model.py")]

        assert len(model_edges) == 1
        assert ImportKind.TYPE_IMPORT in model_edges[0].import_kinds
        assert ImportKind.CONDITIONAL_IMPORT not in model_edges[0].import_kinds

        ignored_graph = extract_graph(
            project_root,
            options=CheckOptions(
                clear_cache=True,
                ignore_type_checking_imports=True,
            ),
        )
        assert not any(
            edge.source.endswith("/service.py")
            and edge.target.endswith("/fast_model.py")
            for edge in ignored_graph
        )


class TestIgnoreDirectives:
    def setup_method(self):
        clear_graph_cache()

    def _build_project(self, service_source: str) -> str:
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
        (package_dir / "service.py").write_text(service_source, encoding="utf-8")
        self._temp_dir = project_root
        return str(project_root)

    def teardown_method(self):
        temp_dir = getattr(self, "_temp_dir", None)
        if temp_dir is not None:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _service_to_model_edges(self, project_root: str) -> list[Edge]:
        graph = extract_graph(project_root)
        models_path = os.path.abspath(
            os.path.join(project_root, "sample_project", "models.py")
        ).replace("\\", "/")
        service_path = os.path.abspath(
            os.path.join(project_root, "sample_project", "service.py")
        ).replace("\\", "/")
        return [
            edge
            for edge in graph
            if edge.source == service_path and edge.target == models_path
        ]

    def test_inline_ignore_directive_removes_import_edge(self):
        project_root = self._build_project(
            "from sample_project.models import User  # archunit: ignore\n"
        )

        assert self._service_to_model_edges(project_root) == []

    def test_standalone_ignore_directive_removes_next_import_edge(self):
        project_root = self._build_project(
            "# archunit: ignore\nfrom sample_project.models import User\n"
        )

        assert self._service_to_model_edges(project_root) == []

    def test_module_scoped_ignore_only_removes_matching_import(self):
        project_root = self._build_project(
            "# archunit: ignore other.module\nfrom sample_project.models import User\n"
        )

        assert len(self._service_to_model_edges(project_root)) == 1


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
        assert ImportKind.CONDITIONAL_IMPORT.value == "conditional"
