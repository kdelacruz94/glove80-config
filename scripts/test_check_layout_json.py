"""Exercise the layout check through its CI command with isolated fixtures."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
LAYOUT = "V52-Everforest-QWERTY.json"


class LayoutTests(unittest.TestCase):
    def check(self, data=None, filename=LAYOUT):
        with tempfile.TemporaryDirectory(dir=REPO) as temp:
            root = Path(temp)
            if data is not None:
                (root / "layout").mkdir()
                (root / "layout" / filename).write_text(json.dumps(data))
            return subprocess.run(
                [sys.executable, str(REPO / "scripts/check_layout_json.py")],
                cwd=root, capture_output=True, text=True,
            )

    def test_missing_expected_layout_fails(self):
        for data, filename in [(None, LAYOUT), ({"layers": [[{}]]}, "other.json")]:
            with self.subTest(filename=filename):
                result = self.check(data, filename)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("required layout file missing", result.stderr)

    def test_missing_or_empty_layers_fail(self):
        for data in [{}, {"layers": []}, {"layers": [[]]}, {"layers": None},
                     {"layers": {}}, {"layers": ["invalid"]}]:
            with self.subTest(data=data):
                result = self.check(data)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("non-empty", result.stderr)

    def test_bad_modifier_still_fails(self):
        result = self.check({"layers": [[{"value": "LG(LS(S))"}]]})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("parenthesised modifier string", result.stderr)

    def test_nested_modifiers_and_custom_values_pass(self):
        result = self.check({"layers": [[
            {"value": "LG", "params": [{"value": "S"}]},
            {"value": "&kp _C(L)"},
        ]]})
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_current_export_passes(self):
        result = self.check(json.loads((REPO / "layout" / LAYOUT).read_text()))
        self.assertEqual(result.returncode, 0, result.stderr)
