#!/usr/bin/env python3
"""Scaffold the Solution that carries an ontology's coded-action jobs.

    solution_scaffold.py --workdir DIR --solution-name NAME
                         --project NAME[=path/to/job.ts] [--project ...]
                         [--template] [--execute]

One Solution per ontology, one Function project per coded action. The projects are the unit
Orchestrator deploys; the jobs.map.json this writes is what solution_release.py stages from.

Two modes, same output shape.

  CLI mode (default)  uip solution init -> uip functions new --empty -> uip solution projects add.
                      The fresh SolutionId comes from `uip solution init`; nothing here mints one.
                      Verified live: this route deploys a real job-capable release
                      (ProcessType=Function), with no SolutionStorage.json and none needed.

  --template          instantiates assets/solution-skeleton instead, kept as the fallback whose
                      manifests mirror a Studio Web export. The skeleton's .uipx CARRIES the
                      SolutionId, so template mode reuses the exported one rather than inventing
                      a value the backend never issued. See assets/NOTES.md.

Both modes write each project's .npmrc: the @uipath npm scope resolves from GitHub Packages, not
npmjs, and `uip functions new`/`uip functions pack` shell out to an installer that 404s without
it. The file references the token as ${GH_NPM_REGISTRY_TOKEN}; no literal token is ever written.
Export GH_NPM_REGISTRY_TOKEN before running with --execute.

Re-running is safe: an existing solution directory is reused, an existing project directory is
left alone, and only the missing pieces are created.

Nothing is written and no `uip` command runs without --execute. The default prints the exact
plan, because scaffolding writes to disk and `uip solution init` is not a read.

Environment:
  UIP_CLI                path to the uip binary (default: "uip")
  GH_NPM_REGISTRY_TOKEN  read by the installer through the generated .npmrc, never by this script
"""

import argparse
import json
import os
import pathlib
import shutil
import subprocess
import sys
import uuid

HERE = pathlib.Path(__file__).resolve().parent
SKELETON = HERE.parent / "assets" / "solution-skeleton"
# The one project directory that survived the export. Every instantiated project is copied from it.
SKELETON_PROJECT = "TagOverdueTicketProcess"
UIP = os.environ.get("UIP_CLI", "uip")
# The @uipath scope lives on GitHub Packages, not npmjs. The token stays an env-var reference the
# installer resolves at run time; writing a literal here would commit a credential to disk.
NPMRC = ("@uipath:registry=https://npm.pkg.github.com/\n"
         "//npm.pkg.github.com/:_authToken=${GH_NPM_REGISTRY_TOKEN}\n")


def die(message, **extra):
    payload = {"ok": False, "error": message}
    payload.update(extra)
    print(json.dumps(payload), file=sys.stderr)
    raise SystemExit(1)


def run(argv, cwd):
    """Run a uip command, returning its stdout. Stderr never reaches stdout.

    `uip` writes an INFO log to stderr even at --log-level error, and one of those lines contains
    a literal "{solutionKey}". Folding the two streams together makes the first brace in the
    stream a log line, so a JSON parse of the result silently yields nothing.
    """
    proc = subprocess.run(argv, cwd=str(cwd), capture_output=True, text=True)
    if proc.returncode != 0:
        tail = " ".join((proc.stderr or proc.stdout or "").strip().splitlines()[-5:])
        die("command failed: %s" % " ".join(argv), detail=tail)
    return proc.stdout


def read_json(path):
    return json.loads(pathlib.Path(path).read_text())


def write_json(path, data):
    pathlib.Path(path).write_text(json.dumps(data, indent=2) + "\n")


def write_npmrc(directory):
    """Write .npmrc for the @uipath scope, if the directory does not carry one already."""
    path = pathlib.Path(directory) / ".npmrc"
    if not path.exists():
        path.write_text(NPMRC)


def parse_project(spec):
    name, _, source = spec.partition("=")
    name = name.strip()
    if not name:
        die("--project needs a project name: %r" % spec)
    return name, (source.strip() or None)


