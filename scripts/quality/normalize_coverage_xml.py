from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence
from defusedxml import ElementTree

SCRIPT_PATH_PREFIX = "scripts/"


def _normalize_filename(value: str) -> str:
    normalized = value.replace('\\', '/').lstrip('./')
    if normalized.startswith((SCRIPT_PATH_PREFIX, 'tests/')):
        return normalized
    return SCRIPT_PATH_PREFIX + normalized


def normalize_coverage_xml_paths(path: str | Path) -> bool:
    coverage_path = Path(path)
    tree = ElementTree.parse(coverage_path)
    root = tree.getroot()
    changed = False
    for class_element in root.findall('.//class'):
        filename = class_element.get('filename')
        if not filename:
            continue
        normalized = _normalize_filename(filename)
        if normalized != filename:
            class_element.set('filename', normalized)
            changed = True
    if changed:
        tree.write(coverage_path, encoding='utf-8', xml_declaration=True)
    return changed


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Normalize Cobertura XML paths for provider uploads.')
    parser.add_argument('coverage_xml', type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(list(argv) if argv is not None else None)
    normalize_coverage_xml_paths(args.coverage_xml)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
