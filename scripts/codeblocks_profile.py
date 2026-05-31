"""Profile normalization and overlay-contract helpers."""
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
_DEV_ONLY_STL_VIEWS = (
    r"source C:\Devel\CodeBlocks\share\codeblocks/scripts/stl-views-1.0.3.gdb"
)
DEFAULT_PROFILE_OVERLAY_REPLACEMENTS = (
    {
        "path": "default.conf",
        "search": _DEV_ONLY_STL_VIEWS,
        "replace": "# Removed legacy dev-only stl-views hook",
    },
)


def resolve_manifest_roots(manifest: Mapping[str, Any]) -> dict[str, Path]:
    """Expand the manifest's path fields into resolved ``Path`` roots."""
    rewrites = manifest["profile_rewrites"]
    return {
        "current_install_root": expand_manifest_path(
            manifest["current_official_install_root"]
        ),
        "edition_install_root": expand_manifest_path(manifest["edition_install_root"]),
        "current_profile_root": expand_manifest_path(manifest["current_profile_root"]),
        "managed_profile_root": expand_manifest_path(manifest["managed_profile_root"]),
        "toolchain_root": expand_manifest_path(rewrites["toolchain_root"]),
        "debugger_python_root": expand_manifest_path(rewrites["debugger_python_root"]),
        "debugger_executable": expand_manifest_path(rewrites["debugger_executable"]),
    }


def case_insensitive_replace(text: str, old: str, new: str) -> str:
    """Replace every case-insensitive occurrence of ``old`` with ``new``."""
    pattern = re.compile(re.escape(old), flags=re.IGNORECASE)
    return pattern.sub(lambda _match: new, text)


def rewrite_windows_paths(
    text: str,
    replacements: Sequence[tuple[str | Path, str | Path]],
) -> str:
    """Rewrite Windows paths in ``text`` honouring longest-match order."""
    rewritten = text
    token_map: list[tuple[str, str]] = []
    ordered_replacements = sorted(
        replacements,
        key=lambda pair: len(as_windows_string(pair[0])),
        reverse=True,
    )
    for index, (old, new) in enumerate(ordered_replacements):
        token = f"__CBSTABLE_TOKEN_{index}__"
        token_map.append((token, as_windows_string(new)))
        rewritten = re.sub(
            re.escape(as_windows_string(old)),
            token,
            rewritten,
            flags=re.IGNORECASE,
        )
    for token, replacement in token_map:
        rewritten = rewritten.replace(token, replacement)
    return rewritten


def toolchain_python_relative_path(manifest: Mapping[str, Any]) -> Path:
    """Return the manifest's bundled-python relative path as a ``Path``."""
    value = require_non_empty_string(
        manifest["toolchain_python_relative_root"],
        "toolchain_python_relative_root",
    )
    return Path(as_windows_string(value))


def normalize_codeblocks_profile(text: str, manifest: Mapping[str, Any]) -> str:
    """Rewrite ``default.conf`` paths to the managed edition layout."""
    roots = resolve_manifest_roots(manifest)
    python_relative_path = toolchain_python_relative_path(manifest)
    toolchain_share_python = roots["toolchain_root"] / python_relative_path
    debugger_executable_name = roots["debugger_executable"].name
    current_root = roots["current_install_root"]
    debugger = roots["debugger_executable"]
    toolchain_root = roots["toolchain_root"]
    edition_install_root = roots["edition_install_root"]
    managed_profile_root = roots["managed_profile_root"]
    replacements = [
        # Identity-protect already-normalized destination roots so the shorter
        # current_root / current_profile_root prefix substitutions below cannot
        # corrupt them on a second normalization pass (idempotence guard).
        (edition_install_root, edition_install_root),
        (managed_profile_root, managed_profile_root),
        (current_root / "MinGW" / python_relative_path, toolchain_share_python),
        (current_root / "MINGW" / python_relative_path, toolchain_share_python),
        (current_root / "MinGW" / "bin" / debugger_executable_name, debugger),
        (current_root / "MINGW" / "bin" / debugger_executable_name, debugger),
        (current_root / "MinGW", toolchain_root),
        (current_root / "MINGW", toolchain_root),
        (GENERIC_MINGW_ROOT / python_relative_path, toolchain_share_python),
        (GENERIC_MINGW_ROOT / "bin" / debugger_executable_name, debugger),
        (GENERIC_MINGW_ROOT, toolchain_root),
        (current_root, edition_install_root),
        (roots["current_profile_root"], managed_profile_root),
    ]
    return rewrite_windows_paths(text, replacements)


def normalize_codesnippets_ini(text: str, manifest: Mapping[str, Any]) -> str:
    """Rewrite ``codesnippets.ini`` paths to the managed profile root."""
    roots = resolve_manifest_roots(manifest)
    current_profile = roots["current_profile_root"]
    managed_profile = roots["managed_profile_root"]
    replacements = [
        # Identity-protect the managed profile root for idempotence on repeated
        # invocations (current_profile is a prefix of managed_profile).
        (managed_profile, managed_profile),
        (current_profile / "codesnippets.xml", managed_profile / "codesnippets.xml"),
        (current_profile, managed_profile),
    ]
    return rewrite_windows_paths(text, replacements)


def normalize_profile_bundle(
    files: Mapping[str, str],
    manifest: Mapping[str, Any],
) -> dict[str, str]:
    """Normalize each known profile file and pass others through."""
    expected = set(ensure_str_list(manifest["profile_sources"], "profile_sources"))
    missing = expected - set(files)
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
    """Build the default overlay-contract document for the profile seed."""
    return {
        "schema_version": 1,
        "replacements": [dict(entry) for entry in DEFAULT_PROFILE_OVERLAY_REPLACEMENTS],
    }


def _validate_overlay_replacement(index: int, entry: Any) -> None:
    """Validate a single replacement ``entry`` from the overlay contract."""
    if not isinstance(entry, Mapping):
        raise ValueError(f"profile overlay replacement {index} must be an object")
    for key in ("path", "search", "replace"):
        require_non_empty_string(
            entry.get(key), f"profile overlay replacement {index}.{key}"
        )


def validate_profile_overlay_contract(payload: Mapping[str, Any]) -> None:
    """Validate the structure of a profile overlay-contract ``payload``."""
    if payload.get("schema_version") != 1:
        raise ValueError("profile overlay schema_version must be 1")
    replacements = payload.get("replacements")
    if not isinstance(replacements, list):
        raise ValueError("profile overlay replacements must be a list")
    for index, entry in enumerate(replacements):
        _validate_overlay_replacement(index, entry)


def build_managed_profile(
    source_profile_dir: str | Path,
    manifest: Mapping[str, Any],
) -> dict[str, str]:
    """Read source profile files and return the normalized bundle."""
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
    """Write the normalized profile seed and overlay contract to disk."""
    profile = build_managed_profile(source_profile_dir, manifest)
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    for name, content in profile.items():
        (destination / name).write_text(content, encoding="utf-8")
    write_json_document(replacements_path, build_profile_overlay_contract())
    return profile
