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


REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclasses.dataclass(frozen=True)
class NoticeEntry:
    path: str
    category: str


def load_json_document(path: str | Path) -> dict[str, Any]:
    file_path = Path(path)
    with file_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"{file_path} must contain a JSON object")
    return payload


def _as_windows_string(value: str | Path) -> str:
    return str(value).replace("/", "\\")


def _expand_manifest_path(value: str | Path) -> Path:
    expanded = os.path.expandvars(_as_windows_string(value))
    return Path(expanded)


def _ensure_str_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        raise ValueError(f"{label} must be a non-empty list of strings")
    return [item.strip() for item in value]


def validate_payload_manifest(manifest: Mapping[str, Any]) -> None:
    required_keys = [
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
    ]
    missing = [key for key in required_keys if key not in manifest]
    if missing:
        raise ValueError(f"manifest missing keys: {', '.join(missing)}")
    if manifest["schema_version"] != 1:
        raise ValueError("schema_version must be 1")
    if not isinstance(manifest["repo_name"], str) or not manifest["repo_name"].strip():
        raise ValueError("repo_name must be a non-empty string")
    if not isinstance(manifest["edition_name"], str) or not manifest["edition_name"].strip():
        raise ValueError("edition_name must be a non-empty string")
    if not isinstance(manifest["product_name"], str) or not manifest["product_name"].strip():
        raise ValueError("product_name must be a non-empty string")
    if manifest["install_scope"] != "machine-wide":
        raise ValueError("install_scope must be machine-wide")
    if manifest["host_architecture"] != "x64":
        raise ValueError("host_architecture must be x64")
    target_architectures = _ensure_str_list(manifest["target_architectures"], "target_architectures")
    if {"x86", "x64"} - set(target_architectures):
        raise ValueError("target_architectures must include x86 and x64")
    if not isinstance(manifest["bundled_toolchain"], dict):
        raise ValueError("bundled_toolchain must be a JSON object")
    for key in ("gcc_version", "gdb_version", "family"):
        if not isinstance(manifest["bundled_toolchain"].get(key), str) or not manifest["bundled_toolchain"][key].strip():
            raise ValueError(f"bundled_toolchain.{key} must be a non-empty string")
    _ensure_str_list(manifest["profile_sources"], "profile_sources")
    _ensure_str_list(manifest["profile_outputs"], "profile_outputs")
    _ensure_str_list(manifest["notice_name_patterns"], "notice_name_patterns")
    if not isinstance(manifest["profile_rewrites"], dict):
        raise ValueError("profile_rewrites must be a JSON object")
    for key in ("debugger_executable", "debugger_python_root", "toolchain_root", "profile_root"):
        value = manifest["profile_rewrites"].get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"profile_rewrites.{key} must be a non-empty string")


def load_manifest(path: str | Path) -> dict[str, Any]:
    manifest = load_json_document(path)
    validate_payload_manifest(manifest)
    return manifest


def resolve_manifest_roots(manifest: Mapping[str, Any]) -> dict[str, Path]:
    validate_payload_manifest(manifest)
    current_install_root = _expand_manifest_path(manifest["current_official_install_root"])
    edition_install_root = _expand_manifest_path(manifest["edition_install_root"])
    current_profile_root = _expand_manifest_path(manifest["current_profile_root"])
    managed_profile_root = _expand_manifest_path(manifest["managed_profile_root"])
    toolchain_root = _expand_manifest_path(manifest["profile_rewrites"]["toolchain_root"])
    debugger_python_root = _expand_manifest_path(manifest["profile_rewrites"]["debugger_python_root"])
    debugger_executable = _expand_manifest_path(manifest["profile_rewrites"]["debugger_executable"])
    return {
        "current_install_root": current_install_root,
        "edition_install_root": edition_install_root,
        "current_profile_root": current_profile_root,
        "managed_profile_root": managed_profile_root,
        "toolchain_root": toolchain_root,
        "debugger_python_root": debugger_python_root,
        "debugger_executable": debugger_executable,
    }


def _case_insensitive_replace(text: str, old: str, new: str) -> str:
    if not old:
        return text
    pattern = re.compile(re.escape(old), flags=re.IGNORECASE)
    return pattern.sub(lambda _match: new, text)


def rewrite_windows_paths(text: str, replacements: Sequence[tuple[str, str]]) -> str:
    rewritten = text
    token_map: list[tuple[str, str]] = []
    for index, (old, new) in enumerate(sorted(replacements, key=lambda pair: len(_as_windows_string(pair[0])), reverse=True)):
        token = f"__CBSTABLE_TOKEN_{index}__"
        token_map.append((token, _as_windows_string(new)))
        pattern = re.compile(re.escape(_as_windows_string(old)), flags=re.IGNORECASE)
        rewritten = pattern.sub(token, rewritten)
    for token, new in token_map:
        rewritten = rewritten.replace(token, new)
    return rewritten


def normalize_codeblocks_profile(text: str, manifest: Mapping[str, Any]) -> str:
    roots = resolve_manifest_roots(manifest)
    toolchain_share_python = roots["toolchain_root"] / "share" / "gcc-14.2.0" / "python"
    replacements = [
        (
            roots["current_install_root"] / "MinGW" / "share" / "gcc-14.2.0" / "python",
            toolchain_share_python,
        ),
        (
            roots["current_install_root"] / "MINGW" / "share" / "gcc-14.2.0" / "python",
            toolchain_share_python,
        ),
        (roots["current_install_root"] / "MinGW" / "bin" / "gdb.exe", roots["debugger_executable"]),
        (roots["current_install_root"] / "MINGW" / "bin" / "gdb.exe", roots["debugger_executable"]),
        (roots["current_install_root"] / "MinGW", roots["toolchain_root"]),
        (roots["current_install_root"] / "MINGW", roots["toolchain_root"]),
        (roots["current_install_root"], roots["edition_install_root"]),
        (roots["current_profile_root"], roots["managed_profile_root"]),
    ]
    normalized = rewrite_windows_paths(text, replacements)
    return normalized


