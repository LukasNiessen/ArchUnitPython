# ArchUnitPy

Architecture testing library for Python projects. Inspired by [ArchUnitTS](https://github.com/LukasNiessen/ArchUnitTS).

## Installation

```bash
pip install archunitpy
```

## Quick Start

```python
from archunitpy import project_files, project_slices, metrics, assert_passes

# No circular dependencies
rule = project_files("src/").in_folder("myapp/**").should().have_no_cycles()
assert_passes(rule)

# Layer dependencies
rule = (
    project_files("src/")
    .in_folder("**/presentation/**")
    .should_not()
    .depend_on_files()
    .in_folder("**/data/**")
)
assert_passes(rule)

# Metrics
rule = metrics("src/").count().lines_of_code().should_be_below(500)
assert_passes(rule)
```

## License

MIT
