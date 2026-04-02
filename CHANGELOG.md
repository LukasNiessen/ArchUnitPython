# Changelog

All notable changes to ArchUnitPython will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!-- This file is automatically updated by python-semantic-release. -->

## [0.1.0] (2026-04-01)

### Features

* Initial release of ArchUnitPython
* File-level architecture rules: circular dependencies, layer dependencies, naming conventions, custom rules
* Slice-level architecture rules: PlantUML diagram validation, forbidden dependency checks
* Code metrics: 8 count metrics, 8 LCOM cohesion variants, distance metrics (abstractness, instability, zones)
* Custom metrics with arbitrary calculation and assertion logic
* HTML report export (experimental)
* Pattern matching with glob and regex support
* Testing integration: `assert_passes()` for pytest, `check()` for any framework
* Debug logging with file output
* Empty test protection
* Zero runtime dependencies
