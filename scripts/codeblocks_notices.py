"""Notice-harvesting policy for redistributable license/runtime files."""
from __future__ import annotations

import fnmatch
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path

from scripts.codeblocks_shared import NoticeEntry, ensure_str_list


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


def is_runtime_notice_pattern(pattern: str) -> bool:
    """Return ``True`` when ``pattern`` matches a runtime notice file."""
    normalized = pattern.lower()
    return (
        normalized in RUNTIME_NOTICE_PATTERNS
        or normalized.endswith(".gdb.py")
        or normalized.startswith("stl-views-")
    )


def _category_for_manifest_match(
    lowered_name: str,
    categories: Mapping[str, Iterable[str]],
) -> str | None:
    """Return the manifest category whose patterns match ``lowered_name``."""
    for category, patterns in categories.items():
        if any(
            fnmatch.fnmatchcase(lowered_name, str(pattern).lower())
            for pattern in patterns
        ):
            return str(category)
    return None


def _category_for_default_match(
    lowered_name: str,
    default_patterns: Sequence[str],
) -> str | None:
    """Return the default category whose pattern matches ``lowered_name``."""
    for pattern in default_patterns:
        if fnmatch.fnmatchcase(lowered_name, pattern.lower()):
            return "runtime_notice" if is_runtime_notice_pattern(pattern) else "license"
    return None


def notice_category_from_name(
    name: str,
    categories: Mapping[str, Iterable[str]],
    default_patterns: Sequence[str],
) -> str | None:
    """Classify a file ``name`` into a notice category, or ``None``."""
    lowered_name = name.lower()
    manifest_category = _category_for_manifest_match(lowered_name, categories)
    if manifest_category is not None:
        return manifest_category
    return _category_for_default_match(lowered_name, default_patterns)


def _resolve_inventory_config(
    manifest: Mapping[str, object] | None,
) -> tuple[Sequence[str], Mapping[str, Iterable[str]]]:
    """Resolve the patterns/categories pair from an optional manifest."""
    if manifest is None:
        return DEFAULT_NOTICE_PATTERNS, {}
    patterns = ensure_str_list(
        manifest.get("included_patterns", DEFAULT_NOTICE_PATTERNS),
        "included_patterns",
    )
    raw_categories = manifest.get("categories", {})
    if not isinstance(raw_categories, Mapping):
        raise ValueError("categories must be a JSON object")
    return patterns, raw_categories


def _iter_candidate_files(root_path: Path) -> Iterable[Path]:
    """Yield candidate files under ``root_path`` excluding ``.git`` paths."""
    for file_path in root_path.rglob("*"):
        if file_path.is_file() and ".git" not in file_path.parts:
            yield file_path


def collect_notice_inventory(
    root: str | Path,
    manifest: Mapping[str, object] | None = None,
) -> list[NoticeEntry]:
    """Walk ``root`` and collect matching notice files as entries."""
    patterns, categories = _resolve_inventory_config(manifest)
    root_path = Path(root)
    entries = [
        NoticeEntry(path=file_path.relative_to(root_path).as_posix(), category=category)
        for file_path in _iter_candidate_files(root_path)
        for category in [notice_category_from_name(file_path.name, categories, patterns)]
        if category is not None
    ]
    entries.sort(key=lambda item: item.path.lower())
    return entries


def render_notice_inventory(entries: Sequence[NoticeEntry]) -> str:
    """Render the notice inventory ``entries`` as a Markdown list."""
    body = [
        f"- {entry.path} ({entry.category})" for entry in entries
    ] or ["- None found"]
    return "\n".join(["# Notice inventory", "", *body, ""])
