"""Dependency graph querying and report generation."""

from __future__ import annotations

import csv
import fnmatch
import json
import os
import re
from dataclasses import asdict, dataclass, replace
from html import escape as escape_html
from io import StringIO
from pathlib import Path
from typing import Literal

from archunitpython.common.extraction.extract_graph import extract_graph
from archunitpython.common.extraction.graph import Graph
from archunitpython.common.fluentapi.checkable import CheckOptions
from archunitpython.common.types import Pattern

GraphReportFormat = Literal["dot", "mermaid", "d2", "csv", "json", "html"]

DEFAULT_TITLE = "ArchUnitPython Dependency Graph"


@dataclass(frozen=True)
class FolderDepthCollapse:
    """Collapse file nodes to their folder path up to a fixed depth."""

    depth: int


@dataclass(frozen=True)
class PatternCollapse:
    """Collapse file nodes by applying a regular expression replacement."""

    pattern: re.Pattern[str]
    replacement: str


GraphCollapseStrategy = FolderDepthCollapse | PatternCollapse


@dataclass(frozen=True)
class GraphQueryOptions:
    """Options for selecting, collapsing, and rendering a dependency graph."""

    include_external_dependencies: bool = False
    include_self_dependencies: bool = False
    focus: Pattern | None = None
    focus_depth: int = 1
    reachable_from: Pattern | None = None
    dependents_of: Pattern | None = None
    collapse: GraphCollapseStrategy | None = None
    title: str | None = None
    project_path: str | None = None


@dataclass(frozen=True)
class GraphReportNode:
    """A rendered graph node."""

    id: str
    label: str


@dataclass
class GraphReportEdge:
    """A rendered graph edge, possibly aggregating multiple raw edges."""

    source: str
    target: str
    count: int
    external: bool
    import_kinds: tuple[str, ...]


@dataclass(frozen=True)
class GraphReportSummary:
    """Basic counts for a rendered graph snapshot."""

    node_count: int
    edge_count: int
    raw_edge_count: int
    external_edge_count: int


@dataclass(frozen=True)
class GraphReportSnapshot:
    """A dependency graph after filtering, collapsing, and aggregation."""

    title: str
    nodes: tuple[GraphReportNode, ...]
    edges: tuple[GraphReportEdge, ...]
    summary: GraphReportSummary


@dataclass(frozen=True)
class _DisplayEdge:
    source: str
    target: str
    external: bool
    import_kinds: tuple[object, ...]


def project_graph(project_path: str | None = None) -> ProjectGraphBuilder:
    """Create a builder for dependency graph reports."""
    return ProjectGraphBuilder(project_path)


dependency_graph = project_graph


