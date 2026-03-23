from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from scripts.codeblocks_shared import (
    as_windows_string,
    ensure_str_list,
    expand_manifest_path,
    require_non_empty_string,
    write_json_document,
)


GENERIC_MINGW_ROOT = Path(r"C:\MinGW")
DEFAULT_PROFILE_OVERLAY_REPLACEMENTS = (
    {
        "path": "default.conf",
        "search": r"source C:\Devel\CodeBlocks\share\codeblocks/scripts/stl-views-1.0.3.gdb",
        "replace": "# Removed legacy dev-only stl-views hook",
    },
)


def resolve_manifest_roots(manifest: Mapping[str, Any]) -> dict[str, Path]:
    rewrites = manifest["profile_rewrites"]
    return {
        "current_install_root": expand_manifest_path(manifest["current_official_install_root"]),
        "edition_install_root": expand_manifest_path(manifest["edition_install_root"]),
        "current_profile_root": expand_manifest_path(manifest["current_profile_root"]),
        "managed_profile_root": expand_manifest_path(manifest["managed_profile_root"]),
        "toolchain_root": expand_manifest_path(rewrites["toolchain_root"]),
        "debugger_python_root": expand_manifest_path(rewrites["debugger_python_root"]),
        "debugger_executable": expand_manifest_path(rewrites["debugger_executable"]),
    }


def case_insensitive_replace(text: str, old: str, new: str) -> str:
    pattern = re.compile(re.escape(old), flags=re.IGNORECASE)
    return pattern.sub(lambda _match: new, text)


def rewrite_windows_paths(text: str, replacements: Sequence[tuple[str | Path, str | Path]]) -> str:
    rewritten = text
    token_map: list[tuple[str, str]] = []
    ordered_replacements = sorted(replacements, key=lambda pair: len(as_windows_string(pair[0])), reverse=True)
    for index, (old, new) in enumerate(ordered_replacements):
        token = f"__CBSTABLE_TOKEN_{index}__"
        token_map.append((token, as_windows_string(new)))
        rewritten = re.sub(re.escape(as_windows_string(old)), token, rewritten, flags=re.IGNORECASE)
    for token, replacement in token_map:
        rewritten = rewritten.replace(token, replacement)
    return rewritten


def toolchain_python_relative_path(manifest: Mapping[str, Any]) -> Path:
    value = require_non_empty_string(manifest["toolchain_python_relative_root"], "toolchain_python_relative_root")
    return Path(as_windows_string(value))


def normalize_codeblocks_profile(text: str, manifest: Mapping[str, Any]) -> str:
    roots = resolve_manifest_roots(manifest)
    python_relative_path = toolchain_python_relative_path(manifest)
    toolchain_share_python = roots["toolchain_root"] / python_relative_path
    debugger_executable_name = roots["debugger_executable"].name
    replacements = [
        (roots["current_install_root"] / "MinGW" / python_relative_path, toolchain_share_python),
        (roots["current_install_root"] / "MINGW" / python_relative_path, toolchain_share_python),
        (roots["current_install_root"] / "MinGW" / "bin" / debugger_executable_name, roots["debugger_executable"]),
        (roots["current_install_root"] / "MINGW" / "bin" / debugger_executable_name, roots["debugger_executable"]),
        (roots["current_install_root"] / "MinGW", roots["toolchain_root"]),
        (roots["current_install_root"] / "MINGW", roots["toolchain_root"]),
        (GENERIC_MINGW_ROOT / python_relative_path, toolchain_share_python),
        (GENERIC_MINGW_ROOT / "bin" / debugger_executable_name, roots["debugger_executable"]),
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
    missing = set(ensure_str_list(manifest["profile_sources"], "profile_sources")) - set(files)
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
            require_non_empty_string(entry.get(key), f"profile overlay replacement {index}.{key}")


def build_managed_profile(source_profile_dir: str | Path, manifest: Mapping[str, Any]) -> dict[str, str]:
    profile_root = Path(source_profile_dir)
    files = {
        name: (profile_root / name).read_text(encoding="utf-8")
        for name in ensure_str_list(manifest["profile_sources"], "profile_sources")
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
