# 1.0.0 (2026-04-02)


* feat!: rename package from archunitpy to archunitpython ([95c0b3a](https://github.com/LukasNiessen/ArchUnitPython/commit/95c0b3a0047534302f04e42c0bfca3389c9926bf))


### Bug Fixes

* **deps:** bump the actions-updates group with 7 updates ([54521e4](https://github.com/LukasNiessen/ArchUnitPython/commit/54521e492256dcd1f612f119ae03ec87a08dd0c1))
* lint issues ([d69666b](https://github.com/LukasNiessen/ArchUnitPython/commit/d69666b9cb179225d5520f696035e5ca28f2b7ff))
* pypi packaging config ([5bc8b8e](https://github.com/LukasNiessen/ArchUnitPython/commit/5bc8b8eec35b5dcdd8cb391216181963970e4e6e))
* README ([9d41438](https://github.com/LukasNiessen/ArchUnitPython/commit/9d414386245de7288ff441618f0dd56215d032ca))
* resolve all ruff lint errors ([3a349f9](https://github.com/LukasNiessen/ArchUnitPython/commit/3a349f95c686df2bfb0582bcafeeef5e109ba626))
* update README ([e3e8949](https://github.com/LukasNiessen/ArchUnitPython/commit/e3e89493bcdd3458221666cb5f7ee46dc7996a8c))


### BREAKING CHANGES

* Package import changed from `import archunitpy` to
`import archunitpython`.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>

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
