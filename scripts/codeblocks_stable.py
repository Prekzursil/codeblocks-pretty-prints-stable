from __future__ import annotations

import argparse
import dataclasses
import fnmatch
import json
import os
import re
import sys
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any


@dataclasses.dataclass(frozen=True)
class NoticeEntry:
    path: str
    category: str


DEFAULT_NOTICE_PATTERNS = [
    "LICENSE*",
    "COPYING*",
    "NOTICE*",
    "AUTHORS*",
    "README*",
    "gpl.7",
    "gdbinit",
    "*.gdb.py",
    "*dll.a-gdb.py",
    "printers.py",
    "xmethods.py",
    "stl-views-*.gdb",
]

RUNTIME_NOTICE_PATTERNS = {"gdbinit", "printers.py", "xmethods.py"}
GENERIC_MINGW_ROOT = Path(r"C:\MinGW")
DEFAULT_PROFILE_OVERLAY_REPLACEMENTS = (
    {
        "path": "default.conf",
        "search": r"source C:\Devel\CodeBlocks\share\codeblocks/scripts/stl-views-1.0.3.gdb",
        "replace": "# Removed legacy dev-only stl-views hook",
    },
)


def load_json_document(path: str | Path) -> dict[str, Any]:
    file_path = Path(path)
    with file_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"{file_path} must contain a JSON object")
    return payload


def write_json_document(path: str | Path, payload: Mapping[str, Any]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(dict(payload), indent=2) + "\n", encoding="utf-8")


def _as_windows_string(value: str | Path) -> str:
    return str(value).replace("/", "\\")


def _expand_manifest_path(value: str | Path) -> Path:
    return Path(os.path.expandvars(_as_windows_string(value)))


def _ensure_str_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        raise ValueError(f"{label} must be a non-empty list of strings")
    return [item.strip() for item in value]


def _require_non_empty_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value.strip()


def validate_payload_manifest(manifest: Mapping[str, Any]) -> None:
    required_keys = (
        "schema_version",
        "repo_name",
        "edition_name",
        "product_name",
        "install_scope",
        "host_architecture",
        "target_architectures",
        "current_official_install_root",
        "edition_install_root",
        "current_profile_root",
        "managed_profile_root",
        "toolchain_relative_root",
        "toolchain_python_relative_root",
        "bundled_toolchain",
        "profile_sources",
        "profile_outputs",
        "notice_name_patterns",
        "profile_rewrites",
    )
    missing = [key for key in required_keys if key not in manifest]
    if missing:
        raise ValueError(f"manifest missing keys: {', '.join(missing)}")

    expected_literals = {
        "schema_version": 1,
        "install_scope": "machine-wide",
        "host_architecture": "x64",
    }
    for key, expected in expected_literals.items():
        if manifest[key] != expected:
            raise ValueError(f"{key} must be {expected}")

    for key in ("repo_name", "edition_name", "product_name"):
        _require_non_empty_string(manifest[key], key)

    if not {"x86", "x64"}.issubset(set(_ensure_str_list(manifest["target_architectures"], "target_architectures"))):
        raise ValueError("target_architectures must include x86 and x64")

    bundled_toolchain = manifest["bundled_toolchain"]
    if not isinstance(bundled_toolchain, dict):
        raise ValueError("bundled_toolchain must be a JSON object")
    for key in ("gcc_version", "gdb_version", "family"):
        _require_non_empty_string(bundled_toolchain.get(key), f"bundled_toolchain.{key}")

    _ensure_str_list(manifest["profile_sources"], "profile_sources")
    _ensure_str_list(manifest["profile_outputs"], "profile_outputs")
    _ensure_str_list(manifest["notice_name_patterns"], "notice_name_patterns")

    profile_rewrites = manifest["profile_rewrites"]
    if not isinstance(profile_rewrites, dict):
        raise ValueError("profile_rewrites must be a JSON object")
    for key in ("debugger_executable", "debugger_python_root", "toolchain_root", "profile_root"):
        _require_non_empty_string(profile_rewrites.get(key), f"profile_rewrites.{key}")


def load_manifest(path: str | Path) -> dict[str, Any]:
    manifest = load_json_document(path)
    validate_payload_manifest(manifest)
    return manifest


def resolve_manifest_roots(manifest: Mapping[str, Any]) -> dict[str, Path]:
    validate_payload_manifest(manifest)
    rewrites = manifest["profile_rewrites"]
    return {
        "current_install_root": _expand_manifest_path(manifest["current_official_install_root"]),
        "edition_install_root": _expand_manifest_path(manifest["edition_install_root"]),
        "current_profile_root": _expand_manifest_path(manifest["current_profile_root"]),
        "managed_profile_root": _expand_manifest_path(manifest["managed_profile_root"]),
        "toolchain_root": _expand_manifest_path(rewrites["toolchain_root"]),
        "debugger_python_root": _expand_manifest_path(rewrites["debugger_python_root"]),
        "debugger_executable": _expand_manifest_path(rewrites["debugger_executable"]),
    }