class ProjectGraphBuilder:
    """Fluent builder for dependency graph reports."""

    def __init__(
        self,
        project_path: str | None = None,
        options: GraphQueryOptions | None = None,
        check_options: CheckOptions | None = None,
    ) -> None:
        self._project_path = project_path
        self._options = options or GraphQueryOptions()
        self._check_options = check_options

    def include_external_dependencies(self) -> "ProjectGraphBuilder":
        """Include imports to external modules in graph reports."""
        return self._with_options(
            replace(self._options, include_external_dependencies=True)
        )

    def include_self_dependencies(self) -> "ProjectGraphBuilder":
        """Include self edges used to keep files visible as graph nodes."""
        return self._with_options(replace(self._options, include_self_dependencies=True))

    def focus_on(self, pattern: Pattern, depth: int = 1) -> "ProjectGraphBuilder":
        """Keep matching nodes and their neighbors up to the given depth."""
        return self._with_options(
            replace(self._options, focus=pattern, focus_depth=depth)
        )

    def reachable_from(self, pattern: Pattern) -> "ProjectGraphBuilder":
        """Keep matching nodes and all dependencies reachable from them."""
        return self._with_options(replace(self._options, reachable_from=pattern))

    def dependents_of(self, pattern: Pattern) -> "ProjectGraphBuilder":
        """Keep matching nodes and all files that transitively depend on them."""
        return self._with_options(replace(self._options, dependents_of=pattern))

    def collapse_to_folder_depth(self, depth: int) -> "ProjectGraphBuilder":
        """Aggregate file nodes to folders at the requested depth."""
        return self._with_options(
            replace(self._options, collapse=FolderDepthCollapse(depth=depth))
        )

    def collapse_by_pattern(
        self,
        pattern: str | re.Pattern[str],
        replacement: str = r"\1",
    ) -> "ProjectGraphBuilder":
        """Aggregate nodes by applying a regular expression replacement."""
        compiled = re.compile(pattern) if isinstance(pattern, str) else pattern
        return self._with_options(
            replace(
                self._options,
                collapse=PatternCollapse(pattern=compiled, replacement=replacement),
            )
        )

    def titled(self, title: str) -> "ProjectGraphBuilder":
        """Set the graph report title."""
        return self._with_options(replace(self._options, title=title))

    def with_check_options(
        self, check_options: CheckOptions
    ) -> "ProjectGraphBuilder":
        """Use the given check options when extracting the graph."""
        return ProjectGraphBuilder(self._project_path, self._options, check_options)

    def snapshot(self) -> GraphReportSnapshot:
        """Return the filtered, collapsed graph snapshot."""
        return GraphReporter.create_snapshot(self._get_graph(), self._report_options())

    def to_dot(self) -> str:
        """Render the graph in DOT format."""
        return GraphReporter.to_dot(self._get_graph(), self._report_options())

    def to_mermaid(self) -> str:
        """Render the graph in Mermaid flowchart format."""
        return GraphReporter.to_mermaid(self._get_graph(), self._report_options())

    def to_d2(self) -> str:
        """Render the graph in D2 format."""
        return GraphReporter.to_d2(self._get_graph(), self._report_options())

    def to_csv(self) -> str:
        """Render the graph as CSV."""
        return GraphReporter.to_csv(self._get_graph(), self._report_options())

    def to_json(self) -> str:
        """Render the graph snapshot as JSON."""
        return GraphReporter.to_json(self._get_graph(), self._report_options())

    def to_html(self) -> str:
        """Render the graph as a self-contained HTML report."""
        return GraphReporter.to_html(self._get_graph(), self._report_options())

    def export_as_dot(self, output_path: str) -> None:
        """Write a DOT report to disk."""
        GraphReporter.export_as_dot(
            self._get_graph(), output_path, self._report_options()
        )

    def export_as_mermaid(self, output_path: str) -> None:
        """Write a Mermaid report to disk."""
        GraphReporter.export_as_mermaid(
            self._get_graph(), output_path, self._report_options()
        )

    def export_as_d2(self, output_path: str) -> None:
        """Write a D2 report to disk."""
        GraphReporter.export_as_d2(self._get_graph(), output_path, self._report_options())

    def export_as_csv(self, output_path: str) -> None:
        """Write a CSV report to disk."""
        GraphReporter.export_as_csv(
            self._get_graph(), output_path, self._report_options()
        )

    def export_as_json(self, output_path: str) -> None:
        """Write a JSON report to disk."""
        GraphReporter.export_as_json(
            self._get_graph(), output_path, self._report_options()
        )

    def export_as_html(self, output_path: str) -> None:
        """Write an HTML report to disk."""
        GraphReporter.export_as_html(
            self._get_graph(), output_path, self._report_options()
        )

    def _with_options(self, options: GraphQueryOptions) -> "ProjectGraphBuilder":
        return ProjectGraphBuilder(
            self._project_path,
            options,
            self._check_options,
        )

    def _report_options(self) -> GraphQueryOptions:
        return replace(self._options, project_path=self._project_path)

    def _get_graph(self) -> Graph:
        return extract_graph(self._project_path, options=self._check_options)