def normalize_codesnippets_ini(text: str, manifest: Mapping[str, Any]) -> str:
    roots = resolve_manifest_roots(manifest)
    return rewrite_windows_paths(
        text,
        [
            (roots["current_profile_root"] / "codesnippets.xml", roots["managed_profile_root"] / "codesnippets.xml"),
            (roots["current_profile_root"], roots["managed_profile_root"]),
        ],
    )


def normalize_profile_bundle(files: Mapping[str, str], manifest: Mapping[str, Any]) -> dict[str, str]:
    normalized: dict[str, str] = {}
    allowed = set(_ensure_str_list(manifest["profile_sources"], "profile_sources"))
    missing = allowed - set(files)
    if missing:
        raise ValueError(f"profile bundle missing files: {', '.join(sorted(missing))}")
    for name, content in files.items():
        if name == "default.conf":
            normalized[name] = normalize_codeblocks_profile(content, manifest)
        elif name == "codesnippets.ini":
            normalized[name] = normalize_codesnippets_ini(content, manifest)
        else:
            normalized[name] = content
    return normalized


def build_managed_profile(source_profile_dir: str | Path, manifest: Mapping[str, Any]) -> dict[str, str]:
    profile_root = Path(source_profile_dir)
    source_files: dict[str, str] = {}
    for name in _ensure_str_list(manifest["profile_sources"], "profile_sources"):
        source_files[name] = (profile_root / name).read_text(encoding="utf-8")
    return normalize_profile_bundle(source_files, manifest)


def _notice_category_from_name(name: str, categories: Mapping[str, Iterable[str]], default_patterns: Sequence[str]) -> str | None:
    for category, patterns in categories.items():
        for pattern in patterns:
            if fnmatch.fnmatchcase(name.lower(), pattern.lower()):
                return str(category)
    for pattern in default_patterns:
        if fnmatch.fnmatchcase(name.lower(), pattern.lower()):
            if pattern.lower() in {"gdbinit", "printers.py", "xmethods.py"} or pattern.lower().endswith(".gdb.py") or pattern.lower().startswith("stl-views-"):
                return "runtime_notice"
            return "license"
    return None


def collect_notice_inventory(root: str | Path, manifest: Mapping[str, Any] | None = None) -> list[NoticeEntry]:
    root_path = Path(root)
    patterns = [
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
    categories: Mapping[str, Iterable[str]] = {}
    if manifest is not None:
        patterns = _ensure_str_list(manifest.get("included_patterns", patterns), "included_patterns")
        categories = manifest.get("categories", {})
        if not isinstance(categories, Mapping):
            raise ValueError("categories must be a JSON object")

    entries: list[NoticeEntry] = []
    for file_path in root_path.rglob("*"):
        if not file_path.is_file():
            continue
        category = _notice_category_from_name(file_path.name, categories, patterns)
        if category is None:
            continue
        relative = file_path.relative_to(root_path).as_posix()
        entries.append(NoticeEntry(path=relative, category=category))

    entries.sort(key=lambda item: item.path.lower())
    return entries


def _render_notice_inventory(entries: Sequence[NoticeEntry]) -> str:
    lines = ["# Notice inventory", ""]
    if not entries:
        lines.extend(["- None found", ""])
        return "\n".join(lines)
    for entry in entries:
        lines.append(f"- {entry.path} ({entry.category})")
    lines.append("")
    return "\n".join(lines)


def validate_release_inputs(repo_root: str | Path) -> dict[str, Any]:
    repo = Path(repo_root)
    manifest = load_manifest(repo / "manifests" / "codeblocks_stable_toolchain.json")
    notices_manifest = load_json_document(repo / "manifests" / "notice_inventory.json")
    if notices_manifest.get("schema_version") != 1:
        raise ValueError("notice_inventory schema_version must be 1")
    if not isinstance(notices_manifest.get("included_patterns"), list):
        raise ValueError("notice_inventory included_patterns must be a list")
    overlay_seed = load_json_document(repo / "overlay" / "profile_seed.json")
    if overlay_seed.get("schema_version") != 1:
        raise ValueError("overlay profile_seed schema_version must be 1")
    if not isinstance(overlay_seed.get("debugger_init_commands"), list) or not overlay_seed["debugger_init_commands"]:
        raise ValueError("overlay profile_seed debugger_init_commands must be a non-empty list")
    notices = collect_notice_inventory(repo, notices_manifest)
    if not notices:
        raise ValueError("notice inventory is empty")
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
    entries = collect_notice_inventory(args.root, notice_manifest)
    payload = [dataclasses.asdict(entry) for entry in entries]
    if args.output == "-":
        json.dump(payload, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        Path(args.output).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return 0


def _cmd_normalize_profile(args: argparse.Namespace) -> int:
    manifest = load_manifest(args.manifest)
    source_profile = Path(args.source_profile)
    output_dir = Path(args.output_dir)
    bundle = build_managed_profile(source_profile, manifest)
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, content in bundle.items():
        (output_dir / name).write_text(content, encoding="utf-8")
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

    inventory_notices = subparsers.add_parser("inventory-notices", help="Inventory redistributable notice files.")
    inventory_notices.add_argument("root", type=Path)
    inventory_notices.add_argument("--notice-manifest", type=Path, default=None)
    inventory_notices.add_argument("--output", default="-")
    inventory_notices.set_defaults(func=_cmd_inventory_notices)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())

