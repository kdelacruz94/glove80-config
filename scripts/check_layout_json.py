#!/usr/bin/env python3
"""Require the expected layout with populated layers and valid modifier encoding.

MoErgo's Layout Editor rejects `LG(LS(S))` on import; it wants nested params:
`{"value": "LG", "params": [{"value": "LS", "params": [{"value": "S"}]}]}`.
The keymap file keeps the ZMK string form -- only the JSON is affected.

Values starting with `&` (Custom devicetree passthrough, e.g. `&kp _C(L)`) are
not key codes and are left alone.
"""
import json
import re
import sys
from pathlib import Path

BAD = re.compile(r"^[A-Z][A-Z0-9_]*\(")
EXPECTED_LAYOUT = Path("layout/V52-Everforest-QWERTY.json")


def walk(node, path, bad):
    if isinstance(node, dict):
        value = node.get("value")
        if isinstance(value, str) and BAD.match(value):
            bad.append(f"{path} = {value!r}")
        for key, child in node.items():
            if key != "value":
                walk(child, f"{path}/{key}", bad)
    elif isinstance(node, list):
        for i, child in enumerate(node):
            walk(child, f"{path}[{i}]", bad)


def main() -> int:
    if not EXPECTED_LAYOUT.is_file():
        print(f"required layout file missing: {EXPECTED_LAYOUT}", file=sys.stderr)
        return 1
    bad = []
    for path in sorted(Path("layout").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        layers = data.get("layers") if isinstance(data, dict) else None
        if not isinstance(layers, list) or not layers:
            print(f"{path}: layers must be a non-empty array", file=sys.stderr)
            return 1
        for li, layer in enumerate(layers):
            if not isinstance(layer, list) or not layer:
                print(f"{path}: layer {li} must be a non-empty array", file=sys.stderr)
                return 1
            for ki, key in enumerate(layer):
                walk(key, f"{path}: layer {li} index {ki}", bad)
    for line in bad:
        print(f"parenthesised modifier string in key code: {line}", file=sys.stderr)
    if bad:
        print(
            "\nRe-encode as nested params, e.g. LG(LS(S)) ->"
            ' {"value": "LG", "params": [{"value": "LS", "params": [{"value": "S"}]}]}',
            file=sys.stderr,
        )
        return 1
    print(f"ok: no parenthesised key codes in layout/*.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
