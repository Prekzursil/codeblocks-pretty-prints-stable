# AGENTS.md

## Repository role

`codeblocks-pretty-prints-stable` is the public packaging and governance repo for **Code::Blocks Stable Toolchain Edition**.

This repo owns:

- root product docs
- release-policy metadata
- notice-harvesting policy
- GitHub governance files
- workflow wiring for repo sanity and release validation

## Scope guidance for future agents

- Keep edits within the repo’s root docs/config files or `.github/` unless a later task explicitly expands scope.
- Do not blur the line between repository policy and installer payload logic.
- Do not silently change release ownership or cleanup policy.
- Treat security, notices, and release metadata as first-class artifacts.

## Verification guidance

Before claiming this repo is ready, verify:

- the README matches the current product contract
- SECURITY / CONTRIBUTING / SUPPORT are aligned
- `release-manifest.json` parses cleanly
- `.github` templates and workflows are present and coherent

## Working style

- Prefer additive changes.
- Keep release policy explicit.
- Avoid placeholders in user-facing docs.
- If a future task needs implementation outside this scope, coordinate before touching it.
