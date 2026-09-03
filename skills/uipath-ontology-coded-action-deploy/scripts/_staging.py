"""Build the staging tree a package is made from, and derive each project's manifest.

The source tree is never mutated: a job lives beside the action TTL that invokes it, and staging
copies it in as the project's main.ts inside a temp directory. That is why the solution directory
is not directly packable and everything goes through here.

`uip solution pack` requires each project's entry-points.json and never produces one.
`uip functions pack` would, but it cannot lower the type<T>() contract idiom at all, so the
manifest is derived here from the job's own interfaces instead. `uip solution pack` reads no
TypeScript -- it only zips the tree -- so supplying the manifest alongside main.ts is enough.
"""

import importlib.util
import json
import os
import pathlib
import shutil
import tempfile

from _solution import manifest_projects
from _uip import die, uip_json


def entry_points_module():
    """Load tools/entry_points.py, the shared contract deriver.

    `uip solution pack` requires each project's entry-points.json and never produces one. Studio
    Web's packer derives it; `uip functions pack` cannot, and fails outright on the type<T>()
    idiom the contract guide mandates. So we derive it here from the job's own interfaces, which
    keeps them the single source of truth and keeps this pipeline on `uip solution pack` alone.
    """
    override = os.environ.get("ENTRY_POINTS_TOOL")
    candidates = [pathlib.Path(override)] if override else [
        parent / "tools" / "entry_points.py" for parent in pathlib.Path(__file__).resolve().parents
    ]
    found = next((c for c in candidates if c.is_file()), None)
    if not found:
        die("cannot find tools/entry_points.py above %s; set ENTRY_POINTS_TOOL to its path"
            % pathlib.Path(__file__).resolve().parent)
    spec = importlib.util.spec_from_file_location("ontology_entry_points", found)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_entry_points(project_dir, job_source):
    """Derive the project's entry-points.json from the staged job. Returns a status string.

    A contract that cannot be lowered is fatal here, and deliberately so. This used to fall back to
    "keep whatever manifest is already in the project", which is wrong in the one case it fires:
    the template skeleton ships a manifest, so an unlowerable job inherited the EXEMPLAR's input
    schema and deployed under a contract that has nothing to do with it -- passing every check and
    faulting at invoke time on additionalProperties. A schema that was not derived from this job
    cannot be attributed to it, so there is nothing safe to keep.

    Only the entry point's identity survives from an existing manifest: uniqueId, which the
    project's bindings reference, and which module.manifest carries over.
    """
    module = entry_points_module()
    target = project_dir / "entry-points.json"
    existing = json.loads(target.read_text()) if target.is_file() else None
    try:
        doc = module.manifest(job_source, existing, "content/main.ts")
    except module.Unlowerable as exc:
        die("cannot derive entry-points.json for %s from %s: %s. The manifest is the contract the "
            "platform validates against, and one that was not derived from this job would deploy "
            "the wrong schema. Declare the contract as plain interfaces behind type<T>()."
            % (project_dir.name, pathlib.Path(job_source).name, exc))
    target.write_text(json.dumps(doc, indent=2) + "\n")
    return "derived"


def write_functions_map(project_dir):
    """Point the project's uipath.json functions map at the main.ts staging just wrote.

    `uip functions new --language ts --empty` leaves `"functions": {}`, and `uip solution pack`
    then reports `No functions defined in uipath.json` and produces nothing. The map, the staged
    source and the manifest's `content/main.ts` all have to name the same file, so the step that
    writes the source writes the map -- setting it anywhere earlier means it can drift from what
    is actually staged, and setting it by hand means it can simply be forgotten.
    """
    path = project_dir / "uipath.json"
    if not path.is_file():
        die("%s has no uipath.json; `uip functions new` did not create this project"
            % project_dir.name)
    doc = json.loads(path.read_text())
    wanted = {"main": "main.ts:default"}
    if doc.get("functions") == wanted:
        return "already correct"
    doc["functions"] = wanted
    path.write_text(json.dumps(doc, indent=2) + "\n")
    return "written"


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
        # main.ts at the project root, which is the layout the verified Studio Web export used
        # and what uipath.json's functions map and the manifest's `content/main.ts` both name.
        target = staging / project / "main.ts"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        manifest_status = write_entry_points(staging / project, target)
        map_status = write_functions_map(staging / project)
        staged.append({"project": project, "from": rel, "to": "main.ts",
                       "bytes": source.stat().st_size, "entryPoints": manifest_status,
                       "functionsMap": map_status})

    # Belt and braces: check EVERY project, not just the mapped ones. An unmapped project with a
    # missing or empty main.ts is the same silent failure, and pack will not catch it.
    for project in projects:
        entry = staging / project / "main.ts"
        if not entry.is_file():
            shutil.rmtree(staging, ignore_errors=True)
            die("%s/main.ts is missing and the project is not in jobs.map.json; "
                "pack would publish an empty function" % project)
        if entry.stat().st_size == 0:
            shutil.rmtree(staging, ignore_errors=True)
            die("%s/main.ts is empty; pack would publish an empty function" % project)
        if not (staging / project / "entry-points.json").is_file():
            shutil.rmtree(staging, ignore_errors=True)
            die("%s has no entry-points.json; solution pack requires one per project" % project)

    return staging, {"projects": projects, "authority": authority, "staged": staged}


def pack(src, name, version, outdir):
    staging, report = stage(src)
    try:
        # No `uip functions pack` here. It exists to derive entry-points.json, which stage has
        # already written from the job's interfaces, and it cannot lower the type<T>() contract
        # idiom at all. `uip solution pack` only zips the tree and reads no TypeScript, so a
        # manifest supplied alongside main.ts is exactly what the verified pipeline shipped.
        # (A project with no entry-points.json fails solution pack with an error naming
        # 'uipath-functions pack', a binary that does not exist. stage guards against that.)
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
