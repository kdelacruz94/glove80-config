# Project agent memory

This file is the project's committed home for project-intrinsic agent knowledge: build, test, release, architecture, and sharp-edge notes that should travel with the code.

- Add durable project-specific notes here as they are discovered through real work.

## Key positions in the binding rows

`config/glove80.keymap` and `layout/*.json` index the same 80 positions in the same
order, so a keymap edit and its JSON counterpart use the identical index. The six
binding rows split as:

| Row | Left | Thumbs | Right |
|---|---|---|---|
| R1 | 0-4 | - | 5-9 |
| R2 | 10-15 | - | 16-21 |
| R3 | 22-27 | - | 28-33 |
| R4 | 34-39 | - | 40-45 |
| R5 | 46-51 | 52-57 | 58-63 |
| R6 | 64-68 | 69-74 | 75-79 |

MoErgo names keys `C<col>R<row>` with columns numbered **inside-out** -- C1 is the
index-finger column, C6 the outer column. So left C6R3 is position 22 and right C6R6
is position 79. The README and the layout JSON's `notes` field both use that naming.

## Editing a binding

Edit `config/glove80.keymap` and `layout/<name>.json` in the same commit; they are two
views of one layout. The JSON round-trips through
`json.dumps(d, indent=2, ensure_ascii=False)` with no diff churn, so a scripted
single-index edit stays a single-hunk diff.

## Home-row Shift tuning

Before tuning the active f/j hold-taps (`left_index` / `right_index`), read
README's "Home-row Shift" section for the roll/nested-tap distinction, timer and
prior-idle knobs, and hand tests. Prior idle cannot protect word-start rolls.
Behavior edits must also update the JSON's `custom_defined_behaviors` string.

## Modifier chords: two different encodings

The keymap and the layout JSON do NOT share the chord syntax. `config/glove80.keymap`
uses ZMK's string form (`&kp LG(LS(S))`); the JSON must use MoErgo's nested params, or
the Layout Editor rejects the whole file on import with `invalid key code`. `Custom`
values (`&kp _C(L)`) are raw devicetree passthrough and keep their parens.
`scripts/check_layout_json.py` (CI job `layout-json`) fails on the wrong form.

## The layout JSON's `version` field

`layout/*.json` must keep the top-level `"version": 1` the Layout Editor writes.
It is the first key in the file and the only thing a hand-built JSON is likely to
miss; without it MoergoLayerViz falls back to stale labels rather than erroring,
so the loss is silent. Round-trip a hand-edit through the editor (import, export)
if you are unsure, and keep the file byte-identical to that export -- no trailing
newline.

## The JSON's encoding aliases are not key differences

The editor writes `&magic` for the keymap's `&magic LAYER_Magic 0`, `&reset` for
`&sys_reset`, and **numeric layer indices** (`&to 17`) where the keymap uses the
`LAYER_*` macros. The index is the position in `layer_names`. Compare the two
files through those aliases; a naive string diff reports ~23 false mismatches.

## Chords that need a host-side binding

Some keys emit a chord that does nothing until the *host* binds it. Keep this list
current when adding one, because the keymap alone cannot show the dependency:

- `F13` (base pos 22, Terminal pos 4) -- Handy on Windows, hyprwhspr on CachyOS.
- `F14` (Function pos 45 only) -- host mute binding on Windows and CachyOS/Hyprland;
  see the base-layer shortcuts section in `README.md`.
- `LG(LS(S))` (base pos 4) -- native on Windows; on CachyOS/Hyprland the same chord
  must be bound to a `grim`/`slurp` or `hyprshot` command.
- `LC(LA(LG(F11)))` / `LC(LA(LG(F12)))` (base pos 0 / 1) -- absolute monitor input
  select (DisplayPort / USB-C) via ControlMyMonitor VCP `0x60`; per-machine setup in
  `README.md`. Replaced the round-2 single toggle key.
- `&term_herdr_*` macros -- herdr's prefix is `ctrl+b`; the macro sends prefix and action
  as two separate taps, never chorded. Actions come from `docs/glove80-terminal-layer-chords.md`
  in `~/Projects/terminal-config` (the chord contract), which also lists the emulator chords
  (WezTerm/kitty) the Terminal layer's right hand sends: `ctrl+shift+c/v/f/k/n/page_up/page_down`
  and `ctrl+=` / `ctrl+-` / `ctrl+0` for text zoom. Change a chord there first, then re-map the key.

There is no local build. CI (`.github/workflows/build.yml`) is the only acceptance
check. Before editing source pins or the workflow, read README's "Pinned firmware
builds and provenance" and "Two traps worth remembering" sections; imported Zephyr
needs its own override with MoErgo's imports/exclusions preserved.

## Maintaining this file

Keep this file for knowledge useful to almost every future agent session in this project.
Do not repeat what the codebase already shows; point to the authoritative file or command instead.
Prefer rewriting or pruning existing entries over appending new ones.
When updating this file, preserve this bar for all agents and keep entries concise.
