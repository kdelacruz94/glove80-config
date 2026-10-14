#!/usr/bin/env python3
"""Semantic checks the firmware compiler cannot make: layer shape, export sync,
UUID agreement, persistent-mode recovery and overlay precedence.

Per-key RGB presence needs the generated devicetree, so scripts/check_rgb_build.py
checks it after each board build instead.

The layer model follows ZMK: the highest active layer with a non-`&trans`
binding wins, `&to N` leaves only the default layer and N, and a combo fires
only when its `layers` list holds the highest active layer.

Findings that a sibling card has not fixed yet are listed in PENDING. A pending
finding is reported but does not fail; a pending entry that no longer fires
does fail, so the fixing card must delete its entry and the check turns on.
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KEYMAP = "config/glove80.keymap"
LAYOUT = "layout/V52-Everforest-QWERTY.json"
CONF = "config/glove80_lh.conf"
README = "README.md"
POSITIONS = 80
MAX_HELD = 2  # momentary layers held at once while searching for a way out

HOME_ROW = ("LeftPinky", "LeftRingy", "LeftMiddy", "LeftIndex",
            "RightIndex", "RightMiddy", "RightRingy", "RightPinky")
PENDING = {
    # Card 2 (precedence): a base numbered above the overlays it inherits masks them.
    **{f"precedence:{overlay}<Excel": "card 2" for overlay in HOME_ROW},
    **{f"precedence:{overlay}<Maple": "card 2"
       for overlay in HOME_ROW[4:] + ("Lower", "System", "Mouse", "Magic")},
    **{f"precedence:Typing<{base}": "card 2" for base in ("Gaming", "Excel", "Lower", "Maple")},
}


class Keymap:
    def __init__(self, text):
        self.text = text
        self.layers = {}
        for name, index in re.findall(r"^#define LAYER_(\w+) (\d+)$", text, re.M):
            self.layers.setdefault(name, int(index))
        self.names = sorted(self.layers, key=self.layers.get)
        self.defines = {}
        for name, value in re.findall(r"^\s*#define (\w+)[ \t]+(.+)$", text.replace("\\\n", " "), re.M):
            self.defines.setdefault(name, value.split("//")[0].strip())
        keymap = text.split("/* Automatically generated keymap */", 1)[-1]
        self.bindings = {
            name: split_bindings(body)
            for name, body in re.findall(r"layer_(\w+) \{\s*bindings = <(.*?)>;", keymap, re.S)
        }
        self.hold_mo = {
            label for label, body in re.findall(r"(\w+): \w+ \{([^{}]*)\}", text)
            if "zmk,behavior-hold-tap" in body and re.search(r"bindings = <&mo>", body)
        }
        self.combos = [
            (set(map(self.layer, self.expand(layers.split()))) if layers else None, binding)
            for binding, layers in combos(text)
        ]

    def expand(self, tokens):
        """Replace object-like macros (such as named combo layer groups) by their tokens."""
        out = []
        for token in tokens:
            value = self.defines.get(token)
            out += self.expand(value.split()) if value and not token.startswith("LAYER_") else [token]
        return out

    def layer(self, token):
        token = self.defines.get(token, token) if token.startswith("LAY_") else token
        if token.isdigit():
            return int(token)
        if token.startswith("LAYER_") and token[6:] in self.layers:
            return self.layers[token[6:]]
        return None

    def actions(self, binding):
        """Layer actions of one binding: ("to"|"tog"|"mo", layer index)."""
        name, *args = re.split(r"[\s(),]+", binding.strip().rstrip(")"))
        name = name[1:]
        first = self.layer(args[0]) if args else None
        if name in ("to", "tog") and first is not None:
            return [(name, first)]
        if name == "lower":  # tap-dance: tap is &mo, double tap is &to
            return [("mo", self.layers["Lower"]), ("to", self.layers["Lower"])]
        if name in self.layers:  # home-row macros hold their own layer
            return [("mo", self.layers[name])]
        if (name in self.hold_mo or name in ("mo", "sl")) and first is not None:
            return [("mo", first)]
        return [("mo", layer) for layer in map(self.layer, args) if layer is not None]


def split_bindings(body):
    return [" ".join(b.split()) for b in re.split(r"(?=&)", body) if b.strip()]


def combo_blocks(text):
    """Each `combos` node, with #ifdef branches of never-defined macros removed."""
    defined = set(re.findall(r"^\s*#define (\w+)", text, re.M))
    for start in (m.start() for m in re.finditer(r"\bcombos \{", text)):
        depth, end = 0, start
        for end in range(start, len(text)):
            depth += {"{": 1, "}": -1}.get(text[end], 0)
            if depth == 0 and text[end] == "}":
                break
        out, stack = [], []
        for line in text[start:end].splitlines():
            directive = re.match(r"\s*#\s*(ifdef|ifndef|if|else|elif|endif)\b(.*)", line)
            if not directive:
                if all(stack):
                    out.append(line)
                continue
            kind, rest = directive.groups()
            if kind == "endif":
                stack.pop()
            elif kind == "else":
                stack[-1] = not stack[-1]
            elif kind in ("ifdef", "ifndef"):
                stack.append((rest.split()[0] in defined) == (kind == "ifdef"))
            elif kind == "if" and re.fullmatch(r"[\s()!&|]*(defined\(\w+\)[\s()!&|]*)+", rest):
                expr = re.sub(r"defined\((\w+)\)", lambda m: f" {m[1] in defined} ", rest)
                stack.append(eval(expr.replace("&&", " and ").replace("||", " or ").replace("!", " not ")))
            else:
                raise ValueError(f"unsupported conditional in combos: {line.strip()}")
        yield "\n".join(out)


