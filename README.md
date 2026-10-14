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
| Colors | Everforest Dark Hard palette; per-key RGB unsupported by current firmware |
| Editor UUID | `15da8b74-bc9e-47fe-8334-34ea6d2318dc` |

Layer families beyond stock Engrammer: an **Excel** family (Excel, Excel_WordPP,
Excel_Code, Excel_TBD) for Office/dev contexts, and a **Gaming** family (Gaming/WoW,
Maple, LoL, Gaming_TBD). Both are switched from the **Magic** layer with persistent
`&to`, using the same mechanism Engrammer uses for base-alphabet switching.

Only Excel, Gaming/WoW and Maple are selectable today. Excel_WordPP, Excel_Code,
Excel_TBD, LoL and Gaming_TBD are still all-`&none` placeholders, so their Magic
selectors are `&none` until each layer gets bindings; the layers stay in place so
layer numbers do not shift. Restore the selector in the same change that fills the
layer.

**Emergency return to QWERTY:** press the three upper thumb keys of either hand
together (T1+T2+T3) to run `&to 0` from any layer, 0-30. In Maple this is the
only keyboard-alone escape: Maple sits above Magic, so the Magic key cannot reach
Magic's QWERTY key there.

### Everforest RGB firmware decision

The retained Everforest layer/modifier color block is **not active** on the pinned
MoErgo firmware, [ce69e85f585c724142aae37ddf8a7e019ff19e93](https://github.com/moergo-sc/zmk/tree/ce69e85f585c724142aae37ddf8a7e019ff19e93/app).
It lacks `rgb_colors.h`, the `zmk,underglow-layer` binding and per-key driver.
Ordinary underglow support does not implement these layer/modifier colors.
The keymap and editor export now warn during preprocessing rather than silently
omitting the block. CI's `scripts/check_rgb_build.py` checks each half's actual
`zephyr.dts` and `.config`, emits a warning and job summary for missing firmware
support, and rejects supported firmware that omits the node or disables its driver.
A source-level RGB presence check must distinguish this explicit deferral from
effective support; an unpreprocessed block does not prove it reached firmware.

Firmware candidates inspected on 2026-10-13 against both pinned HID modules:

| Revision | Source evidence and result |
|---|---|
| Current MoErgo pin `ce69e85f585c724142aae37ddf8a7e019ff19e93` | Known green for both HID modules; lacks per-key RGB implementation. |
| [PR36 head in darknao/zmk, `db2ba9fcd3dec4c7afcf171f123585a9f8292595`](https://github.com/darknao/zmk/tree/db2ba9fcd3dec4c7afcf171f123585a9f8292595/app) | Has the header, binding and driver; relevant ZMK HID/event APIs and imported West manifest match the current pin. Candidate for both HID modules by source inspection; a full two-half build with this config is still unproven. |
| [Historical MoErgo `aca523dfce9b6447ffd19d833b791d44f1f286de`](https://github.com/moergo-sc/zmk/tree/aca523dfce9b6447ffd19d833b791d44f1f286de/app) | The old keymap citation supplies legacy palette values, not the required per-key header/driver. |
| [Superseded PR30](https://github.com/moergo-sc/zmk/pull/30) | Uses an older raw-array RGB format incompatible with this block's `&ug` bindings; lacks the BLE active-profile API required by the pinned Raw HID module. |

[PR36 remains experimental and unmerged](https://github.com/moergo-sc/zmk/pull/36).
Its candidate preserves the HID APIs but lacks the current pin's input workqueue
fixes and changes split transport. Source inspection is not a hardware or build
compatibility claim. No revision or RGB flag has been changed.

**Decision: defer Everforest per-key RGB and keep the current known-green
firmware.** A trial of the PR36 candidate with both HID modules or a forward port
onto current firmware are separate follow-ups requiring approval and validation.
An approved RGB implementation must produce `underglow-layer` in each generated
devicetree and enable both `CONFIG_ZMK_RGB_UNDERGLOW` and
`CONFIG_EXPERIMENTAL_RGB_LAYER`. Preserve both boards' brightness safety ceiling
of **80**, step/minimum **4**, and initial brightness **16**; do not raise the
ceiling to compensate for palette changes. RGB colors, layer/modifier indicators,
brightness, split synchronization and battery behavior still require a hand test
after flashing both matching UF2s.

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

#### Thumb timing and Shift

The former AI thumb uses a balanced hold-tap: a 200 ms hold selects Terminal;
the tap sends sticky one-shot Right Shift (expires after 500 ms unused).
The positional trigger list is the left hand plus the ten emulator positions
(28-32, 40-44). With `hold-trigger-on-release`, a right-hand key outside that
list must **release before the 200 ms timer** to force the Shift tap. The list
does not prevent a standalone long hold from activating Terminal. Once Terminal
is active, its `&none` keys swallow presses instead of producing shifted letters
(for example, N at position 58). Even a same-hand key pressed before the timer
can be swallowed if it remains held across the timer.

For ordinary held Shift, use the dedicated left C6R5 key (position 46): tap for
sticky one-shot Left Shift, hold at least 200 ms for traditional Left Shift.
It has no layer action. The f/j home-row Shifts are another option; their
150 ms timer and prior-idle requirements are described [above](#home-row-shift-fj).

These are expected outcomes from the configured behavior and pinned hold-tap
implementation; physical keyboard confirmation is still required. Start each
isolated test on QWERTY with no modifiers held and at least 300 ms since the
previous thumb press (except the rapid-repeat test).

| Gesture | Expected outcome |
|---|---|
| Tap position 75, release before 200 ms, then tap N within 500 ms | One-shot Shift produces `N`; the following N is lowercase. Terminal stays inactive. |
| Fast same-hand chord: hold 75, press and release N, then release 75, all before 200 ms | Produces `N` via the Shift tap; Terminal stays inactive. This guarantee excludes the ten emulator positions. |
| Long hold: hold 75 alone past 200 ms, then press N | Terminal activates; N is `&none` and produces nothing. Release 75, then N works normally. A mapped Terminal key sends its documented chord instead. |
| Rapid tap-then-hold: tap 75, press it again within 300 ms of the first **press**, and hold past 200 ms | The 300 ms `quick-tap-ms` guard forces the second gesture to the Shift tap action; Terminal stays inactive. Waiting more than 300 ms before pressing again permits the normal long hold. |

#### Macro prerequisites

These macros send keystrokes to the focused host application; they cannot check
focus, detect a composer, or wait for the host to become ready. Before using
them, focus the intended terminal and herdr instance with the matching
[terminal-config chord contract](https://github.com/kdelacruz94/terminal-config/blob/main/docs/glove80-terminal-layer-chords.md)
loaded (`ctrl+b` prefix and the configured actions). Prefix and action are
separate taps, with fixed 15 ms tap/wait timing. Release other modifiers and
consume or let any sticky Shift expire first; extra modifiers can change the
chords. Use a disposable pane for checks, especially close-tab and clear-screen.

The right-hand chords require the matching WezTerm or kitty configuration.
Copy needs a selection; paste needs the intended clipboard content and a
focused composer ready to accept it. Dialogs, search/picker modes, completion
menus, or a running command can interpret input differently. This layer no
longer sends Claude Code slash commands, so it has no Claude Code/Codex
composer-version requirement. No minimum supported herdr, WezTerm, or kitty
version or hardware-tested version matrix is recorded here: compatibility is
conditional on the installed host versions supporting the contract's actions.
Record the OS, terminal, herdr, and composer versions during the hand test;
a green firmware build does not verify host compatibility.

#### Captain hardware hand test

- [ ] Tap: verify one-shot `N`, then lowercase `n`, and unused Shift expiry.
- [ ] Fast same-hand chord: verify `N` with N released before 200 ms; also
      hold N across the timer and confirm the documented suppression.
- [ ] Long hold: verify Terminal activates after 200 ms, N is suppressed,
      a mapped chord fires, and releasing 75 restores QWERTY typing.
- [ ] Rapid tap-then-hold: verify no Terminal activation within the 300 ms
      quick-tap window, then normal activation after waiting beyond it.
- [ ] Dedicated left Shift: verify its sticky tap and traditional held Shift
      without a layer change; check f/j separately using the tests above.
- [ ] Record host versions and confirm focus, selection/clipboard, composer
      readiness, modifier state, and representative herdr/emulator actions
      against the installed chord contract.

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
| `config/glove80.conf` | Shared Kconfig: pointing. |
| `config/glove80_lh.conf` | Central-only Kconfig: Raw HID, visualizer config ID. |
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

If you export a new layout (new UUID), update `CONFIG_HID_VIZ_CONFIG_ID` in
`config/glove80_lh.conf` to match.

## Pinned firmware builds and provenance

`config/west.yml` pins the known-green source graph from
[run 37090566575](https://github.com/kdelacruz94/glove80-config/actions/runs/37090566575),
including imported Zephyr and the Raw HID static-buffer fix. The Zephyr override
retains MoErgo's imports and exclusions; top-level definitions take precedence
under [West's import rules](https://docs.zephyrproject.org/latest/develop/west/manifest.html#manifest-import-details).
Dependency upgrades are reviewed manifest edits. CI rejects floating revisions
throughout the resolved graph and active checkouts that differ from their pins.

The pins were rechecked after the RGB deferral and visualizer changes against
[main run 38645294885](https://github.com/kdelacruz94/glove80-config/actions/runs/38645294885)
(config `141c3453385c5e6d4b14ec57d02d50ec2a1ca1df`). These are the existing
PR #11 pins, retained without a firmware upgrade:

| Input | Full revision | Evidence in the downloaded `firmware` archive |
|---|---|---|
| MoErgo ZMK | `ce69e85f585c724142aae37ddf8a7e019ff19e93` | `west-frozen-glove80_lh.yml`, project `zmk` |
| Raw HID (ovandongen fork) | `35d3b77f2022f774d856450e2951b094a831fb38` | Same manifest, project `zmk-raw-hid` |
| HID visualizer | `6a28994f93aac00d32200ed975ec441736e7d98f` | Same manifest, project `zmk-hid-viz` |
| Imported Zephyr | `dacab4875df72109b96cc8977547a0dc04875bcd` | Same manifest, project `zephyr` |
| `actions/checkout` | `11d5960a326750d5838078e36cf38b85af677262` | `provenance-glove80_lh.json`, `actions` |
| `actions/upload-artifact` | `ea165f8d65b6e75b540449e92b4886f43607fa02` | Same metadata, `actions` |
| `actions/download-artifact` | `d3f86a106a0bac45b974a628896c90dbdf5c8093` | Same metadata, `actions` |

The right-half manifest and metadata must report the same revisions. The remaining
imported projects are frozen in those manifests too. The workflow is maintained
locally rather than calling a moving reusable workflow; its exact file hash and
config commit are recorded in each provenance JSON.

`.github/workflows/build.yml` owns the compatible MoErgo build commands at
`ce69e85f585c724142aae37ddf8a7e019ff19e93`, pins every action to a full SHA,
and uses the baseline compiler image by digest for matrix parsing and compilation.
The hosted Ubuntu runner, Docker execution, and artifact service remain external
infrastructure. These pins establish input identity. The comparison below verifies
byte identity for two tested builds; compare UF2 checksums again after changes.

Each downloaded `firmware` archive includes both board-specific UF2s,
`SHA256SUMS`, and a `provenance-<board>.json` for each half. Metadata records the
config commit, workflow ref/SHA/file hash, action SHAs, container digest, board and
shield, tool versions, run ID/attempt/URL, source graph hashes, and UF2 checksum.
`west-frozen-<board>.yml` freezes actual active checkouts;
`west-resolved-<board>.yml` also records pinned optional projects disabled by West's
group filters. CI compares both graphs and the build identities between halves
before publishing the final archive; either missing UF2 fails packaging.

Download the combined **`firmware`** artifact for flashing. The per-half artifacts
are named `artifact-glove80_lh` and `artifact-glove80_rh`; their files also appear
in the combined archive with these exact names:

| Half | UF2 to flash | Frozen manifest retained alongside it |
|---|---|---|
| Left / central | `raw_hid_adapter-glove80_lh-zmk.uf2` | `west-frozen-glove80_lh.yml` |
| Right / peripheral | `glove80_rh-zmk.uf2` | `west-frozen-glove80_rh.yml` |

The left filename includes the `raw_hid_adapter` shield. Keep that name in hand-test
instructions; it identifies the central firmware with the visualizer endpoint.

Both halves built successfully in main run `38645294885` and
[PR #20 run 38643864962](https://github.com/kdelacruz94/glove80-config/actions/runs/38643864962).
Their firmware inputs and per-half UF2 SHA-256 hashes are identical:

```text
b94637bb5a115baff4a9545a68b37890bb70d758560fad0a6fb97b79bb7d9eb3  raw_hid_adapter-glove80_lh-zmk.uf2
5cbd91b3efd2bdf4a103079a2d4d6097378b864f52a260a5e32bd76c28f9099e  glove80_rh-zmk.uf2
```

This pin/artifact audit changes documentation only and requires no additional
hardware testing. Existing RGB and visualizer hardware checks remain as documented
in their sections; matching hashes do not establish those features' behavior.

After extracting an archive, verify its UF2s with `sha256sum -c SHA256SUMS`.
To also check metadata, both graphs, and agreement between halves, run
`python3 scripts/firmware_provenance.py verify <extracted-directory>` from this repo.
Local checks are `python3 scripts/check_layout_json.py`,
`python3 scripts/check_keymap_semantics.py`,
`python3 -m unittest discover -s scripts -p 'test_*.py'`, and `actionlint` when installed.
The actual firmware acceptance check remains the two CI board builds.

`check_keymap_semantics.py` gates the board builds. It checks what compiling cannot:
80 bindings per layer, keymap/export binding, combo, macro and custom-section sync,
one UUID across the export, `glove80.conf` and this README, a keyboard-only way back
to QWERTY from every persistent mode (and a `&to 0` reset combo covering it), that a
`&to`-selected base never masks an overlay held from it. Per-key RGB presence is
checked after each board build by `check_rgb_build.py`. Known failures awaiting a fix are listed in its `PENDING` table
with the owning card; once a fix lands the entry fails as stale until it is deleted.

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

`config/glove80.conf` keeps pointing enabled on both halves. Raw HID, visualizer
reporting, and the config ID live in `config/glove80_lh.conf`: Raw HID depends on
the central role, so assigning these settings on the right half causes Kconfig
dependency warnings. The pinned firmware loads both the shared and board-specific
configuration files.

`zmk-raw-hid` is pulled from **ovandongen's fork**, not zzeneg upstream, for a
static-HID-report-buffer fix that upstream lacks.

### Point the viz at the repo file, not a Downloads export

MoergoLayerViz reads a layout JSON for its key labels. Select **this repo's**
copy manually, so it stays aligned with what CI flashes:

1. Use the toolbar's **Load layout JSON** button and choose
   `layout/V52-Everforest-QWERTY.json` from the checkout matching the flashed build.
   If the app is on another machine, download that JSON from the same commit.
   The current default-branch copy is available at
   [this raw URL](https://raw.githubusercontent.com/kdelacruz94/glove80-config/main/layout/V52-Everforest-QWERTY.json).
   The inspected app opens local files; download the URL before selecting it.
2. Confirm Glove80 is selected and the expected layer names and key labels appear.
3. After updating the matching firmware and JSON, use the toolbar's **Refresh**
   button to reload the file. The app remembers the selected path per keyboard
   profile; moving the file requires selecting it again.

After a keymap change, refresh it by pushing the `config/glove80.keymap` +
`layout/*.json` pair (they change in the same commit — see `AGENTS.md`) and
reloading the viz. A one-off editor export sitting in `Downloads` is not a source:
it goes stale the moment the next binding lands.

### Config-ID limitation and host compatibility

The pinned Raw HID module uses **32-byte reports**. The pinned visualizer module's
legacy `0xFB` query returns a single `0xFA` report with at most 31 ID bytes: this
layout's 36-character UUID becomes `15da8b74-bc9e-47fe-8334-34ea6d2`.
That is not the full layout ID. Keep the full UUID in the config; shortening it
would lose its correspondence with the editor export.

The same pinned firmware already supports full IDs through `0xF9` manifest queries
and `0xF8` continuation reports, with a six-byte header and 26-byte chunks at the
existing report size ([legacy response](https://github.com/ovandongen/zmk-hid-viz/blob/6a28994f93aac00d32200ed975ec441736e7d98f/src/command_handler.c#L65),
[manifest framing](https://github.com/ovandongen/zmk-hid-viz/blob/6a28994f93aac00d32200ed975ec441736e7d98f/src/capabilities.h#L90)).
`HID_VIZ_MANIFEST` defaults to enabled when visualizer reporting is enabled.

Host source checked on 2026-10-13: MoergoLayerViz at
`5e5b7911f8676525674a2d6a49f2b3df9abff60b`, with its protocol submodule at
`c63590c54329a9d4a5cde380d4cfb757d42eefd0`, has no manifest query or continuation
parser. Its [protocol constants](https://github.com/ovandongen/zmk-hid-protocol/blob/c63590c54329a9d4a5cde380d4cfb757d42eefd0/src/ZmkHidProtocol/Protocol/HidConstants.cs)
fix reports at 32 bytes and support the legacy ID query; the app exposes that
query only in its [diagnostic plumbing](https://github.com/ovandongen/moergo-layer-viz/blob/5e5b7911f8676525674a2d6a49f2b3df9abff60b/src/MoergoLayerViz.App/ViewModels/MainWindowViewModel.cs#L734).
The Settings [Testing tab is hidden](https://github.com/ovandongen/moergo-layer-viz/blob/5e5b7911f8676525674a2d6a49f2b3df9abff60b/src/MoergoLayerViz.App/Views/SettingsWindow.axaml#L484)
in that source (`IsVisible="False"`), so a normal build need not expose the query.
Layout loading uses a local file picker and a saved path, with no UUID-based
automatic matching ([file picker](https://github.com/ovandongen/moergo-layer-viz/blob/5e5b7911f8676525674a2d6a49f2b3df9abff60b/src/MoergoLayerViz.App/App.axaml.cs#L194)).

Full-ID retrieval and matching-layout selection are therefore **unresolved host
integration work**. A future host implementation could consume the existing
manifest chunks without enlarging reports. This config preserves the HID report
size, usage IDs, UUID, dependency pins, and wire protocol. Source inspection and
CI builds do not verify USB behavior: after flashing both matching UF2s, check
manual loading, live layer/key tracking on each hand, the saved path after an app
restart, and, if diagnostics are exposed, the truncated config ID. No end-to-end automatic selection or
hardware test has been performed for this change.
