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

### Home-row Shift (f/j)

The base f/j keys (positions 38/41, left/right C2R4) hold Shift. Their active
`left_index` / `right_index` behaviors use dedicated tuning; other home-row
modifiers and layer bindings keep their existing settings.

| ZMK setting | Before → after | Reason |
|---|---|---|
| `flavor` | `tap-preferred` → `hold-preferred` | Shift resolves when the opposite-hand key goes down, even if f/j is released first. |
| `hold-trigger-on-release` | enabled → omitted (false) | Check the existing opposite-hand position list on press, protecting same-hand rolls. |
| `quick-tap-ms` | 300 → 0 | A recent f/j tap no longer forces the next use to be a letter. |
| `require-prior-idle-ms` | 150 → 100 | Shorten the capitalization lockout while retaining protection during typing streaks. |
| `tapping-term-ms` | 180 → 180 | Preserve standalone Shift and deliberate same-hand Shift timing. |

This adapts the positional protection in [urob's timer-less HRMs](https://github.com/urob/zmk-config#timeless-homerow-mods)
for Shift-first release order, using [ZMK's interrupt flavors](https://zmk.dev/docs/keymaps/behaviors/hold-tap#interrupt-flavors)
and [positional hold-tap](https://zmk.dev/docs/keymaps/behaviors/hold-tap#positional-hold-tap-and-hold-trigger-key-positions).
`balanced` still requires the other key to be released first. In this MoErgo
fork, `hold-preferred` with release-time position checks can commit a hold before
checking the position, so these two behaviors check on press instead. This also
means same-hand multi-mod chords starting with f/j need a 180 ms hold first.

After flashing **each half's matching UF2**, test in a plain text editor:

1. From idle, press f, press y/u/n, release f first, release the other key;
   repeat rapidly. Expect `Y U N`, with no extra f. Mirror with j + q/w/v:
   expect `Q W V`, with no extra j. Also try the other key's release first.
2. Tap f, wait about 200 ms, use f + y as above; expect `fY`. Mirror j + q:
   expect `jQ`. Type `a`, wait about 120 ms, then f + y; expect `aY`.
3. Type `fj fjord fluffy jiffy jazz` at normal speed, including overlapping
   f→r and j→u rolls. Expect lowercase text without accidental capitals.
4. Hold f/j alone for over 180 ms before using a same-hand letter or Shift-click;
   expect Shift. A short isolated f/j tap must still type its letter.

The calibration knob is `HRM_SHIFT_PRIOR_IDLE_MS` near the top of the keymap
(and in the JSON's `custom_defined_behaviors`): reduce 100 to 80 if cross-hand
capitalization during typing still emits f/j; raise it to 120 for accidental
capitals or noticeable f/j tap delay. Below 100 ms, the current typing-streak
guard deliberately produces a letter. Rebuild after changing the knob.

### Terminal layer (layer 30, `Terminal`)

Hold the **right C2R6 thumb** (position 75): the **left hand** sends herdr actions
(`ctrl+b` prefix, then the key) and the **right hand** sends the terminal emulator
chords that WezTerm and kitty share. Tapping that key is still a one-shot Right
Shift, and releasing returns to base. The chord contract lives in
[terminal-config `docs/glove80-terminal-layer-chords.md`](https://github.com/kdelacruz94/terminal-config/blob/main/docs/glove80-terminal-layer-chords.md);
this layer only maps keys to it. Replaces the round-2 `AI_Claude` layer (Claude Code
slash-command keys removed).

| Position | Key | Sends |
|---|---|---|
| 11-15 | Left C5-C1 R2 | herdr new tab `c` · close tab `shift+x` · split side `v` · split below `minus` · pane zoom `z` |
| 24-27 | Left C4-C1 R3 | herdr focus pane left/down/up/right `h` `j` `k` `l` |
| 35-38 | Left C5-C2 R4 | herdr previous/next workspace `shift+h` `shift+l` · previous/next tab `p` `n` |
| 47-51 | Left C5-C1 R5 | herdr workspace picker `w` · goto `g` · last pane `a` · next/prev agent `shift+j` `shift+k` |
| 28-32 | Right C1-C5 R3 | copy `ctrl+shift+c` · paste `ctrl+shift+v` · scrollback search `ctrl+shift+f` · clear `ctrl+shift+k` · new window `ctrl+shift+n` |
| 40-44 | Right C1-C5 R4 | page up/down `ctrl+shift+page_up/down` · font bigger/smaller/reset `ctrl+=` `ctrl+-` `ctrl+0` |
| 4 | Left C2R1 | `F13` dictation, unchanged |

Left C4R1 / C3R1 (base positions 2, 3) stay `&none`, reserved for PIP/PBP. System-layer
app keys are deferred.

The hold resolves on the left hand plus the ten emulator positions (28-32, 40-44), so
Right Shift still shifts every other right-hand key.

### Base-layer first row (positions 0–4)

| Position | Key | Output | Needs a host binding |
|---|---|---|---|
| 0 | Left C6R1 | Win+Ctrl+Alt+F11 | yes — monitor input → DisplayPort |
| 1 | Left C5R1 | Win+Ctrl+Alt+F12 | yes — monitor input → USB-C |
| 2 | Left C4R1 | `&none` (reserved for PIP/PBP) | — |
| 3 | Left C3R1 | `&none` (reserved for PIP/PBP) | — |
| 4 | Left C2R1 | Win+Shift+S | native on Windows; on CachyOS/Hyprland bind the chord to `grim`/`slurp` or `hyprshot` |

### Base-layer shortcuts (positions 5–10)

| Position | Key | Output |
|---|---|---|
| 5 | Right C2R1 | herdr last pane (Ctrl+B, `a`) |
| 6 | Right C3R1 | Win+Ctrl+Left — previous workspace |
| 7 | Right C4R1 | Win+Shift+F |
| 8 | Right C5R1 | Win+Alt+] (`oem_6` on Windows) |
| 9 | Right C6R1 | Win+Ctrl+Right |
| 10 | Left C6R2 | Ctrl+B — the herdr prefix, as a plain tap |

Position 10 is just the prefix: tap it, then press the herdr action key. It needs no
host binding. Mute lives on the **Function** layer (position 45, `F14`) and still
needs one — on Windows remap `F14` to `Volume Mute` with [PowerToys Keyboard
Manager](https://learn.microsoft.com/en-us/windows/powertoys/keyboard-manager)
(PowerToys must stay running); on CachyOS add this to
`terminal-config/cachyos/desktop/hypr/config/keybinds.lua`:

```lua
hl.bind("F14", hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle"))
```

[WirePlumber's `wpctl`](https://pipewire.pages.freedesktop.org/wireplumber/man/wpctl.html)
toggles the default output sink. These bindings belong in the host configs, outside
this repo.

### Monitor input switching — host setup

Positions 0 and 1 are **absolute**, not a toggle: each one sets the monitor to one
fixed input, so the same key does the same thing from either machine. Set both up on
**each** machine that drives the monitor (work desktop and work laptop).

1. Put [ControlMyMonitor](https://www.nirsoft.net/utils/control_my_monitor.html)
   (portable, no installer) in `%LOCALAPPDATA%\ControlMyMonitor\ControlMyMonitor.exe`.
2. Read the input values **once**, with the monitor on each input in turn:
   `ControlMyMonitor.exe /GetValue "<monitor-id>" 60` — VCP code `0x60` is
   *Input Select*. Note the number for DisplayPort and the number for USB-C; they are
   monitor-specific (commonly `15` for DP and `27` for USB-C, but do not assume).
   `ControlMyMonitor.exe /smonitors` lists monitor IDs.
3. Create two `.cmd` scripts next to the exe, substituting the values from step 2:

   ```bat
   rem monitor-dp.cmd
   "%LOCALAPPDATA%\ControlMyMonitor\ControlMyMonitor.exe" /SetValue Primary 60 15
   ```

   ```bat
   rem monitor-usbc.cmd
   "%LOCALAPPDATA%\ControlMyMonitor\ControlMyMonitor.exe" /SetValue Primary 60 27
   ```

4. In **PowerToys Keyboard Manager → Remap a shortcut**, add two entries of type
   *Run program*:

   | Shortcut | Runs |
   |---|---|
   | Win+Ctrl+Alt+F11 | `monitor-dp.cmd` |
   | Win+Ctrl+Alt+F12 | `monitor-usbc.cmd` |

   PowerToys must stay running for these to work.

This replaces the round-2 single toggle key (Win+Ctrl+Alt+F12 on the System layer),
which asked the host script to guess which input to move to.

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
