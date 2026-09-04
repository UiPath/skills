"""Reading the state of a Solution: on disk, and as the tenant currently has it.

Nothing here mutates anything.

SOLUTION_SRC is resolved lazily and only by the scripts that actually need the source tree, which
is why resolving a folder id or awaiting a release does not require it. The multi-verb script this
replaced resolved it before dispatch, so those two commands failed without it.
"""

import json
import os
import pathlib

from _uip import die, uip_json

SOLUTION_SRC = os.environ.get("SOLUTION_SRC", "")
# A new version means a new deployment in a new folder. The folder must be created UNDER Shared,
# or it has no unattended robot permissions and the job cannot start.
PARENT_FOLDER_PATH = os.environ.get("PARENT_FOLDER_PATH", "Shared")


def solution_src():
    """Resolved lazily, and only by the scripts that pack, so `await_release.py` still works
    without it."""
    if not SOLUTION_SRC:
        die("SOLUTION_SRC is not set; the caller must supply it, nothing is baked into this script")
    path = pathlib.Path(SOLUTION_SRC).expanduser().resolve()
    if not path.is_dir():
        die("solution source not found: %s" % path)
    return path


def solution_name():
    name = os.environ.get("SOLUTION_NAME")
    if name:
        return name
    return solution_src().name


def manifest_projects(src):
    """Which projects the package contains, from the manifest and never from a directory listing.

    Listing directories would silently include a stray folder, or miss a project the manifest
    still references. SolutionStorage.json is authoritative when it exists, which is the case for
    a Studio Web export; a CLI-scaffolded solution has only the .uipx, whose Projects array says
    the same thing.
    """
    storage = src / "SolutionStorage.json"
    if storage.exists():
        entries = json.loads(storage.read_text()).get("Projects") or []
        return [p["ProjectRelativePath"].rsplit("/", 1)[0] for p in entries], "SolutionStorage.json"
    uipx = sorted(src.glob("*.uipx"))
    if not uipx:
        die("no SolutionStorage.json and no .uipx in %s; nothing declares what the package holds"
            % src)
    entries = json.loads(uipx[0].read_text()).get("Projects") or []
    if not entries:
        die("%s declares no projects; add them with `uip solution projects add` "
            "(see the skill's phase 1)" % uipx[0].name)
    return [p["ProjectRelativePath"].rsplit("/", 1)[0] for p in entries], uipx[0].name


def tombstone(record):
    """An uninstalled deployment lingers in the list: Operation=Uninstall, no activation, only a
    Delete action left. It owns no folder and runs nothing, so it must never be reported as the
    current deployment; picking one up gives a real-looking version for a dead record."""
    return (record.get("Operation") == "Uninstall"
            and record.get("ActivationStatus") in (None, "None"))


def deployments():
    """Every deployment the tenant reports.

    Dies rather than returning empty when the listing itself fails. The idempotence guards read
    this, and an empty list means "nothing is deployed" -- so a transient CLI or API failure would
    otherwise read as "safe to create", and the run would add a second deployment and a second
    Orchestrator folder for a version that already has one.

    Left to uip_json to die rather than checking for None here: it carries the CLI's own stderr
    tail into the failure, which is the part that says why the listing failed.
    """
    data = uip_json(["solution", "deploy", "list"]) or {}
    return data.get("Data") or []


def version_info(name):
    hits = [d for d in deployments()
            if (d.get("PackageName") == name or d.get("Name") == name) and not tombstone(d)]
    if not hits:
        # A first release, not an error: there is no current version to compute `next` from. The
        # caller decides what that means; publish_package treats it as "the version is yours to
        # choose" rather than refusing.
        return None

    def vkey(d):
        parts = (d.get("CurrentPackageVersion") or d.get("PackageVersion") or "").split(".")
        return tuple(int(p) if p.isdigit() else -1 for p in parts)

    # Highest version wins when several deployments carry the same package, so `next` is computed
    # from the newest release rather than whichever the API happened to list first.
    d = sorted(hits, key=vkey)[-1]
    cur = d.get("CurrentPackageVersion") or d.get("PackageVersion") or ""
    parts = cur.split(".")
    nxt = ""
    if len(parts) == 3 and parts[-1].isdigit():
        nxt = ".".join(parts[:-1] + [str(int(parts[-1]) + 1)])
    return {"ok": True, "current": cur, "next": nxt, "deployment": d.get("Name"),
            "activation": d.get("ActivationStatus"), "actions": d.get("Actions")}


def live_at_version(name, version):
    for r in deployments():
        if r.get("PackageName") != name or tombstone(r):
            continue
        if r.get("CurrentPackageVersion") == version:
            return r.get("Name")
    return None


def release_records(folder_path, allow_fail=False):
    data = uip_json(["or", "processes", "list", "--folder-path", folder_path],
                    allow_fail=allow_fail) or {}
    return data.get("Data") or []


def release_version(record):
    # `uip or processes list` reports the release version as ProcessVersion. Verified live.
    return record.get("ProcessVersion")