class GraphReporter:
    """Create dependency graph snapshots and render them in report formats."""

    @staticmethod
    def create_snapshot(
        graph: Graph,
        options: GraphQueryOptions | None = None,
    ) -> GraphReportSnapshot:
        """Create a queryable report snapshot from a raw dependency graph."""
        opts = options or GraphQueryOptions()
        display_graph = _to_display_edges(graph, opts.project_path)
        filtered_by_external = (
            display_graph
            if opts.include_external_dependencies
            else [edge for edge in display_graph if not edge.external]
        )
        selected_nodes = _select_nodes(filtered_by_external, opts)
        display_edges = [
            edge
            for edge in filtered_by_external
            if (opts.include_self_dependencies or edge.source != edge.target)
            and edge.source in selected_nodes
            and edge.target in selected_nodes
        ]

        collapsed_nodes = {
            _collapse_node(node, opts.collapse) for node in selected_nodes
        }
        edge_map: dict[tuple[str, str], GraphReportEdge] = {}

        for edge in display_edges:
            source = _collapse_node(edge.source, opts.collapse)
            target = _collapse_node(edge.target, opts.collapse)

            if not opts.include_self_dependencies and source == target:
                continue

            key = (source, target)
            existing = edge_map.get(key)
            if existing is not None:
                existing.count += 1
                existing.external = existing.external or edge.external
                existing.import_kinds = _unique_sorted_import_kinds(
                    (*existing.import_kinds, *edge.import_kinds)
                )
                continue

            edge_map[key] = GraphReportEdge(
                source=source,
                target=target,
                count=1,
                external=edge.external,
                import_kinds=_unique_sorted_import_kinds(edge.import_kinds),
            )

        edges = tuple(sorted(edge_map.values(), key=lambda e: (e.source, e.target)))
        edge_node_labels = [label for edge in edges for label in (edge.source, edge.target)]
        labels = _unique_sorted((*collapsed_nodes, *edge_node_labels))
        nodes = tuple(
            GraphReportNode(id=f"n{index}", label=label)
            for index, label in enumerate(labels)
        )

        return GraphReportSnapshot(
            title=opts.title or DEFAULT_TITLE,
            nodes=nodes,
            edges=edges,
            summary=GraphReportSummary(
                node_count=len(nodes),
                edge_count=len(edges),
                raw_edge_count=len(display_edges),
                external_edge_count=sum(1 for edge in display_edges if edge.external),
            ),
        )

    @staticmethod
    def to_dot(graph: Graph, options: GraphQueryOptions | None = None) -> str:
        """Render a dependency graph in DOT format."""
        snapshot = GraphReporter.create_snapshot(graph, options)
        lines = ["digraph dependencies {", "\trankdir=LR;"]

        for node in snapshot.nodes:
            lines.append(f"\t{_quote_dot(node.label)};")

        for edge in snapshot.edges:
            label = f' [label="{edge.count}"]' if edge.count > 1 else ""
            lines.append(
                f"\t{_quote_dot(edge.source)} -> {_quote_dot(edge.target)}{label};"
            )

        lines.append("}")
        return "\n".join(lines)

    @staticmethod
    def to_mermaid(graph: Graph, options: GraphQueryOptions | None = None) -> str:
        """Render a dependency graph in Mermaid flowchart format."""
        snapshot = GraphReporter.create_snapshot(graph, options)
        node_ids = {node.label: node.id for node in snapshot.nodes}
        lines = ["flowchart LR"]

        for node in snapshot.nodes:
            lines.append(f'  {node.id}["{_escape_mermaid_label(node.label)}"]')

        for edge in snapshot.edges:
            source = node_ids.get(edge.source)
            target = node_ids.get(edge.target)
            if source is None or target is None:
                continue
            label = f"|{edge.count}|" if edge.count > 1 else ""
            lines.append(f"  {source} -->{label} {target}")

        return "\n".join(lines)

    @staticmethod
    def to_d2(graph: Graph, options: GraphQueryOptions | None = None) -> str:
        """Render a dependency graph in D2 format."""
        snapshot = GraphReporter.create_snapshot(graph, options)
        lines = [f"# {snapshot.title}"]

        for node in snapshot.nodes:
            lines.append(_quote_d2(node.label))

        for edge in snapshot.edges:
            label = f": {_quote_d2(str(edge.count))}" if edge.count > 1 else ""
            lines.append(f"{_quote_d2(edge.source)} -> {_quote_d2(edge.target)}{label}")

        return "\n".join(lines)

    @staticmethod
    def to_csv(graph: Graph, options: GraphQueryOptions | None = None) -> str:
        """Render a dependency graph as CSV."""
        snapshot = GraphReporter.create_snapshot(graph, options)
        output = StringIO()
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow(["source", "target", "count", "external", "import_kinds"])

        for edge in snapshot.edges:
            writer.writerow(
                [
                    edge.source,
                    edge.target,
                    str(edge.count),
                    str(edge.external).lower(),
                    "|".join(edge.import_kinds),
                ]
            )

        return output.getvalue().rstrip("\n")

    @staticmethod
    def to_json(graph: Graph, options: GraphQueryOptions | None = None) -> str:
        """Render a dependency graph snapshot as formatted JSON."""
        return json.dumps(asdict(GraphReporter.create_snapshot(graph, options)), indent=2)

    @staticmethod
    def to_html(graph: Graph, options: GraphQueryOptions | None = None) -> str:
        """Render a dependency graph as an HTML report."""
        snapshot = GraphReporter.create_snapshot(graph, options)
        mermaid = GraphReporter.to_mermaid(graph, options)
        dot = GraphReporter.to_dot(graph, options)
        d2 = GraphReporter.to_d2(graph, options)

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{escape_html(snapshot.title)}</title>
  <style>
    body {{
      font-family: Arial, sans-serif;
      margin: 0;
      color: #1f2933;
      background: #f8fafc;
    }}
    header {{ background: #102a43; color: white; padding: 24px 32px; }}
    main {{ padding: 24px 32px; }}
    h1 {{ margin: 0 0 8px; font-size: 28px; }}
    h2 {{ margin-top: 32px; font-size: 20px; }}
    .summary {{ display: flex; flex-wrap: wrap; gap: 12px; margin-top: 16px; }}
    .metric {{
      background: white;
      border: 1px solid #d9e2ec;
      border-radius: 6px;
      padding: 12px 16px;
      min-width: 140px;
    }}
    .metric strong {{ display: block; font-size: 24px; color: #102a43; }}
    table {{
      border-collapse: collapse;
      width: 100%;
      background: white;
      border: 1px solid #d9e2ec;
    }}
    th, td {{
      text-align: left;
      border-bottom: 1px solid #d9e2ec;
      padding: 8px 10px;
      vertical-align: top;
    }}
    th {{ background: #eef2f7; font-weight: 700; }}
    pre {{
      background: #0b1220;
      color: #e6edf3;
      padding: 16px;
      border-radius: 6px;
      overflow: auto;
    }}
    pre.mermaid {{ background: white; color: #1f2933; border: 1px solid #d9e2ec; }}
    details {{ margin: 16px 0; }}
    summary {{ cursor: pointer; font-weight: 700; }}
    .empty {{
      color: #627d98;
      background: white;
      border: 1px solid #d9e2ec;
      padding: 16px;
      border-radius: 6px;
    }}
  </style>
</head>
<body>
  <header>
    <h1>{escape_html(snapshot.title)}</h1>
    <div>Generated by ArchUnitPython graph reporting</div>
  </header>
  <main>
    <section class="summary">
      <div class="metric"><strong>{snapshot.summary.node_count}</strong>Nodes</div>
      <div class="metric"><strong>{snapshot.summary.edge_count}</strong>Aggregated Edges</div>
      <div class="metric"><strong>{snapshot.summary.raw_edge_count}</strong>Raw Edges</div>
      <div class="metric">
        <strong>{snapshot.summary.external_edge_count}</strong>External Edges
      </div>
    </section>

    <h2>Dependencies</h2>
    {_render_edge_table(snapshot)}

    <h2>Mermaid Preview</h2>
    <pre class="mermaid">{escape_html(mermaid)}</pre>

    <details>
      <summary>Mermaid Source</summary>
      <pre>{escape_html(mermaid)}</pre>
    </details>

    <details>
      <summary>DOT</summary>
      <pre>{escape_html(dot)}</pre>
    </details>

    <details>
      <summary>D2</summary>
      <pre>{escape_html(d2)}</pre>
    </details>
  </main>
  <script type="module">
    import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
    mermaid.initialize({{ startOnLoad: true, securityLevel: 'loose' }});
  </script>
</body>
</html>"""

    @staticmethod
    def export_as_dot(
        graph: Graph,
        output_path: str,
        options: GraphQueryOptions | None = None,
    ) -> None:
        """Write a DOT report to disk."""
        _write_report(output_path, GraphReporter.to_dot(graph, options))

    @staticmethod
    def export_as_mermaid(
        graph: Graph,
        output_path: str,
        options: GraphQueryOptions | None = None,
    ) -> None:
        """Write a Mermaid report to disk."""
        _write_report(output_path, GraphReporter.to_mermaid(graph, options))

    @staticmethod
    def export_as_d2(
        graph: Graph,
        output_path: str,
        options: GraphQueryOptions | None = None,
    ) -> None:
        """Write a D2 report to disk."""
        _write_report(output_path, GraphReporter.to_d2(graph, options))

    @staticmethod
    def export_as_csv(
        graph: Graph,
        output_path: str,
        options: GraphQueryOptions | None = None,
    ) -> None:
        """Write a CSV report to disk."""
        _write_report(output_path, GraphReporter.to_csv(graph, options))

    @staticmethod
    def export_as_json(
        graph: Graph,
        output_path: str,
        options: GraphQueryOptions | None = None,
    ) -> None:
        """Write a JSON report to disk."""
        _write_report(output_path, GraphReporter.to_json(graph, options))

    @staticmethod
    def export_as_html(
        graph: Graph,
        output_path: str,
        options: GraphQueryOptions | None = None,
    ) -> None:
        """Write an HTML report to disk."""
        _write_report(output_path, GraphReporter.to_html(graph, options))


def _to_display_edges(graph: Graph, project_path: str | None) -> list[_DisplayEdge]:
    return [
        _DisplayEdge(
            source=_display_label(edge.source, project_path),
            target=(
                _normalize(edge.target)
                if edge.external
                else _display_label(edge.target, project_path)
            ),
            external=edge.external,
            import_kinds=edge.import_kinds,
        )
        for edge in graph
    ]


def _display_label(node: str, project_path: str | None) -> str:
    normalized = _normalize(node)
    if project_path is None or not os.path.isabs(node):
        return normalized

    try:
        absolute_node = os.path.abspath(node)
        absolute_root = os.path.abspath(project_path)
        common_path = os.path.commonpath([absolute_node, absolute_root])
    except ValueError:
        return normalized

    if os.path.normcase(common_path) != os.path.normcase(absolute_root):
        return normalized

    relative = os.path.relpath(absolute_node, absolute_root)
    return "." if relative == "." else _normalize(relative)


def _select_nodes(graph: list[_DisplayEdge], options: GraphQueryOptions) -> set[str]:
    all_nodes = {node for edge in graph for node in (edge.source, edge.target)}
    has_query = (
        options.focus is not None
        or options.reachable_from is not None
        or options.dependents_of is not None
    )

    if not has_query:
        return all_nodes

    selected: set[str] = set()

    if options.focus is not None:
        selected.update(_expand_focus(graph, options.focus, options.focus_depth))

    if options.reachable_from is not None:
        selected.update(_walk_graph(graph, options.reachable_from, "outgoing"))

    if options.dependents_of is not None:
        selected.update(_walk_graph(graph, options.dependents_of, "incoming"))

    return selected


def _expand_focus(
    graph: list[_DisplayEdge],
    pattern: Pattern,
    depth: int,
) -> set[str]:
    selected: set[str] = set()
    queue: list[tuple[str, int]] = []

    for node in {node for edge in graph for node in (edge.source, edge.target)}:
        if _matches(pattern, node):
            selected.add(node)
            queue.append((node, 0))

    while queue:
        current, current_depth = queue.pop(0)
        if current_depth >= depth:
            continue

        for neighbor in _neighbors_of(graph, current):
            if neighbor not in selected:
                selected.add(neighbor)
                queue.append((neighbor, current_depth + 1))

    return selected


def _walk_graph(
    graph: list[_DisplayEdge],
    pattern: Pattern,
    direction: Literal["incoming", "outgoing"],
) -> set[str]:
    selected: set[str] = set()
    queue: list[str] = []

    for node in {node for edge in graph for node in (edge.source, edge.target)}:
        if _matches(pattern, node):
            selected.add(node)
            queue.append(node)

    while queue:
        current = queue.pop(0)
        next_nodes: list[str] = []
        for edge in graph:
            if direction == "outgoing" and edge.source == current:
                next_nodes.append(edge.target)
            elif direction == "incoming" and edge.target == current:
                next_nodes.append(edge.source)

        for next_node in next_nodes:
            if next_node not in selected:
                selected.add(next_node)
                queue.append(next_node)

    return selected


def _neighbors_of(graph: list[_DisplayEdge], node: str) -> list[str]:
    neighbors: list[str] = []
    for edge in graph:
        if edge.source == node and edge.target != node:
            neighbors.append(edge.target)
        elif edge.target == node and edge.source != node:
            neighbors.append(edge.source)
    return neighbors


def _collapse_node(node: str, strategy: GraphCollapseStrategy | None) -> str:
    if strategy is None:
        return node

    normalized = _normalize(node)

    if isinstance(strategy, PatternCollapse):
        return strategy.pattern.sub(strategy.replacement, normalized)

    depth = max(1, strategy.depth)
    parts = [part for part in normalized.split("/") if part]
    if len(parts) <= 1:
        return normalized

    folder_parts = parts[:-1]
    if not folder_parts:
        return normalized

    return "/".join(folder_parts[:depth])


def _matches(pattern: Pattern, node: str) -> bool:
    normalized = _normalize(node)
    if isinstance(pattern, str):
        return fnmatch.fnmatchcase(normalized, pattern)
    return bool(pattern.search(normalized))


def _normalize(node: str) -> str:
    return node.replace("\\", "/")


def _unique_sorted(values: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    return tuple(sorted(set(values)))


def _unique_sorted_import_kinds(values: tuple[object, ...]) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                str(getattr(value, "value", value))
                for value in values
            }
        )
    )


def _quote_dot(input_value: str) -> str:
    return '"' + input_value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _quote_d2(input_value: str) -> str:
    return '"' + input_value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _escape_mermaid_label(input_value: str) -> str:
    return input_value.replace("\\", "\\\\").replace('"', "#quot;")


def _render_edge_table(snapshot: GraphReportSnapshot) -> str:
    if not snapshot.edges:
        return '<div class="empty">No dependency edges matched this graph query.</div>'

    rows = "\n".join(
        f"""      <tr>
        <td>{escape_html(edge.source)}</td>
        <td>{escape_html(edge.target)}</td>
        <td>{edge.count}</td>
        <td>{"yes" if edge.external else "no"}</td>
        <td>{escape_html(", ".join(edge.import_kinds))}</td>
      </tr>"""
        for edge in snapshot.edges
    )

    return f"""<table>
  <thead>
    <tr>
      <th>Source</th>
      <th>Target</th>
      <th>Count</th>
      <th>External</th>
      <th>Import Kinds</th>
    </tr>
  </thead>
  <tbody>
{rows}
  </tbody>
</table>"""


def _write_report(output_path: str, content: str) -> None:
    path = Path(output_path)
    if path.parent != Path("."):
        path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
