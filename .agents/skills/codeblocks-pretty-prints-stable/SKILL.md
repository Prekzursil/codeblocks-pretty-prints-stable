```markdown
# codeblocks-pretty-prints-stable Development Patterns

> Auto-generated skill from repository analysis

## Overview
This skill teaches you the development patterns and conventions used in the `codeblocks-pretty-prints-stable` Python codebase. You'll learn how to structure files, write imports and exports, follow commit message conventions, and organize your code for clarity and maintainability. This guide also covers how to write and organize tests, even if the framework is not explicitly defined.

## Coding Conventions

### File Naming
- Use **snake_case** for all file names.
  - Example: `pretty_printer.py`, `utils/helpers.py`

### Import Style
- Use **relative imports** within the package.
  - Example:
    ```python
    from .utils import format_block
    from ..core import Block
    ```

### Export Style
- Use **named exports** (explicitly define what is exported).
  - Example:
    ```python
    __all__ = ['PrettyPrinter', 'format_block']
    ```

### Commit Messages
- Follow the **Conventional Commits** format.
- Allowed prefixes: `fix`, `test`, `chore`
- Example:
  ```
  fix: handle edge case in block formatting
  test: add tests for nested block rendering
  chore: update dependencies
  ```

## Workflows

### Fixing a Bug
**Trigger:** When you need to resolve a bug in the codebase  
**Command:** `/fix-bug`

1. Identify the bug and create a new branch.
2. Make code changes following the coding conventions.
3. Write a commit message with the `fix:` prefix.
4. Run tests to ensure the bug is resolved.
5. Submit a pull request for review.

### Adding or Updating Tests
**Trigger:** When adding new features or fixing bugs  
**Command:** `/add-test`

1. Create or update test files using the `*.test.ts` pattern.
2. Write tests covering the new or changed functionality.
3. Run the test suite to verify correctness.
4. Commit with the `test:` prefix.
5. Submit for review.

### Maintenance or Chores
**Trigger:** When performing non-functional updates (e.g., dependency updates, code formatting)  
**Command:** `/chore`

1. Make the necessary maintenance changes.
2. Commit with the `chore:` prefix.
3. Ensure all tests pass.
4. Submit for review.

## Testing Patterns

- Test files follow the `*.test.ts` naming convention.
  - Example: `pretty_printer.test.ts`
- The specific test framework is not defined, but tests should be organized in these files.
- Write tests that cover both typical and edge-case scenarios.

## Commands
| Command     | Purpose                                      |
|-------------|----------------------------------------------|
| /fix-bug    | Start the workflow to fix a bug              |
| /add-test   | Add or update tests for new/existing code    |
| /chore      | Perform maintenance or non-functional changes |
```