def combos(text):
    for block in combo_blocks(text):
        for body in re.findall(r"\{([^{}]*key-positions[^{}]*)\}", block):
            binding = re.search(r"bindings = <([^>]*)>", body)
            layers = re.search(r"layers = <([^>]*)>", body)
            yield binding[1], layers[1] if layers else ""


def resolve(km, active, position):
    for layer in sorted(active, reverse=True):
        binding = km.bindings[km.names[layer]][position]
        if binding != "&trans":
            return layer, binding
    return 0, "&none"


def moves(km, persistent, held):
    """Every (persistent, held) state one key press or combo away."""
    active = persistent | held
    presses = [resolve(km, active, p)[1] for p in range(POSITIONS)]
    top = max(active)
    presses += [b for layers, b in km.combos if layers is None or top in layers]
    for binding in presses:
        for kind, layer in km.actions(binding):
            if kind == "to":
                yield frozenset({0, layer}), frozenset()
            elif kind == "tog" and layer != 0 and layer not in held:
                yield persistent ^ {layer}, held
            elif kind == "mo" and layer not in active and len(held) < MAX_HELD:
                yield persistent, held | {layer}
    if held:
        yield persistent, frozenset()


def explore(km):
    start = (frozenset({0}), frozenset())
    edges, todo = {}, [start]
    while todo:
        state = todo.pop()
        if state in edges:
            continue
        edges[state] = set(moves(km, *state))
        todo.extend(edges[state] - edges.keys())
    return edges


def check_recovery(km, edges):
    reverse = {}
    for state, nexts in edges.items():
        for n in nexts:
            reverse.setdefault(n, set()).add(state)
    home = (frozenset({0}), frozenset())
    safe, todo = set(), [home]
    while todo:
        state = todo.pop()
        if state not in safe:
            safe.add(state)
            todo.extend(reverse.get(state, ()))
    stuck = {max(p) for p, h in edges if not h and (p, h) not in safe}
    for layer in sorted(stuck):
        yield f"recovery:{km.names[layer]}", "no key sequence returns this persistent mode to QWERTY"
    modes = {max(p) for p, h in edges if not h} - {0}
    resets = [layers for layers, b in km.combos if ("to", 0) in km.actions(b)]
    for layer in sorted(modes):
        if not any(layers is None or layer in layers for layers in resets):
            yield f"reset-combo:{km.names[layer]}", "no `&to 0` emergency combo covers this mode"


def check_precedence(km, edges):
    """An overlay held from a persistent base must not be masked by that base.

    Bases are the layers a `&to` selects; a toggled overlay is not a base.
    """
    targets = [b for layer in km.bindings.values() for b in layer]
    targets += [b for _, b in km.combos]
    bases = {layer for b in targets for kind, layer in km.actions(b) if kind == "to"}
    seen = set()
    for persistent, held in edges:
        base = max(persistent)
        if len(persistent) != 2 or base not in bases:
            continue
        for overlay in sorted(held):
            masked = [p for p in range(POSITIONS) if overlay < base
                      and km.bindings[km.names[overlay]][p] != "&trans"
                      and km.bindings[km.names[base]][p] != "&trans"]
            if masked and (overlay, base) not in seen:
                seen.add((overlay, base))
                yield (f"precedence:{km.names[overlay]}<{km.names[base]}",
                       f"{km.names[overlay]} held from {km.names[base]} is masked at positions {masked}")


def render(node, layer_names):
    value = node["value"]
    if isinstance(value, int):
        return str(value)
    if value == "Custom":
        return node["params"][0]["value"]
    params = [render(p, layer_names) for p in node.get("params", [])]
    if value == "&magic":
        return f"&magic {layer_names.index('Magic')} 0"
    if value == "&reset":
        return "&sys_reset"
    if not value.startswith("&"):
        return f"{value}({','.join(params)})" if params else str(value)
    return " ".join([value, *params])


def normalize(binding, km):
    tokens = re.findall(r"LAYER_\w+|\w+|[^\w\s]", binding)
    return " ".join(str(km.layer(t)) if t.startswith("LAYER_") and km.layer(t) is not None else t
                    for t in tokens)


