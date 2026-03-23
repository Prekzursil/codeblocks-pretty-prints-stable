from __future__ import annotations

import unittest

from scripts.codeblocks_stable import (
    normalize_codeblocks_profile,
    normalize_codesnippets_ini,
    normalize_profile_bundle,
)
from tests.support import base_manifest


class ProfileNormalizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = base_manifest()
        self.manifest["notice_name_patterns"] = ["LICENSE*", "gdbinit"]

    def test_default_conf_rewrites_install_root_and_debugger_paths(self) -> None:
        text = r"""\
<gdb_debugger>
  <conf1>
    <values>
      <EXECUTABLE_PATH>
        <str><![CDATA[C:\Program Files\CodeBlocks\MINGW\bin\gdb.exe]]></str>
      </EXECUTABLE_PATH>
      <INIT_COMMANDS>
        <str><![CDATA[set print pretty on
set auto-load safe-path C:\Program Files\CodeBlocks\MinGW\share\gcc-14.2.0\python
python
sys.path.insert(0, r"C:\Program Files\CodeBlocks\MinGW\share\gcc-14.2.0\python")
from libstdcxx.v6.printers import register_libstdcxx_printers
register_libstdcxx_printers(None)
end]]></str>
      </INIT_COMMANDS>
    </values>
  </conf1>
</gdb_debugger>
<gcc_mingw64>
  <MASTER_PATH><str><![CDATA[C:\Program Files\CodeBlocks\MinGW]]></str></MASTER_PATH>
  <INCLUDE_DIRS><str><![CDATA[C:\Program Files\CodeBlocks\MinGW\include;]]></str></INCLUDE_DIRS>
  <LIBRARY_DIRS><str><![CDATA[C:\Program Files\CodeBlocks\MinGW\lib;]]></str></LIBRARY_DIRS>
</gcc_mingw64>
"""
        normalized = normalize_codeblocks_profile(text, self.manifest)
        self.assertIn("CodeBlocks Stable Toolchain Edition", normalized)
        self.assertIn(
            r"C:\Program Files\CodeBlocks Stable Toolchain Edition\MinGW\bin\gdb.exe",
            normalized,
        )
        self.assertIn(
            r"C:\Program Files\CodeBlocks Stable Toolchain Edition\MinGW\share\gcc-14.2.0\python",
            normalized,
        )
        self.assertNotIn(r"C:\Program Files\CodeBlocks\MinGW", normalized)

    def test_default_conf_rewrites_generic_mingw_root_and_custom_python_relative_path(self) -> None:
        self.manifest["toolchain_python_relative_root"] = r"share\gcc-custom\python"
        self.manifest["profile_rewrites"]["debugger_python_root"] = (
            r"C:\Program Files\CodeBlocks Stable Toolchain Edition\MinGW\share\gcc-custom\python"
        )
        text = r"""\
<gdb_debugger>
  <conf1>
    <values>
      <EXECUTABLE_PATH>
        <str><![CDATA[C:\MinGW\bin\gdb.exe]]></str>
      </EXECUTABLE_PATH>
      <INIT_COMMANDS>
        <str><![CDATA[set auto-load safe-path C:\MinGW\share\gcc-custom\python]]></str>
      </INIT_COMMANDS>
    </values>
  </conf1>
</gdb_debugger>
<gcc_mingw32>
  <MASTER_PATH><str><![CDATA[C:\MinGW]]></str></MASTER_PATH>
</gcc_mingw32>
"""
        normalized = normalize_codeblocks_profile(text, self.manifest)
        self.assertIn(
            r"C:\Program Files\CodeBlocks Stable Toolchain Edition\MinGW\bin\gdb.exe",
            normalized,
        )
        self.assertIn(
            r"C:\Program Files\CodeBlocks Stable Toolchain Edition\MinGW\share\gcc-custom\python",
            normalized,
        )
        self.assertNotIn(r"C:\MinGW", normalized)

    def test_codesnippets_ini_profile_root_is_normalized(self) -> None:
        text = r"""\
ExternalEditor=
SnippetFile=C:\Users\Prekzursil\AppData\Roaming\CodeBlocks\codesnippets.xml
SnippetFolder=
"""
        normalized = normalize_codesnippets_ini(text, self.manifest)
        expected = (
            r"C:\Users\Prekzursil\AppData\Roaming\CodeBlocks Stable Toolchain Edition\codesnippets.xml"
        )
        self.assertIn(expected, normalized)
        self.assertNotIn(
            r"C:\Users\Prekzursil\AppData\Roaming\CodeBlocks\codesnippets.xml",
            normalized,
        )

    def test_profile_bundle_requires_expected_inputs(self) -> None:
        bundle = {
            "default.conf": r"C:\Program Files\CodeBlocks\MinGW",
            "default.cbKeyBinder20.conf": "{}",
            "codesnippets.ini": r"SnippetFile=C:\Users\Prekzursil\AppData\Roaming\CodeBlocks\codesnippets.xml",
        }
        normalized = normalize_profile_bundle(bundle, self.manifest)
        self.assertIn("CodeBlocks Stable Toolchain Edition", normalized["default.conf"])
        self.assertEqual(normalized["default.cbKeyBinder20.conf"], "{}")


if __name__ == "__main__":
    unittest.main()
