# Code::Blocks Pretty Prints Stable

`codeblocks-pretty-prints-stable` is the public control-plane repository for **Code::Blocks Stable Toolchain Edition**: a curated, machine-wide Windows distribution of Code::Blocks that ships a pinned bundled MinGW/GDB stack, preserves the useful local settings already in the field, and installs with safe ownership boundaries.

This repository is intentionally a **fetch-and-package** project:

- it keeps the upstream IDE payload and bundled toolchain **out of git history**
- it stores the release metadata, manifests, docs, notices, and installer/governance wiring
- it produces a curated Windows installer that points Code::Blocks at the right compiler, linker, debugger, and pretty-printer chain by **absolute path**

## What this project is

- A public repo for the **Code::Blocks Stable Toolchain Edition** release pipeline
- A machine-wide Windows installer story with:
  - managed fresh profile seeding
  - backup-first migration
  - optional replacement of the current official Code::Blocks install after confirmation
  - pinned bundled MinGW/GDB defaults
  - reproducible release artifacts
- A place to keep release metadata, notices, issue templates, and required GitHub governance files

## What this project is not

- Not a deep fork of Code::Blocks source
- Not a generic system-wide MinGW manager
- Not an unconditional delete-all-old-toolchains installer
- Not a portable ZIP-first product

## Core promises

1. **Same app feel, better defaults**  
   The UI stays basically Code::Blocks; the package only changes the parts that matter for reliability.

2. **Pinned toolchain resolution**  
   Compiler, linker, debugger, and pretty-printer paths are set explicitly inside the edition install root.

3. **Managed profile seeding**  
   We preserve known-good user settings intentionally, rather than merging arbitrary drift into a live profile.

4. **Safe cleanup boundaries**  
   We replace or remove our own edition footprint and the confirmed official Code::Blocks install only after confirmation. Unrelated toolchains remain untouched unless a future advanced cleanup flow explicitly opts in.

5. **Release truth is evidence-backed**  
   Release artifacts are gated on manifest/hash/notice validation, and the repo is designed to support the strict-zero workflow stack used elsewhere in the user’s control-plane repos.

## Repository layout

This repo is intentionally small at the source level:

- `README.md` — project overview and user-facing contract
- `AGENTS.md` — repo-local operating guidance for future Codex runs
- `SECURITY.md` — vulnerability reporting policy
- `CONTRIBUTING.md` — change and review expectations
- `SUPPORT.md` — supported platforms and support boundaries
- `LICENSE` — license for repo-authored material
- `THIRD_PARTY_NOTICES.md` — notice-harvesting and redistribution policy
- `release-manifest.json` — curated baseline metadata for the packaged edition
- `.github/` — GitHub governance, templates, and workflows

## Release model

The release pipeline is expected to:

1. fetch pinned upstream payloads
2. verify hashes
3. harvest and bundle notices
4. apply the curated overlay
5. build the Windows installer
6. publish checksums, SBOM, and provenance/attestation artifacts

Public binary releases are gated. The repository itself may be public immediately, but release artifacts should not be published until the release workflow and verification checks are complete.

## Supported baseline

- Windows 10/11 x64 hosts
- Machine-wide installs only
- Both 32-bit and 64-bit **target** builds on x64 hosts
- Bundled MinGW/GDB defaults only; no PATH dependency

## Verification

Until the implementation files arrive, the authoritative checks for this repo are:

- root docs and manifests are present and internally consistent
- GitHub templates and workflows exist and parse cleanly
- the release manifest matches the named edition and policy
- notice handling is explicit and separate from the repository license

## Support and feedback

For supported issues, use the issue templates in `.github/`.

For security-sensitive issues, use the process described in `SECURITY.md` instead of opening a public issue.
