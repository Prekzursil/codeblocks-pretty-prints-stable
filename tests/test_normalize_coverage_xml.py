from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.quality.normalize_coverage_xml import main, normalize_coverage_xml_paths


class NormalizeCoverageXmlTests(unittest.TestCase):
    def test_normalize_coverage_xml_paths_prefixes_repo_relative_script_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            coverage_xml = Path(tempdir) / 'coverage.xml'
            coverage_xml.write_text(
                '<coverage><packages><package name="scripts"><classes>'
                '<class name="codeblocks_stable.py" filename="codeblocks_stable.py" />'
                '<class name="validate_release_inputs.py" filename="quality/validate_release_inputs.py" />'
                '<class name="already.py" filename="scripts/already.py" />'
                '</classes></package></packages></coverage>',
                encoding='utf-8',
            )

            changed = normalize_coverage_xml_paths(coverage_xml)

            payload = coverage_xml.read_text(encoding='utf-8')
            self.assertTrue(changed)
            self.assertIn('filename="scripts/codeblocks_stable.py"', payload)
            self.assertIn('filename="scripts/quality/validate_release_inputs.py"', payload)
            self.assertIn('filename="scripts/already.py"', payload)

    def test_normalize_coverage_xml_paths_is_noop_when_paths_are_already_repo_relative(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            coverage_xml = Path(tempdir) / 'coverage.xml'
            coverage_xml.write_text(
                '<coverage><packages><package name="scripts"><classes>'
                '<class name="codeblocks_stable.py" filename="scripts/codeblocks_stable.py" />'
                '</classes></package></packages></coverage>',
                encoding='utf-8',
            )

            changed = normalize_coverage_xml_paths(coverage_xml)

            self.assertFalse(changed)

    def test_normalize_coverage_xml_paths_ignores_classes_without_filenames_and_main_runs(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            coverage_xml = Path(tempdir) / 'coverage.xml'
            coverage_xml.write_text(
                '<coverage><packages><package name="scripts"><classes>'
                '<class name="missing.py" />'
                '<class name="note.py" filename="note.py" />'
                '</classes></package></packages></coverage>',
                encoding='utf-8',
            )

            rc = main([str(coverage_xml)])

            self.assertEqual(rc, 0)
            payload = coverage_xml.read_text(encoding='utf-8')
            self.assertIn('filename="scripts/note.py"', payload)


if __name__ == '__main__':
    unittest.main()
