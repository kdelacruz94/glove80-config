#!/usr/bin/env python3
"""Check effective per-key RGB support after each half's firmware build.

Absent firmware support is an explicit warning (RGB deferred). A firmware that
provides support must emit the node and enable its driver, or this check fails.
Card 7's semantic checks can call check_rgb with a resolved app/build directory;
checking the unpreprocessed keymap alone cannot prove RGB reached the firmware.
"""
import os
from pathlib import Path
import re
import sys

SUPPORT_FILES = (
    "include/dt-bindings/zmk/rgb_colors.h",
    "dts/bindings/zmk,underglow-layer.yaml",
    "src/rgb_underglow_layer.c",
)
DRIVER_FLAGS = ("CONFIG_ZMK_RGB_UNDERGLOW", "CONFIG_EXPERIMENTAL_RGB_LAYER")


def check_rgb(app: Path, build: Path) -> str:
    """Return 'implemented' or a deferred reason; reject incomplete integration."""
    dts = (build / "zephyr/zephyr.dts").read_text()
    config = (build / "zephyr/.config").read_text()
    node = re.search(r'\bunderglow-layer\s*\{([^{}]*)', dts)
    if node and not re.search(r'\bcompatible\s*=\s*"zmk,underglow-layer"\s*;', node[1]):
        node = None
    missing = [name for name in SUPPORT_FILES if not (app / name).is_file()]
    if missing:
        if node:
            raise ValueError("RGB node emitted without complete firmware support")
        return "Everforest per-key RGB deferred: firmware lacks " + ", ".join(missing)
    if not node:
        raise ValueError("RGB-capable firmware silently omitted underglow-layer")
    status = re.search(r'\bstatus\s*=\s*"([^"]+)"', node[1])
    if status and status[1] not in ("ok", "okay"):
        raise ValueError("underglow-layer exists but its devicetree status is disabled")
    for flag in DRIVER_FLAGS:
        if not re.search(rf"^{flag}=y$", config, re.M):
            raise ValueError(f"underglow-layer exists but its driver is disabled: {flag}")
    return "implemented"


def main() -> int:
    try:
        result = check_rgb(Path(sys.argv[1]), Path(sys.argv[2]))
    except (OSError, ValueError) as exc:
        print(f"::error::{exc}", file=sys.stderr)
        return 1
    if result == "implemented":
        print("ok: generated underglow-layer and per-key RGB driver are enabled")
    else:
        print(f"::warning::{result}; see README Everforest RGB firmware decision.")
        summary = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary:
            with open(summary, "a") as output:
                output.write(f"\n**RGB validation:** {result}. Hardware RGB testing remains outstanding.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
