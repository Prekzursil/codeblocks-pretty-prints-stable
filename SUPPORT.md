# Support

## Supported baseline

This edition is designed for:

- Windows 10 x64
- Windows 11 x64
- machine-wide installs only
- 32-bit and 64-bit **target** builds from an x64 host

## Supported product shape

The supported distribution is:

- **Code::Blocks Stable Toolchain Edition**
- packaged via the fetch-and-package control plane
- installed to an edition-owned path
- configured to use the bundled MinGW/GDB stack

## What we support

- installer and upgrade issues for this edition
- managed profile seeding and migration behavior
- bundled compiler/debugger selection
- pretty-printing configuration for the bundled GDB setup
- release-manifest / notice-policy questions

## What we do not support

- generic upstream Code::Blocks installation support
- arbitrary third-party MinGW/MSYS2/WinLibs toolchain mixes
- unsupported host architectures
- manual PATH-based compiler selection troubleshooting for unrelated shells
- deleting unrelated toolchains outside the edition’s ownership boundary

## What to include in a support request

Please include:

- your Windows version
- the edition version or release tag
- whether this is a fresh install or an upgrade
- the install path
- any installer log output
- the relevant release-manifest version if you have it
- whether the issue is compile, link, debug, or profile migration related

## Best first check

If Code::Blocks appears to be using the wrong compiler or debugger, confirm:

1. the edition install completed successfully
2. the bundled toolchain path is the one selected in the profile
3. the old official install was removed or deprioritized as expected
4. you are launching the edition-owned shortcut, not the old upstream shortcut
