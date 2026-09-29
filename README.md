# Glove80 — V52 Everforest QWERTY

ZMK config for a MoErgo Glove80, built from the **Glorious Engrammer v52**
base ([sunaku/glove80-keymaps](https://github.com/sunaku/glove80-keymaps))
and reskinned to Everforest Dark Hard.

This repo exists so the layout can be **diffed across iterations** and so the
firmware can carry things the Layout Editor cannot express.

## Layout

| | |
|---|---|
| Layers | 31 |
| Base | QWERTY (alternate alphabets, macOS, World, emoji all removed) |
| Colors | Everforest Dark Hard |
| Editor UUID | `15da8b74-bc9e-47fe-8334-34ea6d2318dc` |

Layer families beyond stock Engrammer: an **Excel** family (Excel, Excel_WordPP,
Excel_Code, Excel_TBD) for Office/dev contexts, and a **Gaming** family (Gaming/WoW,
Maple, LoL, Gaming_TBD). Both are switched from the **Magic** layer with persistent
`&to`, using the same mechanism Engrammer uses for base-alphabet switching.

### AI control layer (layer 30, `AI_Claude`)

Hold the **right C2R6 thumb** (position 75): the **left hand** drives Claude Code
and the **right home block** drives herdr, the terminal multiplexer Claude Code
runs inside. Tapping that key is still a one-shot Right Shift, and releasing
returns to base. Ported from
[dongdongbh/glove80](https://github.com/dongdongbh/glove80).

It's a positional hold-tap: the hold resolves on the left hand plus the nine herdr
positions (28–31, 41–45) rather than the left hand alone, so Right Shift still
shifts every other right-hand key.

Slash commands are typed directly. Upstream defines `AI_VIM_COMPOSER` to prefix
them with `ESC` `I` for a Vim-mode composer — left undefined here, since Claude
Code's composer isn't Vim-mode by default. Define it if you switch.

Two deliberate omissions:

- **Codex half not installed.** It wants position 68, which here is
  `&stumb LAYER_Excel LSFT`, so it would displace the Excel thumb.
- **QWERTY only.** Maple also has a free `&kp RSHFT` at 75, but it's the
  MapleStory layer — the trigger would sit under a thumb mid-game for no gain.

### Base-layer shortcuts (positions 7–10)

| Position | Key | Output |
|---|---|---|
| 7 | Right C4R1 | Win+Shift+F |
| 8 | Right C5R1 | Win+Alt+] (`oem_6` on Windows) |
| 9 | Right C6R1 | Win+Ctrl+Right |
| 10 | Left C6R2 | F14 |

**F14 mutes through a host binding.** On Windows, use [PowerToys Keyboard
Manager](https://learn.microsoft.com/en-us/windows/powertoys/keyboard-manager)
to remap the `F14` key to `Volume Mute`; keep PowerToys running for the remap to
work. On CachyOS with Hyprland's `hyprland.conf` bind syntax, add:

```ini
bindl = , F14, exec, wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle
```

The `l` flag lets the [Hyprland bind](https://wiki.hypr.land/0.52.0/Configuring/Binds/)
work while the screen is locked; [WirePlumber's `wpctl`](https://pipewire.pages.freedesktop.org/wireplumber/man/wpctl.html)
toggles the default output sink. These bindings belong in the host configs,
outside this repo. They also make the existing F14 on the Function layer
(position 45) mute.

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

## Where this repo lives

The authoritative copy is WSL `~/Projects/glove80-config` plus GitHub. Any
OneDrive/VS Code copy is Windows-only, kept fast-forwarded from that source,
and never edited directly — see the code source-of-truth policy in
[`Schema/operator-context.md`](https://github.com/kdelacruz94/AI-Brain/blob/main/Schema/operator-context.md)
([AI-Brain#99](https://github.com/kdelacruz94/AI-Brain/pull/99)).

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

### Point the viz at the repo file, not a Downloads export

MoergoLayerViz reads a layout JSON for its key labels. Point it at **this repo's**
copy, so it never drifts from what CI flashes:

- raw URL — `https://raw.githubusercontent.com/kdelacruz94/glove80-config/main/layout/V52-Everforest-QWERTY.json`
- or the local path — `layout/V52-Everforest-QWERTY.json`

After a keymap change, refresh it by pushing the `config/glove80.keymap` +
`layout/*.json` pair (they change in the same commit — see `CLAUDE.md`) and
reloading the viz. A one-off editor export sitting in `Downloads` is not a source:
it goes stale the moment the next binding lands.
