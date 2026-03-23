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
    normalized = pattern.lower()
    return normalized in RUNTIME_NOTICE_PATTERNS or normalized.endswith(".gdb.py") or normalized.startswith("stl-views-")


def notice_category_from_name(
    name: str,
    categories: Mapping[str, Iterable[str]],
    default_patterns: Sequence[str],
) -> str | None:
    lowered_name = name.lower()
    for category, patterns in categories.items():
        if any(fnmatch.fnmatchcase(lowered_name, str(pattern).lower()) for pattern in patterns):
            return str(category)
    for pattern in default_patterns:
        if fnmatch.fnmatchcase(lowered_name, pattern.lower()):
            return "runtime_notice" if is_runtime_notice_pattern(pattern) else "license"
    return None


def collect_notice_inventory(root: str | Path, manifest: Mapping[str, object] | None = None) -> list[NoticeEntry]:
    patterns = DEFAULT_NOTICE_PATTERNS
    categories: Mapping[str, Iterable[str]] = {}
    if manifest is not None:
        patterns = ensure_str_list(manifest.get("included_patterns", patterns), "included_patterns")
        categories = manifest.get("categories", {})
        if not isinstance(categories, Mapping):
            raise ValueError("categories must be a JSON object")

    root_path = Path(root)
    entries = [
        NoticeEntry(path=file_path.relative_to(root_path).as_posix(), category=category)
        for file_path in root_path.rglob("*")
        if file_path.is_file() and ".git" not in file_path.parts
        for category in [notice_category_from_name(file_path.name, categories, patterns)]
        if category is not None
    ]
    entries.sort(key=lambda item: item.path.lower())
    return entries


def render_notice_inventory(entries: Sequence[NoticeEntry]) -> str:
    body = [f"- {entry.path} ({entry.category})" for entry in entries] or ["- None found"]
    return "\n".join(["# Notice inventory", "", *body, ""])
