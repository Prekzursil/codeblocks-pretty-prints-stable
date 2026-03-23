from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from scripts.codeblocks_notices import (
    DEFAULT_NOTICE_PATTERNS,
    RUNTIME_NOTICE_PATTERNS,
    collect_notice_inventory,
    is_runtime_notice_pattern as _is_runtime_notice_pattern,
    notice_category_from_name as _notice_category_from_name,
    render_notice_inventory as _render_notice_inventory,
)
from scripts.codeblocks_profile import (
    DEFAULT_PROFILE_OVERLAY_REPLACEMENTS,
    build_managed_profile,
    build_profile_overlay_contract,
    case_insensitive_replace as _case_insensitive_replace,
    materialize_profile_seed,
    normalize_codeblocks_profile,
    normalize_codesnippets_ini,
    normalize_profile_bundle,
    resolve_manifest_roots,
    rewrite_windows_paths,
    toolchain_python_relative_path as _toolchain_python_relative_path,
    validate_profile_overlay_contract,
)
from scripts.codeblocks_shared import (
    NoticeEntry,
    as_windows_string as _as_windows_string,
    ensure_str_list as _ensure_str_list,
    expand_manifest_path as _expand_manifest_path,
    load_json_document,
    require_non_empty_string as _require_non_empty_string,
    write_json_document,
)
from scripts.codeblocks_validation import (
    load_manifest,
    release_input_checks as _release_input_checks,
    validate_bundled_toolchain as _validate_bundled_toolchain,
    validate_manifest_literals as _validate_manifest_literals,
    validate_payload_manifest,
    validate_profile_rewrites as _validate_profile_rewrites,
    validate_release_inputs,
)

__all__ = [
    "DEFAULT_NOTICE_PATTERNS",
    "RUNTIME_NOTICE_PATTERNS",
    "DEFAULT_PROFILE_OVERLAY_REPLACEMENTS",
    "NoticeEntry",
    "load_json_document",
    "write_json_document",
    "validate_payload_manifest",
    "load_manifest",
    "resolve_manifest_roots",
    "_case_insensitive_replace",
    "rewrite_windows_paths",
    "_toolchain_python_relative_path",
    "normalize_codeblocks_profile",
    "normalize_codesnippets_ini",
    "normalize_profile_bundle",
    "build_profile_overlay_contract",
    "validate_profile_overlay_contract",
    "build_managed_profile",
    "materialize_profile_seed",
    "_is_runtime_notice_pattern",
    "_notice_category_from_name",
    "collect_notice_inventory",
    "_render_notice_inventory",
    "_release_input_checks",
    "validate_release_inputs",
    "_validate_bundled_toolchain",
    "_validate_manifest_literals",
    "_validate_profile_rewrites",
    "_as_windows_string",
    "_ensure_str_list",
    "_expand_manifest_path",
    "_require_non_empty_string",
]


def _cmd_validate_manifest(args: argparse.Namespace) -> int:
    load_manifest(args.manifest)
    print(f"validated manifest: {args.manifest}")
    return 0


def _cmd_inventory_notices(args: argparse.Namespace) -> int:
    notice_manifest = load_json_document(args.notice_manifest) if args.notice_manifest else None
    if notice_manifest is not None and notice_manifest.get("schema_version") != 1:
        raise SystemExit("notice manifest schema_version must be 1")
    payload = [
        {
            "path": entry.path,
            "category": entry.category,
        }
        for entry in collect_notice_inventory(args.root, notice_manifest)
    ]
    if args.output == "-":
        json.dump(payload, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        Path(args.output).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return 0


def _cmd_normalize_profile(args: argparse.Namespace) -> int:
    manifest = load_manifest(args.manifest)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, content in build_managed_profile(args.source_profile, manifest).items():
        (output_dir / name).write_text(content, encoding="utf-8")
    return 0


def _cmd_materialize_profile_seed(args: argparse.Namespace) -> int:
    manifest = load_manifest(args.manifest)
    materialize_profile_seed(
        args.source_profile,
        manifest,
        args.output_dir,
        args.replacements_path,
    )
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fetch-and-package helpers for Code::Blocks Stable Toolchain Edition.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_manifest = subparsers.add_parser("validate-manifest", help="Validate the payload manifest JSON.")
    validate_manifest.add_argument("manifest", type=Path)
    validate_manifest.set_defaults(func=_cmd_validate_manifest)

    normalize_profile = subparsers.add_parser("normalize-profile", help="Normalize a source Code::Blocks profile bundle.")
    normalize_profile.add_argument("manifest", type=Path)
    normalize_profile.add_argument("source_profile", type=Path)
    normalize_profile.add_argument("output_dir", type=Path)
    normalize_profile.set_defaults(func=_cmd_normalize_profile)

    materialize_profile = subparsers.add_parser(
        "materialize-profile-seed",
        help="Write a normalized managed profile seed bundle and overlay contract.",
    )
    materialize_profile.add_argument("manifest", type=Path)
    materialize_profile.add_argument("source_profile", type=Path)
    materialize_profile.add_argument("output_dir", type=Path)
    materialize_profile.add_argument("replacements_path", type=Path)
    materialize_profile.set_defaults(func=_cmd_materialize_profile_seed)

    inventory_notices = subparsers.add_parser("inventory-notices", help="Inventory redistributable notice files.")
    inventory_notices.add_argument("root", type=Path)
    inventory_notices.add_argument("--notice-manifest", type=Path, default=None)
    inventory_notices.add_argument("--output", default="-")
    inventory_notices.set_defaults(func=_cmd_inventory_notices)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(list(argv) if argv is not None else None)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
