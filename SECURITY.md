# Security Policy

## Supported versions

This repository governs the **Code::Blocks Stable Toolchain Edition** release line for the current public packaging baseline.

## Reporting a vulnerability

Please **do not** open a public issue for:

- secrets or credentials accidentally exposed in the repo or release artifacts
- a packaging flow that could disclose private paths, tokens, or machine data
- a release artifact integrity problem
- any issue that could impact redistribution notices or the trusted release chain

Use GitHub’s private vulnerability reporting flow for this repository whenever possible.

If GitHub private reporting is unavailable, contact the repository owner privately through GitHub rather than posting the report publicly.

## What counts as security-sensitive here

Examples include:

- leaked tokens in workflow files or release metadata
- release scripts that could publish unverified payloads
- notice-generation bugs that could mislabel a redistributed component
- installer cleanup logic that could delete unrelated third-party toolchains
- tampering with checksums, manifests, or provenance artifacts

## What we will do

When a security report is received, we will:

1. acknowledge receipt privately
2. reproduce the issue on a controlled branch
3. patch the problem in the release/control-plane layer
4. verify the fix with evidence before release

## Safe reporting details

Include:

- the affected file or release artifact
- the exact version or commit if known
- the observed impact
- whether the issue is in docs, installer logic, manifests, or GitHub workflow wiring

Avoid sending secrets, customer identifiers, or private credentials in the initial report. If such data is involved, redact it before sending.
