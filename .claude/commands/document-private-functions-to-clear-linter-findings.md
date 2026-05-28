---
name: document-private-functions-to-clear-linter-findings
description: Workflow command scaffold for document-private-functions-to-clear-linter-findings in codeblocks-pretty-prints-stable.
allowed_tools: ["Bash", "Read", "Write", "Grep", "Glob"]
---

# /document-private-functions-to-clear-linter-findings

Use this workflow when working on **document-private-functions-to-clear-linter-findings** in `codeblocks-pretty-prints-stable`.

## Goal

Adds docstrings to private or internal functions to satisfy linter or code quality tool requirements.

## Common Files

- `scripts/quality/*.py`

## Suggested Sequence

1. Understand the current state and failure mode before editing.
2. Make the smallest coherent change that satisfies the workflow goal.
3. Run the most relevant verification for touched files.
4. Summarize what changed and what still needs review.

## Typical Commit Signals

- Identify private/internal functions lacking docstrings as flagged by linter.
- Add appropriate docstrings to these functions.
- Verify that the linter/code quality tool findings are cleared.

## Notes

- Treat this as a scaffold, not a hard-coded script.
- Update the command if the workflow evolves materially.