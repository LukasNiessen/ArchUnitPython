---
name: Feature Request
about: Suggest an idea for ArchUnitPython
title: '[FEATURE] '
labels: ['enhancement']
assignees: []
---

# Feature Request

Describe the feature you'd like to see added.

## Problem

What problem does this solve? Is your feature request related to a problem?

## Proposed Solution

How would this feature work? What would the API look like?

```python
# Example usage
from archunitpython import project_files

rule = project_files("src/").in_folder("src").should().your_new_feature()
assert_passes(rule)
```

## Use Case

How would you use this feature in your project?

## Alternatives Considered

Describe alternatives you've considered.

## Impact Assessment

What areas would this affect?

- [ ] Core architecture testing
- [ ] File dependencies
- [ ] Metrics calculation
- [ ] Slice testing
- [ ] Error messages
- [ ] Test framework integration
- [ ] Performance
- [ ] Documentation

## Checklist

- [ ] I have searched existing issues to make sure this isn't a duplicate
- [ ] I have provided a clear use case
- [ ] I have considered the API design
- [ ] I have thought about backward compatibility
