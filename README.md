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

The base f/j keys (positions 38/41, left/right C2R4) hold Shift. Only their
active `left_index` / `right_index` behaviors receive this tuning; the other
home-row modifiers keep their existing settings.

| ZMK setting | Value | Effect |
|---|---|---|
| `flavor` | `tap-preferred` | An overlapping or nested letter tap cannot select Shift before the timer. |
| `tapping-term-ms` | 150 | Activate Shift after a short deliberate hold. |
| `require-prior-idle-ms` | 200 | A non-modifier press less than 200 ms before f/j forces a letter, even on a long hold. |
| `quick-tap-ms` | 0 | No additional same-key repeat guard. |
| `hold-trigger-key-positions` | opposite hand | Check the first other **press**, including a same-hand key held across the timeout. |
| `hold-trigger-on-release` | omitted (false) | A held same-hand letter can veto Shift before the timer expires. |

PR #10's `hold-preferred` setting selected Shift on an opposite-hand press.
PR #13's `balanced` setting instead selected Shift on an opposite-hand release:
`f-down → o-down → o-up → f-up` could still produce `O`, losing f.
With release-time position checks, `j-down → u-down → timer → j-up → u-up`
could produce `U`, losing j: no target position had been recorded when the
280 ms timer fired, even though u is on j's own hand. A prior idle over 100 ms
allowed both bugs; the old streak guard masked them only during faster typing.

The current `tap-preferred` setting prevents overlap or nested taps from
selecting Shift before the timer.
Press-time positional checks also make same-hand overlaps tap regardless of
how long f/j linger, provided the same-hand press precedes the timer.
Increasing prior idle alone cannot protect a word after a long pause.
PR #16 used 400 ms to protect longer rolls. After flashing it, deliberate
`Quality` / `Inventory` required too much waiting. The current tuning lowers
only the f/j timer to 150 ms; the PR #16 decision rule stays intact.

**Deliberate Shift:** pause at least 250 ms after the previous letter press,
hold f/j alone for **150–250 ms**, then press the target. Either release
order produces a capital. This also supports same-hand Shift and Shift-click
once Shift has activated. An f/j + letter gesture released before 150 ms
types both letters; use the deliberate hold for capitalization.

This is a timing distinction, not a way to infer intention. After a long idle,
a word-start f/j held **at least 150 ms** can now select Shift where 400 ms
previously kept a letter. An opposite-hand target pressed before the timer
can capitalize when f/j remains down across it, even if the target releases
first. A same-hand target only vetoes Shift if its press precedes 150 ms.
For example, a slow `for` can become `Or` or `OR`; `just` can become `Ust`
when u arrives at or after 150 ms. The f/j disappears in these cases; a long
standalone hold released before the target can also lose f/j without a capital.
Rolls that release f/j before 150 ms stay lowercase in either release order.
The replay keeps the 60–180 ms inter-key gaps and f/j dwells through 320 ms,
with explicit expectations for these newly capitalized or missing-letter cases.

