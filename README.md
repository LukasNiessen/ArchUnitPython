# ArchUnitPython - Architecture Testing

<div align="center" name="top">
  <img align="center" src="assets/logo-rounded.png" width="150" height="150" alt="ArchUnitPython Logo">

<!-- spacer -->
<p></p>

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![Build & tests](https://img.shields.io/github/actions/workflow/status/LukasNiessen/ArchUnitPython/integrate.yaml?branch=main&label=build%20%26%20tests)](https://github.com/LukasNiessen/ArchUnitPython/actions/workflows/integrate.yaml) [![GitHub stars](https://img.shields.io/github/stars/LukasNiessen/ArchUnitPython.svg)](https://github.com/LukasNiessen/ArchUnitPython)<br>
[![PyPI downloads](https://static.pepy.tech/badge/archunitpython/month)](https://pepy.tech/project/archunitpython) [![PyPI total downloads](https://img.shields.io/pepy/dt/archunitpython?label=total%20downloads&color=007ec6)](https://pepy.tech/project/archunitpython)
<!-- [![PyPI version](https://img.shields.io/pypi/v/archunitpython.svg)](https://pypi.org/project/archunitpython/) -->

</div>

Enforce architecture rules in Python projects. Check for dependency directions, detect circular dependencies, enforce coding standards and much more. Integrates with pytest and any other testing framework. Very simple setup and pipeline integration. Zero runtime dependencies.

The #1 ArchUnit-style architecture testing library for Python, measured by GitHub stars.

_Inspired by the amazing ArchUnit library but we are not affiliated with ArchUnit._

[Setup](#-setup) • [Use Cases](#-use-cases) • [Features](#-features) • [Why ArchUnitPython?](#-library-comparison) • [Sponsor](https://github.com/sponsors/LukasNiessen) • [Contributing](CONTRIBUTING.md)

## ⚡ 5 min Quickstart

### Installation

```bash
pip install archunitpython
```

### Add tests

Simply add tests to your existing test suites. The following is an example using pytest. First we ensure that we have no circular dependencies.

```python
from archunitpython import project_files, metrics, assert_passes

def test_no_circular_dependencies():
    rule = project_files("src/").in_folder("src/**").should().have_no_cycles()
    assert_passes(rule)
```

Next we ensure that our layered architecture is respected.

```python
def test_presentation_should_not_depend_on_database():
    rule = (
        project_files("src/")
        .in_folder("**/presentation/**")
        .should_not()
        .depend_on_files()
        .in_folder("**/database/**")
    )
    assert_passes(rule)

def test_business_should_not_depend_on_database():
    rule = (
        project_files("src/")
        .in_folder("**/business/**")
        .should_not()
        .depend_on_files()
        .in_folder("**/database/**")
    )
    assert_passes(rule)

# More layers ...
```

Lastly we ensure that some code metric rules are met.

```python
def test_no_large_files():
    rule = metrics("src/").count().lines_of_code().should_be_below(1000)
    assert_passes(rule)

def test_high_cohesion():
    # LCOM metric (lack of cohesion of methods), low = high cohesion
    rule = metrics("src/").lcom().lcom96b().should_be_below(0.3)
    assert_passes(rule)
```

### CI Integration

These tests run automatically in your testing setup, for example in your CI pipeline, so that's basically it. This setup ensures that the architectural rules you have defined are always adhered to!

```yaml
# GitHub Actions
- name: Run Architecture Tests
  run: pytest tests/test_architecture.py -v
```

You can also export dependency graph reports as CI artifacts:

```python
from archunitpython import project_graph

def test_generate_dependency_graph_reports():
    graph = project_graph("src/").titled("Application Architecture")

    graph.collapse_to_folder_depth(2).export_as_html(
        "reports/dependency-graph.html"
    )
    graph.export_as_mermaid("reports/dependency-graph.mmd")

    assert graph.snapshot().summary.node_count >= 0
```

## 🚐 Setup

Installation:

```bash
pip install archunitpython
```

That's it. Works with **pytest**, **unittest**, or any Python testing framework.

### pytest (Recommended)

Use `assert_passes()` for clean assertion messages:

```python
from archunitpython import project_files, assert_passes

def test_my_architecture():
    rule = project_files("src/").should().have_no_cycles()
    assert_passes(rule)
```

### Any Other Framework

Use `.check()` directly and assert on the violations list:

```python
from archunitpython import project_files

rule = project_files("src/").should().have_no_cycles()
violations = rule.check()
assert len(violations) == 0
```

### Configuration Options

Both `assert_passes()` and `.check()` accept configuration options:

```python
from archunitpython import CheckOptions

options = CheckOptions(
    allow_empty_tests=True,  # Don't fail when no files match
    clear_cache=True,        # Clear the graph cache
    ignore_type_checking_imports=True,  # Ignore imports inside if TYPE_CHECKING
)

violations = rule.check(options)
```

## 🐹 Use Cases

Here is an overview of common use cases.

**Layered Architecture:**

Enforce that higher layers don't depend on lower layers and vice versa.

**Clean Architecture / Hexagonal:**

Validate that domain logic doesn't depend on infrastructure.

**Microservices / Modular:**

Ensure services/modules don't have forbidden cross-dependencies.

## 🐲 Example Repository

Here is a repository with a fully functioning example that uses ArchUnitPython to ensure architectural rules:

- **[RAG Pipeline Test Showcase](https://github.com/LukasNiessen/ArchUnitPython-TestRepo-RAG)**: A test showcase demonstrating ArchUnitPython's architecture testing capabilities on a RAG pipeline

## 🐣 Features

This is an overview of what you can do with ArchUnitPython.

### Circular Dependencies

```python
def test_services_cycle_free():
    rule = project_files("src/").in_folder("**/services/**").should().have_no_cycles()
    assert_passes(rule)
```

### Layer Dependencies

```python
def test_clean_architecture_layers():
    rule = (
        project_files("src/")
        .in_folder("**/presentation/**")
        .should_not()
        .depend_on_files()
        .in_folder("**/database/**")
    )
    assert_passes(rule)

def test_business_not_depend_on_presentation():
    rule = (
        project_files("src/")
        .in_folder("**/business/**")
        .should_not()
        .depend_on_files()
        .in_folder("**/presentation/**")
    )
    assert_passes(rule)
```

### Named Layer Rules

```python
from archunitpython import project_layers

def test_clean_architecture_layers():
    rule = (
        project_layers("src/")
        .layer("presentation").defined_by_folder("**/presentation/**")
        .layer("business").defined_by_folder("**/business/**")
        .layer("database").defined_by_folder("**/database/**")
        .where_layer("presentation")
        .may_only_depend_on_layers("business")
        .where_layer("business")
        .may_only_depend_on_layers()
        .where_layer("database")
        .may_only_depend_on_layers()
    )
    assert_passes(rule)
```

### External Dependencies

```python
def test_domain_does_not_import_requests():
    rule = (
        project_files("src/")
        .in_folder("**/domain/**")
        .should_not()
        .depend_on_external_modules()
        .matching("requests")
    )
    assert_passes(rule)
```

### TYPE_CHECKING-aware Analysis

```python
from archunitpython import CheckOptions

def test_type_only_dependencies_do_not_count_as_runtime_coupling():
    rule = (
        project_files("src/")
        .in_folder("**/api/**")
        .should_not()
        .depend_on_files()
        .in_folder("**/infrastructure/**")
    )
    assert_passes(rule, CheckOptions(ignore_type_checking_imports=True))
```

### Dynamic Imports and Ignore Directives

ArchUnitPython detects string-based dynamic imports such as `importlib.import_module("my_app.adapters.sql")` and `__import__("my_app.adapters.sql")`. For known migration shims, you can suppress one import edge locally:

```python
from my_app.adapters.sql import Repository  # archunit: ignore
```

### Naming Conventions

```python
def test_naming_patterns():
    rule = (
        project_files("src/")
        .in_folder("**/services/**")
        .should()
        .have_name("*_service.py")
    )
    assert_passes(rule)
```

### Code Metrics

```python
def test_no_large_files():
    rule = metrics("src/").count().lines_of_code().should_be_below(1000)
    assert_passes(rule)

def test_high_class_cohesion():
    rule = metrics("src/").lcom().lcom96b().should_be_below(0.3)
    assert_passes(rule)

def test_method_count():
    rule = metrics("src/").count().method_count().should_be_below(20)
    assert_passes(rule)

def test_field_count_for_data_classes():
    rule = (
        metrics("src/")
        .for_classes_matching("*Data*")
        .count()
        .field_count()
        .should_be(3)
    )
    assert_passes(rule)
```

### Distance Metrics

```python
def test_proper_coupling():
    rule = metrics("src/").distance().distance_from_main_sequence().should_be_below(0.3)
    assert_passes(rule)

def test_not_in_zone_of_pain():
    rule = metrics("src/").distance().not_in_zone_of_pain()
    assert_passes(rule)
```

### Custom Rules

You can define your own custom rules.

```python
rule_desc = "Python files should have docstrings"

def has_docstring(file):
    return '"""' in file.content or "'''" in file.content

violations = (
    project_files("src/")
    .with_name("*.py")
    .should()
    .adhere_to(has_docstring, rule_desc)
    .check()
)

assert len(violations) == 0
```

### Custom Metrics

You can define your own metrics as well.

```python
def test_method_field_ratio():
    rule = (
        metrics("src/")
        .custom_metric(
            "methodFieldRatio",
            "Ratio of methods to fields",
            lambda ci: len(ci.methods) / max(len(ci.fields), 1),
        )
        .should_be_below(10)
    )
    assert_passes(rule)
```

### Architecture Slices

```python
import re
from archunitpython import project_slices

def test_adhere_to_diagram():
    diagram = """
@startuml
  component [controllers]
  component [services]
  [controllers] --> [services]
@enduml"""

    rule = (
        project_slices("src/")
        .defined_by_regex(re.compile(r"/([^/]+)/[^/]+\.py$"))
        .should()
        .adhere_to_diagram(diagram)
    )
    assert_passes(rule)

def test_no_forbidden_dependency():
    rule = (
        project_slices("src/")
        .defined_by("src/(**)/**")
        .should_not()
        .contain_dependency("services", "controllers")
    )
    assert_passes(rule)
```

### Dependency Graph Reports

Generate dependency graph reports in multiple formats and narrow them to the part of the codebase you want to inspect.

```python
from archunitpython import project_graph

def test_export_dependency_graph_reports():
    graph = project_graph("src/").titled("Application Architecture")

    graph.collapse_to_folder_depth(2).export_as_mermaid(
        "reports/dependencies.mmd"
    )

    graph.focus_on("**/domain/**", 1).export_as_html(
        "reports/domain-dependencies.html"
    )

    assert graph.snapshot().summary.node_count >= 0
```

Supported formats:

- DOT (`export_as_dot`, `to_dot`)
- Mermaid (`export_as_mermaid`, `to_mermaid`)
- D2 (`export_as_d2`, `to_d2`)
- CSV (`export_as_csv`, `to_csv`)
- JSON (`export_as_json`, `to_json`)
- HTML (`export_as_html`, `to_html`)

Graph exploration options:

- `focus_on(pattern, depth)` keeps matching files and their neighbors.
- `reachable_from(pattern)` keeps matching files and their transitive dependencies.
- `dependents_of(pattern)` keeps files that transitively depend on the matching files.
- `collapse_to_folder_depth(depth)` aggregates files to folder-level graph nodes.
- `collapse_by_pattern(pattern, replacement)` maps files to custom graph nodes.
- `include_external_dependencies()` includes imports to external modules such as `requests` or `sqlalchemy`.
- `include_self_dependencies()` keeps self edges that are normally hidden in reports.

When you create reports through `project_graph("src/")`, internal file paths are displayed relative to that project root so the output stays readable.

### Reports

Generate HTML reports for your metrics. _Note that this feature is in beta._

```python
from archunitpython.metrics.fluentapi.export_utils import MetricsExporter, ExportOptions

MetricsExporter.export_as_html(
    {"MethodCount": 5, "FieldCount": 3, "LinesOfCode": 150},
    ExportOptions(
        output_path="reports/metrics.html",
        title="Architecture Metrics Dashboard",
    ),
)
```

## 🔎 Pattern Matching System

We offer three targeting options for pattern matching across all modules:

- **`with_name(pattern)`** - Pattern is checked against the filename (e.g. `service.py` from `src/services/service.py`)
- **`in_path(pattern)`** - Pattern is checked against the full relative path (e.g. `src/services/service.py`)
- **`in_folder(pattern)`** - Pattern is checked against the path without filename (e.g. `src/services` from `src/services/service.py`)

For the metrics module there is an additional one:

- **`for_classes_matching(pattern)`** - Pattern is checked against class names. The filepath or filename does not matter here

### Pattern Types

We support string patterns and regular expressions. String patterns support glob.

```python
# String patterns with glob support (case sensitive)
.with_name("*_service.py")       # All files ending with _service.py
.in_folder("**/services")        # All files in any services folder
.in_path("src/api/**/*.py")      # All Python files under src/api

# Regular expressions
import re
.with_name(re.compile(r".*Service\.py$"))
.in_folder(re.compile(r"services$"))

# For metrics module: Class name matching
.for_classes_matching("*Service*")
.for_classes_matching(re.compile(r"^User.*"))
```

### Glob Patterns Guide

#### Basic Wildcards

- `*` - Matches any characters within a single path segment (except `/`)
- `**` - Matches any characters across multiple path segments
- `?` - Matches exactly one character

#### Common Glob Examples

```python
# Filename patterns
.with_name("*.py")              # All Python files
.with_name("*_service.py")      # Files ending with _service.py
.with_name("test_*.py")         # Files starting with test_

# Folder patterns
.in_folder("**/services")       # Any services folder at any depth
.in_folder("src/services")      # Exact src/services folder
.in_folder("**/test/**")        # Any folder containing test in path

# Path patterns
.in_path("src/**/*.py")                # Python files anywhere under src
.in_path("**/test/**/*_test.py")       # Test files in any test folder
```

### Recommendation

We generally recommend using string patterns with glob support unless you need very special cases. Regular expressions add extra complexity that is not necessary for most cases.

### Supported Metric Types

#### LCOM (Lack of Cohesion of Methods)

The LCOM metrics measure how well the methods and fields of a class are connected. Lower values indicate better cohesion.

```python
# LCOM96a (Henderson et al.)
metrics("src/").lcom().lcom96a().should_be_below(0.8)

# LCOM96b (Henderson et al.) - most commonly used
metrics("src/").lcom().lcom96b().should_be_below(0.7)
```

All 8 LCOM variants are available: `lcom96a()`, `lcom96b()`, `lcom1()` through `lcom5()`, and `lcomstar()`.

The LCOM96b metric is calculated as:

```
LCOM96b = (1/a) * sum((1/m) * (m - mu(Ai)))
```

Where:

- `m` is the number of methods in the class
- `a` is the number of attributes (fields) in the class
- `mu(Ai)` is the number of methods that access attribute Ai

The result is a value between 0 and 1:

- 0: perfect cohesion (all methods access all attributes)
- 1: complete lack of cohesion (each method accesses its own attribute)

#### Count Metrics

```python
metrics("src/").count().method_count().should_be_below(20)
metrics("src/").count().field_count().should_be_below(15)
metrics("src/").count().lines_of_code().should_be_below(200)
metrics("src/").count().statements().should_be_below(100)
metrics("src/").count().imports().should_be_below(20)
```

#### Distance Metrics

```python
metrics("src/").distance().abstractness().should_be_above(0.3)
metrics("src/").distance().instability().should_be_below(0.8)
metrics("src/").distance().distance_from_main_sequence().should_be_below(0.5)
```

#### Custom Metrics

```python
metrics("src/").custom_metric(
    "complexityRatio",
    "Ratio of methods to fields",
    lambda ci: len(ci.methods) / max(len(ci.fields), 1),
).should_be_below(3.0)
```

## 📐 UML Diagram Support

ArchUnitPython can validate your architecture against PlantUML diagrams, ensuring your code matches your architectural designs.

### Component Diagrams

```python
def test_component_architecture():
    diagram = """
@startuml
component [UserInterface]
component [BusinessLogic]
component [DataAccess]

[UserInterface] --> [BusinessLogic]
[BusinessLogic] --> [DataAccess]
@enduml"""

    rule = (
        project_slices("src/")
        .defined_by("src/(**)/**")
        .should()
        .adhere_to_diagram(diagram)
    )
    assert_passes(rule)
```

### Diagram from File

```python
def test_from_file():
    rule = (
        project_slices("src/")
        .defined_by("src/(**)/**")
        .should()
        .adhere_to_diagram_in_file("docs/architecture.puml")
    )
    assert_passes(rule)
```

## 📊 Library Comparison

Here's how ArchUnitPython compares to other Python architecture-enforcement libraries.

ArchUnitPython is optimized for **architecture rules as tests**: rules live next to your normal unit tests, run in pytest/unittest/CI, and fail with test-style violation messages. Broader CLI-first tools such as [Tach](https://github.com/tach-org/tach) and [Import Linter](https://github.com/seddonym/import-linter) are excellent adjacent tools, but they solve the problem through separate configuration and commands rather than a test-native ArchUnit-style API.

| Feature | **ArchUnitPython** | **Tach** | **Import Linter** | **PyTestArch** |
| ------- | ------------------ | -------- | ----------------- | -------------- |
| **Primary workflow** | ✅ Architecture rules as unit tests | ⚠️ CLI + `tach.toml` | ⚠️ CLI + contracts config | ⚠️ pytest-oriented evaluable architecture |
| **ArchUnit-style fluent API** | ✅ Yes | ❌ No | ❌ No | ⚠️ Partial |
| **Testing framework integration** | ✅ pytest, unittest, any runner | ⚠️ CI/pre-commit CLI | ⚠️ CI/pre-commit CLI | ⚠️ pytest-focused |
| **Zero runtime dependencies** | ✅ Standard library only | ⚠️ No app runtime impact, Rust-backed tool | ❌ Tool dependencies | ❌ Tool dependencies |
| **Circular dependency detection** | ✅ First-class | ✅ First-class | ⚠️ Contract/graph based | ⚠️ Import-rule based |
| **File/folder dependency rules** | ✅ Glob + regex | ✅ Module config | ✅ Import contracts | ✅ Module rules |
| **Named layer rules** | ✅ `project_layers()` | ✅ Supported | ✅ Supported | ✅ Supported |
| **External dependency rules** | ✅ `depend_on_external_modules()` | ⚠️ Internal module focus | ⚠️ Import contract focus | ⚠️ Internal import focus |
| **TYPE_CHECKING-aware analysis** | ✅ Configurable | ⚠️ Not the core API | ⚠️ Not the core API | ⚠️ Not the core API |
| **Dynamic import detection** | ✅ `importlib` + `__import__` string calls | ⚠️ Not the core workflow | ⚠️ Not the core workflow | ⚠️ Import analysis focused |
| **Inline ignore directives** | ✅ `# archunit: ignore` | ✅ Supported | ⚠️ Config-based ignores | ⚠️ Rule/exclusion based |
| **Naming convention checks** | ✅ Files and paths | ❌ No | ❌ No | ⚠️ Module-name oriented |
| **Code metrics** | ✅ Counts, LCOM, distance metrics | ❌ No | ❌ No | ❌ No |
| **Custom rules and metrics** | ✅ Full support | ❌ No | ⚠️ Custom contracts | ⚠️ Limited custom rule composition |
| **PlantUML diagram validation** | ✅ Supported | ❌ No | ❌ No | ❌ No |
| **Empty test protection** | ✅ Fails by default | ⚠️ Config validation | ⚠️ Contract validation | ⚠️ Not the main focus |
| **Graph/reporting** | ✅ DOT, Mermaid, D2, CSV, JSON, HTML graph reports + metrics HTML | ✅ DOT, JSON, web graph | ✅ Browser UI | ⚠️ Optional graph visualization |
| **Best fit** | Architecture tests, CI fitness functions, metrics, diagrams | Modular monolith dependency governance | Config-driven import contracts | pytest import-boundary checks |

The most important differences:

- **Test-native by design**: ArchUnitPython rules are just Python tests, so architecture decisions are reviewed, run, and debugged in the same workflow as the rest of your test suite.
- **Broader rule surface**: dependency direction, cycles, layer policies, external modules, type-only imports, dynamic imports, naming, metrics, custom rules, and PlantUML validation live in one API.
- **False-positive protection**: empty checks fail by default, which helps catch typos in file and folder patterns before they silently make your architecture tests meaningless.
- **Quality beyond imports**: ArchUnitPython can enforce code metrics such as LCOM cohesion, field/method counts, abstractness, instability, and distance from the main sequence.

## 📢 Informative Error Messages

When tests fail, you get helpful output with file paths and violation details:

```
Found 2 architecture violation(s):

  1. File dependency violation
     'src/api/bad_shortcut.py' depends on 'src/retrieval/vector_store.py'

  2. File dependency violation
     'src/api/bad_shortcut.py' depends on 'src/retrieval/embedder.py'
```

## 📝 Debug Logging & Configuration

We support logging to help you understand what files are being analyzed and troubleshoot test failures. Logging is disabled by default to keep test output clean.

### Enabling Debug Logging

```python
from archunitpython import CheckOptions
from archunitpython.common.logging.types import LoggingOptions

options = CheckOptions(
    logging=LoggingOptions(
        enabled=True,
        level="debug",       # "error" | "warn" | "info" | "debug"
        log_file=True,       # Creates logs/archunit-YYYY-MM-DD_HH-MM-SS.log
    ),
)

violations = rule.check(options)
```

### CI Pipeline Integration

```yaml
# GitHub Actions
- name: Run Architecture Tests
  run: pytest tests/test_architecture.py -v

- name: Upload Test Logs
  if: always()
  uses: actions/upload-artifact@v3
  with:
    name: architecture-test-logs
    path: logs/
```

## 🏈 Architecture Fitness Functions

The features of ArchUnitPython can very well be used as architectural fitness functions. See [here](https://www.thoughtworks.com/en-de/insights/articles/fitness-function-driven-development) for more information about that topic.

## 🔲 Core Modules

| Module      | Description                    | Status       |
| ----------- | ------------------------------ | ------------ |
| **Files**   | File and folder based rules    | Stable       |
| **Metrics** | Code quality metrics           | Stable       |
| **Slices**  | Architecture slicing           | Stable       |
| **Graph**   | Dependency graph reports       | Experimental |
| **Testing** | Test framework integration     | Stable       |
| **Common**  | Shared utilities               | Stable       |
| **Reports** | Generate HTML reports          | Experimental |

### ArchUnitPython uses ArchUnitPython

We use ourselves to ensure the architectural rules for this repository.

## 🦊 Contributing

We highly appreciate contributions. See [Contributing](CONTRIBUTING.md) for the full workflow.

- Use feature branches and open pull requests against `main`.
- Use [Conventional Commits](https://www.conventionalcommits.org/) so releases can be versioned automatically.
- Do not bump versions manually for normal feature or fix work; semantic-release updates `pyproject.toml`, `src/archunitpython/__init__.py`, and `CHANGELOG.md`.
- CI checks linting, typing, tests, package builds, and release metadata sync.

## ℹ️ FAQ

**Q: What Python testing frameworks are supported?**

ArchUnitPython works with pytest, unittest, and any other testing framework. We recommend pytest with `assert_passes()`.

**Q: What Python versions are supported?**

Python 3.10 and above.

**Q: Does ArchUnitPython have any runtime dependencies?**

No. ArchUnitPython uses only the Python standard library. Development dependencies (pytest, mypy, ruff) are optional.

**Q: How does it analyze Python imports?**

ArchUnitPython uses Python's built-in `ast` module to parse source files and resolve imports. It handles absolute imports, relative imports, and package imports.

**Q: How do I handle false positives in architecture rules?**

Use the filtering and targeting capabilities to exclude specific files or patterns. You can filter by file paths, class names, or custom predicates to fine-tune your rules.

## 📅 Plans

ArchUnitPython is the Python port of ArchUnitTS. We plan to keep it in sync with the TypeScript version's features, and extend it with Python-specific capabilities.

## 🐣 Origin Story

ArchUnitPython started as the Python port of [ArchUnitTS](https://github.com/LukasNiessen/ArchUnitTS). With the rise of LLMs and AI integration, enforcing architectural boundaries and QA in general has become more critical than ever -- especially in Python, the dominant language in the AI/ML ecosystem.

## 💟 Community

### Maintainers

- **[LukasNiessen](https://github.com/LukasNiessen)** - Creator and main maintainer

### Contributors

<a href="https://github.com/LukasNiessen/ArchUnitPython/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=LukasNiessen/ArchUnitPython&max=1000&contributors=10" />
</a>

### Questions

Found a bug? Want to discuss features?

- Submit an [issue on GitHub](https://github.com/LukasNiessen/ArchUnitPython/issues/new/choose)
- Join our [GitHub Discussions](https://github.com/LukasNiessen/ArchUnitPython/discussions)

If ArchUnitPython helps your project, please consider:

- Starring the repository 💚
- Sponsoring development via [GitHub Sponsors](https://github.com/sponsors/LukasNiessen)
- Suggesting new features 💭
- Contributing code or documentation ⌨️

### Star History

[![Star History Chart](https://api.star-history.com/svg?repos=LukasNiessen/ArchUnitPython&type=Date)](https://www.star-history.com/#LukasNiessen/ArchUnitPython&Date)

## 📄 License

This project is under the **MIT** license.

---

<p align="center">
  <a href="#top"><strong>Go Back to Top</strong></a>
</p>
