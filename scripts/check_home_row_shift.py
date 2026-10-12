#!/usr/bin/env python3
"""Replay f/j traces through the pinned ZMK C implementation using host adapters.

Requires Python, cc, and HTTPS access; --source accepts an offline copy of the
pinned behavior_hold_tap.c. This is a host regression check, not Zephyr/firmware.
"""
import argparse
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
SOURCE_SHA256 = "2968f11ed5407d492ad71918e58432ccb8a389e8fc044003782cc46ac689358f"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path)
    args = parser.parse_args()
    manifest = (ROOT / "config/west.yml").read_text()
    revision = re.search(r"name: zmk\n\s+remote: moergo-sc\n\s+revision: ([0-9a-f]{40})", manifest)[1]
    url = f"https://raw.githubusercontent.com/moergo-sc/zmk/{revision}/app/src/behaviors/behavior_hold_tap.c"
    if args.source:
        source = args.source.read_bytes()
    else:
        with urlopen(url, timeout=60) as response:
            source = response.read()
    if hashlib.sha256(source).hexdigest() != SOURCE_SHA256:
        raise ValueError("hold-tap source changed; review the host adapters before updating its hash")

    keymap = (ROOT / "config/glove80.keymap").read_text()
    export = json.loads((ROOT / "layout/V52-Everforest-QWERTY.json").read_text())["custom_defined_behaviors"]
    assert not re.search(r"^\s*#define (ENFORCE_BILATERAL|SHIFT_FORGIVENESS)\b", keymap, re.M), "host replay needs adaptation for optional behavior paths"
    configs = []
    for side, hand in [("left", "RIGHT_HAND_KEYS"), ("right", "LEFT_HAND_KEYS")]:
        node_pattern = rf"{side}_index: homey_{side}_index {{(.*?)\n  }};"
        node = re.search(node_pattern, keymap, re.S)[1]
        assert node == re.search(node_pattern, export, re.S)[1], f"{side} index JSON differs"
        hand = re.search(r"hold-trigger-key-positions = <(\w+)>;", node)[1]
        positions = re.search(r"#define\s+\\\s*" + hand + r"(.*?)(?=\n  #)", keymap, re.S)[1]
        positions = re.findall(r"\b\d+\b", positions)
        flavor = re.search(r'flavor = "([^"]+)"', node)[1].upper().replace("-", "_")
        settings = {}
        for name in ["TAPPING_TERM", "PRIOR_IDLE"]:
            pattern = rf"#define HRM_SHIFT_{name}_MS (\d+)"
            settings[name] = re.search(pattern, keymap)[1]
            assert settings[name] == re.search(pattern, export)[1], f"{name} JSON differs"
        quick_tap = re.search(r"quick-tap-ms = <(\d+)>;", node)[1]
        release = "true" if re.search(r"^\s*hold-trigger-on-release;", node, re.M) else "false"
        assert "hold-while-undecided;" not in node.split("#ifdef SHIFT_FORGIVENESS")[0]
        configs.append(
            f"static const struct behavior_hold_tap_config {side}_cfg = {{"
            f".flavor=FLAVOR_{flavor},.tapping_term_ms={settings['TAPPING_TERM']},"
            f".require_prior_idle_ms={settings['PRIOR_IDLE']},.quick_tap_ms={quick_tap},"
            f".hold_trigger_on_release={release},.hold_behavior_dev=\"kp\",.tap_behavior_dev=\"kp\","
            f".hold_trigger_key_positions_len={len(positions)},"
            ".hold_trigger_key_positions={" + ",".join(positions) + "}};"
        )
    fixture = (ROOT / "scripts/fixtures/home_row_shift.c").read_text()
    # Only platform headers are replaced; decision, capture, release and timer code stay intact.
    source = re.sub(r"^#include .*$", "", source.decode(), flags=re.M)
    fixture = fixture.replace("/* PINNED_HOLD_TAP_SOURCE */", source)
    fixture = fixture.replace("/* KEYMAP_CONFIG */", "\n".join(configs))
    scratch = ROOT / ".scratch"
    scratch.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=scratch) as build:
        path = Path(build)
        (path / "replay.c").write_text(fixture)
        subprocess.run(["cc", "-std=gnu11", "-O0", "-Wall", "-Werror", "-Wno-unused-function",
                        "-Wno-unused-variable", str(path / "replay.c"), "-o", str(path / "replay")], check=True)
        subprocess.run([str(path / "replay")], check=True)


if __name__ == "__main__":
    main()
