#!/usr/bin/env python3
"""Apply a derived entity set into a UiPath solution on disk, locally.

Usage:
  apply-entities.py --entities entities.json --solution <SOLUTION_DIR>
                    [--open-items <PATH>] [--dry-run]

Four passes (references/datafabric-emission-guide.md § The applier):
  0  validate the graph   self-references discarded, cycles fail hard, targets exist
  1  entities             uip df entities create <Name> --local, SCALAR FIELDS ONLY
  2  gate                 uip df entities validate --local
  3  open items           the complex tier, as an ordered checklist with commands

The local authoring path carries scalar fields only. RELATIONSHIP and CHOICE_SET_*
cannot be authored into a solution — not by the CLI, and not by editing the resource
file either: `validate --local` rejects both with FIELD_TYPE_NOT_ALLOWED, and
`uip df choice-sets` has no --local flag. So this script never writes into
resources/solution_folder/; the CLI owns those files. The complex tier leaves as
open items for the engineer to run against the target tenant after deploy.

Local only: no login, no tenant, no record is written.

Exit 0 when every pass completed; exit 1 with one line per failure.
"""

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys

CLI_ENV = dict(os.environ, UIPATH_CLI_DISABLE_VERSION_SYNC="1")

SCALAR_TYPES = {"STRING", "MULTILINE_TEXT", "MULTILINE_MAX", "DECIMAL", "BOOLEAN",
                "DATE", "DATETIME_WITH_TZ", "AUTO_NUMBER", "FILE"}

SQL_FOR_CLI = {
    "STRING": "NVARCHAR", "MULTILINE_TEXT": "MULTILINE", "MULTILINE_MAX": "MULTILINE_MAX",
    "DECIMAL": "DECIMAL", "AUTO_NUMBER": "DECIMAL", "BOOLEAN": "BIT", "DATE": "DATE",
    "DATETIME_WITH_TZ": "DATETIMEOFFSET",
}


class ApplyError(Exception):
    pass


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


def scalar_field_body(field):
    """The CLI write shape for `uip df entities create --body`."""
    if field["type"] not in SCALAR_TYPES:
        raise ApplyError(f"field {field['name']}: {field['type']} is not a scalar type; "
                         f"complex fields are open items, not solution content")
    body = {"name": field["name"], "type": field["type"]}
    for key in ("displayName", "description", "lengthLimit", "decimalPrecision",
                "minValue", "maxValue", "defaultValue"):
        if field.get(key) is not None:
            body[key] = field[key]
    for key in ("isRequired", "isUnique", "isEncrypted"):
        if field.get(key):
            body[key] = True
    return body


def run_cli(cmd, dry_run, cwd):
    printable = shlex.join(cmd)
    if dry_run:
        print(f"  [dry-run] {printable}")
        return None
    if shutil.which(cmd[0]) is None:
        raise ApplyError(f"{cmd[0]} not found on PATH; install the UiPath CLI or use --dry-run")
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, env=CLI_ENV)
    if proc.returncode != 0:
        raise ApplyError(f"{printable}\n{proc.stdout.strip()}\n{proc.stderr.strip()}")
    return proc.stdout


def entity_resource_path(solution, name):
    return os.path.join(solution, "resources", "solution_folder", "entity", "native",
                        f"{name}.json")


def read_resource(solution, name):
    path = entity_resource_path(solution, name)
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh).get("resource") or {}
    except (OSError, json.JSONDecodeError) as exc:
        raise ApplyError(f"{path}: {exc}")


def minted_id(solution, name):
    """Read back the id the CLI minted. Returns None before the entity exists."""
    resource = read_resource(solution, name)
    return resource.get("key") if resource else None


def scalar_drift(solution, name, entity):
    """What the solution ships minus what the model says. Empty when they agree.

    Existence is not agreement: a re-derived model applied over an older one
    would otherwise report success while shipping the stale schema.
    """
    resource = read_resource(solution, name)
    if not resource:
        return []
    try:
        schema = json.loads(resource.get("spec", {}).get("resourceJson") or "{}")
    except json.JSONDecodeError as exc:
        return [f"resourceJson is not readable ({exc})"]
    on_disk = {f["Name"]: f for f in schema.get("Fields", [])
               if isinstance(f, dict) and not f.get("IsSystemField") and f.get("Name")}
    wanted = {f["name"]: f for f in entity.get("fields", [])}
    delta = []
    for missing in sorted(set(wanted) - set(on_disk)):
        delta.append(f"{missing} is in the model and not in the solution")
    for extra in sorted(set(on_disk) - set(wanted)):
        if extra not in {r["name"] for r in entity.get("relationships", [])} and \
           extra not in {c["name"] for c in entity.get("choiceSetFields", [])}:
            delta.append(f"{extra} is in the solution and not in the model")
    for shared in sorted(set(wanted) & set(on_disk)):
        want, have = wanted[shared], on_disk[shared]
        want_sql = SQL_FOR_CLI.get(want["type"])
        have_sql = (have.get("SqlType") or {}).get("Name")
        if want_sql and have_sql and want_sql != have_sql:
            delta.append(f"{shared} is {have_sql}, the model says {want_sql}")
        want_len, have_len = want.get("lengthLimit"), (have.get("SqlType") or {}).get("LengthLimit")
        if want_len is not None and have_len is not None and int(want_len) != int(have_len):
            delta.append(f"{shared} lengthLimit is {have_len}, the model says {want_len}")
        if bool(want.get("isRequired")) != bool(have.get("IsRequired")):
            delta.append(f"{shared} isRequired is {bool(have.get('IsRequired'))}, "
                         f"the model says {bool(want.get('isRequired'))}")
    return delta


