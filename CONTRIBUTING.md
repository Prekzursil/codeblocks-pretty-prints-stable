# Contributing

Thanks for helping improve **Code::Blocks Stable Toolchain Edition**.

This repository is a **packaging and governance** repo. Most changes should stay within:

- root docs and metadata
- `.github/`
- release manifests and notice policy

If you think a change belongs in the installer payload or Code::Blocks itself, write that up clearly before editing so the scope stays clean.

## How to contribute

1. Create a branch.
2. Make a narrowly scoped change.
3. Keep docs, manifests, and workflows in sync.
4. Verify the repo shape before asking for review.
5. Open a pull request with a clear summary of:
   - what changed
   - what files are affected
   - whether the change affects release artifacts, notices, or installer behavior

## What we expect in a PR

- A short summary of the intent
- The exact files changed
- Any security, release, or notice impact
- Verification evidence when relevant

## Required hygiene

- Do not commit secrets, tokens, passwords, or private customer data.
- Do not add unrelated toolchain deletions or cleanup behavior without an explicit policy update.
- Keep release and notice metadata explicit; do not bury important redistribution details in comments only.

## Review expectations

Please prefer:

- additive changes over disruptive rewrites
- explicit file ownership over broad “fix everything” edits
- release-manifest updates when policy or packaging behavior changes

## Verification

For this repo, verification means confirming:

- the root docs still describe the current product contract
- `.github` templates and workflows parse cleanly
- the release manifest and notice policy stay consistent

If a change affects installer behavior later, it will need additional package/build verification in the implementation repo or workflow.