def _case_insensitive_replace(text: str, old: str, new: str) -> str:
    pattern = re.compile(re.escape(old), flags=re.IGNORECASE)
    return pattern.sub(lambda _match: new, text)


def rewrite_windows_paths(text: str, replacements: Sequence[tuple[str, str]]) -> str:
    rewritten = text
    token_map: list[tuple[str, str]] = []
    for index, (old, new) in enumerate(
        sorted(replacements, key=lambda pair: len(_as_windows_string(pair[0])), reverse=True)
    ):
        token = f"__CBSTABLE_TOKEN_{index}__"
        token_map.append((token, _as_windows_string(new)))
        rewritten = re.sub(re.escape(_as_windows_string(old)), token, rewritten, flags=re.IGNORECASE)
    for token, replacement in token_map:
        rewritten = rewritten.replace(token, replacement)
    return rewritten


def _toolchain_python_relative_path(manifest: Mapping[str, Any]) -> Path:
    return Path(_as_windows_string(_require_non_empty_string(manifest["toolchain_python_relative_root"], "toolchain_python_relative_root")))


def normalize_codeblocks_profile(text: str, manifest: Mapping[str, Any]) -> str:
    roots = resolve_manifest_roots(manifest)
    toolchain_share_python = roots["toolchain_root"] / _toolchain_python_relative_path(manifest)
    replacements = [
        (roots["current_install_root"] / "MinGW" / _toolchain_python_relative_path(manifest), toolchain_share_python),
        (roots["current_install_root"] / "MINGW" / _toolchain_python_relative_path(manifest), toolchain_share_python),
        (roots["current_install_root"] / "MinGW" / "bin" / "gdb.exe", roots["debugger_executable"]),
        (roots["current_install_root"] / "MINGW" / "bin" / "gdb.exe", roots["debugger_executable"]),
        (roots["current_install_root"] / "MinGW", roots["toolchain_root"]),
        (roots["current_install_root"] / "MINGW", roots["toolchain_root"]),
        (GENERIC_MINGW_ROOT / _toolchain_python_relative_path(manifest), toolchain_share_python),
        (GENERIC_MINGW_ROOT / "bin" / "gdb.exe", roots["debugger_executable"]),
        (GENERIC_MINGW_ROOT, roots["toolchain_root"]),
        (roots["current_install_root"], roots["edition_install_root"]),
        (roots["current_profile_root"], roots["managed_profile_root"]),
    ]
    return rewrite_windows_paths(text, replacements)


def normalize_codesnippets_ini(text: str, manifest: Mapping[str, Any]) -> str:
    roots = resolve_manifest_roots(manifest)
    replacements = [
        (roots["current_profile_root"] / "codesnippets.xml", roots["managed_profile_root"] / "codesnippets.xml"),
        (roots["current_profile_root"], roots["managed_profile_root"]),
    ]
    return rewrite_windows_paths(text, replacements)


def normalize_profile_bundle(files: Mapping[str, str], manifest: Mapping[str, Any]) -> dict[str, str]:
    missing = set(_ensure_str_list(manifest["profile_sources"], "profile_sources")) - set(files)
    if missing:
        raise ValueError(f"profile bundle missing files: {', '.join(sorted(missing))}")

    normalizers = {
        "default.conf": normalize_codeblocks_profile,
        "codesnippets.ini": normalize_codesnippets_ini,
    }
    normalized: dict[str, str] = {}
    for name, content in files.items():
        transform = normalizers.get(name)
        normalized[name] = transform(content, manifest) if transform else content
    return normalized


def build_profile_overlay_contract() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "replacements": [dict(entry) for entry in DEFAULT_PROFILE_OVERLAY_REPLACEMENTS],
    }


def validate_profile_overlay_contract(payload: Mapping[str, Any]) -> None:
    if payload.get("schema_version") != 1:
        raise ValueError("profile overlay schema_version must be 1")
    replacements = payload.get("replacements")
    if not isinstance(replacements, list):
        raise ValueError("profile overlay replacements must be a list")
    for index, entry in enumerate(replacements):
        if not isinstance(entry, Mapping):
            raise ValueError(f"profile overlay replacement {index} must be an object")
        for key in ("path", "search", "replace"):
            _require_non_empty_string(entry.get(key), f"profile overlay replacement {index}.{key}")


def build_managed_profile(source_profile_dir: str | Path, manifest: Mapping[str, Any]) -> dict[str, str]:
    profile_root = Path(source_profile_dir)
    files = {
        name: (profile_root / name).read_text(encoding="utf-8")
        for name in _ensure_str_list(manifest["profile_sources"], "profile_sources")
    }
    return normalize_profile_bundle(files, manifest)


