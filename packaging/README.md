# Packaging: Code::Blocks Stable Toolchain Edition

This directory owns the Windows packaging layer for the curated
**Code::Blocks Stable Toolchain Edition** distribution.

The repo is intentionally organized as a **fetch-and-package** control plane:

- upstream payloads are fetched from pinned URLs
- hashes and manifests are validated before release
- curated profile/overlay output is applied on top of the payload
- a machine-wide Inno Setup installer is produced from the staged assets
- public releases are gated by verification and notice completeness

## Expected inputs from other repo lanes

This packaging layer expects other tasks/layers to provide build output in
the following logical locations:

- `manifests/` — pinned release manifest, payload hashes, notice map
- `overlay/` — profile seed, text replacement map, and any profile patches
- `dist/` or `artifacts/` — staged payloads and final release assets

The exact filenames are intentionally conservative and easy to adjust.

## Packaging outputs

The installer workflow should ultimately produce:

- the Inno Setup `.exe`
- checksums
- a release manifest
- an SBOM
- `THIRD_PARTY_NOTICES` material
- provenance / attestation artifacts

## Files in this directory

- `CodeBlocksStableToolchainEdition.iss` — the machine-wide installer
- `scripts/` — helper scripts used by the installer and release staging
- `templates/` — placeholders for release manifests, notices, and profile seed structure


