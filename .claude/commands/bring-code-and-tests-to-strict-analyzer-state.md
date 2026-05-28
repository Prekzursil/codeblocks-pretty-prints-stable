---
name: bring-code-and-tests-to-strict-analyzer-state
description: Workflow command scaffold for bring-code-and-tests-to-strict-analyzer-state in codeblocks-pretty-prints-stable.
allowed_tools: ["Bash", "Read", "Write", "Grep", "Glob"]
---

# /bring-code-and-tests-to-strict-analyzer-state

Use this workflow when working on **bring-code-and-tests-to-strict-analyzer-state** in `codeblocks-pretty-prints-stable`.

## Goal

Brings both code and test suites into compliance with strict static analysis and linting requirements (e.g., docstrings, line length, mypy, pylint, flake8).

## Common Files

- `scripts/*.py`
- `scripts/quality/*.py`
- `tests/*.py`
- `tests/__init__.py`
- `.pylintrc`
- `setup.cfg`

## Suggested Sequence

1. Understand the current state and failure mode before editing.
2. Make the smallest coherent change that satisfies the workflow goal.
3. Run the most relevant verification for touched files.
4. Summarize what changed and what still needs review.

## Typical Commit Signals

- Add or update docstrings for modules, functions, and classes in both source and test files.
- Wrap lines to the configured line length limit (e.g., 100 chars).
- Fix type annotations and mypy errors (e.g., Optionals, imports).
- Update or add linter configurations (e.g., .pylintrc, setup.cfg, flake8 config).
- Refactor code to comply with linter rules (e.g., argument/local limits, import resolution).

## Notes

- Treat this as a scaffold, not a hard-coded script.
- Update the command if the workflow evolves materially.