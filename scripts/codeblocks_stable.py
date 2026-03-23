from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from scripts import codeblocks_notices, codeblocks_profile, codeblocks_shared, codeblocks_validation

DEFAULT_NOTICE_PATTERNS = codeblocks_notices.DEFAULT_NOTICE_PATTERNS
RUNTIME_NOTICE_PATTERNS = codeblocks_notices.RUNTIME_NOTICE_PATTERNS
collect_notice_inventory = codeblocks_notices.collect_notice_inventory
_is_runtime_notice_pattern = codeblocks_notices.is_runtime_notice_pattern
_notice_category_from_name = codeblocks_notices.notice_category_from_name
_render_notice_inventory = codeblocks_notices.render_notice_inventory

DEFAULT_PROFILE_OVERLAY_REPLACEMENTS = codeblocks_profile.DEFAULT_PROFILE_OVERLAY_REPLACEMENTS
build_managed_profile = codeblocks_profile.build_managed_profile
build_profile_overlay_contract = codeblocks_profile.build_profile_overlay_contract
_case_insensitive_replace = codeblocks_profile.case_insensitive_replace
materialize_profile_seed = codeblocks_profile.materialize_profile_seed
normalize_codeblocks_profile = codeblocks_profile.normalize_codeblocks_profile
normalize_codesnippets_ini = codeblocks_profile.normalize_codesnippets_ini
normalize_profile_bundle = codeblocks_profile.normalize_profile_bundle
resolve_manifest_roots = codeblocks_profile.resolve_manifest_roots
rewrite_windows_paths = codeblocks_profile.rewrite_windows_paths
_toolchain_python_relative_path = codeblocks_profile.toolchain_python_relative_path
validate_profile_overlay_contract = codeblocks_profile.validate_profile_overlay_contract

NoticeEntry = codeblocks_shared.NoticeEntry
_as_windows_string = codeblocks_shared.as_windows_string
_ensure_str_list = codeblocks_shared.ensure_str_list
_expand_manifest_path = codeblocks_shared.expand_manifest_path
load_json_document = codeblocks_shared.load_json_document
_require_non_empty_string = codeblocks_shared.require_non_empty_string
write_json_document = codeblocks_shared.write_json_document

load_manifest = codeblocks_validation.load_manifest
_release_input_checks = codeblocks_validation.release_input_checks
_validate_bundled_toolchain = codeblocks_validation.validate_bundled_toolchain
_validate_manifest_literals = codeblocks_validation.validate_manifest_literals
validate_payload_manifest = codeblocks_validation.validate_payload_manifest
_validate_profile_rewrites = codeblocks_validation.validate_profile_rewrites
validate_release_inputs = codeblocks_validation.validate_release_inputs

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