def solution_id_of(solution_dir, solution_name):
    uipx = solution_dir / ("%s.uipx" % solution_name)
    if not uipx.exists():
        candidates = sorted(solution_dir.glob("*.uipx"))
        if not candidates:
            return None, None
        uipx = candidates[0]
    try:
        return uipx, read_json(uipx).get("SolutionId")
    except (ValueError, OSError):
        return uipx, None


# --------------------------------------------------------------------------- CLI mode


def scaffold_cli(workdir, solution_name, projects, execute):
    solution_dir = workdir / solution_name
    steps = []
    plan = []

    existing = solution_dir.exists() and any(solution_dir.glob("*.uipx"))
    if existing:
        steps.append({"step": "init", "status": "reused", "path": str(solution_dir)})
    else:
        plan.append([UIP, "solution", "init", solution_name])
        if execute:
            workdir.mkdir(parents=True, exist_ok=True)
            run([UIP, "solution", "init", solution_name], cwd=workdir)
            steps.append({"step": "init", "status": "created", "path": str(solution_dir)})

    # Before any `uip functions new`: its own install resolves @uipath through the nearest .npmrc
    # up the tree, and the project directory it needs does not exist yet.
    plan.append(["write", str(solution_dir / ".npmrc"), "(@uipath scope -> GitHub Packages)"])
    if execute:
        write_npmrc(solution_dir)

    reported = []
    for name, source in projects:
        project_dir = solution_dir / name
        if project_dir.exists():
            if execute:
                write_npmrc(project_dir)
            steps.append({"step": "functions new", "project": name, "status": "reused"})
            reported.append({"name": name, "path": str(project_dir), "status": "reused",
                             "jobSource": source})
            continue
        # --empty, never the hello-world default: a scaffolded sample job is a second copy of
        # the entry point, free to drift from the job source that phase 2 stages in.
        plan.append([UIP, "functions", "new", name, "--language", "ts", "--empty"])
        plan.append(["write", str(project_dir / ".npmrc"), "(@uipath scope -> GitHub Packages)"])
        plan.append([UIP, "solution", "projects", "add", "./%s" % name,
                     "./%s.uipx" % solution_name])
        if execute:
            run([UIP, "functions", "new", name, "--language", "ts", "--empty"], cwd=solution_dir)
            write_npmrc(project_dir)
            run([UIP, "solution", "projects", "add", "./%s" % name, "./%s.uipx" % solution_name],
                cwd=solution_dir)
            steps.append({"step": "functions new", "project": name, "status": "created"})
        reported.append({"name": name, "path": str(project_dir), "status": "created",
                         "jobSource": source})

    if execute:
        write_jobs_map(solution_dir, projects)
        uipx, solution_id = solution_id_of(solution_dir, solution_name)
        return {"ok": True, "mode": "cli", "solutionDir": str(solution_dir),
                "solutionFile": str(uipx) if uipx else None, "solutionId": solution_id,
                "projects": reported, "steps": steps,
                "jobsMap": str(solution_dir / "jobs.map.json")}

    return {"ok": True, "mode": "cli", "dryRun": True, "solutionDir": str(solution_dir),
            "projects": reported, "steps": steps, "commands": plan}


def write_jobs_map(solution_dir, projects):
    """Record which job source supplies which project's functions/ entry point.

    Paths are resolved by solution_release.py against this file's own directory, so a job that
    lives beside its action TTL is written as a relative path and one outside the tree is written
    absolute. A project with no job source keeps whatever functions/*.ts it has and is packed
    as-is.
    """
    mapping = {name: source for name, source in projects if source}
    path = solution_dir / "jobs.map.json"
    write_json(path, {
        "$comment": [
            "Maps a Solution function project to the job source staged in as",
            "functions/{actionName}.ts at pack time. Relative paths resolve against this",
            "file's directory. solution_release.py copies each one into a staging tree, so",
            "the job source stays the single source of truth and keeps living next to the",
            "action that invokes it. A project listed here MUST NOT have a committed",
            "functions/*.ts: the staged copy supplies it, and a committed one would be a",
            "second copy free to drift.",
        ],
        "projects": mapping,
    })
    return path


