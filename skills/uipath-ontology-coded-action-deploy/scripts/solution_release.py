#!/usr/bin/env python3
"""Publish a new release of the Solution that carries an ontology's coded-action jobs.

Every job in one ontology's Solution ships in one package, so a publish bumps them all onto the
same version line. That is why `version` reads the current value from the deployment rather than
tracking one locally, and why `publish` and `deploy` need a confirmation.

  solution_release.py version                            -> {current, next, deployment}
  solution_release.py stage                              -> build+validate the staging tree
  solution_release.py pack    <version> [outdir]         -> local .zip, no tenant writes
  solution_release.py publish <version> [--execute]      -> pack + upload to feed    [MUTATES]
  solution_release.py deploy  <version> [name] [--execute]  -> NEW deployment+folder [MUTATES]
  solution_release.py folder-id <fullyQualifiedName>     -> numeric Id for ont:processFolderId
  solution_release.py await   <processName> <version> --folder-path PATH

publish and deploy PRINT the command and change nothing unless --execute is passed. They write to
a live tenant and affect every function in the Solution, so the default is to show what would
happen and let a human decide.

`stage` and `pack` only ever write to a temp directory. `pack` additionally runs `uip functions
pack` inside every staged project, which installs dependencies: it needs the network and
GH_NPM_REGISTRY_TOKEN (the @uipath scope resolves from GitHub Packages via each project's .npmrc).

WHY STAGING EXISTS
------------------
SOLUTION_SRC holds the Solution source, but its function projects have no committed job source:
the source is the job that lives beside the action TTL that invokes it, per jobs.map.json.
Staging copies the tree to a temp dir, writes each mapped job in as that project's
functions/{actionName}.ts, and packs the copy. The source tree is never mutated, and a job has
exactly one home. functions/ is the only place `uip functions pack` looks: it rebuilds the
uipath.json functions map from a directory scan of functions/*.ts and silently discards
hand-written entries, so a job staged anywhere else (a root main.ts included) is invisible.

The guard in stage() is load-bearing, not decorative: `uip solution pack` reports Status: Valid
for a project whose job source is MISSING OR EMPTY. It will happily build a package containing an
empty function, and nothing fails until invoke time. A 0-byte entry point is exactly what a Studio
Web export shipped.

WHY PACK RUNS `uip functions pack` FIRST
----------------------------------------
`uip solution pack` does not generate entry-points.json; only `uip functions pack` does, and
without it solution pack fails with "entry-points.json not found. Run 'uipath-functions pack' to
generate it." (that error names a binary that does not exist; the working command is
`uip functions pack`). pack() runs it inside every staged project before solution pack.

Configuration. Nothing here names a tenant, a folder or a path on anyone's machine: the value that
identifies one is REQUIRED and the caller supplies it per run. Only the conventions keep a default.

  SOLUTION_SRC        REQUIRED  the solution directory to pack (holds the .uipx)
  SOLUTION_NAME       optional  the solution directory's name, the solution PACKAGE name
  DEPLOY_NAME         optional  <SOLUTION_NAME>  deployment + folder name created by `deploy`
  PARENT_FOLDER_PATH  optional  Shared           MUST be a folder with robot permissions to inherit
  UIP_CLI             optional  uip              path to the uip binary
"""

import argparse
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import time

UIP = os.environ.get("UIP_CLI", "uip")
SOLUTION_SRC = os.environ.get("SOLUTION_SRC", "")
# A new version means a new deployment in a new folder (see deploy_release). The folder must be
# created UNDER Shared, or it has no unattended robot permissions and the job cannot start.
PARENT_FOLDER_PATH = os.environ.get("PARENT_FOLDER_PATH", "Shared")

AWAIT_POLLS = 60
AWAIT_INTERVAL = 10


def die(message, **extra):
    """Errors go to stderr, never stdout: a caller parsing stdout must not see a failure as data."""
    payload = {"ok": False, "error": message}
    payload.update(extra)
    print(json.dumps(payload), file=sys.stderr)
    raise SystemExit(1)


def emit(payload):
    print(json.dumps(payload, indent=2))


def solution_src():
    """Resolved lazily, and only by the subcommands that pack, so `version`, `folder-id` and
    `await` still work without it."""
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


