"""Regressions for silent source omission and disabled RGB runtime."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from check_rgb_build import check_rgb, DRIVER_FLAGS, SUPPORT_FILES


class RGBBuildTests(unittest.TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.app = Path(tmp.name) / "app"
        self.build = Path(tmp.name) / "build"
        (self.build / "zephyr").mkdir(parents=True)
        for name in SUPPORT_FILES:
            path = self.app / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()
        self.dts = self.build / "zephyr/zephyr.dts"
        self.dts.write_text('/ { underglow-layer { compatible = "zmk,underglow-layer"; '
                            'base { layer-id = <0>; }; }; };')
        self.config = self.build / "zephyr/.config"
        self.config.write_text("\n".join(f"{flag}=y" for flag in DRIVER_FLAGS))

    def test_supported_firmware_requires_generated_node_and_driver(self):
        self.assertEqual(check_rgb(self.app, self.build), "implemented")
        self.dts.write_text('/ { keymap { }; };')
        with self.assertRaisesRegex(ValueError, "silently omitted"):
            check_rgb(self.app, self.build)

    def test_disabled_driver_is_fatal_even_when_node_exists(self):
        for flag in DRIVER_FLAGS:
            with self.subTest(flag=flag):
                self.config.write_text("\n".join(f"{item}={'n' if item == flag else 'y'}"
                                                  for item in DRIVER_FLAGS))
                with self.assertRaisesRegex(ValueError, flag):
                    check_rgb(self.app, self.build)

    def test_each_missing_support_file_is_explicitly_deferred(self):
        self.dts.write_text('/ { keymap { }; };')
        for name in SUPPORT_FILES:
            with self.subTest(name=name):
                path = self.app / name
                path.unlink()
                self.assertIn(name, check_rgb(self.app, self.build))
                path.touch()

    def test_node_without_support_is_fatal(self):
        (self.app / SUPPORT_FILES[1]).unlink()
        with self.assertRaisesRegex(ValueError, "without complete firmware support"):
            check_rgb(self.app, self.build)

    def test_disabled_node_cannot_be_reported_as_implemented(self):
        self.dts.write_text('/ { underglow-layer { status = "disabled"; '
                            'compatible = "zmk,underglow-layer"; }; };')
        with self.assertRaisesRegex(ValueError, "devicetree status is disabled"):
            check_rgb(self.app, self.build)

    def test_missing_build_output_cannot_be_treated_as_deferred(self):
        self.dts.unlink()
        with self.assertRaises(FileNotFoundError):
            check_rgb(self.app, self.build)
