"""Exercise the semantic checks on mutated copies of the repo and tiny keymaps."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_keymap_semantics as semantics  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
FILES = [semantics.KEYMAP, semantics.LAYOUT, semantics.CONF, semantics.README]


def tiny_keymap(*layers):
    """A keymap with named layers; each layer is {position: binding}, default &none."""
    defines = "\n".join(f"#define LAYER_{name} {i}" for i, (name, _) in enumerate(layers))
    blocks = "\n".join(
        f"layer_{name} {{\n bindings = <{' '.join(keys.get(p, '&none') for p in range(80))}>;\n}};"
        for name, keys in layers)
    return semantics.Keymap(f"{defines}\n/* Automatically generated keymap */\n{blocks}\n")


def model(km):
    edges = semantics.explore(km)
    return dict(semantics.check_recovery(km, edges)) | dict(semantics.check_precedence(km, edges))


class ModelTests(unittest.TestCase):
    def test_mode_without_escape_is_a_lockout(self):
        km = tiny_keymap(("Base", {0: "&to 1"}), ("Mode", {}))
        self.assertIn("recovery:Mode", model(km))

    def test_overlay_below_its_base_is_masked(self):
        km = tiny_keymap(("Base", {0: "&to 2"}), ("Over", {1: "&to 0"}),
                         ("Mode", {0: "&mo 1", 1: "&kp A"}))
        found = model(km)
        self.assertIn("precedence:Over<Mode", found)
        self.assertIn("recovery:Mode", found)  # the masked overlay held the only escape

    def test_overlay_above_its_base_is_reachable(self):
        km = tiny_keymap(("Base", {0: "&to 1"}), ("Mode", {0: "&mo 2", 1: "&kp A"}),
                         ("Over", {1: "&to 0"}))
        found = model(km)
        self.assertNotIn("precedence:Over<Mode", found)
        self.assertNotIn("recovery:Mode", found)
        self.assertIn("reset-combo:Mode", found)  # no `&to 0` combo in this keymap


class RepoTests(unittest.TestCase):
    def check(self, mutate=None):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name in FILES:
                (root / name).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(REPO / name, root / name)
            if mutate:
                mutate(root)
            return subprocess.run(
                [sys.executable, str(REPO / "scripts/check_keymap_semantics.py"), "--root", str(root)],
                capture_output=True, text=True)

    def edit(self, root, name, old, new):
        path = root / name
        text = path.read_text(encoding="utf-8")
        self.assertIn(old, text)
        path.write_text(text.replace(old, new, 1), encoding="utf-8")

    def edit_keymap(self, root, old, new):
        """Edit the keymap and mirror its custom sections into the export, as a real fix must."""
        self.edit(root, semantics.KEYMAP, old, new)
        text = (root / semantics.KEYMAP).read_text(encoding="utf-8")
        self.edit_export(root, lambda d: d.update(
            {field: semantics.section(text, *markers) for field, markers in semantics.SECTIONS.items()}))

    def edit_export(self, root, change):
        path = root / semantics.LAYOUT
        data = json.loads(path.read_text(encoding="utf-8"))
        change(data)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def assertFails(self, result, message):
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn(message, result.stderr)

    def test_current_config_passes_with_pending_findings(self):
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("precedence:Magic<Maple", result.stdout)
        self.assertNotIn("recovery:", result.stdout)

    def test_layer_with_79_bindings_fails(self):
        def drop(root):
            self.edit_export(root, lambda d: d["layers"][30].pop())
            self.edit(root, semantics.KEYMAP, "&kp F13  &none", "&kp F13")
        self.assertFails(self.check(drop), "bindings:json:Terminal")

    def test_export_binding_drift_fails(self):
        def drift(root):
            self.edit_export(root, lambda d: d["layers"][0][2].update(value="&trans"))
        self.assertFails(self.check(drift), "sync:QWERTY:2")

    def test_custom_dts_drift_fails(self):
        def drift(root):
            self.edit_export(root, lambda d: d.update(custom_devicetree=d["custom_devicetree"] + "\n"))
        self.assertFails(self.check(drift), "custom:custom_devicetree")

    def test_uuid_drift_fails(self):
        def drift(root):
            self.edit(root, semantics.CONF, 'CONFIG_HID_VIZ_CONFIG_ID="15', 'CONFIG_HID_VIZ_CONFIG_ID="25')
        self.assertFails(self.check(drift), "uuid")

    def test_mode_dropped_from_reset_combos_fails(self):
        def drop(root):
            for _ in range(4):  # both Typing access combos and both reset combos
                self.edit_keymap(root, "22 23 24 25 26", "22 23 25 26")
        result = self.check(drop)
        self.assertFails(result, "reset-combo:Maple")
        self.assertIn("recovery:Maple", result.stderr)

    def test_reselecting_placeholder_locks_out(self):
        def select(root):
            self.edit_keymap(root, "&to LAYER_Maple         &none", "&to LAYER_Maple         &to LAYER_LoL")
        self.assertFails(self.check(select), "FAIL precedence:Magic<LoL")


if __name__ == "__main__":
    unittest.main()
