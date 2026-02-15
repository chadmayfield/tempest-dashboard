---
name: test
description: Run the project test suite and report results.
argument-hint: [test-pattern]
allowed-tools: Bash(python3* -m pytest *)
---

# Run Tests

Run the test suite and report results.

## Steps

1. Run pytest with verbose output from the project root
2. If arguments are provided (e.g. `/test tests/test_browser.py` or `/test -k unit_toggle`), pass them through
3. Report pass/fail counts and any failures

## Command

```bash
python3 -m pytest tests/ -v $ARGUMENTS
```

If `$ARGUMENTS` specifies a path or `-k` filter, use that instead of the default `tests/`.
