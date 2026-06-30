# CI / Merge Automation (3-tier)

This repo runs a 3-tier automation stack to stay 0-GREEN with minimal manual work.

## Tier 1 - Dependabot auto-merge (free, native)
`.github/workflows/dependabot-auto-merge.yml` enables GitHub native auto-merge
(`gh pr merge --auto --squash`) on every Dependabot PR. The PR only merges once
**all required status checks pass** (branch protection requires `codeql / CodeQL`
and `quality / quality`). The repo setting **Allow auto-merge** is enabled.
No check is ever bypassed; a red Dependabot PR simply waits / is resolved.

## Tier 2 - GitHub Models autofix (free, in-Actions) - PRIMARY auto-fix
`.github/workflows/autofix-models.yml` fires only when **default-branch CI fails**
(`workflow_run` conclusion `failure` for `quality` or `CodeQL`). It feeds the
trailing failing logs to the free GitHub Models inference action
(`openai/gpt-4o-mini`) and opens a **draft, `autofix`-labelled** PR with a
suggested real fix. This PR is **never auto-merged** - normal CI + branch
protection + human review gate it. Bounded: failure-only, single PR per run.

## Tier 3 - Copilot coding agent (student sub - JUDICIOUS escalation)
Premium Copilot requests are finite, so this is **manual escalation only** and is
**not** wired to fire on every failure. Escalate **only when the free Tier-2
Models autofix cannot resolve a stuck failing check**:

1. Open (or reuse) a GitHub Issue describing the stuck failing check, linking the
   failing run and the unsuccessful Tier-2 `autofix` PR.
2. Assign the issue to **@copilot** to have the Copilot coding agent attempt a fix.
3. Review the resulting Copilot PR like any other - CI + branch protection gate it;
   never auto-merge a non-Dependabot fix.

Do **not** assign issues to @copilot reflexively - reserve it for genuinely stuck
cases the free lane could not handle.
