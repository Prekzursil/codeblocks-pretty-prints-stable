from __future__ import annotations

import argparse
import json
import shutil
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any

from scripts.codeblocks_notices import collect_notice_inventory
from scripts.codeblocks_shared import load_json_document
from scripts.codeblocks_validation import load_manifest

DEV_ONLY_GDB_SOURCE = r"source C:\Devel\CodeBlocks\share\codeblocks/scripts/stl-views-1.0.3.gdb"
PATCHED_GDB_COMMENT = "# dev-only stl-views source removed; managed pretty-printers are configured in the seeded profile"
PATCHED_GDB_PATH = Path("share") / "CodeBlocks" / "scripts" / "gdb_init.gdb"
LOCAL_PAYLOAD_KIND = "local-known-good-install"


def sanitize_gdb_init(text: str) -> str:
    lines = []
    replaced = False
    for raw_line in text.splitlines():
        if raw_line.strip() == DEV_ONLY_GDB_SOURCE:
            lines.append(PATCHED_GDB_COMMENT)
            replaced = True
            continue
        lines.append(raw_line)
    if not replaced:
        return text
    return "\n".join(lines) + "\n"


def patch_staged_gdb_init(payload_root: str | Path) -> bool:
    gdb_init_path = Path(payload_root) / PATCHED_GDB_PATH
    if not gdb_init_path.is_file():
        return False
    original = gdb_init_path.read_text(encoding="utf-8")
    patched = sanitize_gdb_init(original)
    if patched == original:
        return False
    gdb_init_path.write_text(patched, encoding="utf-8")
    return True


def file_sha256(path: str | Path) -> str:
    digest = sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def render_release_notes(version: str, manifest: Mapping[str, Any]) -> str:
    toolchain = manifest["bundled_toolchain"]
    return (
        f"# Code::Blocks Stable Toolchain Edition {version}\n\n"
        "## What this release is\n\n"
        "This release mirrors the known-good local Code::Blocks setup that was already working properly, "
        "including the managed debugger and pretty-printer defaults needed for useful watch-window debugging.\n\n"
        "## Baseline\n\n"
        f"- Code::Blocks: {manifest['product_name']} {manifest['schema_version'] and '25.03'}\n"
        f"- GCC/G++: {toolchain['gcc_version']}\n"
        f"- GDB: {toolchain['gdb_version']}\n"
        f"- Host support: {manifest['host_architecture']} Windows 10/11\n"
        f"- Target builds: {', '.join(manifest['target_architectures'])}\n\n"
        "## Included behavior\n\n"
        "- Managed profile seeding from the known-good local baseline\n"
        "- Pinned bundled MinGW/GDB paths by absolute path\n"
        "- Pretty-printer init commands for libstdc++ STL watch rendering\n"
        "- Safe backup-first migration and bounded cleanup behavior\n\n"
        "## Notes\n\n"
        "- This first public release is unsigned.\n"
        "- The installer is intended to be plug-and-play on other Windows x64 machines.\n"
    )


def build_release_manifest(
    *,
    version: str,
    payload_manifest: Mapping[str, Any],
    source_install_root: str | Path,
    source_payload_sha256: str,
) -> dict[str, Any]:
    toolchain = payload_manifest["bundled_toolchain"]
    return {
        "schema_version": 1,
        "version": version,
        "product": payload_manifest["edition_name"],
        "repo": payload_manifest["repo_name"],
        "baseline_source": {
            "kind": LOCAL_PAYLOAD_KIND,
            "install_root": str(source_install_root),
            "sha256": source_payload_sha256,
        },
        "bundled_toolchain": {
            "gcc_version": toolchain["gcc_version"],
            "gdb_version": toolchain["gdb_version"],
            "family": toolchain["family"],
        },
        "install": {
            "scope": payload_manifest["install_scope"],
            "edition_root": payload_manifest["edition_install_root"],
            "managed_profile_root": payload_manifest["managed_profile_root"],
        },
        "outputs": {
            "installer": f"codeblocks-pretty-prints-stable-{version}-setup.exe",
            "checksums": "SHA256SUMS.txt",
            "sbom": "sbom.json",
            "provenance": "provenance.json",
            "release_notes": f"RELEASE_NOTES_{version}.md",
        },
    }


def build_sbom(
    *,
    version: str,
    payload_manifest: Mapping[str, Any],
    source_payload_sha256: str,
) -> dict[str, Any]:
    toolchain = payload_manifest["bundled_toolchain"]
    timestamp = datetime.now(timezone.utc).isoformat()
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "version": 1,
        "metadata": {
            "timestamp": timestamp,
            "component": {
                "type": "application",
                "name": payload_manifest["edition_name"],
                "version": version,
            },
        },
        "components": [
            {
                "type": "application",
                "name": payload_manifest["product_name"],
                "version": "25.03",
                "hashes": [{"alg": "SHA-256", "content": source_payload_sha256}],
            },
            {
                "type": "framework",
                "name": "MinGW-w64 GCC/G++",
                "version": toolchain["gcc_version"],
            },
            {
                "type": "framework",
                "name": "GDB",
                "version": toolchain["gdb_version"],
            },
            {
                "type": "library",
                "name": "libstdc++ pretty-printers",
                "version": toolchain["gcc_version"],
            },
        ],
    }


