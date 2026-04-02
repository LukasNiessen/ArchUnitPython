# Contributing

Thanks for contributing!

## Setup

- Fork & clone: `git clone https://github.com/LukasNiessen/ArchUnitPy.git`
- Install: `pip install -e ".[dev]"`
- Test: `pytest`
- Lint: `ruff check src/`
- Type check: `mypy src/`

## Guidelines

- Code Style: Run `ruff check` and `ruff format` before committing
- Commits: Use [Conventional Commits](https://www.conventionalcommits.org/) (see below)
- PRs: Use feature branches, clear descriptions, ensure CI passes
- Tests: Maintain high coverage

## Commit Convention

We use [Conventional Commits](https://www.conventionalcommits.org/) to automate versioning and changelog generation. Your commit messages determine the next version number:

| Commit prefix | Version bump | Example |
|---|---|---|
| `fix:` | Patch (0.1.0 -> 0.1.1) | `fix: handle empty project in graph extraction` |
| `feat:` | Minor (0.1.0 -> 0.2.0) | `feat: add support for namespace packages` |
| `feat!:` or `BREAKING CHANGE:` in footer | Major (0.1.0 -> 1.0.0) | `feat!: remove deprecated API` |

Other prefixes like `chore:`, `docs:`, `refactor:`, `test:`, `ci:` do **not** trigger a release.

## Releases

Releases are automated. When a PR is merged to `main`:

1. CI runs lint + tests
2. If CI passes, the version is bumped based on commit messages
3. Published to PyPI
4. GitHub release created

## Issues

Bugs: Include environment, expected/actual behavior, steps, errors
Features: Check existing issues, provide use case

## Code of Conduct

Be respectful and inclusive.
Happy coding!
