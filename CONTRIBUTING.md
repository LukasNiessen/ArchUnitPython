# Contributing

Thanks for contributing!

## Setup

- Fork & clone: `git clone https://github.com/LukasNiessen/ArchUnitPy.git`
- Install: `pip install -e ".[dev]"`
- Test: `pytest`
- Lint: `ruff check src/`
- Type check: `mypy src/archunitpy/`

## Guidelines

- Code Style: Run `ruff check` and `ruff format` before committing
- Commits: Use [Conventional Commits](https://www.conventionalcommits.org/) (see below)
- PRs: Use feature branches, clear descriptions, ensure CI passes
- Tests: Maintain high coverage

## Commit Convention

We use [Conventional Commits](https://www.conventionalcommits.org/) to automate versioning and changelog generation via [semantic-release](https://github.com/semantic-release/semantic-release). Your commit messages determine the next version number:

| Commit prefix | Version bump | Example |
|---|---|---|
| `fix:` | Patch (0.1.0 -> 0.1.1) | `fix: handle empty project in graph extraction` |
| `feat:` | Minor (0.1.0 -> 0.2.0) | `feat: add support for namespace packages` |
| `feat!:` or `BREAKING CHANGE:` in footer | Major (0.1.0 -> 1.0.0) | `feat!: remove deprecated API` |

Other prefixes like `chore:`, `docs:`, `refactor:`, `test:`, `ci:` do **not** trigger a release.

## Releases

Releases are fully automated. When a PR is merged to `main`:

1. CI runs lint + type checking + tests (across Python 3.10-3.13)
2. If CI passes, [semantic-release](https://github.com/semantic-release/semantic-release) analyzes commit messages since the last release
3. If there are `fix:` or `feat:` commits, it automatically:
   - Bumps the version in `pyproject.toml`
   - Updates `CHANGELOG.md`
   - Publishes to PyPI
   - Creates a GitHub release with release notes

No manual version bumping or publishing is needed.

## Documentation

Documentation is automatically generated from Python docstrings using [pdoc](https://pdoc.dev/) and deployed to GitHub Pages.

### Local Development

```bash
# Install pdoc
pip install pdoc

# Generate docs
pdoc src/archunitpy/ -o docs/

# Serve locally with live reload
pdoc src/archunitpy/
```

### Writing Good Documentation

- Add docstrings to all public APIs
- Use Google-style docstring format
- Include code examples in docstrings where helpful
- Keep docstrings concise but informative

### Documentation Deployment

- Documentation is automatically deployed to [GitHub Pages](https://lukasniessen.github.io/ArchUnitPy/) on push to `main`
- Configuration is in `.github/workflows/docs.yaml`

## Issues

Bugs: Include environment, expected/actual behavior, steps, errors
Features: Check existing issues, provide use case

## Code of Conduct

Be respectful and inclusive.
Happy coding!
