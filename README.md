# ArchUnitPy - Architecture Testing

<div align="center" name="top">

<!-- spacer -->
<p></p>

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://img.shields.io/pypi/v/archunitpython.svg)](https://pypi.org/project/archunitpython/)
[![Python versions](https://img.shields.io/pypi/pyversions/archunitpython.svg)](https://pypi.org/project/archunitpython/)
[![GitHub stars](https://img.shields.io/github/stars/LukasNiessen/ArchUnitPython.svg)](https://github.com/LukasNiessen/ArchUnitPython)

</div>

Enforce architecture rules in Python projects. Check for dependency directions, detect circular dependencies, enforce coding standards and much more. Integrates with pytest and any other testing framework. Very simple setup and pipeline integration. Zero runtime dependencies.

_The Python port of [ArchUnitTS](https://github.com/LukasNiessen/ArchUnitTS). Inspired by the amazing ArchUnit library but we are not affiliated with ArchUnit._

[Setup](#-setup) • [Use Cases](#-use-cases) • [Features](#-features) • [Contributing](CONTRIBUTING.md)

## ⚡ 5 min Quickstart

### Installation

```bash
pip install archunitpython
```

### Add tests

Simply add tests to your existing test suites. The following is an example using pytest. First we ensure that we have no circular dependencies.

```python
from archunitpy import project_files, metrics, assert_passes

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

## 🚐 Setup

Installation:

```bash
pip install archunitpy
```

That's it. Works with **pytest**, **unittest**, or any Python testing framework.

### pytest (Recommended)

Use `assert_passes()` for clean assertion messages:

```python
from archunitpy import project_files, assert_passes

def test_my_architecture():
    rule = project_files("src/").should().have_no_cycles()
    assert_passes(rule)
```

### Any Other Framework

Use `.check()` directly and assert on the violations list:

```python
from archunitpy import project_files

rule = project_files("src/").should().have_no_cycles()
violations = rule.check()
assert len(violations) == 0
```

### Configuration Options

Both `assert_passes()` and `.check()` accept configuration options:

```python
from archunitpy import CheckOptions

options = CheckOptions(
    allow_empty_tests=True,  # Don't fail when no files match
    clear_cache=True,        # Clear the graph cache
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

Here is a repository with a fully functioning example that uses ArchUnitPy to ensure architectural rules:

- **[RAG Pipeline Example](https://github.com/LukasNiessen/ArchUnitPy-Example-RAG)**: A mock AI/RAG pipeline with layered architecture and intentional violations demonstrating ArchUnitPy catching real problems

## 🐣 Features

This is an overview of what you can do with ArchUnitPy.

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
from archunitpy import project_slices

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

### Reports

Generate HTML reports for your metrics. _Note that this feature is in beta._

```python
from archunitpy.metrics.fluentapi.export_utils import MetricsExporter, ExportOptions

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

ArchUnitPy can validate your architecture against PlantUML diagrams, ensuring your code matches your architectural designs.

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
from archunitpy import CheckOptions
from archunitpy.common.logging.types import LoggingOptions

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

The features of ArchUnitPy can very well be used as architectural fitness functions. See [here](https://www.thoughtworks.com/en-de/insights/articles/fitness-function-driven-development) for more information about that topic.

## 🔲 Core Modules

| Module      | Description                    | Status       |
| ----------- | ------------------------------ | ------------ |
| **Files**   | File and folder based rules    | Stable       |
| **Metrics** | Code quality metrics           | Stable       |
| **Slices**  | Architecture slicing           | Stable       |
| **Testing** | Test framework integration     | Stable       |
| **Common**  | Shared utilities               | Stable       |
| **Reports** | Generate HTML reports          | Experimental |

### ArchUnitPy uses ArchUnitPy

We use ourselves to ensure the architectural rules for this repository.

## 🦊 Contributing

We highly appreciate contributions. We use GitHub Flow, meaning that we use feature branches. As soon as something is merged or pushed to `main` it gets deployed. Versioning is automated via [Conventional Commits](https://www.conventionalcommits.org/). See more in [Contributing](CONTRIBUTING.md).

## ℹ️ FAQ

**Q: What Python testing frameworks are supported?**

ArchUnitPy works with pytest, unittest, and any other testing framework. We recommend pytest with `assert_passes()`.

**Q: What Python versions are supported?**

Python 3.10 and above.

**Q: Does ArchUnitPy have any runtime dependencies?**

No. ArchUnitPy uses only the Python standard library. Development dependencies (pytest, mypy, ruff) are optional.

**Q: How does it analyze Python imports?**

ArchUnitPy uses Python's built-in `ast` module to parse source files and resolve imports. It handles absolute imports, relative imports, and package imports.

**Q: How do I handle false positives in architecture rules?**

Use the filtering and targeting capabilities to exclude specific files or patterns. You can filter by file paths, class names, or custom predicates to fine-tune your rules.

## 📅 Plans

ArchUnitPy is the Python port of ArchUnitTS. We plan to keep it in sync with the TypeScript version's features, and extend it with Python-specific capabilities.

## 🐣 Origin Story

ArchUnitPy started as the Python port of [ArchUnitTS](https://github.com/LukasNiessen/ArchUnitTS). With the rise of LLMs and AI integration, enforcing architectural boundaries and QA in general has become more critical than ever -- especially in Python, the dominant language in the AI/ML ecosystem.

## 💟 Community

### Maintainers

- **[LukasNiessen](https://github.com/LukasNiessen)** - Creator and main maintainer

### Questions

Found a bug? Want to discuss features?

- Submit an [issue on GitHub](https://github.com/LukasNiessen/ArchUnitPy/issues/new/choose)
- Join our [GitHub Discussions](https://github.com/LukasNiessen/ArchUnitPy/discussions)

If ArchUnitPy helps your project, please consider:

- Starring the repository
- Suggesting new features
- Contributing code or documentation

## 📄 License

This project is under the **MIT** license.

---

<p align="center">
  <a href="#top"><strong>Go Back to Top</strong></a>
</p>