# --------------------------------------------------------------------------- template mode


def instantiate_project(skeleton, solution_dir, name, action_name):
    """Copy the skeleton project into place. Returns (status, projectId).

    An already-instantiated project keeps the id its uipath.json carries. Minting a new one on a
    re-run would leave the manifests and the project disagreeing about which project this is, and
    a deploy provisions nothing for a project whose id the manifest does not match.
    """
    src = skeleton / SKELETON_PROJECT
    dst = solution_dir / name
    if dst.exists():
        write_npmrc(dst)
        existing = read_json(dst / "uipath.json").get("projectId")
        return "reused", existing or str(uuid.uuid4())
    project_id = str(uuid.uuid4())
    shutil.copytree(src, dst)
    write_npmrc(dst)

    uiproj = read_json(dst / "project.uiproj")
    uiproj["Name"] = name
    write_json(dst / "project.uiproj", uiproj)

    uipath = read_json(dst / "uipath.json")
    uipath["name"] = name
    uipath["projectId"] = project_id
    uipath["id"] = project_id
    # `uip functions pack` rebuilds this map by scanning functions/, so the value here only has
    # to agree with what the stage step will place there; the exemplar's own entry would not.
    uipath["functions"] = {action_name: "functions/%s.ts:default" % action_name}
    write_json(dst / "uipath.json", uipath)

    package = read_json(dst / "package.json")
    package["name"] = name.lower().replace(" ", "-")
    # The skeleton predates the zod contract idiom; the staged jobs import zod for real, and
    # `uip functions pack` installs from this manifest.
    package.setdefault("dependencies", {}).setdefault("zod", "^4.2.0")
    write_json(dst / "package.json", package)

    entry_id = str(uuid.uuid4())
    entries = read_json(dst / "entry-points.json")
    for entry in entries.get("entryPoints", []):
        entry["uniqueId"] = entry_id
        entry["filePath"] = "content/functions/%s.ts" % action_name
    write_json(dst / "entry-points.json", entries)

    bindings = read_json(dst / "bindings_v2.json")
    for resource in bindings.get("resources", []):
        resource["key"] = str(uuid.uuid4())
        resource["id"] = str(uuid.uuid4())
        value = resource.get("value") or {}
        if "EntryPointUniqueId" in value:
            value["EntryPointUniqueId"]["DefaultValue"] = entry_id
        meta = resource.get("metadata") or {}
        if meta:
            meta["Name"] = action_name
            meta["Slug"] = "/%s" % action_name
            meta["Description"] = None
    write_json(dst / "bindings_v2.json", bindings)
    return "created", project_id


def instantiate_resources(solution_dir, solution_name, name, project_id):
    """Write the descriptors that make the release a job rather than an HTTP endpoint.

    kind: process / type: function / spec.type: "Function" / targetFrameworkValue: "Portable"
    is what produces a ProcessType=Function release. Prune this tree and the package still packs
    and publishes, and the action has nothing to invoke.
    """
    pkg_dir = solution_dir / "resources" / "solution_folder" / "package"
    proc_dir = solution_dir / "resources" / "solution_folder" / "process" / "function"
    pkg_dir.mkdir(parents=True, exist_ok=True)
    proc_dir.mkdir(parents=True, exist_ok=True)
    # Read the shapes from the pristine skeleton, never from the solution being built: the
    # instantiated tree has already had the export's own descriptors cleared out of it.
    tpl_pkg = SKELETON / "resources" / "solution_folder" / "package"
    tpl_proc = SKELETON / "resources" / "solution_folder" / "process" / "function"

    package_key = str(uuid.uuid4())
    pkg = read_json(tpl_pkg / ("%s.json" % SKELETON_PROJECT))
    res = pkg["resource"]
    res["name"] = name
    res["projectKey"] = project_id
    res["key"] = package_key
    res["spec"]["name"] = name
    write_json(pkg_dir / ("%s.json" % name), pkg)

    proc = read_json(tpl_proc / ("%s.json" % SKELETON_PROJECT))
    res = proc["resource"]
    res["name"] = name
    res["projectKey"] = project_id
    res["key"] = str(uuid.uuid4())
    res["dependencies"] = [{"name": name, "kind": "package"}]
    res["spec"]["name"] = name
    res["spec"]["package"] = {"key": package_key}
    res["spec"]["packageName"] = "%s.function.%s" % (solution_name, name)
    write_json(proc_dir / ("%s.json" % name), proc)


