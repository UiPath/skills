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

    An existing manifest is honoured when the contract cannot be lowered: a job whose contract is
    declared some other way already carries a schema the platform can read, and overwriting it
    with a guess would be worse than leaving it. Only the case with neither is fatal.
    """
    module = entry_points_module()
    target = project_dir / "entry-points.json"
    existing = json.loads(target.read_text()) if target.is_file() else None
    try:
        doc = module.manifest(job_source, existing, "content/main.ts")
    except module.Unlowerable as exc:
        if existing and (existing.get("entryPoints") or [{}])[0].get("input"):
            return "kept existing manifest (%s)" % exc
        die("cannot derive entry-points.json for %s and none is committed: %s"
            % (project_dir.name, exc))
    target.write_text(json.dumps(doc, indent=2) + "\n")
    return "derived"


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
        staged.append({"project": project, "from": rel, "to": "main.ts",
                       "bytes": source.stat().st_size, "entryPoints": manifest_status})

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
