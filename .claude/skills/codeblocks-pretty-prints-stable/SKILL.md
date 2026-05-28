```markdown
# codeblocks-pretty-prints-stable Development Patterns

> Auto-generated skill from repository analysis

## Overview

This skill teaches you the core development patterns, coding conventions, and maintenance workflows used in the `codeblocks-pretty-prints-stable` Python codebase. The repository focuses on robust code quality, strict static analysis, and clear CLI logic, with a strong emphasis on maintainability and testability. You'll learn how to write code and tests that pass strict linting, structure files and imports, and follow the team's documented workflows for code quality and refactoring.

## Coding Conventions

- **File Naming:**  
  Use `snake_case` for all Python files and modules.
  ```
  scripts/quality/check_formatting.py
  tests/test_codeblocks_cli.py
  ```

- **Import Style:**  
  Prefer **relative imports** within packages.
  ```python
  from .utils import shared_helper
  ```

- **Export Style:**  
  Use **named exports** (explicitly define what is exported).
  ```python
  __all__ = ["main", "helper_function"]
  ```

- **Commit Messages:**  
  Follow **conventional commit** prefixes:  
  `fix:`, `test:`, `chore:`, `docs:`, `refactor:`
  ```
  fix: handle edge case in pretty print formatter
  ```

- **Docstrings:**  
  All modules, classes, functions (including private/internal) must have docstrings.
  ```python
  def _parse_args(args):
      """Parse CLI arguments for internal use."""
      ...
  ```

- **Line Length:**  
  Wrap lines to the configured limit (typically 100 chars).

## Workflows

### bring-code-and-tests-to-strict-analyzer-state
**Trigger:** When you want to ensure the codebase and tests pass all static analysis and linting checks at the strictest level.  
**Command:** `/strict-analyzer-upgrade`

1. Add or update docstrings for all modules, functions, and classes (including tests).
2. Wrap lines to the configured line length (e.g., 100 chars).
3. Fix type annotations and resolve mypy errors.
   ```python
   from typing import Optional

   def pretty_print(text: str, style: Optional[str] = None) -> str:
       """Format text with optional style."""
       ...
   ```
4. Update or add linter configurations (`.pylintrc`, `setup.cfg`, `flake8`).
5. Refactor code to comply with linter rules (e.g., argument/local limits, import resolution).
6. Make the `tests` directory a package if needed (add `__init__.py`).
7. Extract or refactor shared fixtures/utilities in tests for reuse.

### document-private-functions-to-clear-linter-findings
**Trigger:** When you need to clear missing-docstring findings for private/internal functions flagged by static analysis tools.  
**Command:** `/document-private-functions`

1. Identify private/internal functions lacking docstrings (as flagged by linter).
2. Add appropriate docstrings to these functions.
   ```python
   def _internal_helper():
       """Internal helper for formatting blocks."""
       ...
   ```
3. Verify that the linter/code quality tool findings are cleared.

### refactor-shared-cli-dispatch-and-add-tests
**Trigger:** When you want to eliminate code duplication in CLI entrypoints and ensure the new shared logic is fully tested.  
**Command:** `/refactor-shared-cli`

1. Identify duplicated CLI parsing/dispatch code in multiple scripts.
2. Extract shared logic into a common/shared module.
   ```python
   # scripts/codeblocks_shared.py
   def parse_cli_args(argv):
       """Parse CLI arguments for all codeblocks scripts."""
       ...
   ```
3. Update original scripts to use the shared helper.
   ```python
   from .codeblocks_shared import parse_cli_args
   ```
4. Add or update unit tests to cover the shared helper, including edge cases.
   ```python
   def test_parse_cli_args_handles_invalid_input():
       ...
   ```

## Testing Patterns

- **Test File Naming:**  
  Test files use `test_*.py` naming convention and are placed in the `tests/` directory.
  ```
  tests/test_codeblocks_cli.py
  ```

- **Test Framework:**  
  The specific framework is not detected, but tests follow standard Python test patterns.

- **Test Structure:**  
  - Each test function should have a descriptive name.
  - Use fixtures/utilities for shared test setup.
  - Make the `tests` directory a package (include `__init__.py` if needed).

  ```python
  def test_pretty_print_applies_style():
      assert pretty_print("hello", style="bold") == "<b>hello</b>"
  ```

## Commands

| Command                     | Purpose                                                                 |
|-----------------------------|-------------------------------------------------------------------------|
| /strict-analyzer-upgrade    | Bring code and tests into strict analyzer/linter compliance              |
| /document-private-functions | Add docstrings to private/internal functions to clear linter findings    |
| /refactor-shared-cli        | Refactor shared CLI logic and add/update tests for shared code           |
```
