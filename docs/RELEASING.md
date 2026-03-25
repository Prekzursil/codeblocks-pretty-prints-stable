# Releasing Code::Blocks Stable Toolchain Edition

This project’s public release process mirrors the **known-good local Code::Blocks installation**
that already has the debugger, pretty-printers, and watch-window behavior working correctly.

## v0.1.0 baseline

- release tag: `v0.1.0`
- baseline payload source: local install at `C:\Program Files\CodeBlocks`
- machine-wide install target: `C:\Program Files\CodeBlocks Stable Toolchain Edition`
- managed profile seed source: `overlay/profile-seed`
- installer signing: **unsigned**

## Build a local mirror release

Run this from the repository root in PowerShell:

```powershell
.\packaging\scripts\Build-LocalMirrorRelease.ps1 `
  -RepositoryRoot . `
  -Version 0.1.0 `
  -SourceInstallRoot "C:\Program Files\CodeBlocks" `
  -InstallInnoSetupIfMissing
```

This stages:

- `dist\payload\CodeBlocks\`
- `dist\release-assets\`
- `dist\installer\codeblocks-pretty-prints-stable-0.1.0-setup.exe`
- `dist\publish\` (installer + manifest + checksums + SBOM + provenance + release notes)

## Publish the GitHub release

Once `main` is green and you are ready to publish:

```powershell
.\packaging\scripts\Build-LocalMirrorRelease.ps1 `
  -RepositoryRoot . `
  -Version 0.1.0 `
  -SourceInstallRoot "C:\Program Files\CodeBlocks" `
  -InstallInnoSetupIfMissing `
  -CreateGitHubRelease
```

That flow creates/pushes tag `v0.1.0` if needed and uploads the staged files to a GitHub Release.

## Required checks before publishing

- `bash scripts/verify`
- `Quality Zero Platform`
- `Quality Zero Gate`
- `Codecov Analytics`
- `SonarCloud Code Analysis`
- provider truth clean enough for:
  - Codacy
  - SonarCloud
  - DeepScan
  - Semgrep
  - Sentry

## Conservative cleanup after release

After the release is published:

- cancel stale queued remediation/backlog runs
- leave completed historical workflow runs intact
- keep the repo on `main` clean and synced
