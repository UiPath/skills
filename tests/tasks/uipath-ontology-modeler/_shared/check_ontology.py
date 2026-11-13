#!/usr/bin/env python3
"""Grading checks for the ontology tasks, run from the sandbox root via $REFERENCE_DIR.

    check_ontology.py artifacts <WORKDIR> <NAME>       every artifact passes `uip ont artifacts check`, no GUID
    check_ontology.py validate  <SOLUTION_DIR> <NAME>  `uip ont validate --local` is clean and the service ran
    check_ontology.py package   <SOLUTION_DIR> <NAME>  one packed zip; it holds the schema, constraints and mapping
    check_ontology.py classes   <WORKDIR> <NAME> [CLASS…] [--count N]
                                                       offline: each CLASS is declared in <NAME>.ofn, and every
                                                       declared class has rdfs:label, rdfs:comment and a property
                                                       whose domain it is; --count N pins how many are declared

Exit 0 on pass; exit 1 prints the reason. UIP_CLI overrides the `uip` binary (a JS entry point runs with node).
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

GUID = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")
# file-name suffix -> (media type, artifact type); `{name}` prefixes each
ARTIFACTS = {
    ".ofn": ("text/owl-functional", "schema"),
    "-mapping.yarrrml.yml": ("application/yaml", "mapping"),
    "-summary.json": ("application/json", "summary"),
    "-context.json": ("application/json", "context"),
}
REQUIRED_TYPES = {"schema", "constraints", "mapping"}


def uip(*args: str) -> dict:
    cli = os.environ.get("UIP_CLI", "uip")
    command = ["node", cli] if cli.endswith((".js", ".mjs", ".cjs")) else [cli]
    env = {**os.environ, "UIPATH_CLI_DISABLE_VERSION_SYNC": "1"}
    result = subprocess.run([*command, *args, "--output", "json"], text=True, capture_output=True, env=env,
                            timeout=180)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        fail(f"uip {' '.join(args)}: non-JSON output (exit {result.returncode}): {result.stdout}{result.stderr}")


def fail(reason: str):
    print(f"FAIL: {reason}")
    sys.exit(1)


def field(data: dict, name: str):
    for candidate in (name, name[:1].upper() + name[1:], name[:1].lower() + name[1:]):
        if candidate in data:
            return data[candidate]
    return None


def errors(violations) -> list:
    return [v for v in violations or [] if field(v, "severity") == "ERROR"]


def artifact_files(workdir: Path, name: str) -> list[tuple[Path, str, str]]:
    files = []
    for suffix, (media, kind) in ARTIFACTS.items():
        path = workdir / f"{name}{suffix}"
        if path.is_file():
            files.append((path, media, kind))
    files += [(p, "text/turtle", "constraints") for p in sorted(workdir.glob(f"{name}-constraints*.ttl"))]
    return files


def check_artifacts(workdir: Path, name: str):
    files = artifact_files(workdir, name)
    kinds = {kind for _, _, kind in files}
    if not REQUIRED_TYPES <= kinds:
        fail(f"{workdir} is missing {sorted(REQUIRED_TYPES - kinds)}")
    for path, media, kind in files:
        if GUID.search(path.read_text()):
            fail(f"{path.name} holds a GUID; artifacts reference entities by name")
        checked = uip("ont", "artifacts", "check", path.name, "--content-type", media, "--type", kind,
                      "--file", str(path))
        if checked.get("Result") != "Success" or errors(field(checked.get("Data") or {}, "violations")):
            fail(f"artifacts check {path.name}: {json.dumps(checked)[:2000]}")
    print(f"OK: {len(files)} artifacts pass `uip ont artifacts check`")


def check_validate(solution: Path, name: str):
    payload = uip("ont", "validate", "--local", "--solution-folder", str(solution))
    entries = [e for e in payload.get("Data") or [] if isinstance(e, dict) and field(e, "name") == name]
    if payload.get("Result") != "Success" or len(entries) != 1:
        fail(f"validate: {json.dumps(payload)[:2000]}")
    if errors(field(entries[0], "violations")) or field(entries[0], "ServiceValidation") != "Done":
        fail(f"validate not clean: {json.dumps(entries[0])[:2000]}")
    print("OK: validate is clean and the service validated")


def check_package(solution: Path, name: str):
    packages = sorted((solution / "out").glob("*.zip"))
    if len(packages) != 1:
        fail(f"expected one package in {solution / 'out'}, found {[p.name for p in packages]}")
    listed = uip("ont", "files", "list", name, "--package", str(packages[0]))
    artifacts = field(listed.get("Data") or {}, "artifacts") or []
    kinds = {field(a, "type") for a in artifacts}
    if listed.get("Result") != "Success" or not REQUIRED_TYPES <= kinds:
        fail(f"files list --package: {json.dumps(listed)[:2000]}")
    print(f"OK: {packages[0].name} holds {len(artifacts)} ontology files")


def schema_term(name: str) -> str:
    """A class or property as written in the schema: `:X` or the full `<…#X>` IRI."""
    return r"(?::|<https://ontology\.uipath\.com/" + re.escape(name) + r"#)([A-Za-z_][\w.-]*)>?"


def check_classes(workdir: Path, name: str, expected: list[str], count: int | None):
    schema_path = workdir / f"{name}.ofn"
    if not schema_path.is_file():
        fail(f"{schema_path.name} does not exist in {workdir}")
    schema = schema_path.read_text()
    term = schema_term(name)
    declared = re.findall(r"Declaration\(\s*Class\(\s*" + term + r"\s*\)\s*\)", schema)
    if not declared:
        fail(f"{schema_path.name} declares no class")
    for cls in expected:
        if cls not in declared:
            fail(f"{cls} is not declared: no Declaration(Class(:{cls})) in {schema_path.name}")
    if count is not None and len(set(declared)) != count:
        fail(f"expected {count} classes, found {len(set(declared))}: {sorted(set(declared))}")
    domains = set(re.findall(r"(?:Data|Object)PropertyDomain\(\s*" + term + r"\s+" + term + r"\s*\)", schema))
    domain_classes = {cls for _, cls in domains}
    for cls in sorted(set(declared)):
        for annotation in ("rdfs:label", "rdfs:comment"):
            if not re.search(r"AnnotationAssertion\(\s*" + annotation + r"\s+(?::|<[^>]*#)" + re.escape(cls) + r">?\s",
                             schema):
                fail(f"{cls} has no {annotation}")
        if cls not in domain_classes:
            fail(f"{cls} is not the domain of any property")
    print(f"OK: {len(set(declared))} classes declared, each labelled, commented and a property domain: "
          f"{', '.join(sorted(set(declared)))}")


def main():
    if len(sys.argv) >= 4 and sys.argv[1] == "classes":
        folder, name, rest = Path(sys.argv[2]).resolve(), sys.argv[3], sys.argv[4:]
        count = None
        if "--count" in rest:
            at = rest.index("--count")
            if at + 1 >= len(rest) or not rest[at + 1].isdigit():
                fail(__doc__)
            count = int(rest[at + 1])
            rest = rest[:at] + rest[at + 2:]
        check_classes(folder, name, rest, count)
        return
    if len(sys.argv) != 4 or sys.argv[1] not in ("artifacts", "validate", "package"):
        fail(__doc__)
    command, folder, name = sys.argv[1], Path(sys.argv[2]).resolve(), sys.argv[3]
    if not folder.is_dir():
        fail(f"{folder} does not exist")
    {"artifacts": check_artifacts, "validate": check_validate, "package": check_package}[command](folder, name)


if __name__ == "__main__":
    main()
