# Keep the installed Layer Viz layout current

The September 2026 host deployment manually staged `layout/` under
`~/.local/share/glove80-config/layout/` and copied its JSON to
`~/Downloads/MoergoLayerViz Layout/`. There was no reusable install command;
both copies could remain stale after updating the repo. This deploy step replaces
those copies with links using the same installed paths:

```text
~/Downloads/MoergoLayerViz Layout/V52-Everforest-QWERTY.json
  -> $XDG_DATA_HOME/glove80-config/layout/V52-Everforest-QWERTY.json
  -> <chosen checkout>/layout/V52-Everforest-QWERTY.json
```

`XDG_DATA_HOME` defaults to `~/.local/share`. The checkout is the layout source;
the command does not pull Git, download firmware, or flash the keyboard. Once
installed, changes in that checkout appear through both links without another
copy operation or a background service. Keep the checkout on disk and update
it to main when you want main's labels. Preview labels can differ from flashed
firmware until that firmware is installed.

## One-time activation on the home desktop

After this change lands and `~/Projects/glove80-config` is updated to main, run
this fish-compatible command:

```fish
python3 ~/Projects/glove80-config/scripts/install_viz_layout.py --source ~/Projects/glove80-config
```

In Layer Viz, use **Load Layout** and select
`$HOME/Downloads/MoergoLayerViz Layout/V52-Everforest-QWERTY.json`.
Do this once even if the app currently points directly into the repo, so PR
previews use the same stable path. Use **Refresh** after pulling layout changes
or switching the source (restarting Layer Viz also reloads it).

Layer Viz persists the selected filename in `LayoutJsonPaths["Glove80"]` and
reads it on startup and Refresh; it does not continuously watch the checkout.
See the upstream [v2.2.1 loading and Refresh implementation](https://github.com/ovandongen/moergo-layer-viz/blob/v2.2.1/src/MoergoLayerViz.App/ViewModels/MainWindowViewModel.cs).
This command leaves the application's settings alone.

Existing files, directories, or symlinks are saved beside each destination with
the suffix `.before-viz-link`. Repeating activation or changing the source keeps
those original backups. A conflicting backup causes an error before changes.

Rollback (fish-compatible):

```fish
python3 ~/Projects/glove80-config/scripts/install_viz_layout.py --rollback
```

Rollback restores both originals, or removes a link if that path was originally
absent. It refuses if the pair no longer has the expected link structure. Refresh
the app afterward; if you selected another filename, select the restored file.

## Preview a PR worktree, then return to main

For an existing PR worktree at `~/worktrees/glove80-pr-preview`, run:

```fish
python3 ~/Projects/glove80-config/scripts/install_viz_layout.py --source ~/worktrees/glove80-pr-preview
```

Click **Refresh** in Layer Viz. To switch back:

```fish
python3 ~/Projects/glove80-config/scripts/install_viz_layout.py --source ~/Projects/glove80-config
```

Click **Refresh** again before removing the PR worktree. The source is a checkout
root containing `layout/V52-Everforest-QWERTY.json`, not a branch name or a JSON
filename. To preview a branch without a worktree, create one first; for example,
for the already-fetched `fm/g80-lockout-escape` branch:

```fish
git -C ~/Projects/glove80-config worktree add --detach ~/worktrees/glove80-pr-preview origin/fm/g80-lockout-escape
```

## Isolated verification

`python3 -m unittest discover -s scripts -p 'test_install_viz_layout.py' -v`
exercises the CLI with `HOME` and `XDG_DATA_HOME` pointing inside a temporary
directory in this repo. It never installs into the real home.