def build_provenance(
    *,
    version: str,
    source_install_root: str | Path,
    source_payload_sha256: str,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "version": version,
        "built_at_utc": datetime.now(timezone.utc).isoformat(),
        "payload_source": {
            "kind": LOCAL_PAYLOAD_KIND,
            "install_root": str(source_install_root),
            "sha256": source_payload_sha256,
        },
        "build_system": {
            "type": "local-mirror-build",
        },
    }


def materialize_notice_bundle(
    *,
    repo_root: Path,
    payload_root: Path,
    release_assets_root: Path,
) -> list[str]:
    notice_manifest = load_json_document(repo_root / "manifests" / "notice_inventory.json")
    entries = collect_notice_inventory(payload_root, notice_manifest)
    harvested_root = release_assets_root / "notices"
    harvested_paths: list[str] = []
    for entry in entries:
        source = payload_root / entry.path
        destination = harvested_root / entry.path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        harvested_paths.append(entry.path)
    return harvested_paths


def compose_notice_policy(
    *,
    repo_root: Path,
    harvested_paths: Sequence[str],
    version: str,
) -> str:
    policy = (repo_root / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8").rstrip()
    lines = [
        policy,
        "",
        f"## Harvested notice inventory for {version}",
        "",
    ]
    if harvested_paths:
        lines.extend(f"- `{path}`" for path in harvested_paths)
    else:
        lines.append("- No notice files were harvested.")
    lines.append("")
    return "\n".join(lines)


def prepare_local_release(
    *,
    repo_root: str | Path,
    source_install_root: str | Path,
    version: str,
    output_root: str | Path,
) -> dict[str, Any]:
    repo = Path(repo_root)
    source_root = Path(source_install_root)
    if not (source_root / "codeblocks.exe").is_file():
        raise ValueError(f"Code::Blocks executable not found under {source_root}")

    payload_manifest = load_manifest(repo / "manifests" / "codeblocks_stable_toolchain.json")
    output = Path(output_root)
    payload_root = output / "payload" / "CodeBlocks"
    release_assets_root = output / "release-assets"

    if output.exists():
        shutil.rmtree(output)
    payload_root.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_root, payload_root)
    patched = patch_staged_gdb_init(payload_root)
    source_sha = file_sha256(payload_root / "codeblocks.exe")

    release_assets_root.mkdir(parents=True, exist_ok=True)
    harvested_paths = materialize_notice_bundle(
        repo_root=repo,
        payload_root=payload_root,
        release_assets_root=release_assets_root,
    )
    release_notes = render_release_notes(version, payload_manifest)
    release_notes_name = f"RELEASE_NOTES_{version}.md"
    (release_assets_root / release_notes_name).write_text(release_notes, encoding="utf-8")

    notice_text = compose_notice_policy(repo_root=repo, harvested_paths=harvested_paths, version=version)
    (release_assets_root / "THIRD_PARTY_NOTICES.md").write_text(notice_text, encoding="utf-8")

    release_manifest = build_release_manifest(
        version=version,
        payload_manifest=payload_manifest,
        source_install_root=source_root,
        source_payload_sha256=source_sha,
    )
    (release_assets_root / "release-manifest.json").write_text(
        json.dumps(release_manifest, indent=2) + "\n",
        encoding="utf-8",
    )

    sbom = build_sbom(version=version, payload_manifest=payload_manifest, source_payload_sha256=source_sha)
    (release_assets_root / "sbom.json").write_text(json.dumps(sbom, indent=2) + "\n", encoding="utf-8")

    provenance = build_provenance(
        version=version,
        source_install_root=source_root,
        source_payload_sha256=source_sha,
    )
    (release_assets_root / "provenance.json").write_text(
        json.dumps(provenance, indent=2) + "\n",
        encoding="utf-8",
    )

    return {
        "output_root": str(output),
        "payload_root": str(payload_root),
        "release_assets_root": str(release_assets_root),
        "release_notes_path": str(release_assets_root / release_notes_name),
        "notices_path": str(release_assets_root / "THIRD_PARTY_NOTICES.md"),
        "manifest_path": str(release_assets_root / "release-manifest.json"),
        "sbom_path": str(release_assets_root / "sbom.json"),
        "provenance_path": str(release_assets_root / "provenance.json"),
        "patched_dev_gdb_init": patched,
        "harvested_notice_count": len(harvested_paths),
    }


def _cmd_prepare_local_release(args: argparse.Namespace) -> int:
    payload = prepare_local_release(
        repo_root=args.repo_root,
        source_install_root=args.source_install_root,
        version=args.version,
        output_root=args.output_root,
    )
    Path(args.output_root).mkdir(parents=True, exist_ok=True)
    print(json.dumps(payload, indent=2))
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Release-preparation helpers for Code::Blocks Stable Toolchain Edition.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser(
        "prepare-local-release",
        help="Stage a local known-good Code::Blocks install into dist payload/release-assets output.",
    )
    prepare.add_argument("--repo-root", type=Path, required=True)
    prepare.add_argument("--source-install-root", type=Path, required=True)
    prepare.add_argument("--version", required=True)
    prepare.add_argument("--output-root", type=Path, required=True)
    prepare.set_defaults(func=_cmd_prepare_local_release)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(list(argv) if argv is not None else None)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
