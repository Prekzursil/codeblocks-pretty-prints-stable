# Third-Party Notices

This repository’s own docs, templates, workflow metadata, and release policy are covered by the repository license in `LICENSE`.

Any redistributed installer payloads or bundled binaries are **not** relicensed by this repository. They keep their own upstream licenses and notices, which must be harvested into the release assets and preserved alongside the installer.

## Notice policy

Every public binary release must include:

- a release manifest
- checksum files
- a notice bundle copied from the fetched upstream payloads
- any license text required by bundled runtime components

## Known component families that the release pipeline must account for

The current baseline package family includes the upstream Code::Blocks IDE and the bundled toolchain/runtime stack. The exact upstream source and license texts are expected to be pinned and harvested during the fetch-and-package release stage.

The local inventory used to seed this repository already shows the following component families that need notice handling:

| Component family | Typical notice handling |
| --- | --- |
| Code::Blocks IDE | Preserve upstream license/redistribution notices from the fetched payload |
| MinGW-w64 GCC/G++ | Preserve the GCC / MinGW-w64 license and any bundled runtime notices |
| Binutils / linker tools | Preserve the matching GPL/LGPL notices from the fetched toolchain payload |
| GDB | Preserve GDB license notices and debugger helper notices |
| libstdc++ pretty-printer scripts | Preserve the script headers and upstream license text |
| Python runtime | Preserve the Python Software Foundation license text |
| Bundled docs and helper scripts | Preserve any redistributable notices that ship with the payload |

## Release asset expectation

The release artifact should contain a dedicated notices directory or archive so that anyone installing the edition can inspect the upstream redistribution terms without needing to search through the release notes.

## Important boundary

This file is intentionally a policy and inventory document. It does not claim to be the full upstream legal notice bundle. The canonical notice set for a given release is the one harvested from the pinned fetched payloads at release time.