def materialize_profile_seed(
    source_profile_dir: str | Path,
    manifest: Mapping[str, Any],
    output_dir: str | Path,
    replacements_path: str | Path,
) -> dict[str, str]:
    profile = build_managed_profile(source_profile_dir, manifest)
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    for name, content in profile.items():
        (destination / name).write_text(content, encoding="utf-8")
    write_json_document(replacements_path, build_profile_overlay_contract())
    return profile


def _is_runtime_notice_pattern(pattern: str) -> bool:
    normalized = pattern.lower()
    return normalized in RUNTIME_NOTICE_PATTERNS or normalized.endswith(".gdb.py") or normalized.startswith("stl-views-")


def _notice_category_from_name(name: str, categories: Mapping[str, Iterable[str]], default_patterns: Sequence[str]) -> str | None:
    lowered_name = name.lower()
    for category, patterns in categories.items():
        if any(fnmatch.fnmatchcase(lowered_name, str(pattern).lower()) for pattern in patterns):
            return str(category)
    for pattern in default_patterns:
        if fnmatch.fnmatchcase(lowered_name, pattern.lower()):
            return "runtime_notice" if _is_runtime_notice_pattern(pattern) else "license"
    return None


def collect_notice_inventory(root: str | Path, manifest: Mapping[str, Any] | None = None) -> list[NoticeEntry]:
    patterns = DEFAULT_NOTICE_PATTERNS
    categories: Mapping[str, Iterable[str]] = {}
    if manifest is not None:
        patterns = _ensure_str_list(manifest.get("included_patterns", patterns), "included_patterns")
        categories = manifest.get("categories", {})
        if not isinstance(categories, Mapping):
            raise ValueError("categories must be a JSON object")

    root_path = Path(root)
    entries = [
        NoticeEntry(path=file_path.relative_to(root_path).as_posix(), category=category)
        for file_path in root_path.rglob("*")
        if file_path.is_file() and ".git" not in file_path.parts
        for category in [_notice_category_from_name(file_path.name, categories, patterns)]
        if category is not None
    ]
    entries.sort(key=lambda item: item.path.lower())
    return entries


def _render_notice_inventory(entries: Sequence[NoticeEntry]) -> str:
    body = [f"- {entry.path} ({entry.category})" for entry in entries] or ["- None found"]
    return "\n".join(["# Notice inventory", "", *body, ""])


def validate_release_inputs(repo_root: str | Path) -> dict[str, Any]:
    repo = Path(repo_root)
    manifest = load_manifest(repo / "manifests" / "codeblocks_stable_toolchain.json")
    notices_manifest = load_json_document(repo / "manifests" / "notice_inventory.json")
    overlay_seed = load_json_document(repo / "overlay" / "profile_seed.json")
    profile_seed_root = repo / "overlay" / "profile-seed"
    replacements_path = repo / "overlay" / "profile-replacements.json"
    notices = collect_notice_inventory(repo, notices_manifest)
    expected_profile_outputs = _ensure_str_list(manifest["profile_outputs"], "profile_outputs")
    missing_profile_seed_files = [
        name for name in expected_profile_outputs if not (profile_seed_root / name).is_file()
    ]

    checks = [
        (notices_manifest.get("schema_version") == 1, "notice_inventory schema_version must be 1"),
        (isinstance(notices_manifest.get("included_patterns"), list), "notice_inventory included_patterns must be a list"),
        (overlay_seed.get("schema_version") == 1, "overlay profile_seed schema_version must be 1"),
        (profile_seed_root.is_dir(), "materialized profile seed directory is missing"),
        (not missing_profile_seed_files, f"profile seed is missing files: {', '.join(missing_profile_seed_files)}"),
        (replacements_path.is_file(), "profile seed overlay contract is missing"),
        (
            isinstance(overlay_seed.get("debugger_init_commands"), list) and bool(overlay_seed["debugger_init_commands"]),
            "overlay profile_seed debugger_init_commands must be a non-empty list",
        ),
        (bool(notices), "notice inventory is empty"),
    ]
    for condition, message in checks:
        if not condition:
            raise ValueError(message)

    profile_replacements = load_json_document(replacements_path)
    validate_profile_overlay_contract(profile_replacements)

    return {
        "manifest": manifest,
        "notice_count": len(notices),
        "notices": notices,
        "overlay_seed": overlay_seed,
    }


def _cmd_validate_manifest(args: argparse.Namespace) -> int:
    load_manifest(args.manifest)
    print(f"validated manifest: {args.manifest}")
    return 0


def _cmd_inventory_notices(args: argparse.Namespace) -> int:
    notice_manifest = load_json_document(args.notice_manifest) if args.notice_manifest else None
    if notice_manifest is not None and notice_manifest.get("schema_version") != 1:
        raise SystemExit("notice manifest schema_version must be 1")
    payload = [dataclasses.asdict(entry) for entry in collect_notice_inventory(args.root, notice_manifest)]
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
