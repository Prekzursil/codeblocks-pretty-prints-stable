#!/usr/bin/env bash
# Charter <-> active-gate consistency check (lean 6-gate charter, 2026-06-16).
# Invoked by the lean template charter-check step when .quality/charter.yml is
# present. Fails (non-zero) if any gate config artifact is missing, i.e. the
# active gate set has drifted from the declared closed set.
set -euo pipefail

fail=0
require() {
  # require <path> <gate-description>
  if [ ! -e "$1" ]; then
    echo "charter-check: MISSING $1 (gate: $2)" >&2
    fail=1
  else
    echo "charter-check: ok  $1 (gate: $2)"
  fi
}

require ".quality/charter.yml"          "charter declaration"
require ".pre-commit-config.yaml"       "gate 1 lint/format/imports/sec-lint + gate 5 secrets autofix lane"
require ".coveragerc"                   "gate 3 tests + 100% coverage"
require ".quality/opengrep"             "gate 4 SAST (opengrep ruleset)"
require ".gitleaks.toml"                "gate 5 secrets"
require "osv-scanner.toml"              "gate 6 deps (osv-scanner)"
require ".github/dependabot.yml"        "gate 6 deps (Dependabot)"

if [ "$fail" -ne 0 ]; then
  echo "charter-check: FAILED - active gate set drifted from the lean 6-gate charter." >&2
  exit 1
fi
echo "charter-check: PASS - all 6 lean gates have their config present."
