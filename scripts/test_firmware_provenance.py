"""Exercise bundle integrity and source pin enforcement without building firmware."""
import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
from unittest.mock import patch
import unittest

import firmware_provenance as provenance


class BundleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.bundle = Path(self.temp.name)
        for board, (shield, filename) in provenance.EXPECTED.items():
            (self.bundle / filename).write_bytes(board.encode())
            manifest = f"west-frozen-{board}.yml"
            (self.bundle / manifest).write_text("same pinned source graph\n")
            (self.bundle / f"west-resolved-{board}.yml").write_text("all pins\n")
            data = dict(board=board, shield=shield, firmware=filename, manifest=manifest,
                        source_graph_sha256=provenance.digest(self.bundle / manifest),
                        resolved_graph_sha256=provenance.digest(self.bundle / f"west-resolved-{board}.yml"),
                        firmware_sha256=provenance.digest(self.bundle / filename),
                        config_sha="a" * 40, container="image@sha256:" + "b" * 64)
            (self.bundle / f"provenance-{board}.json").write_text(json.dumps(data))

    def test_complete_bundle_writes_verifiable_checksums(self):
        provenance.verify(self.bundle)
        lines = (self.bundle / "SHA256SUMS").read_text().splitlines()
        self.assertEqual(len(lines), 2)
        for line in lines:
            checksum, filename = line.split()
            self.assertEqual(checksum, provenance.digest(self.bundle / filename))

    def test_missing_half_or_metadata_is_fatal(self):
        for filename in ["glove80_rh-zmk.uf2", "provenance-glove80_lh.json"]:
            with self.subTest(filename=filename):
                path = self.bundle / filename
                content = path.read_bytes()
                path.unlink()
                with self.assertRaises(FileNotFoundError):
                    provenance.verify(self.bundle)
                path.write_bytes(content)

    def test_modified_firmware_or_manifest_is_fatal(self):
        for filename in ["glove80_rh-zmk.uf2", "west-frozen-glove80_lh.yml",
                         "west-resolved-glove80_rh.yml"]:
            with self.subTest(filename=filename):
                path = self.bundle / filename
                content = path.read_bytes()
                path.write_bytes(b"different")
                with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                    provenance.verify(self.bundle)
                path.write_bytes(content)

    def test_different_dependencies_or_build_environment_is_fatal(self):
        path = self.bundle / "provenance-glove80_rh.json"
        original = json.loads(path.read_text())
        for field in ["container", "config_sha", "source_graph_sha256"]:
            with self.subTest(field=field):
                data = copy.deepcopy(original)
                data[field] = "different"
                if field == "source_graph_sha256":
                    manifest = self.bundle / data["manifest"]
                    manifest.write_text("different pinned graph\n")
                    data[field] = provenance.digest(manifest)
                path.write_text(json.dumps(data))
                with self.assertRaisesRegex(ValueError, "halves disagree"):
                    provenance.verify(self.bundle)


    def test_record_packages_actual_uf2_and_required_provenance(self):
        try:
            import yaml
        except ImportError:
            self.skipTest("record integration requires the build image's PyYAML")
        repo = Path(__file__).resolve().parents[1]
        image = yaml.safe_load((repo / ".github/workflows/build.yml").read_text())["env"]["BUILD_IMAGE"]
        build = self.bundle / "build"
        (build / "zephyr").mkdir(parents=True)
        (build / "sdk").mkdir()
        (build / "sdk/sdk_version").write_text("0.16.9")
        (build / "CMakeCache.txt").write_text(
            f"CMAKE_C_COMPILER:FILEPATH=/compiler\nZEPHYR_SDK_INSTALL_DIR:PATH={build / 'sdk'}\n")
        for kind in ["frozen", "resolved"]:
            (build / f"west-{kind}-glove80_lh.yml").write_text("source graph")
        env = dict(BOARD="glove80_lh", SHIELD="raw_hid_adapter", BUILD_IMAGE=image,
                   GITHUB_WORKSPACE=str(repo), GITHUB_REPOSITORY="owner/config",
                   GITHUB_WORKFLOW_REF="owner/config/.github/workflows/build.yml@ref",
                   GITHUB_WORKFLOW_SHA="a" * 40, GITHUB_RUN_ID="123",
                   GITHUB_RUN_ATTEMPT="1", GITHUB_SERVER_URL="https://github.com")
        with patch.dict("os.environ", env), patch.object(provenance, "command", return_value="tool identity"):
            with self.assertRaises(FileNotFoundError):
                provenance.record(build)
            (build / "artifacts").rmdir()
            (build / "zephyr/zmk.uf2").write_bytes(b"actual firmware")
            provenance.record(build)
        metadata = json.loads((build / "artifacts/provenance-glove80_lh.json").read_text())
        self.assertEqual(metadata["tools"]["zephyr_sdk"], "0.16.9")
        self.assertEqual(metadata["container"], image)
        self.assertEqual(metadata["firmware_sha256"], provenance.digest(build / "zephyr/zmk.uf2"))
        self.assertTrue(metadata["actions"])


class SourceTests(unittest.TestCase):
    def test_source_validation_and_active_freeze(self):
        active = SimpleNamespace(name="zmk", revision="a" * 40, abspath="zmk")
        optional = SimpleNamespace(name="unused", revision="b" * 40, abspath="unused")
        manifest = SimpleNamespace(projects=[None, active, optional],
                                   is_active=lambda p: p is active,
                                   as_yaml=lambda: "full resolved graph")
        factory = SimpleNamespace(from_topdir=lambda: manifest)
        module = SimpleNamespace(Manifest=factory)
        with tempfile.TemporaryDirectory() as temp, \
             patch.dict("sys.modules", {"west.manifest": module}), \
             patch.dict("os.environ", {"BOARD": "glove80_lh"}), \
             patch.object(provenance, "command") as command:
            command.side_effect = [active.revision, "active frozen graph"]
            out = Path(temp)
            provenance.sources(out)
            self.assertEqual((out / "west-frozen-glove80_lh.yml").read_text(),
                             "active frozen graph\n")
            self.assertEqual((out / "west-resolved-glove80_lh.yml").read_text(),
                             "full resolved graph")
            command.assert_any_call("west", "manifest", "--freeze", "--active-only")
            command.side_effect = None
            command.return_value = "c" * 40
            with self.assertRaisesRegex(ValueError, "checkout differs"):
                provenance.sources(out)
            for project in [active, optional]:
                old = project.revision
                project.revision = "main"
                command.return_value = active.revision
                with self.assertRaisesRegex(ValueError, "floating source"):
                    provenance.sources(out)
                project.revision = old


if __name__ == "__main__":
    unittest.main()