def scaffold_template(workdir, solution_name, projects, execute):
    if not SKELETON.exists():
        die("template not found: %s" % SKELETON)
    solution_dir = workdir / solution_name
    wanted = [name for name, _ in projects]

    if not execute:
        return {"ok": True, "mode": "template", "dryRun": True,
                "solutionDir": str(solution_dir), "template": str(SKELETON),
                "wouldInstantiate": wanted,
                "note": "the template's .uipx carries the exported SolutionId; template mode "
                        "reuses it rather than minting one. See assets/NOTES.md."}

    uipx_path = solution_dir / ("%s.uipx" % solution_name)
    if not uipx_path.exists():
        # Take the two manifests and nothing else. The skeleton's project directory and its
        # resource descriptors are boilerplate to instantiate FROM, not content to inherit: the
        # export left descriptors for four projects whose directories it never shipped, and a
        # jobs.map.json pointing at another tree's paths.
        solution_dir.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(SKELETON / "Solution.uipx", uipx_path)
        shutil.copyfile(SKELETON / "SolutionStorage.json", solution_dir / "SolutionStorage.json")
    write_npmrc(solution_dir)
    uipx = read_json(uipx_path)
    storage = read_json(solution_dir / "SolutionStorage.json")

    entries, storage_entries, reported = [], [], []
    for name, source in projects:
        # The descriptors below must name the SAME project id the .uipx does, or deploy
        # provisions nothing for the project.
        action = pathlib.Path(source).stem
        status, project_id = instantiate_project(SKELETON, solution_dir, name, action)
        instantiate_resources(solution_dir, solution_name, name, project_id)
        entries.append({"Type": "Function",
                        "ProjectRelativePath": "%s/project.uiproj" % name,
                        "Id": project_id})
        storage_entries.append({"ProjectId": project_id,
                                "ProjectRelativePath": "%s/project.uiproj" % name})
        reported.append({"name": name, "path": str(solution_dir / name), "status": status,
                         "jobSource": source})

    uipx["Projects"] = entries
    write_json(uipx_path, uipx)
    storage["SolutionId"] = uipx.get("SolutionId")
    storage["Projects"] = storage_entries
    write_json(solution_dir / "SolutionStorage.json", storage)

    write_jobs_map(solution_dir, projects)
    return {"ok": True, "mode": "template", "solutionDir": str(solution_dir),
            "solutionFile": str(uipx_path), "solutionId": uipx.get("SolutionId"),
            "solutionIdSource": "template .uipx (not freshly minted)",
            "projects": reported, "jobsMap": str(solution_dir / "jobs.map.json")}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workdir", required=True, help="directory the solution folder is created in")
    ap.add_argument("--solution-name", required=True, help="solution name, e.g. {ontology}-jobs")
    ap.add_argument("--project", action="append", default=[], metavar="NAME[=JOB.ts]",
                    help="one Function project per coded action; repeatable")
    ap.add_argument("--template", action="store_true",
                    help="instantiate assets/solution-skeleton instead of calling uip")
    ap.add_argument("--execute", action="store_true", help="actually write; default prints the plan")
    args = ap.parse_args()

    if not args.project:
        die("at least one --project is required")
    projects = [parse_project(p) for p in args.project]
    names = [n for n, _ in projects]
    if len(set(names)) != len(names):
        die("duplicate project name in --project")

    workdir = pathlib.Path(args.workdir).expanduser().resolve()
    if args.template:
        result = scaffold_template(workdir, args.solution_name, projects, args.execute)
    else:
        result = scaffold_cli(workdir, args.solution_name, projects, args.execute)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
