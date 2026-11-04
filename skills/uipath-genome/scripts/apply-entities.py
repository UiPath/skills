#!/usr/bin/env python3
"""Apply a derived entity set into a UiPath solution on disk, locally.

Usage:
  apply-entities.py --entities entities.json --solution <SOLUTION_DIR> [--dry-run]

Five passes (references/datafabric-emission-guide.md § The applier):
  0  validate the graph   self-references discarded, cycles fail hard
  1  mint ids             deterministic per entity name, reused as resource.key and Id
  2  choice sets          write resources/solution_folder/choiceSet/<Name>.json
  3  entities             uip df entities create <Name> --local, SCALAR FIELDS ONLY
  4  complex fields       append Relationship / ChoiceSet fields to the resource the CLI
                          wrote, plus the matching resource.dependencies rows

Local only: no login, no tenant, no record is written. The CLI refuses RELATIONSHIP
and CHOICE_SET_* on the local path but the resource file accepts them, which is why
pass 4 edits the file the CLI produced rather than authoring one from scratch.

Idempotent: pass 3 skips an entity whose resource exists, pass 4 appends only fields
whose Name is absent. Re-running changes nothing.

Exit 0 when every pass completed; exit 1 with one line per failure.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import uuid

UNASSIGNED_FOLDER = "99999999-9999-9999-9999-999999999999"
NS = uuid.UUID("6ba7b811-9dad-11d1-80b4-00c04fd430c8")  # RFC 4122 URL namespace

SQL_FOR_CLI = {
    "STRING": "NVARCHAR", "MULTILINE_TEXT": "NVARCHAR", "MULTILINE_MAX": "NVARCHAR",
    "DECIMAL": "DECIMAL", "AUTO_NUMBER": "DECIMAL", "BOOLEAN": "BIT", "DATE": "DATE",
    "DATETIME_WITH_TZ": "DATETIMEOFFSET", "CHOICE_SET_SINGLE": "INT",
    "CHOICE_SET_MULTIPLE": "NVARCHAR", "RELATIONSHIP": "UNIQUEIDENTIFIER",
    "FILE": "UNIQUEIDENTIFIER",
}

FIELD_FLAGS = (("isRequired", "IsRequired"), ("isUnique", "IsUnique"),
               ("isEncrypted", "IsEncrypted"))
SQL_EXTRAS = (("lengthLimit", "LengthLimit"), ("minValue", "MinValue"),
              ("maxValue", "MaxValue"), ("decimalPrecision", "DecimalPrecision"))


class ApplyError(Exception):
    pass


def entity_guid(project, name):
    return str(uuid.uuid5(NS, f"uipath-genome:entity:{project}:{name}"))


def choiceset_guid(project, name):
    return str(uuid.uuid5(NS, f"uipath-genome:choiceSet:{project}:{name}"))


def find_cycle(edges):
    graph = {}
    for a, b in edges:
        graph.setdefault(a, set()).add(b)
    colour, stack = {}, []

    def visit(node):
        colour[node] = 1
        stack.append(node)
        for nxt in sorted(graph.get(node, ())):
            if colour.get(nxt, 0) == 1:
                return stack[stack.index(nxt):] + [nxt]
            if colour.get(nxt, 0) == 0:
                found = visit(nxt)
                if found:
                    return found
        stack.pop()
        colour[node] = 2
        return None

    for node in sorted(graph):
        if colour.get(node, 0) == 0:
            found = visit(node)
            if found:
                return found
    return None


def sql_type_for(field):
    cli = field["type"]
    if cli not in SQL_FOR_CLI:
        raise ApplyError(f"field {field['name']}: unknown type {cli!r}")
    sql = {"Name": SQL_FOR_CLI[cli]}
    for key, out in SQL_EXTRAS:
        if field.get(key) is not None:
            sql[out] = field[key]
    return sql


def scalar_field_body(field):
    """The CLI write shape for `uip df entities create --body`."""
    body = {"name": field["name"], "type": field["type"]}
    for key in ("displayName", "description", "lengthLimit", "decimalPrecision",
                "minValue", "maxValue", "defaultValue"):
        if field.get(key) is not None:
            body[key] = field[key]
    for key, _ in FIELD_FLAGS:
        if field.get(key):
            body[key] = True
    return body


def resource_field(field):
    """The on-disk resourceJson shape."""
    out = {"Name": field["name"], "DisplayName": field.get("displayName") or field["name"],
           "SqlType": sql_type_for(field), "IsSystemField": False}
    for key, out_key in FIELD_FLAGS:
        out[out_key] = bool(field.get(key))
    return out


def run_cli(cmd, dry_run):
    printable = " ".join(cmd)
    if dry_run:
        print(f"  [dry-run] {printable}")
        return None
    if shutil.which(cmd[0]) is None:
        raise ApplyError(f"{cmd[0]} not found on PATH; install the UiPath CLI or use --dry-run")
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise ApplyError(f"{printable}\n{proc.stdout.strip()}\n{proc.stderr.strip()}")
    return proc.stdout


def entity_resource_path(solution, name):
    return os.path.join(solution, "resources", "solution_folder", "entity", "native",
                        f"{name}.json")


def choiceset_resource_path(solution, name):
    return os.path.join(solution, "resources", "solution_folder", "choiceSet", f"{name}.json")


def write_json(path, payload, dry_run):
    if dry_run:
        print(f"  [dry-run] write {path}")
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--entities", required=True)
    ap.add_argument("--solution", required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    with open(args.entities, encoding="utf-8") as fh:
        model = json.load(fh)
    project = model["project"]
    entities = {e["name"]: e for e in model["entities"]}

    # ---- pass 0: validate the graph ----------------------------------------
    edges = sorted({(e["name"], r["target"]) for e in model["entities"]
                    for r in e.get("relationships", [])
                    if r["target"] != e["name"] and r["target"] in entities})
    missing = sorted({r["target"] for e in model["entities"]
                      for r in e.get("relationships", []) if r["target"] not in entities})
    if missing:
        raise ApplyError("relationship targets not in the model: " + ", ".join(missing))
    cycle = find_cycle(edges)
    if cycle:
        raise ApplyError("relationship cycle: " + " -> ".join(cycle))
    print(f"pass 0: {len(entities)} entities, {len(edges)} edges, no cycle")

    # ---- pass 1: mint ids ---------------------------------------------------
    ids = {name: entity_guid(project, name) for name in sorted(entities)}
    cs_ids = {cs["name"]: choiceset_guid(project, cs["name"]) for cs in model["choiceSets"]}
    print(f"pass 1: minted {len(ids)} entity id(s), {len(cs_ids)} choice-set id(s)")

    # ---- pass 2: choice sets ------------------------------------------------
    for cs in sorted(model["choiceSets"], key=lambda c: c["name"]):
        path = choiceset_resource_path(args.solution, cs["name"])
        if os.path.exists(path):
            print(f"  = choiceSet {cs['name']} exists")
            continue
        resource_json = {
            "Name": cs["name"], "DisplayName": cs.get("displayName") or cs["name"],
            "Data": [{"Name": v["name"], "DisplayName": v.get("displayName") or v["name"],
                      "NumberId": v["numberId"]} for v in cs["values"]],
        }
        write_json(path, {
            "docVersion": "1.0.0",
            "resource": {
                "key": cs_ids[cs["name"]], "name": cs["name"], "kind": "choiceSet",
                "apiVersion": "dataservice.uipath.com/v2",
                "dependencies": [], "isOverridable": True, "runtimeDependencies": [],
                "folders": [{"fullyQualifiedName": "solution_folder"}],
                "spec": {"resourceJson": json.dumps(resource_json, sort_keys=True),
                         "name": cs["name"],
                         "displayName": cs.get("displayName") or cs["name"],
                         "description": ""},
            }}, args.dry_run)
        print(f"  + choiceSet {cs['name']} ({len(cs['values'])} values)")
    print(f"pass 2: {len(model['choiceSets'])} choice set(s)")

    # ---- pass 3: entities, scalar fields only -------------------------------
    created = 0
    for name in sorted(entities):
        entity = entities[name]
        path = entity_resource_path(args.solution, name)
        if os.path.exists(path):
            print(f"  = entity {name} exists")
            continue
        body = {"displayName": entity.get("displayName") or name,
                "description": entity.get("description") or "",
                "fields": [scalar_field_body(f) for f in entity["fields"]]}
        run_cli(["uip", "df", "entities", "create", name, "--local",
                 "--project-name", project, "--body", json.dumps(body, sort_keys=True),
                 "--output", "json"], args.dry_run)
        created += 1
        print(f"  + entity {name} ({len(entity['fields'])} scalar field(s))")
    print(f"pass 3: {created} entity/entities created, "
          f"{len(entities) - created} already present")

    # ---- pass 4: complex fields --------------------------------------------
    touched = 0
    for name in sorted(entities):
        entity = entities[name]
        complex_fields = entity.get("relationships", []) + entity.get("choiceSetFields", [])
        if not complex_fields:
            continue
        path = entity_resource_path(args.solution, name)
        if not os.path.exists(path):
            if args.dry_run:
                print(f"  [dry-run] would append {len(complex_fields)} complex field(s) to {name}")
                continue
            raise ApplyError(f"{path} missing; pass 3 did not create {name}")

        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
        resource = doc["resource"]
        spec = resource["spec"]
        schema = json.loads(spec["resourceJson"])
        schema.setdefault("Fields", [])
        schema.setdefault("Id", resource.get("key") or ids[name])
        schema["FolderId"] = UNASSIGNED_FOLDER
        resource["key"] = schema["Id"]
        present = {f.get("Name", "").lower() for f in schema["Fields"]}
        deps = {(d.get("kind"), d.get("name")) for d in resource.get("dependencies", [])}
        added = 0

        for rel in sorted(entity.get("relationships", []), key=lambda r: r["name"]):
            if rel["name"].lower() in present:
                continue
            schema["Fields"].append({
                "Name": rel["name"], "DisplayName": rel["name"],
                "SqlType": {"Name": "UNIQUEIDENTIFIER"}, "IsSystemField": False,
                "IsRequired": bool(rel.get("isRequired")),
                "FieldDisplayType": "Relationship",
                "ReferenceEntity": {"Name": rel["target"],
                                    "Id": ids[rel["target"]],
                                    "FolderId": UNASSIGNED_FOLDER}})
            deps.add(("Entity", rel["target"]))
            added += 1

        for csf in sorted(entity.get("choiceSetFields", []), key=lambda c: c["name"]):
            if csf["name"].lower() in present:
                continue
            multiple = bool(csf.get("multiple"))
            schema["Fields"].append({
                "Name": csf["name"], "DisplayName": csf["name"],
                "SqlType": {"Name": "NVARCHAR" if multiple else "INT"},
                "IsSystemField": False, "IsRequired": bool(csf.get("isRequired")),
                "FieldDisplayType": "ChoiceSetMultiple" if multiple else "ChoiceSetSingle",
                "ReferenceChoiceSet": {"Name": csf["choiceSet"]}})
            deps.add(("ChoiceSet", csf["choiceSet"]))
            added += 1

        if not added:
            print(f"  = {name} complex fields already present")
            continue
        schema["Fields"].sort(key=lambda f: f.get("Name", ""))
        spec["resourceJson"] = json.dumps(schema, sort_keys=True)
        resource["dependencies"] = [{"kind": k, "name": n} for k, n in sorted(deps)]
        write_json(path, doc, args.dry_run)
        touched += 1
        print(f"  ~ {name}: +{added} complex field(s), "
              f"{len(resource['dependencies'])} dependency row(s)")
    print(f"pass 4: {touched} entity/entities amended")

    print("\nNext: uip df entities validate --local"
          f"\n      uip solution pack \"{args.solution}\" --dry-run")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ApplyError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