def open_items_text(model, solution):
    entities = {e["name"]: e for e in model["entities"]}
    lines = ["## Data Fabric — complex fields", "",
             "These could not ship in the solution: the local authoring path carries scalar",
             "fields only, and `uip df choice-sets` has no local form. Run them against the",
             "target tenant after the solution deploys, top to bottom.", ""]

    if model.get("choiceSets"):
        lines += ["### Choice sets", "",
                  "Value order fixes each value's `NumberId`, which is immutable once records",
                  "exist. Create them in the order listed, then re-read and check the numbers",
                  "before any record is written.", ""]
        for cs in model["choiceSets"]:
            values = ", ".join(f"`{v['name']}`={v['numberId']}" for v in cs["values"])
            lines.append(f"- [ ] Create **`{cs['name']}`** — expected numbers: {values}")
            lines.append(f"      `uip df choice-sets create \"{cs['name']}\" --output json`")
            for value in cs["values"]:
                lines.append(f"      `uip df choice-set-values create <choice-set-id> "
                             f"\"{value['name']}\" --output json`")
            lines.append(f"      `uip df choice-sets list-values <choice-set-id> --output json` "
                         f"— check every number against the list above.")
            lines.append(f"      `uip solution resources add --source remote --kind ChoiceSet "
                         f"--name \"{cs['name']}\" --output json` — brings it into the solution "
                         f"as a referenced resource, so later deploys carry it.")
        lines.append("")

    cs_fields = [(e, f) for e in model["entities"] for f in e.get("choiceSetFields", [])]
    if cs_fields:
        lines += ["### Choice-set fields", ""]
        for entity, field in cs_fields:
            kind = "CHOICE_SET_MULTIPLE" if field.get("multiple") else "CHOICE_SET_SINGLE"
            req = ',"isRequired":true' if field.get("isRequired") else ""
            lines.append(f"- [ ] Add **`{entity['name']}.{field['name']}`** → choice set "
                         f"`{field['choiceSet']}`"
                         f"{' (required)' if field.get('isRequired') else ''}")
            lines.append(f"      `uip df entities update <{entity['name']}-id> --body "
                         f"'{{\"addFields\":[{{\"name\":\"{field['name']}\","
                         f"\"type\":\"{kind}\",\"choiceSetId\":\"<choice-set-id>\""
                         f"{req}}}]}}' --output json`")
        lines.append("")

    rels = [(e, r) for e in model["entities"] for r in e.get("relationships", [])]
    if rels:
        lines += ["### Relationship fields", "",
                  "`referenceFieldId` is the **display field** of the target — it decides what",
                  "renders in pickers, and it is not the target's `Id`.", ""]
        for entity, rel in rels:
            target = entities.get(rel["target"], {})
            display = target.get("displayField") or "<CHOOSE A DISPLAY FIELD — none proposed>"
            lines.append(f"- [ ] Add **`{entity['name']}.{rel['name']}`** → `{rel['target']}`, "
                         f"displaying `{display}`")
            req = ',"isRequired":true' if rel.get("isRequired") else ""
            lines.append(f"      `uip df entities update <{entity['name']}-id> --body "
                         f"'{{\"addFields\":[{{\"name\":\"{rel['name']}\","
                         f"\"type\":\"RELATIONSHIP\","
                         f"\"referenceEntityId\":\"<{rel['target']}-id>\","
                         f"\"referenceFieldId\":\"<{rel['target']}.{display}-field-id>\""
                         f"{req}}}]}}' --output json`")
        lines.append("")
        undecided = sorted({r["target"] for _e, r in rels
                            if not entities.get(r["target"], {}).get("displayField")})
        if undecided:
            lines += ["**Choose a display field first** for " +
                      ", ".join(f"`{n}`" for n in undecided) +
                      " — no STRING field was available to propose one, and the display field "
                      "decides what renders in every picker.", ""]
        blocked = sorted({e["name"] for e, _r in rels})
        lines += ["### Blocked until the fields above exist", "",
                  "A workflow that traverses a relationship cannot be built before the field",
                  "exists, because the generated entity types come from the schema. Entities "
                  "affected: " + ", ".join(f"`{n}`" for n in blocked) + ".", ""]

    ids = {name: minted_id(solution, name) for name in sorted(entities)}
    known = {k: v for k, v in ids.items() if v}
    if known:
        lines += ["### Ids minted in the solution", "",
                  "These are the ids the solution ships with; after deploy, confirm each against",
                  "`uip df entities list --folder-key <new-folder> --output json`.", "",
                  "| Entity | Id in the solution |", "|---|---|"]
        lines += [f"| `{name}` | `{value}` |" for name, value in sorted(known.items())]
        lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--entities", required=True)
    ap.add_argument("--solution", required=True)
    ap.add_argument("--open-items")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    try:
        with open(args.entities, encoding="utf-8") as fh:
            model = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        raise ApplyError(f"--entities {args.entities}: {exc}")
    for key in ("project", "entities"):
        if key not in model:
            raise ApplyError(f"--entities {args.entities}: no {key!r} key")
    if not os.path.isdir(args.solution):
        raise ApplyError(f"--solution {args.solution} is not a directory")
    project = model["project"]
    entities = {e["name"]: e for e in model["entities"]}

    # ---- pass 0: validate the graph ----------------------------------------
    missing = sorted({r["target"] for e in model["entities"]
                      for r in e.get("relationships", []) if r["target"] not in entities})
    if missing:
        raise ApplyError("relationship targets not in the model: " + ", ".join(missing))
    edges = sorted({(e["name"], r["target"]) for e in model["entities"]
                    for r in e.get("relationships", []) if r["target"] != e["name"]})
    cycle = find_cycle(edges)
    if cycle:
        raise ApplyError("relationship cycle: " + " -> ".join(cycle) +
                         "; normalize the ontology further before modelling it")
    print(f"pass 0: {len(entities)} entities, {len(edges)} edge(s), no cycle")

    # ---- pass 1: entities, scalar fields only -------------------------------
    created, drifted = 0, []
    for name in sorted(entities):
        entity = entities[name]
        if os.path.exists(entity_resource_path(args.solution, name)):
            delta = scalar_drift(args.solution, name, entity)
            if delta:
                drifted.append((name, delta))
                print(f"  ! {name} differs from the model: {'; '.join(delta)}")
            else:
                print(f"  = {name} matches")
            continue
        body = {"displayName": entity.get("displayName") or name,
                "description": entity.get("description") or "",
                "fields": [scalar_field_body(f) for f in entity["fields"]]}
        run_cli(["uip", "df", "entities", "create", name, "--local",
                 "--project-name", project, "--body", json.dumps(body, sort_keys=True),
                 "--output", "json"], args.dry_run, args.solution)
        created += 1
        print(f"  + {name} ({len(entity['fields'])} scalar field(s))")
    print(f"pass 1: {created} created, {len(entities) - created} already present")
    if drifted:
        raise ApplyError(
            "the solution's entities no longer match the model:\n  " +
            "\n  ".join(f"{n}: {'; '.join(d)}" for n, d in drifted) +
            "\nRe-applying would ship the stale schema and report success. Update them with "
            "`uip df entities update <Name> --local --body '{\"addFields\":[…]}'`, or delete "
            "and re-create, then run again.")

    # ---- pass 2: gate -------------------------------------------------------
    if args.dry_run:
        print("pass 2: [dry-run] uip df entities validate --local")
    else:
        run_cli(["uip", "df", "entities", "validate", "--local", "--output", "json"],
                False, args.solution)
        print("pass 2: validate --local passed")

    # ---- pass 3: open items -------------------------------------------------
    complex_count = sum(len(e.get("relationships", [])) + len(e.get("choiceSetFields", []))
                        for e in model["entities"]) + len(model.get("choiceSets", []))
    if not complex_count:
        print("pass 3: no complex tier — the model ships whole")
    elif not args.open_items:
        print(f"pass 3: {complex_count} complex item(s) and no --open-items path given; "
              f"nothing written", file=sys.stderr)
        return 1
    else:
        text = open_items_text(model, args.solution)
        if args.dry_run:
            print(f"  [dry-run] write {args.open_items} ({len(text.splitlines())} lines)")
        else:
            os.makedirs(os.path.dirname(os.path.abspath(args.open_items)), exist_ok=True)
            with open(args.open_items, "w", encoding="utf-8") as fh:
                fh.write(text + "\n")
        print(f"pass 3: {complex_count} complex item(s) -> {args.open_items}")

    print(f"\nNext: uip solution pack \"{args.solution}\" --dry-run")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ApplyError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
