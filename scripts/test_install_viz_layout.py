"""Exercise deployment through the CLI, always with an isolated home."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts/install_viz_layout.py"
LAYOUT = "V52-Everforest-QWERTY.json"


class InstallVizLayoutTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=REPO)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.home = self.root / "home"
        self.home.mkdir()
        self.data = self.root / "xdg data"
        self.env = dict(os.environ, HOME=str(self.home), XDG_DATA_HOME=str(self.data))
        self.installed = self.data / "glove80-config/layout"
        self.viz = self.home / "Downloads/MoergoLayerViz Layout" / LAYOUT
        self.main = self.checkout("main checkout", b'{"version":1,"name":"main"}')
        self.preview = self.checkout("PR worktree", b'{"version":1,"name":"preview"}')

    def checkout(self, name, content):
        root = self.root / name
        (root / "layout").mkdir(parents=True)
        (root / "layout" / LAYOUT).write_bytes(content)
        return root

    def run_cli(self, *args, succeeds=True):
        result = subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                                env=self.env, capture_output=True, text=True)
        if succeeds:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0)
        return result

    def stage_old_copies(self):
        self.installed.mkdir(parents=True)
        (self.installed / LAYOUT).write_bytes(b"old installed layout")
        (self.installed / "other.json").write_bytes(b"other installed layout")
        self.viz.parent.mkdir(parents=True)
        self.viz.write_bytes(b"old Downloads layout")
        firmware = self.installed.parent / "firmware/test.uf2"
        firmware.parent.mkdir()
        firmware.write_bytes(b"firmware untouched")
        return firmware

    def assert_source(self, root):
        self.assertTrue(self.installed.is_symlink())
        self.assertEqual(self.installed.readlink(), root / "layout")
        self.assertEqual(self.viz.readlink(), self.installed / LAYOUT)
        self.assertEqual(self.viz.read_bytes(), (root / "layout" / LAYOUT).read_bytes())

    def test_existing_deployment_follows_updates_preview_and_rollback(self):
        firmware = self.stage_old_copies()
        self.run_cli("--source", self.main)
        self.assert_source(self.main)
        # A pull can atomically replace the export: both links see the new bytes.
        replacement = self.main / "layout/new.json"
        replacement.write_bytes(b'{"version":1,"name":"updated main"}')
        replacement.replace(self.main / "layout" / LAYOUT)
        self.assert_source(self.main)
        self.run_cli("--source", self.main)  # Idempotent activation.
        self.run_cli("--source", self.preview)
        self.assert_source(self.preview)
        self.run_cli("--source", self.main)
        self.assert_source(self.main)
        self.run_cli("--rollback")
        self.assertEqual((self.installed / LAYOUT).read_bytes(), b"old installed layout")
        self.assertEqual((self.installed / "other.json").read_bytes(), b"other installed layout")
        self.assertEqual(self.viz.read_bytes(), b"old Downloads layout")
        self.assertEqual(firmware.read_bytes(), b"firmware untouched")

    def test_fresh_install_default_source_and_xdg_fallback(self):
        self.env.pop("XDG_DATA_HOME")
        self.installed = self.home / ".local/share/glove80-config/layout"
        self.run_cli()
        self.assert_source(REPO)
        self.run_cli("--rollback")
        self.assertFalse(self.installed.is_symlink())
        self.assertFalse(self.viz.is_symlink())

    def test_preexisting_unmanaged_symlinks_are_restored(self):
        self.installed.parent.mkdir(parents=True)
        self.installed.symlink_to(self.main / "layout", target_is_directory=True)
        self.viz.parent.mkdir(parents=True)
        self.viz.symlink_to(self.main / "layout" / LAYOUT)
        self.run_cli("--source", self.preview)
        self.assert_source(self.preview)
        self.run_cli("--rollback")
        self.assertEqual(self.installed.readlink(), self.main / "layout")
        self.assertEqual(self.viz.readlink(), self.main / "layout" / LAYOUT)

    def test_invalid_source_leaves_both_copies_untouched(self):
        self.stage_old_copies()
        alias = self.root / "source alias"
        alias.mkdir()
        (alias / "layout").symlink_to(self.installed, target_is_directory=True)
        for source in (self.root / "missing", self.installed.parent, alias):
            with self.subTest(source=source):
                self.run_cli("--source", source, succeeds=False)
                self.assertEqual((self.installed / LAYOUT).read_bytes(), b"old installed layout")
                self.assertEqual(self.viz.read_bytes(), b"old Downloads layout")

    def test_backup_collision_leaves_both_copies_untouched(self):
        self.stage_old_copies()
        saved = self.viz.with_name(LAYOUT + ".before-viz-link")
        saved.write_bytes(b"previous backup")
        result = self.run_cli("--source", self.main, succeeds=False)
        self.assertIn("backup already exists", result.stderr)
        self.assertEqual(saved.read_bytes(), b"previous backup")
        self.assertEqual((self.installed / LAYOUT).read_bytes(), b"old installed layout")
        self.assertEqual(self.viz.read_bytes(), b"old Downloads layout")

    def test_failed_downloads_link_restores_installed_directory(self):
        self.installed.mkdir(parents=True)
        (self.installed / LAYOUT).write_bytes(b"old installed layout")
        (self.home / "Downloads").write_bytes(b"not a directory")
        self.run_cli("--source", self.main, succeeds=False)
        self.assertFalse(self.installed.is_symlink())
        self.assertEqual((self.installed / LAYOUT).read_bytes(), b"old installed layout")
        self.assertEqual((self.home / "Downloads").read_bytes(), b"not a directory")

    def test_rollback_refuses_externally_replaced_link(self):
        self.run_cli("--source", self.main)
        self.viz.unlink()
        self.viz.write_bytes(b"external replacement")
        self.run_cli("--rollback", succeeds=False)
        self.assertTrue(self.installed.is_symlink())
        self.assertEqual(self.viz.read_bytes(), b"external replacement")

    def test_relative_xdg_home_is_rejected(self):
        self.env["XDG_DATA_HOME"] = "relative"
        self.run_cli("--source", self.main, succeeds=False)
        self.assertFalse(self.viz.exists())


if __name__ == "__main__":
    unittest.main()