SECTIONS = {
    "custom_devicetree": ("/* Custom Device-tree */\n", "\n\n/* Input Listeners */"),
    "custom_defined_behaviors": ("/* Custom Defined Behaviors */\n/ {\n",
                                 "\n};\n\n/* Generated input processors */"),
}


def section(text, before, after):
    start = text.find(before)
    end = text.find(after, start)
    return text[start + len(before):end] if 0 <= start < end else None


def check_shape(km, export):
    if export["layer_names"] != km.names:
        yield "layer-names", f"export {export['layer_names']} != keymap defines {km.names}"
    if list(km.bindings) != km.names:
        yield "layer-blocks", f"keymap layer blocks {list(km.bindings)} != defines {km.names}"
    for name, layer in zip(export["layer_names"], export["layers"]):
        if len(layer) != POSITIONS:
            yield f"bindings:json:{name}", f"export layer {name} has {len(layer)} bindings"
    for name, bindings in km.bindings.items():
        if len(bindings) != POSITIONS:
            yield f"bindings:keymap:{name}", f"keymap layer {name} has {len(bindings)} bindings"


def check_sync(km, export):
    names = export["layer_names"]
    for name, layer in zip(names, export["layers"]):
        for p, (node, binding) in enumerate(zip(layer, km.bindings.get(name, []))):
            if normalize(render(node, names), km) != normalize(binding, km):
                yield (f"sync:{name}:{p}",
                       f"{name} position {p}: export {render(node, names)!r} != keymap {binding!r}")
    for field, (before, after) in SECTIONS.items():
        if section(km.text, before, after) != export[field]:
            yield f"custom:{field}", f"export {field} differs from the keymap text after {before.strip()!r}"
    generated = section(km.text, "/* Automatically generated combos definitions */",
                        "/* Automatically generated keymap */") or ""
    positions = {f"POS_{m[0]}": m[1] for m in re.findall(r"#define POS_(\w+) (\d+)", km.text)}
    keymap_combos = {
        name: (" ".join(positions.get(t, t) for t in keys.split()), normalize(binding, km),
               " ".join(str(km.layer(t)) for t in layers.split()))
        for name, keys, binding, layers in re.findall(
            r"combo_(\w+) \{\s*key-positions = <([^>]*)>;\s*bindings = <([^>]*)>;\s*layers = <([^>]*)>",
            generated)
    }
    export_combos = {
        c["name"]: (" ".join(map(str, c["keyPositions"])), normalize(render(c["binding"], names), km),
                    " ".join(map(str, c["layers"])))
        for c in export["combos"]
    }
    if keymap_combos != export_combos:
        yield "sync:combos", f"export combos {export_combos} != keymap {keymap_combos}"
    macros = section(km.text, "/* Automatically generated macro definitions */",
                     "/* Automatically generated behavior definitions */") or ""
    keymap_macros = set(re.findall(r'label = "(&\w+)";', macros))
    export_macros = {m["name"] for m in export["macros"]}
    if keymap_macros != export_macros:
        yield "sync:macros", f"export macros {sorted(export_macros)} != keymap {sorted(keymap_macros)}"


def check_uuid(export, conf, readme):
    found = {
        "layout": export.get("uuid"),
        CONF: (re.findall(r'^CONFIG_HID_VIZ_CONFIG_ID="([^"]*)"', conf, re.M) or [None])[0],
        README: (re.findall(r"\| Editor UUID \| `([^`]*)` \|", readme) or [None])[0],
    }
    if len(set(found.values())) != 1 or None in found.values():
        yield "uuid", f"layout UUIDs disagree: {found}"


def findings(root):
    km = Keymap((root / KEYMAP).read_text(encoding="utf-8"))
    export = json.loads((root / LAYOUT).read_text(encoding="utf-8"))
    yield from check_shape(km, export)
    yield from check_uuid(export, (root / CONF).read_text(encoding="utf-8"),
                          (root / README).read_text(encoding="utf-8"))
    if any(len(b) != POSITIONS for b in km.bindings.values()) or list(km.bindings) != km.names:
        return  # the layer model needs a well-formed keymap
    yield from check_sync(km, export)
    edges = explore(km)
    yield from check_recovery(km, edges)
    yield from check_precedence(km, edges)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    found = dict(findings(args.root))
    for key in sorted(found):
        if key in PENDING:
            print(f"pending ({PENDING[key]}): {key}: {found[key]}")
    failed = sorted(set(found) - set(PENDING))
    stale = [] if failed else sorted(set(PENDING) - set(found))  # judge stale on a clean model
    for key in failed:
        print(f"FAIL {key}: {found[key]}", file=sys.stderr)
    for key in stale:
        print(f"FAIL {key}: fixed; delete its PENDING entry ({PENDING[key]}) "
              "so the check stays on", file=sys.stderr)
    if failed or stale:
        return 1
    print(f"ok: semantic checks pass ({len(PENDING)} pending findings for sibling cards)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
