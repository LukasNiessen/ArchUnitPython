# Architecture Testing Landscape

Research date: 2026-05-23

This document compares ArchUnitPython with architecture testing tools in the broader ecosystem and with Python-specific alternatives. It focuses on user-facing features that can inform product direction.

## Current ArchUnitPython Position

ArchUnitPython already covers three valuable surfaces:

- File-level architecture rules through `project_files(...)`: dependency direction, cycle detection, naming/path conventions, external dependency checks, and custom file predicates.
- Slice-level architecture rules through `project_slices(...)`: slice extraction from path patterns or regexes, PlantUML diagram adherence, and forbidden slice dependencies.
- Code metrics through `metrics(...)`: count metrics, LCOM variants, abstractness, instability, distance from the main sequence, zone checks, and custom metrics.

That breadth makes the project closer to ArchUnit-style libraries than to pure import linters. The main gaps are around configuration ergonomics, reporting, incremental adoption, IDE/CI workflow polish, and deeper Python import semantics.

## General Architecture Testing Players

| Tool | Ecosystem | Rule definition style | Dependency/layer rules | Cycles | Diagram support | Metrics | Reports/visualization | Notable strengths | ArchUnitPython comparison |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [ArchUnit](https://www.archunit.org/userguide/html/000_Index.html) | Java | Fluent Java API, JUnit integrations | Yes: packages, classes, layers, slices | Yes | PlantUML component diagrams | Yes: software architecture metrics | Strong test failure output; mature JUnit support | Mature reference implementation; broad rule model and advanced adoption features such as freezing/ignoring violations | ArchUnitPython mirrors the core idea and already has files/slices/metrics, but lacks class/member/annotation richness and mature freeze/import options |
| [ArchUnitNET](https://github.com/TNG/ArchUnitNET) | .NET | Fluent C# API with xUnit/NUnit/MSTest integrations | Yes: assemblies, namespaces, types, members | Yes | PlantUML support and diagram generation in the project ecosystem | Limited compared with ArchUnit | Test framework integrations | Strong .NET analogue to ArchUnit with many framework adapters | ArchUnitPython has stronger built-in code metrics, but less type/member-level expressiveness |
| [NetArchTest](https://github.com/BenMorris/NetArchTest) | .NET | Fluent C# API | Yes: namespace/type dependency and conventions | Not a primary differentiator | No first-class PlantUML in core | No | Policy results; test framework agnostic | Simple, widely adopted dependency/convention tests for .NET | ArchUnitPython is broader on cycles, slices, PlantUML, and metrics |
| [ts-arch](https://github.com/ts-arch/ts-arch) | TypeScript/JavaScript | Fluent API, Jest matcher | Yes: files, folders, slices | Yes | PlantUML diagram adherence | No | Jest-oriented failure output | Very close conceptual sibling: file API, slice API, PlantUML, NX monorepo support | ArchUnitPython has a similar surface plus metrics; ts-arch has stronger monorepo/NX positioning |
| [jQAssistant](https://jqassistant.github.io/jqassistant/current/) | Mostly JVM, plugin-based | Scanner + graph database + rule concepts/constraints | Yes, via graph rules and plugins | Yes, rule-dependent | Documentation validation and living documentation workflows | Software analytics via graph queries | Reports, server/explore mode, graph-backed analysis | Enterprise-scale scanning, graph exploration, living documentation, baseline management | ArchUnitPython is much lighter and easier to embed in tests, but lacks graph database exploration and living-doc workflows |

## Python Architecture Testing Libraries

| Tool | Rule definition style | Dependency/layer rules | Cycles | External dependency rules | Diagram support | Metrics | Reports/visualization | Adoption workflow | How ArchUnitPython stacks up |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [ArchUnitPython](https://github.com/LukasNiessen/ArchUnitPython) | Fluent Python API used from pytest/unittest/any test framework | Yes: file dependencies, external modules, slices, forbidden slice dependencies | Yes: file-level cycles | Yes: external module matching | Yes: PlantUML slice adherence | Yes: count, LCOM, distance, custom metrics | Experimental metric export; no full HTML report yet | Plain test functions; `assert_passes()` or `.check()` | Broadest feature mix among the Python tools reviewed, especially because metrics and PlantUML are built in |
| [Import Linter](https://import-linter.readthedocs.io/en/stable/index.html) | `.importlinter` configuration contracts plus CLI | Yes: forbidden, protected, layers, independence, acyclic siblings, custom contracts | Yes: acyclic siblings | Primarily first-party import contracts | No first-class PlantUML | No | Browser-based architecture UI | CLI, CI, config file, caching | More mature for config-driven import contracts and exploration; ArchUnitPython is more test-native and broader on metrics/PlantUML |
| [Tach](https://docs.gauge.sh/getting-started/introduction/) | `tach.toml` plus CLI commands | Yes: module dependencies and public interfaces | Dependency graph focused | Yes: `check-external` for third-party imports | No | No | `show`, `map`, `report`, VS Code integration | Incremental CLI workflow, sync, pre-commit/CI, public interface enforcement | Tach is stronger for modular-boundary workflow and public APIs; ArchUnitPython is stronger for test-suite rules, metrics, and diagram validation |
| [PyTestArch](https://zyskarch.github.io/pytestarch/latest/features/module_import_checks/) | Python query language evaluated in pytest | Yes: module dependency query language and layered architecture rules | Implicit through dependency rules; not positioned as a primary cycle API | Not a main focus | Yes: generates rules from PlantUML component diagrams | No | Optional matplotlib visualization | Pytest-centered evaluation structures | Similar to ArchUnitPython on Python tests and PlantUML; ArchUnitPython has simpler fluent API and built-in metrics |
| [pytest-archon](https://github.com/jwbargsten/pytest-archon) | Pytest-oriented architecture assertions | Yes: forbidden dependencies and project structure rules | Yes, positioned around avoiding cycles | Not a main differentiator | No | No | Pytest failure output | Lightweight pytest helper | ArchUnitPython is broader and more ArchUnit-like; pytest-archon is smaller and focused |

## Product Takeaways

- ArchUnitPython should lean into being the ArchUnit-style Python test library, not just another import linter.
- The nearest feature gap against Python tools is not raw rule breadth; it is workflow: config files, ignore files, public interfaces, incremental adoption, reporting, and IDE/CI polish.
- Against ArchUnit and ArchUnitNET, the biggest long-term gaps are richer semantic model support, better ignore/freeze mechanisms, and mature documentation/reporting.
- Metrics are a meaningful differentiator in the Python space and should be kept visible in docs and examples.

## Sources

- ArchUnit User Guide: https://www.archunit.org/userguide/html/000_Index.html
- ArchUnitNET repository: https://github.com/TNG/ArchUnitNET
- NetArchTest repository: https://github.com/BenMorris/NetArchTest
- ts-arch repository: https://github.com/ts-arch/ts-arch
- jQAssistant User Manual: https://jqassistant.github.io/jqassistant/current/
- Import Linter documentation: https://import-linter.readthedocs.io/en/stable/index.html
- Tach documentation: https://docs.gauge.sh/getting-started/introduction/
- PyTestArch documentation: https://zyskarch.github.io/pytestarch/latest/features/module_import_checks/
- PyTestArch PlantUML documentation: https://zyskarch.github.io/pytestarch/latest/features/plantuml/
- PyTestArch visualization documentation: https://zyskarch.github.io/pytestarch/latest/features/visualization/
- pytest-archon repository: https://github.com/jwbargsten/pytest-archon
