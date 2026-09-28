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

## Chords that need a host-side binding

Some keys emit a chord that does nothing until the *host* binds it. Keep this list
current when adding one, because the keymap alone cannot show the dependency:

- `F13` (base pos 22, AI_Claude pos 4) -- Handy on Windows, hyprwhspr on CachyOS.
- `LG(LS(S))` (base pos 0) -- native on Windows; on CachyOS/Hyprland the same chord
  must be bound to a `grim`/`slurp` or `hyprshot` command.
- `LC(LA(LG(F12)))` (System layer pos 4) -- monitor DDC input toggle; bound per host,
  see the PR that introduced it for the ControlMyMonitor setup.
- `&ai_herdr_*` macros -- herdr's prefix is `ctrl+b`; the macro sends prefix and action
  as two separate taps, never chorded. Actions come from `herdr/config.linux.toml` in
  `~/Projects/terminal-config`, cross-checked against `herdr --default-config`.

There is no local build. CI (`.github/workflows/build.yml`) is the only acceptance
check -- see the two traps in `README.md` before touching `config/west.yml` or the
workflow.

## Maintaining this file

Keep this file for knowledge useful to almost every future agent session in this project.
Do not repeat what the codebase already shows; point to the authoritative file or command instead.
Prefer rewriting or pruning existing entries over appending new ones.
When updating this file, preserve this bar for all agents and keep entries concise.
