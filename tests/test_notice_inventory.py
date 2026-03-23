from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.codeblocks_stable import collect_notice_inventory, load_json_document


class NoticeInventoryTests(unittest.TestCase):
    def test_collect_notice_inventory_finds_expected_payload_files(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            (root / "MinGW" / "lib" / "python3.9").mkdir(parents=True)
            (root / "MinGW" / "share" / "gcc-14.2.0" / "python" / "libstdcxx" / "v6").mkdir(parents=True)
            (root / "share" / "CodeBlocks" / "scripts").mkdir(parents=True)

            files = {
                root / "MinGW" / "lib" / "python3.9" / "LICENSE.txt": "Python license",
                root / "MinGW" / "lib" / "libstdc++.dll.a-gdb.py": "GPL bridge",
                root / "MinGW" / "share" / "gcc-14.2.0" / "python" / "libstdcxx" / "v6" / "printers.py": "printers",
                root / "share" / "CodeBlocks" / "scripts" / "stl-views-1.0.3.gdb": "stl views",
                root / "docs" / "manual.pdf": "not a notice",
            }
            for path, content in files.items():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")

            manifest = load_json_document(Path(__file__).resolve().parents[1] / "manifests" / "notice_inventory.json")
            entries = collect_notice_inventory(root, manifest)
            paths = {entry.path for entry in entries}
            categories = {entry.path: entry.category for entry in entries}

            self.assertIn("MinGW/lib/python3.9/LICENSE.txt", paths)
            self.assertIn("MinGW/lib/libstdc++.dll.a-gdb.py", paths)
            self.assertIn("MinGW/share/gcc-14.2.0/python/libstdcxx/v6/printers.py", paths)
            self.assertIn("share/CodeBlocks/scripts/stl-views-1.0.3.gdb", paths)
            self.assertEqual(categories["MinGW/lib/python3.9/LICENSE.txt"], "license")
            self.assertEqual(categories["MinGW/lib/libstdc++.dll.a-gdb.py"], "runtime_notice")
            self.assertEqual(categories["share/CodeBlocks/scripts/stl-views-1.0.3.gdb"], "runtime_notice")


if __name__ == "__main__":
    unittest.main()

