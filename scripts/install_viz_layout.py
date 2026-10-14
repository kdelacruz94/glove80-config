#!/usr/bin/env python3
"""Replace the manually staged Layer Viz copies with links to a checkout."""
import argparse
import os
from pathlib import Path


LAYOUT = "V52-Everforest-QWERTY.json"
BACKUP_SUFFIX = ".before-viz-link"


def present(path):
    return path.exists() or path.is_symlink()


def backup(path):
    return path.with_name(path.name + BACKUP_SUFFIX)


def managed(installed, viz):
    return (installed.is_symlink() and viz.is_symlink()
            and viz.readlink() == installed / LAYOUT)


def retarget(path, target):
    # Replace the directory link atomically, including on repeat installs.
    temporary = path.with_name(path.name + ".viz-link-tmp")
    temporary.symlink_to(target, target_is_directory=True)
    try:
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def install(source, installed, viz):
    if not (source / LAYOUT).is_file():
        raise ValueError(f"missing layout: {source / LAYOUT}")
    if source == installed or installed in source.parents:
        raise ValueError("source must be outside the installed layout directory")
    if managed(installed, viz):
        retarget(installed, source)
        return

    # Refuse backup collisions before touching either original.
    for path in (installed, viz):
        if present(backup(path)):
            raise ValueError(f"backup already exists: {backup(path)}")
    moved, linked = [], []
    try:
        for path, target in ((installed, source), (viz, installed / LAYOUT)):
            path.parent.mkdir(parents=True, exist_ok=True)
            if present(path):
                path.rename(backup(path))
                moved.append(path)
            path.symlink_to(target, target_is_directory=(path == installed))
            linked.append(path)
    except OSError:
        for path in reversed(linked):
            path.unlink()
        for path in reversed(moved):
            backup(path).rename(path)
        raise


def rollback(installed, viz):
    if not managed(installed, viz):
        raise ValueError("expected managed links at both paths; refusing rollback")
    for path in (viz, installed):
        path.unlink()
        if present(backup(path)):
            backup(path).rename(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--source", type=Path,
                        default=Path(__file__).resolve().parents[1],
                        help="checkout/worktree root (default: this script's repo)")
    action.add_argument("--rollback", action="store_true",
                        help="restore the copies saved by the first install")
    args = parser.parse_args()
    home = Path.home()
    data = Path(os.environ.get("XDG_DATA_HOME") or home / ".local/share")
    if not data.is_absolute():
        parser.error("XDG_DATA_HOME must be absolute")
    installed = data / "glove80-config/layout"
    viz = home / "Downloads/MoergoLayerViz Layout" / LAYOUT
    try:
        if args.rollback:
            rollback(installed, viz)
            print("Restored the original Layer Viz layout copies.")
        else:
            source = (args.source.expanduser() / "layout").resolve()
            install(source, installed, viz)
            print(f"{viz} -> {installed / LAYOUT} -> {source / LAYOUT}")
            print("Select this Downloads file in Layer Viz, then Refresh after updates.")
    except (OSError, ValueError) as error:
        parser.exit(1, f"error: {error}\n")


if __name__ == "__main__":
    main()
