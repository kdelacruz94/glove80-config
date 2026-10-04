#!/usr/bin/env python3
"""Record pinned west sources and verify the downloaded two-half firmware bundle."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

SHA = re.compile(r"[0-9a-f]{40}")
EXPECTED = {
    "glove80_lh": ("raw_hid_adapter", "raw_hid_adapter-glove80_lh-zmk.uf2"),
    "glove80_rh": ("", "glove80_rh-zmk.uf2"),
}


def command(*args):
    return subprocess.check_output(args, text=True).strip()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sources(build_dir):
    # Validate declared revisions as well as actual checkouts: freeze alone would
    # turn a moving branch into a SHA and hide a missing pin.
    from west.manifest import Manifest
    resolved = Manifest.from_topdir()
    for project in resolved.projects[1:]:
        revision = project.revision
        if not SHA.fullmatch(revision):
            raise ValueError(f"floating source: {project.name} at {revision}")
        if not resolved.is_active(project):
            continue
        actual = command("git", "-C", project.abspath, "rev-parse", "HEAD")
        if actual != revision:
            raise ValueError(f"checkout differs from pin: {project.name}")
    frozen = command("west", "manifest", "--freeze", "--active-only") + "\n"
    build_dir.mkdir(parents=True, exist_ok=True)
    (build_dir / f"west-frozen-{os.environ['BOARD']}.yml").write_text(frozen)
    (build_dir / f"west-resolved-{os.environ['BOARD']}.yml").write_text(resolved.as_yaml())


def record(build_dir):
    # PyYAML is supplied by the pinned build image's west installation.
    import yaml
    board, shield = os.environ["BOARD"], os.environ.get("BUILD_SHIELD", "")
    expected_shield, filename = EXPECTED[board]
    if shield != expected_shield:
        raise ValueError(f"unexpected shield for {board}: {shield}")
    out = build_dir / "artifacts"
    out.mkdir()
    shutil.copyfile(build_dir / "zephyr/zmk.uf2", out / filename)
    manifest = f"west-frozen-{board}.yml"
    shutil.copyfile(build_dir / manifest, out / manifest)
    full_manifest = f"west-resolved-{board}.yml"
    shutil.copyfile(build_dir / full_manifest, out / full_manifest)
    repo = Path(os.environ["GITHUB_WORKSPACE"])
    workflow = repo / ".github/workflows/build.yml"
    workflow_data = yaml.safe_load(workflow.read_text())
    image = workflow_data["env"]["BUILD_IMAGE"]
    for job in workflow_data["jobs"].values():
        if "container" in job and job["container"]["image"] != image:
            raise ValueError("container differs from recorded build image")
    if os.environ["BUILD_IMAGE"] != image or "@sha256:" not in image:
        raise ValueError("build image must match the digest-qualified workflow pin")
    actions = sorted(set(re.findall(r"uses: ([^\s#]+)", workflow.read_text())))
    if any(not SHA.fullmatch(action.rsplit("@", 1)[-1]) for action in actions):
        raise ValueError("all actions must have full SHA pins")
    cache = (build_dir / "CMakeCache.txt").read_text()
    # Read the selected compiler from CMake's generated language configuration;
    # its cache entry type and presence vary between toolchains.
    compiler_info, = build_dir.glob("CMakeFiles/*/CMakeCCompiler.cmake")
    compiler = re.search(r'^set\(CMAKE_C_COMPILER "([^"\n]+)"\)', compiler_info.read_text(), re.M)[1]
    sdk_dir = re.search(r"^ZEPHYR_SDK_INSTALL_DIR:PATH=(.+)$", cache, re.M)[1]
    identity = {
        "schema_version": 1,
        "repository": os.environ["GITHUB_REPOSITORY"],
        "config_sha": command("git", "-c", f"safe.directory={repo}", "-C", str(repo), "rev-parse", "HEAD"),
        "workflow_ref": os.environ["GITHUB_WORKFLOW_REF"],
        "workflow_sha": os.environ["GITHUB_WORKFLOW_SHA"],
        "workflow_file_sha256": digest(workflow),
        "actions": actions,
        "container": image,
        "run_id": os.environ["GITHUB_RUN_ID"],
        "run_attempt": os.environ["GITHUB_RUN_ATTEMPT"],
        "run_url": f"{os.environ['GITHUB_SERVER_URL']}/{os.environ['GITHUB_REPOSITORY']}/actions/runs/{os.environ['GITHUB_RUN_ID']}",
        "source_graph_sha256": digest(out / manifest),
        "resolved_graph_sha256": digest(out / full_manifest),
        "tools": {
            "python": sys.version.split()[0],
            "west": command("west", "--version"),
            "cmake": command("cmake", "--version").splitlines()[0],
            "ninja": command("ninja", "--version"),
            "compiler": command(compiler, "--version").splitlines()[0],
            "zephyr_sdk": (Path(sdk_dir) / "sdk_version").read_text().strip(),
        },
    }
    metadata = dict(identity, board=board, shield=shield, manifest=manifest,
                    firmware=filename, firmware_sha256=digest(out / filename))
    (out / f"provenance-{board}.json").write_text(json.dumps(metadata, indent=2) + "\n")


def verify(bundle):
    identities, checksums = [], []
    for board, (shield, filename) in EXPECTED.items():
        data = json.loads((bundle / f"provenance-{board}.json").read_text())
        if (data["board"], data["shield"], data["firmware"]) != (board, shield, filename):
            raise ValueError(f"incorrect half identity: {board}")
        manifest = f"west-frozen-{board}.yml"
        if data["manifest"] != manifest or digest(bundle / manifest) != data["source_graph_sha256"]:
            raise ValueError(f"source graph checksum mismatch: {board}")
        if digest(bundle / f"west-resolved-{board}.yml") != data["resolved_graph_sha256"]:
            raise ValueError(f"resolved graph checksum mismatch: {board}")
        checksum = digest(bundle / filename)  # Missing either UF2 is fatal.
        if checksum != data["firmware_sha256"]:
            raise ValueError(f"firmware checksum mismatch: {board}")
        checksums.append(f"{checksum}  {filename}\n")
        identities.append({k: v for k, v in data.items() if k not in
                           {"board", "shield", "manifest", "firmware", "firmware_sha256"}})
    if identities[0] != identities[1]:
        raise ValueError("halves disagree on source graph or build identity")
    (bundle / "SHA256SUMS").write_text("".join(checksums))
    print("ok: both UF2s verified; source graph and build identities agree")


if __name__ == "__main__":
    {"sources": sources, "record": record, "verify": verify}[sys.argv[1]](Path(sys.argv[2]))
