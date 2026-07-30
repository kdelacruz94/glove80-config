# Glove80 — V52 Everforest QWERTY

ZMK config for a MoErgo Glove80, built from the **Glorious Engrammer v52**
base ([sunaku/glove80-keymaps](https://github.com/sunaku/glove80-keymaps))
and reskinned to Everforest Dark Hard.

This repo exists so the layout can be **diffed across iterations** and so the
firmware can carry things the Layout Editor cannot express.

## Layout

| | |
|---|---|
| Layers | 30 |
| Base | QWERTY (alternate alphabets, macOS, World, emoji all removed) |
| Colors | Everforest Dark Hard |
| Editor UUID | `15da8b74-bc9e-47fe-8334-34ea6d2318dc` |

Layer families beyond stock Engrammer: an **Excel** family (Excel, Excel_WordPP,
Excel_Code, Excel_TBD) for Office/dev contexts, and a **Gaming** family (Gaming/WoW,
Maple, LoL, Gaming_TBD). Both are switched from the **Magic** layer with persistent
`&to`, using the same mechanism Engrammer uses for base-alphabet switching.

## Files

| Path | What it is |
|---|---|
| `config/glove80.keymap` | The keymap. **This is the diff surface** — real DTS, diffs line by line. |
| `layout/*.json` | The Layout Editor export. Feeds [MoergoLayerViz](https://github.com/ovandongen/moergo-layer-viz). |
| `config/glove80.conf` | Kconfig: pointing, Raw HID, visualizer config ID. |
| `config/west.yml` | Firmware source + modules. |
| `build.yaml` | Board/shield matrix. |

The `.json` is pretty-printed, so key bindings, layer names, combos and macros all
diff line by line. Two lines are the exception and will show as whole-line churn:

| Line | Field | Size |
|---|---|---|
| 30 | `custom_defined_behaviors` | ~342 KB |
| 31 | `custom_devicetree` | ~23 KB |

That's where the Engrammer hold-taps, combos and RGB indicator blocks live. When a
change lands in either, read `config/glove80.keymap` instead — it carries the same
content as real DTS and diffs properly.

## Workflow

1. Edit in the [Layout Editor](https://my.glove80.com).
2. Export **both** the `.keymap` and the `.json`.
3. Drop them in as `config/glove80.keymap` and `layout/<name>.json`, commit, push.
4. CI builds; download `firmware` from the run's artifacts.
5. Flash `glove80_lh-zmk.uf2` to the **left** half and `glove80_rh-zmk.uf2` to the
   **right**. Unlike the editor's combined download, these are **per-half — do not
   flash the same file to both.**

If you export a new layout (new UUID), update `CONFIG_HID_VIZ_CONFIG_ID` to match.

## Two traps worth remembering

**Build from MoErgo's fork, not upstream ZMK.** The `glove80_lh` / `glove80_rh`
boards exist only in `moergo-sc/zmk`. The reusable workflow must also be MoErgo's
copy — `zmkfirmware/zmk@main` has moved to Zephyr 4.1 hardware-model-v2 and dies
with `KeyError: 'qualifiers'` on these boards, after compiling most of the tree.
MoErgo's own template repo still points at zmkfirmware and is stale for this reason;
the config that actually builds green is
[ovandongen/glove80-zmk-config-west](https://github.com/ovandongen/glove80-zmk-config-west).

**`&kp` shift is `LSHFT`/`RSHFT`.** `LSFT`/`RSFT` are modifier-application tokens,
valid only inside compound bindings like `&mt RSFT X` or `LS(...)`. A standalone
`&kp RSFT` fails editor validation. When writing new bindings, copy keycode tokens
from existing valid ones in this file rather than guessing.

## Visualizer

On-screen layer tracking needs the Raw HID endpoint (usage page `0xFF60`, usage
`0x61`), which **stock editor-built firmware does not expose** — hence the
`zmk-raw-hid` + `zmk-hid-viz` modules and the `raw_hid_adapter` shield on the
central (left) half. Firmware from this repo supports MoergoLayerViz v2.x; editor
firmware is limited to v1.2.4, which is one-way and cannot track layers.

`zmk-raw-hid` is pulled from **ovandongen's fork**, not zzeneg upstream, for a
static-HID-report-buffer fix that upstream lacks.
