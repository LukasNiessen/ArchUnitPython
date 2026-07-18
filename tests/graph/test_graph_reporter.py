"""Tests for dependency graph report generation."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Iterator
from uuid import uuid4

import pytest

from archunitpython import project_graph
from archunitpython.common.extraction.graph import Edge, ImportKind
from archunitpython.graph import (
    FolderDepthCollapse,
    GraphQueryOptions,
    GraphReporter,
    PatternCollapse,
)

TEMP_ROOT = Path(__file__).resolve().parent / ".tmp"


@pytest.fixture()
def project_root() -> Iterator[Path]:
    TEMP_ROOT.mkdir(exist_ok=True)
    root = TEMP_ROOT / f"project_{uuid4().hex}"
    root.mkdir()
    try:
        yield root
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _node(root: Path, relative_path: str) -> str:
    return str(root / relative_path).replace("\\", "/")


def _sample_graph(root: Path) -> list[Edge]:
    return [
        Edge(
            source=_node(root, "src/app/controller.py"),
            target=_node(root, "src/domain/service.py"),
            external=False,
            import_kinds=(ImportKind.FROM_IMPORT,),
        ),
        Edge(
            source=_node(root, "src/app/controller.py"),
            target=_node(root, "src/domain/service.py"),
            external=False,
            import_kinds=(ImportKind.IMPORT,),
        ),
        Edge(
            source=_node(root, "src/domain/service.py"),
            target=_node(root, "src/infra/repository.py"),
            external=False,
            import_kinds=(ImportKind.RELATIVE_IMPORT,),
        ),
        Edge(
            source=_node(root, "src/app/controller.py"),
            target=_node(root, "src/infra/repository.py"),
            external=False,
            import_kinds=(ImportKind.IMPORT,),
        ),
        Edge(
            source=_node(root, "src/infra/repository.py"),
            target=_node(root, "src/infra/repository.py"),
            external=False,
        ),
        Edge(
            source=_node(root, "src/app/controller.py"),
            target="requests",
            external=True,
            import_kinds=(ImportKind.IMPORT,),
        ),
    ]


def test_snapshot_aggregates_duplicate_edges_and_excludes_external_and_self_edges(
    project_root: Path,
) -> None:
    graph = _sample_graph(project_root)
    snapshot = GraphReporter.create_snapshot(
        graph,
        GraphQueryOptions(project_path=str(project_root)),
    )

    assert snapshot.summary.node_count == 3
    assert snapshot.summary.edge_count == 3
    assert snapshot.summary.raw_edge_count == 4
    assert snapshot.summary.external_edge_count == 0
    assert snapshot.nodes[0].label == "src/app/controller.py"
    assert any(
        edge.source == "src/app/controller.py"
        and edge.target == "src/domain/service.py"
        and edge.count == 2
        and edge.import_kinds == ("from_import", "import")
        for edge in snapshot.edges
    )


def test_snapshot_can_include_external_dependencies(project_root: Path) -> None:
    snapshot = GraphReporter.create_snapshot(
        _sample_graph(project_root),
        GraphQueryOptions(
            include_external_dependencies=True,
            project_path=str(project_root),
        ),
    )

    assert snapshot.summary.external_edge_count == 1
    assert any(
        edge.source == "src/app/controller.py"
        and edge.target == "requests"
        and edge.external
        for edge in snapshot.edges
    )


def test_snapshot_focuses_on_matching_nodes_and_neighbors(project_root: Path) -> None:
    focused = GraphReporter.create_snapshot(
        _sample_graph(project_root),
        GraphQueryOptions(
            focus="src/domain/**",
            focus_depth=0,
            project_path=str(project_root),
        ),
    )

    assert [node.label for node in focused.nodes] == ["src/domain/service.py"]
    assert focused.edges == ()

    with_neighbors = GraphReporter.create_snapshot(
        _sample_graph(project_root),
        GraphQueryOptions(
            focus="src/domain/**",
            focus_depth=1,
            project_path=str(project_root),
        ),
    )

    assert [node.label for node in with_neighbors.nodes] == [
        "src/app/controller.py",
        "src/domain/service.py",
        "src/infra/repository.py",
    ]
    assert with_neighbors.summary.edge_count == 3


def test_snapshot_filters_to_reachable_dependencies_and_dependents(
    project_root: Path,
) -> None:
    reachable = GraphReporter.create_snapshot(
        _sample_graph(project_root),
        GraphQueryOptions(
            reachable_from="src/domain/**",
            project_path=str(project_root),
        ),
    )

    assert [node.label for node in reachable.nodes] == [
        "src/domain/service.py",
        "src/infra/repository.py",
    ]
    assert len(reachable.edges) == 1

    dependents = GraphReporter.create_snapshot(
        _sample_graph(project_root),
        GraphQueryOptions(
            dependents_of="src/infra/**",
            project_path=str(project_root),
        ),
    )

    assert [node.label for node in dependents.nodes] == [
        "src/app/controller.py",
        "src/domain/service.py",
        "src/infra/repository.py",
    ]
    assert dependents.summary.edge_count == 3


def test_snapshot_collapses_nodes_before_aggregating_edges(project_root: Path) -> None:
    snapshot = GraphReporter.create_snapshot(
        _sample_graph(project_root),
        GraphQueryOptions(
            collapse=PatternCollapse(
                pattern=re.compile(r"src/([^/]+)/.*"),
                replacement=r"\1",
            ),
            project_path=str(project_root),
        ),
    )

    assert [node.label for node in snapshot.nodes] == ["app", "domain", "infra"]
    assert any(
        edge.source == "app"
        and edge.target == "domain"
        and edge.count == 2
        for edge in snapshot.edges
    )


def test_snapshot_collapses_to_folder_depth(project_root: Path) -> None:
    snapshot = GraphReporter.create_snapshot(
        _sample_graph(project_root),
        GraphQueryOptions(project_path=str(project_root)),
    )
    collapsed = GraphReporter.create_snapshot(
        _sample_graph(project_root),
        GraphQueryOptions(
            collapse=FolderDepthCollapse(depth=2),
            project_path=str(project_root),
        ),
    )

    assert snapshot.summary.node_count == 3
    assert [node.label for node in collapsed.nodes] == [
        "src/app",
        "src/domain",
        "src/infra",
    ]


def test_reporter_renders_supported_text_formats(project_root: Path) -> None:
    graph = _sample_graph(project_root)
    options = GraphQueryOptions(
        project_path=str(project_root), title="Architecture Report"
    )

    mermaid = GraphReporter.to_mermaid(graph, options)
    dot = GraphReporter.to_dot(graph, options)
    d2 = GraphReporter.to_d2(graph, options)
    csv = GraphReporter.to_csv(graph, options)
    json_report = GraphReporter.to_json(graph, options)
    html = GraphReporter.to_html(graph, options)

    assert "flowchart LR" in mermaid
    assert "|2|" in mermaid
    assert "digraph dependencies" in dot
    assert '"src/app/controller.py" -> "src/domain/service.py"' in dot
    assert '"src/app/controller.py" -> "src/domain/service.py"' in d2
    assert csv.split("\n")[0] == "source,target,count,external,import_kinds"
    assert json.loads(json_report)["summary"]["edge_count"] == 3
    assert "<title>Architecture Report</title>" in html
    assert "Generated by ArchUnitPython graph reporting" in html


def test_reporter_writes_reports_to_disk(project_root: Path) -> None:
    output_path = project_root / "reports" / "dependencies.mmd"

    GraphReporter.export_as_mermaid(
        _sample_graph(project_root),
        str(output_path),
        GraphQueryOptions(project_path=str(project_root)),
    )

    assert output_path.read_text(encoding="utf-8").startswith("flowchart LR")


def test_project_graph_builder_extracts_and_exports_real_project(
    project_root: Path,
) -> None:
    package = project_root / "sample_project"
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "api.py").write_text(
        "\n".join(
            [
                "import requests",
                "from sample_project.domain import Service",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (package / "domain.py").write_text(
        "from sample_project.infra import Repository\nclass Service: pass\n",
        encoding="utf-8",
    )
    (package / "infra.py").write_text("class Repository: pass\n", encoding="utf-8")

    graph = project_graph(str(project_root)).titled("Sample Project")
    snapshot = graph.include_external_dependencies().snapshot()
    html_path = project_root / "reports" / "sample.html"
    graph.collapse_to_folder_depth(1).export_as_html(str(html_path))

    assert any(edge.target == "requests" for edge in snapshot.edges)
    assert "sample_project/api.py" in graph.to_mermaid()
    assert html_path.exists()
    assert "Sample Project" in html_path.read_text(encoding="utf-8")