def uip_json(argv, allow_fail=False):
    """Run a uip command and parse its stdout as JSON.

    Capture stdout ONLY. `uip` writes a long INFO log to stderr even at --log-level error, and one
    of those lines contains a literal "{solutionKey}"; folding stderr in makes the first brace in
    the stream a log line, so the JSON parse silently yields nothing.
    """
    proc = subprocess.run([UIP] + argv + ["--output", "json", "--log-level", "error"],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        if allow_fail:
            return None
        tail = " ".join((proc.stderr or "").strip().splitlines()[-5:])
        die("uip %s failed" % " ".join(argv), detail=tail)
    try:
        return json.loads(proc.stdout)
    except ValueError:
        if allow_fail:
            return None
        die("uip %s returned unparseable JSON" % " ".join(argv), stdout=proc.stdout[:400])


def uip_plain(argv, cwd):
    """Run a uip command whose output is human text, not JSON (e.g. `uip functions pack`)."""
    proc = subprocess.run([UIP] + argv, cwd=str(cwd), capture_output=True, text=True)
    if proc.returncode != 0:
        tail = " ".join((proc.stderr or proc.stdout or "").strip().splitlines()[-5:])
        die("uip %s failed in %s" % (" ".join(argv), cwd), detail=tail)
    return proc.stdout


def tombstone(record):
    """An uninstalled deployment lingers in the list: Operation=Uninstall, no activation, only a
    Delete action left. It owns no folder and runs nothing, so it must never be reported as the
    current deployment; picking one up gives a real-looking version for a dead record."""
    return (record.get("Operation") == "Uninstall"
            and record.get("ActivationStatus") in (None, "None"))


def deployments():
    data = uip_json(["solution", "deploy", "list"], allow_fail=True) or {}
    return data.get("Data") or []


# --------------------------------------------------------------------------- version


def version_info(name):
    hits = [d for d in deployments()
            if (d.get("PackageName") == name or d.get("Name") == name) and not tombstone(d)]
    if not hits:
        die("no live deployment for package %r" % name,
            hint="first release: pick a starting version yourself, then deploy it")

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


# --------------------------------------------------------------------------- stage


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
        die("%s declares no projects; run solution_scaffold.py first" % uipx[0].name)
    return [p["ProjectRelativePath"].rsplit("/", 1)[0] for p in entries], uipx[0].name


def stage(src):
    """Build the staging tree and validate every entry point. Returns the staging path."""
    staging = pathlib.Path(tempfile.mkdtemp(prefix="ontology-solution-"))
    shutil.copytree(src, staging, dirs_exist_ok=True)
    for junk in ("jobs.map.json", "README.md", "AGENTS.md", "CLAUDE.md"):
        (staging / junk).unlink(missing_ok=True)

    projects, authority = manifest_projects(src)

    mapping = {}
    map_file = src / "jobs.map.json"
    if map_file.exists():
        mapping = json.loads(map_file.read_text()).get("projects") or {}

    unknown = sorted(set(mapping) - set(projects))
    if unknown:
        shutil.rmtree(staging, ignore_errors=True)
        die("jobs.map.json maps project(s) not in %s: %s" % (authority, ", ".join(unknown)))

    staged = []
    for project, rel in sorted(mapping.items()):
        # Relative paths resolve against the solution source, so a job beside its action TTL is
        # written relative and a job outside that tree is written absolute.
        source = pathlib.Path(rel)
        if not source.is_absolute():
            source = (src / rel).resolve()
        if not source.exists():
            shutil.rmtree(staging, ignore_errors=True)
            die("mapped job source missing: %s (for %s)" % (rel, project))
        if source.stat().st_size == 0:
            shutil.rmtree(staging, ignore_errors=True)
            die("mapped job source is empty: %s (for %s)" % (rel, project))
        # Into functions/, never the project root: `uip functions pack` rebuilds the functions map
        # from a scan of functions/*.ts and a root-level source is invisible to it.
        target = staging / project / "functions" / (source.stem + ".ts")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        staged.append({"project": project, "from": rel,
                       "to": "functions/%s" % target.name, "bytes": source.stat().st_size})

    # Belt and braces: check EVERY project, not just the mapped ones. An unmapped project with no
    # non-empty functions/*.ts is the same silent failure, and pack will not catch it.
    for project in projects:
        sources = sorted((staging / project / "functions").glob("*.ts")) \
            if (staging / project / "functions").is_dir() else []
        if not sources:
            shutil.rmtree(staging, ignore_errors=True)
            die("%s/functions holds no .ts source and the project is not in jobs.map.json; "
                "pack would publish an empty function" % project)
        for entry in sources:
            if entry.stat().st_size == 0:
                shutil.rmtree(staging, ignore_errors=True)
                die("%s/functions/%s is empty; pack would publish an empty function"
                    % (project, entry.name))

    return staging, {"projects": projects, "authority": authority, "staged": staged}


# --------------------------------------------------------------------------- pack


def pack(src, name, version, outdir):
    staging, report = stage(src)
    try:
        # `uip functions pack` per project FIRST: it alone generates entry-points.json, which
        # `uip solution pack` requires but never produces. It also rebuilds the uipath.json
        # functions map from the staged functions/*.ts. (Its absence fails solution pack with an
        # error naming 'uipath-functions pack', a binary that does not exist.)
        for project in report["projects"]:
            uip_plain(["functions", "pack"], cwd=staging / project)
            if not (staging / project / "entry-points.json").is_file():
                die("uip functions pack produced no entry-points.json for %s" % project)
        # -n is mandatory. Without it the package is named after the staging directory, which
        # would publish a package the deployment does not recognise.
        result = uip_json(["solution", "pack", str(staging), str(outdir), "-n", name,
                           "-v", version])
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    zip_path = ((result or {}).get("Data") or {}).get("Packages") or ""
    if not zip_path or not pathlib.Path(zip_path).is_file():
        die("pack reported success but produced no zip", packages=zip_path)
    return zip_path, report


# --------------------------------------------------------------------------- deploy


def live_at_version(name, version):
    for r in deployments():
        if r.get("PackageName") != name or tombstone(r):
            continue
        if r.get("CurrentPackageVersion") == version:
            return r.get("Name")
    return None


def name_taken(deploy_name):
    return any(r.get("Name") == deploy_name and not tombstone(r) for r in deployments())


def folder_id(fully_qualified_name, required=True):
    """Resolve a folder path to the numeric Id that ont:processFolderId wants.

    The deploy output gives a FolderPath; the TTL needs the numeric Id, and the one place the CLI
    exposes it is OrganizationUnitId in `uip or processes get --all-fields`. `uip or folders get`
    takes only a GUID or key, never a path, and `uip or processes list` returns only the GUID
    FolderKey. So: list the folder's processes by path, then get one of them with all fields.
    A deployed jobs folder always carries at least one release, so the route is total here.
    """
    records = release_records(fully_qualified_name, allow_fail=not required)
    if not records:
        if not required:
            return None
        die("no processes in folder %r; cannot resolve its numeric id "
            "(OrganizationUnitId comes from `uip or processes get --all-fields`)"
            % fully_qualified_name)
    detail = uip_json(["or", "processes", "get", records[0].get("Key", ""), "--all-fields"]) or {}
    data = detail.get("Data") or {}
    numeric_id = data.get("OrganizationUnitId")
    if numeric_id is None:
        die("`uip or processes get --all-fields` returned no OrganizationUnitId for %r"
            % records[0].get("Name"))
    return {"ok": True, "folderId": numeric_id, "folderKey": records[0].get("FolderKey"),
            "path": fully_qualified_name}


def deploy_release(name, version, deploy_name, execute):
    """`deploy run` does NOT upgrade an existing deployment: it CREATES one, plus a new
    Orchestrator folder (-n required, fresh DeploymentKey returned). So a new version means a NEW
    deployment in a NEW folder, and the action's ont:processFolderId is then repointed at it.

    PARENT_FOLDER_PATH matters and defaults to Shared for a reason. A solution folder created at
    the ROOT gets no user with unattended robot permissions, so the service cannot start the job
    there: Orchestrator answers StartJobs with HTTP 409, errorCode 1671, "Couldn't find any user
    with unattended robot permissions in the current folder", and the invoke reports a bare
    "Unexpected error" on the Running job step. A folder created UNDER Shared inherits Shared's
    assignments and runs the job. Verified both ways.
    """
    # Idempotence first. Deploying a version that is ALREADY running is a no-op, not a new folder;
    # otherwise a repeated deploy quietly multiplies folders, each carrying the same processes,
    # and only one of them is the folder the TTL names.
    already = live_at_version(name, version)
    if already:
        return {"ok": True, "noop": True, "reason": "already deployed",
                "deployment": already, "version": version,
                "folder": folder_id("%s/%s" % (PARENT_FOLDER_PATH, already), required=False)}

    if name_taken(deploy_name):
        die("a deployment named %r already exists at a different version; pass a different name, "
            "or uninstall the old one. Reusing the name would create a duplicate rather than "
            "upgrade it." % deploy_name)

    argv = ["solution", "deploy", "run", "-n", deploy_name, "--package-name", name,
            "--package-version", version, "--folder-name", deploy_name,
            "--parent-folder-path", PARENT_FOLDER_PATH]
    if not execute:
        return {"ok": True, "dryRun": True, "command": [UIP] + argv}
    uip_json(argv)
    # The folder id is what the TTL patch needs, and deploy run reports only the path.
    return {"ok": True, "deployment": deploy_name, "version": version,
            "folder": folder_id("%s/%s" % (PARENT_FOLDER_PATH, deploy_name))}


# --------------------------------------------------------------------------- await


def release_records(folder_path, allow_fail=False):
    data = uip_json(["or", "processes", "list", "--folder-path", folder_path],
                    allow_fail=allow_fail) or {}
    return data.get("Data") or []


def release_version(record):
    # `uip or processes list` reports the release version as ProcessVersion. Verified live.
    return record.get("ProcessVersion")


def await_release(process, want, folder_path):
    """Poll rather than assume. A stale Release is indistinguishable from a fresh one at the API
    surface, and invoking against one is what produced three consecutive
    JsCodedFunction.ValidationFailed faults: the contract had moved on, the deployed job had not.

    Three outcomes: ready (exit 0), stale (keep polling until the timeout), missing (fail at once,
    listing what the folder does contain).
    """
    got = None
    for attempt in range(AWAIT_POLLS):
        records = release_records(folder_path)
        hit = next((r for r in records if r.get("Name") == process), None)
        if hit is None:
            die("release %r not found in folder %s" % (process, folder_path),
                state="missing", available=[r.get("Name") for r in records])
        got = release_version(hit)
        if got == want:
            return {"ok": True, "state": "ready", "process": process, "version": got}
        if attempt + 1 < AWAIT_POLLS:
            time.sleep(AWAIT_INTERVAL)
    die("timed out waiting for %s to reach %s" % (process, want),
        state="stale", process=process, version=got, wanted=want)


# --------------------------------------------------------------------------- entry point


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("version")
    sub.add_parser("stage")

    p = sub.add_parser("pack")
    p.add_argument("version")
    p.add_argument("outdir", nargs="?")

    p = sub.add_parser("publish")
    p.add_argument("version")
    p.add_argument("--execute", action="store_true")

    p = sub.add_parser("deploy")
    p.add_argument("version")
    p.add_argument("deployment_name", nargs="?")
    p.add_argument("--execute", action="store_true")

    p = sub.add_parser("folder-id")
    p.add_argument("path", help="fully qualified folder name, e.g. Shared/support-jobs")

    p = sub.add_parser("await")
    p.add_argument("process")
    p.add_argument("version")
    p.add_argument("--folder-path", required=True,
                   help="fully qualified folder name, e.g. Shared/support-jobs-1-0-3")

    args = ap.parse_args()
    name = solution_name()

    if args.cmd == "version":
        emit(version_info(name))

    elif args.cmd == "stage":
        staging, report = stage(solution_src())
        report.update({"ok": True, "staging": str(staging)})
        emit(report)

    elif args.cmd == "pack":
        outdir = args.outdir or tempfile.mkdtemp(prefix="ontology-pack-")
        zip_path, report = pack(solution_src(), name, args.version, outdir)
        emit({"ok": True, "zip": zip_path, "bytes": os.path.getsize(zip_path),
              "staged": report["staged"]})

    elif args.cmd == "publish":
        # Route: pack locally, then upload the .zip to the tenant solution feed.
        #
        # NOT `uip solution projects publish --project-name`. That publishes an existing *cloud*
        # solution project, and the name it wants is a Studio Web project name, not the deployment
        # name; passing the solution's own name fails with "Project with name '<name>' not found"
        # (error 2003). The CLI cannot enumerate cloud project names either (`projects list` reads
        # only the on-disk manifest), so that route is a dead end. Packing from source needs no
        # cloud project at all.
        if not args.execute:
            emit({"ok": True, "dryRun": True, "steps": [
                [sys.argv[0], "stage"],
                [UIP, "solution", "pack", "<staging>", "<outdir>", "-n", name, "-v", args.version],
                [UIP, "solution", "publish", "<zip>", "--wait"]]})
        else:
            outdir = tempfile.mkdtemp(prefix="ontology-pack-")
            zip_path, _ = pack(solution_src(), name, args.version, outdir)
            # --wait is not optional. publish is ASYNCHRONOUS; deploying before it completes fails
            # with a package-not-found error that never mentions publishing.
            uip_json(["solution", "publish", zip_path, "--wait"])
            shutil.rmtree(outdir, ignore_errors=True)
            emit({"ok": True, "published": name, "version": args.version})

    elif args.cmd == "deploy":
        deploy_name = args.deployment_name or os.environ.get("DEPLOY_NAME") or name
        emit(deploy_release(name, args.version, deploy_name, args.execute))

    elif args.cmd == "folder-id":
        emit(folder_id(args.path))

    elif args.cmd == "await":
        emit(await_release(args.process, args.version, args.folder_path))


if __name__ == "__main__":
    main()
