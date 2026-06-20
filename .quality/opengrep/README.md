# Curated SAST ruleset (Gate 4)

Pinned tool: **opengrep 1.22.0** (CI) — locally interchangeable with **semgrep CE**
(opengrep is a fork of semgrep and consumes the same rule syntax).

## Why an in-repo ruleset instead of `--config auto`

`--config auto` / `p/*` registry packs are fetched from the network at scan time and
change underneath you, which makes the gate **non-deterministic**. The lean model
requires a fixed, reviewable ruleset committed to the repo, so the gate produces the
same result every run, offline, with no registry login.

## Contents

This is a **curated subset** distilled from the relevant upstream packs
(`p/python`, `p/javascript`, `p/r2c-security-audit`) — the high-signal security rules
that apply to this Python-tooling + small JS (`.cjs`) codebase:

- `python-security.yaml` — Python injection / unsafe-deserialization / unsafe-subprocess /
  weak-crypto / insecure-TLS patterns.
- `javascript-security.yaml` — JS/TS XSS / `eval` / unsafe DOM sink / child_process /
  insecure-randomness patterns.
- `general-security.yaml` — language-agnostic patterns (private keys / cloud keys in code).

Upstream registry rules are Apache-2.0 / LGPL-2.1 licensed; rule logic is reproduced /
adapted here. To refresh against upstream, diff the registry packs and port new
high-signal rules in (one-in-one-out review).

## Running the gate

```bash
# CI (opengrep on Linux):
opengrep scan --config .quality/opengrep --error \
  --exclude node_modules --exclude dist --exclude build --exclude out .

# Local (semgrep CE, rule-compatible):
semgrep scan --config .quality/opengrep --error --metrics off \
  --exclude node_modules --exclude dist --exclude build --exclude out .
```

Gate passes on **0 findings** (clean-zero lock; no baseline file). Genuine
false-positives are suppressed inline with a greppable `# nosemgrep: <rule-id> -- <reason>`.
