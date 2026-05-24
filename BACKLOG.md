# Backlog

This backlog collects product and maintenance ideas from project research.

## P0 - Maintenance And Correctness

- [x] Keep package metadata synchronized across `pyproject.toml`, `CHANGELOG.md`, and `src/archunitpython/__init__.py`.
- [x] Keep tool configuration valid for the supported Python range, especially mypy and Ruff target versions.
- [x] Add a release metadata check that fails when the exported `__version__` differs from the project version.
- [x] Add CI jobs that run tests, Ruff, mypy, and a package build from a clean checkout.

## P1 - Adoption Workflow

- Add an `.archignore` or similar file, modeled after `.gitignore`, for files that should never be analyzed.
- Add a `.because(...)` API so rules can carry user-facing rationale into failure messages and generated architecture documentation.
- Add configuration-file support for common rules, while keeping the fluent Python API as the primary interface.
- Add support for monorepo and multi-package Python projects.

## P1 - Python Import Semantics

- Add support for namespace packages that do not contain `__init__.py`.
- Detect dynamic imports such as `importlib.import_module()` and `__import__()`.
- Detect conditional imports such as `try/except ImportError`.
- Add better `TYPE_CHECKING` import handling, including options to ignore, include, or report type-only imports separately.
- Improve external dependency rules so users can express allowed and forbidden third-party packages at module or slice level.
- Consider a public-interface rule inspired by Tach, where modules may only import through declared package APIs.

## P1 - Reporting And Documentation

- Add comprehensive HTML reports with dependency graphs, metric charts, and zone visualization.
- Auto-generate architecture documentation based on tests and rule rationales.
- Make logged paths clickable in IDEs and common terminal integrations.
- Add PlantUML or Mermaid export for discovered architecture graphs.
- Improve metric export examples and document how metric thresholds should be selected.

## P2 - Rule Surface

- Add first-class layered architecture helpers so common clean/hexagonal/layered rules require less boilerplate.
- Add slice isolation helpers for bounded contexts and modular monoliths.
- Add richer custom rule hooks for dependency edges, files, classes, and metrics.
- Add transitive dependency checks, especially for "domain must not transitively reach infrastructure" style rules.
- Add naming and placement conventions for classes/functions, not only files.

## P2 - Performance And Scale

- Improve performance for very large projects through parallel file parsing.
- Add persistent graph caching with invalidation based on file mtimes or content hashes.
- Add benchmarks for small, medium, large, and monorepo-style projects.

## P2 - Metrics

- Add more LCOM edge case handling.
- Add metric documentation with examples for good, suspicious, and failing values.
- Add trend-friendly metric exports for CI artifacts.
- Consider additional architecture metrics such as coupling counts per slice, fan-in/fan-out summaries, and instability per package.

## P3 - Packaging And Docs

- Publish to PyPI as part of the release pipeline if this is not already automated.
- Add a Sphinx or MkDocs documentation site.
- Add a complete example repository or examples folder covering pytest, unittest, PlantUML, metrics, and CI.
- Add contribution guidance for new rule types and metric implementations.