The behavior was checked against the [pinned MoErgo hold-tap source](https://github.com/moergo-sc/zmk/blob/ce69e85f585c724142aae37ddf8a7e019ff19e93/app/src/behaviors/behavior_hold_tap.c)
and its [matching documentation](https://github.com/moergo-sc/zmk/blob/ce69e85f585c724142aae37ddf8a7e019ff19e93/docs/docs/keymaps/behaviors/hold-tap.mdx).
Run `python3 scripts/check_home_row_shift.py` to replay the actual pinned C
implementation with host event/timer adapters. It downloads that immutable
source, checks its SHA256, and reads the keymap's active settings and position
lists; it also checks the JSON's f/j behavior copies. An offline source copy
can be supplied with `--source <behavior_hold_tap.c>`. The replay excludes other
behaviors, transport/scanning, Zephyr scheduling, and real HID reports; both CI
firmware builds and keyboard testing are still required.

After flashing **each half's matching UF2**, test in a plain text editor:

1. Pause at least half a second, hold j alone for 150–250 ms, and type
   `Quality`; repeat with f for `Inventory`. Expect no leading j/f. Try both
   release orders; also check f + r / j + u after the hold and Shift-click.
2. Type `for just of` at normal speed; expect lowercase words with every f/j.
   Repeat slower after a pause to check the 150 ms tradeoff described above.
3. Overlap f→o and j→w, releasing f/j before 150 ms in each release order:
   expect `fo` and `jw`. Overlap j→u and f→r with the target held beyond the
   timer: expect `ju` and `fr` if the target was pressed before 150 ms.
4. Type `of off if` rapidly; expect the exact lowercase text. Check ordinary
   Ctrl/Alt/Super shortcuts too.

The calibration knobs are `HRM_SHIFT_TAPPING_TERM_MS` (150) and
`HRM_SHIFT_PRIOR_IDLE_MS` (200) near the top of the keymap and in the JSON's
`custom_defined_behaviors`. Synchronize both files, rebuild, and repeat the
checklist after any adjustment.

### Win+Space

On Windows, both home-row pinkies hold **LGUI** (Win); the middle fingers hold
Ctrl. Hold Win alone for at least 300 ms before testing shortcuts. The left
pinky's opposite-hand position list includes every right thumb, including
Space at position 74 (`KEY_RH_T4`).

Space normally taps Space or holds Symbol after 200 ms. That timer also used
to select Symbol with Win held, consuming a lingering Win+Space without sending
Space to the host. `&win_space` now uses
[mod-morph with `keep-mods`](https://github.com/moergo-sc/zmk/blob/ce69e85f585c724142aae37ddf8a7e019ff19e93/docs/docs/keymaps/behaviors/mod-morph.md#keep-mods)
to send Space immediately while LGUI is active, retaining Win for the host's
Win+Space → LWin+LAlt+P remap. Ordinary Space/Symbol and f/j tuning are unchanged.

After flashing both matching UF2s on the Windows work desktop:

1. Hold a Win pinky for 300 ms, then press Space. Test a quick tap and a
   350 ms press, with both release orders. Repeat with the other Win pinky.
   Expect the action bound to LWin+LAlt+P each time, without Symbol activation.
2. Test Win+E (Explorer), Win alone (Start), and Space alone (a space).
   Without Win, hold Space and type a symbol to confirm Symbol access.
3. Pause at least half a second before each word, then type `first` and `just`
   quickly several times. Expect exactly those lowercase words, without
   missing f/j or stray capitals.

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
5. Flash `raw_hid_adapter-glove80_lh-zmk.uf2` to the **left** half and `glove80_rh-zmk.uf2` to the
   **right**. Unlike the editor's combined download, these are **per-half — do not
   flash the same file to both.**

If you export a new layout (new UUID), update `CONFIG_HID_VIZ_CONFIG_ID` to match.

## Pinned firmware builds and provenance

`config/west.yml` pins the known-green source graph from
[run 37090566575](https://github.com/kdelacruz94/glove80-config/actions/runs/37090566575),
including imported Zephyr and the Raw HID static-buffer fix. The Zephyr override
retains MoErgo's imports and exclusions; top-level definitions take precedence
under [West's import rules](https://docs.zephyrproject.org/latest/develop/west/manifest.html#manifest-import-details).
Dependency upgrades are reviewed manifest edits. CI rejects floating revisions
throughout the resolved graph and active checkouts that differ from their pins.

`.github/workflows/build.yml` owns the compatible MoErgo build commands at
`ce69e85f585c724142aae37ddf8a7e019ff19e93`, pins every action to a full SHA,
and uses the baseline compiler image by digest for matrix parsing and compilation.
The hosted Ubuntu runner, Docker execution, and artifact service remain external
infrastructure. These pins establish input identity; byte-identical firmware has
not been demonstrated. Compare UF2 checksums before claiming reproducibility.

Each downloaded `firmware` archive includes both board-specific UF2s,
`SHA256SUMS`, and a `provenance-<board>.json` for each half. Metadata records the
config commit, workflow ref/SHA/file hash, action SHAs, container digest, board and
shield, tool versions, run ID/attempt/URL, source graph hashes, and UF2 checksum.
`west-frozen-<board>.yml` freezes actual active checkouts;
`west-resolved-<board>.yml` also records pinned optional projects disabled by West's
group filters. CI compares both graphs and the build identities between halves
before publishing the final archive; either missing UF2 fails packaging.

After extracting an archive, verify its UF2s with `sha256sum -c SHA256SUMS`.
To also check metadata, both graphs, and agreement between halves, run
`python3 scripts/firmware_provenance.py verify <extracted-directory>` from this repo.
Local checks are `python3 scripts/check_layout_json.py`,
`python3 -m unittest discover -s scripts -p 'test_*.py'`, and `actionlint` when installed.
The actual firmware acceptance check remains the two CI board builds.

## Two traps worth remembering

**Build from MoErgo's fork, not upstream ZMK.** The `glove80_lh` / `glove80_rh`
boards exist only in `moergo-sc/zmk`. The build commands must retain MoErgo's compatible
workflow path — `zmkfirmware/zmk@main` has moved to Zephyr 4.1 hardware-model-v2 and dies
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
