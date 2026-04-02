# TODOs

This is our _"backlog"_. Contributions are highly welcome.

- Add an `.archignore` or similar a la `.gitignore` for files that should never be considered by our tests
- Auto generate an architecture documentation based on the tests
- Add a `.because(...)` function a la ArchUnit. Should be used for the error message in case of a failing test as well as for auto-generated arch docs
- Add support for namespace packages (packages without `__init__.py`)
- Detect dynamic imports (`importlib.import_module()`, `__import__()`)
- Detect conditional imports (`try/except ImportError`)
- Add `TYPE_CHECKING` import handling (currently detected but could be filtered separately)
- Make logged paths clickable in IDEs (currently works in some terminals)
- Improve performance for very large projects (parallel file parsing)
- Add comprehensive HTML report with charts and zone visualization
- Add more LCOM edge case handling
- Add support for monorepo / multi-package Python projects
- Publish to PyPI
- Add Sphinx/MkDocs documentation site
