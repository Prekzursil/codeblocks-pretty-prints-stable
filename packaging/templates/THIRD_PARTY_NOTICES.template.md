# Third-Party Notices

This curated distribution bundles upstream and third-party components that
retain their own licenses and notices.

## Product layer

- Code::Blocks installer/packaging logic authored in this repository
- release manifests and helper scripts authored in this repository

## Bundled component families expected by the installer

- Code::Blocks IDE binaries and documentation
- MinGW-w64 GCC/G++/binutils/GDB payload
- libstdc++ pretty-printer support
- Python runtime/support files included in the bundled toolchain
- any other payloads declared in the pinned release manifest

## Notice preservation rules

- Preserve upstream license texts for every bundled component family
- Keep release hashes and manifests next to the installer artifact
- Do not imply that upstream binaries were relicensed by this repository
- Prefer manifest-driven notice harvesting over handwritten guesses

## Placeholder sections for release-time fill

- Upstream Code::Blocks notices
- MinGW-w64 / GCC / binutils / GDB notices
- Python runtime notices
- any additional notices listed in the release manifest


