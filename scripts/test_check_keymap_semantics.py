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
    return (dict(semantics.check_recovery(km, edges)) | dict(semantics.check_precedence(km, edges))
            | dict(semantics.check_magic(km, edges)))


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

    def test_magic_below_a_mode_it_selects_fails(self):
        km = tiny_keymap(("QWERTY", {0: "&mo 1"}), ("Magic", {1: "&to 2", 2: "&to 0"}),
                         ("Mode", {0: "&mo 1"}))
        found = model(km)
        self.assertIn("magic-order:Mode", found)
        self.assertIn("magic-reach:Mode", found)
        self.assertIn("precedence:Magic<Mode", found)

    def test_magic_above_its_modes_passes(self):
        km = tiny_keymap(("QWERTY", {0: "&mo 2"}), ("Mode", {0: "&mo 2"}),
                         ("Magic", {1: "&to 1", 2: "&to 0"}))
        self.assertEqual(model(km), {"reset-combo:Mode": "no `&to 0` emergency combo covers this mode"})

    def test_home_row_helper_may_be_masked_by_a_base(self):
        km = tiny_keymap(("QWERTY", {0: "&mo 3"}), ("RightIndex", {1: "&kp A"}),
                         ("Mode", {0: "&mo 1", 1: "&kp B", 2: "&mo 3"}), ("Magic", {1: "&to 2", 2: "&to 0"}))
        found = model(km)
        self.assertNotIn("precedence:RightIndex<Mode", found)
        self.assertNotIn("magic-order:Mode", found)

    def test_mod_morph_reaches_both_bindings(self):
        km = semantics.Keymap(
            "#define LAYER_Base 0\n#define LAYER_Over 1\n"
            'ws: ws { compatible = "zmk,behavior-mod-morph"; bindings = <&mo LAYER_Over>, <&kp SPACE>; };\n'
            "/* Automatically generated keymap */\n")
        self.assertEqual(km.actions("&ws"), [("mo", 1)])


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

    def test_current_config_passes_with_no_pending_findings(self):
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("pending (", result.stdout)

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
            # one group feeds both reset combos
            self.edit_keymap(root, "LAYER_Gaming LAYER_Maple", "LAYER_Gaming")
        self.assertFails(self.check(drop), "reset-combo:Maple")

    def test_typing_access_widened_to_a_base_fails(self):
        def widen(root):
            self.edit_keymap(root, "COMBO_LAYERS_TYPING_ACCESS LAYER_QWERTY LAYER_Typing",
                             "COMBO_LAYERS_TYPING_ACCESS LAYER_QWERTY LAYER_Typing LAYER_Maple")
        self.assertFails(self.check(widen), "FAIL precedence:Typing<Maple")

    def test_reselecting_placeholder_keeps_magic_reachable(self):
        def select(root):
            self.edit(root, semantics.KEYMAP, "&to LAYER_Maple         &none",
                      "&to LAYER_Maple         &to LAYER_LoL")
            self.edit_export(root, lambda d: d["layers"][d["layer_names"].index("Magic")][24].update(
                value="&to", params=[{"value": d["layer_names"].index("LoL")}]))
        result = self.check(select)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_precedence_table_drift_fails(self):
        def drift(root):
            self.edit(root, semantics.README, "| 11 | `Maple` |", "| 11 | `Mapel` |")
        self.assertFails(self.check(drift), "precedence-doc")


if __name__ == "__main__":
    unittest.main()
