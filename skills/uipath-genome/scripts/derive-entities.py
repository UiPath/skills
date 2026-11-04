#!/usr/bin/env python3
"""Derive a Data Fabric entity set from an ontology-bundle inventory.

Usage:
  derive-entities.py --inventory <inventory.json> --project <EntityProject> --out entities.json
                     [--overrides <overrides.json>] [--previous <entities.json>]
                     [--scope tenant|folder]

Emits only what the inputs and the platform FORCE: `direct` entities and fields,
`junction` entities for many-to-many, and `split-forced` where a platform cap leaves
no option. Consolidation, decomposition and federated views need a consumption
pattern and are never emitted here — see references/entity-derivation-guide.md.

Deterministic: given the same (inventory, overrides, previous) the output is byte
identical. Keys are sorted and every list has a stable order.

--previous carries choice-set numberIds forward. numberId is immutable once deployed,
so a re-run must never renumber an existing value.

--overrides is a JSON object; every key optional:
  { "replicas":      { "<EntityName>": "<source system>" },
    "folderScoped":  { "<EntityName>": "<folder>" },
    "displayFields": { "<EntityName>": "<FieldName>" },
    "lookupEntities": ["<CLASS_IRI>"] }

Exit 0 on a derivation; exit 1 naming a cycle's members or a rule that cannot be
satisfied.
"""

import argparse
import json
import re
import sys

XSD = "http://www.w3.org/2001/XMLSchema#"

RESERVED_FIELDS = {"id", "createdby", "createtime", "updatedby", "updatetime", "recordowner"}

# XSD -> (CLI type, extra options). Never emits a UI-broken type.
TYPE_MAP = {
    XSD + "string": ("STRING", {}),
    XSD + "normalizedString": ("STRING", {}),
    XSD + "token": ("STRING", {}),
    XSD + "anyURI": ("STRING", {}),
    XSD + "integer": ("DECIMAL", {"decimalPrecision": 0}),
    XSD + "int": ("DECIMAL", {"decimalPrecision": 0}),
    XSD + "long": ("DECIMAL", {"decimalPrecision": 0}),
    XSD + "short": ("DECIMAL", {"decimalPrecision": 0}),
    XSD + "nonNegativeInteger": ("DECIMAL", {"decimalPrecision": 0}),
    XSD + "positiveInteger": ("DECIMAL", {"decimalPrecision": 0}),
    XSD + "decimal": ("DECIMAL", {"decimalPrecision": 2}),
    XSD + "float": ("DECIMAL", {"decimalPrecision": 2}),
    XSD + "double": ("DECIMAL", {"decimalPrecision": 2}),
    XSD + "boolean": ("BOOLEAN", {}),
    XSD + "date": ("DATE", {}),
    XSD + "dateTime": ("DATETIME_WITH_TZ", {}),
    XSD + "dateTimeStamp": ("DATETIME_WITH_TZ", {}),
}

SQL_FOR_CLI = {
    "STRING": "NVARCHAR", "MULTILINE_TEXT": "NVARCHAR", "MULTILINE_MAX": "NVARCHAR",
    "DECIMAL": "DECIMAL", "AUTO_NUMBER": "DECIMAL", "BOOLEAN": "BIT", "DATE": "DATE",
    "DATETIME_WITH_TZ": "DATETIMEOFFSET", "CHOICE_SET_SINGLE": "INT",
    "CHOICE_SET_MULTIPLE": "NVARCHAR", "RELATIONSHIP": "UNIQUEIDENTIFIER",
    "FILE": "UNIQUEIDENTIFIER",
}


class DeriveError(Exception):
    pass


# --------------------------------------------------------------------------- #
# Naming — entity-derivation-guide.md § Naming. Fixed before the first name.
# --------------------------------------------------------------------------- #

def local_name(iri):
    for sep in ("#", "/"):
        if sep in iri:
            iri = iri.rsplit(sep, 1)[-1]
    return iri or "Unnamed"


def pascal(text):
    parts = re.split(r"[^A-Za-z0-9]+", text)
    expanded = []
    for part in parts:
        if not part:
            continue
        expanded.extend(re.findall(r"[A-Z]+(?![a-z])|[A-Z][a-z0-9]*|[a-z0-9]+", part) or [part])
    return "".join(p[:1].upper() + p[1:] for p in expanded if p)


def normalize(iri, kind, taken, register, owner=None):
    """kind is 'entity' or 'field'. Records a register row for any change."""
    raw = local_name(iri)
    name = raw
    stripped = re.sub(r"^(has|is|had)(?=[A-Z_])", "", name)
    if len(stripped) >= 3:
        name = stripped
    name = pascal(name)
    if kind == "field":
        name = re.sub(r"[^A-Za-z0-9]", "", name)
    else:
        name = re.sub(r"[^A-Za-z0-9_]", "", name)
    if name and name[0].isdigit():
        name = "N" + name
    if len(name) < 3:
        name += "Fld" if kind == "field" else "Ent"
    if kind == "field" and owner and name.lower() == owner.lower():
        name = name + "Value"
    if kind == "field" and name.lower() in RESERVED_FIELDS:
        name = name + "Value"
    base, n = name, 2
    while name.lower() in taken:
        name = f"{base}{n}"
        n += 1
    taken.add(name.lower())
    if name != raw:
        register.add(source="convention", from_iri=iri,
                     subject=f"{owner}.{name}" if owner else name,
                     statement=f"renamed from the IRI local name {raw!r} to {name!r}",
                     expressible="yes", locus=None, level=None,
                     candidate=None, resolution="default-applied",
                     note="entity-derivation-guide.md § Naming")
    return name


# --------------------------------------------------------------------------- #

class Register:
    def __init__(self):
        self.rows = []

    def add(self, **kw):
        row = {"source": kw["source"], "from": kw.get("from_iri"),
               "subject": kw.get("subject"), "statement": kw["statement"],
               "expressible": kw.get("expressible"), "locus": kw.get("locus"),
               "level": kw.get("level"), "candidate": kw.get("candidate"),
               "resolution": kw.get("resolution", "deferred"),
               "evidence": kw.get("evidence") or {}, "note": kw.get("note")}
        self.rows.append(row)

    def finalize(self):
        ordered = sorted(self.rows, key=lambda r: ((r["subject"] or ""), r["statement"]))
        for i, row in enumerate(ordered, 1):
            row["id"] = f"R{i}"
        return [{k: row[k] for k in sorted(row)} for row in ordered]


def shape_index(inventory):
    """class IRI -> { property path -> property shape }"""
    out = {}
    for shape in inventory.get("shapes", []):
        target = shape.get("targetClass")
        if not target:
            continue
        bucket = out.setdefault(target, {})
        for prop in shape.get("properties", []):
            if prop.get("path"):
                bucket[prop["path"]] = prop
    return out


def r2rml_index(inventory):
    """(class IRI, predicate IRI) -> {logicalTable, column}"""
    out = {}
    for tmap in inventory.get("triplesMaps", []):
        cls = tmap.get("subjectClass")
        table = tmap.get("logicalTable")
        if not cls:
            continue
        for pom in tmap.get("predicateObjectMaps", []):
            if pom.get("column"):
                out[(cls, pom["predicate"])] = {"logicalTable": table, "column": pom["column"]}
    return out


def pick_type(prop, shape, register, subject):
    datatype = (shape or {}).get("datatype") or prop.get("range")
    if datatype in TYPE_MAP:
        cli, extra = TYPE_MAP[datatype]
        return cli, dict(extra)
    if datatype:
        register.add(source="metadata", from_iri=datatype, subject=subject,
                     statement=f"datatype {local_name(datatype)} has no Data Fabric counterpart; "
                               f"emitted STRING",
                     expressible="no", candidate="assumed", resolution="default-applied")
    else:
        register.add(source="metadata", from_iri=prop.get("iri"), subject=subject,
                     statement="no datatype and no range; emitted STRING",
                     expressible="yes", candidate=None, resolution="default-applied")
    return "STRING", {}


def classify_cardinality(prop, shapes):
    """many-to-one | one-to-many | one-to-one | many-to-many"""
    functional = prop.get("functional", False)
    inverse = prop.get("inverseFunctional", False)
    if not functional:
        for dom in prop.get("domain", []):
            shape = shapes.get(dom, {}).get(prop["iri"])
            if shape and shape.get("maxCount") == 1:
                functional = True
                break
    if functional and inverse:
        return "one-to-one"
    if functional:
        return "many-to-one"
    if inverse:
        return "one-to-many"
    return "many-to-many"


def components(entity_names, edges):
    """Weakly connected components of the relationship graph."""
    parent = {name: name for name in entity_names}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in edges:
        if a in parent and b in parent:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[max(ra, rb)] = min(ra, rb)
    groups = {}
    for name in entity_names:
        groups.setdefault(find(name), []).append(name)
    out = {}
    for i, root in enumerate(sorted(groups), 1):
        for name in sorted(groups[root]):
            out[name] = f"C{i}"
    return out


def find_cycle(edges):
    """Directed cycle over edges [(child, parent)], self-loops already removed."""
    graph = {}
    for a, b in edges:
        graph.setdefault(a, set()).add(b)
    WHITE, GREY, BLACK = 0, 1, 2
    colour, stack = {}, []

    def visit(node):
        colour[node] = GREY
        stack.append(node)
        for nxt in sorted(graph.get(node, ())):
            state = colour.get(nxt, WHITE)
            if state == GREY:
                return stack[stack.index(nxt):] + [nxt]
            if state == WHITE:
                found = visit(nxt)
                if found:
                    return found
        stack.pop()
        colour[node] = BLACK
        return None

    for node in sorted(graph):
        if colour.get(node, WHITE) == WHITE:
            found = visit(node)
            if found:
                return found
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--inventory", required=True)
    ap.add_argument("--project", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--overrides")
    ap.add_argument("--previous")
    ap.add_argument("--scope", default="tenant", choices=("tenant", "folder"))
    args = ap.parse_args()

    with open(args.inventory, encoding="utf-8") as fh:
        inv = json.load(fh)
    overrides = {}
    if args.overrides:
        with open(args.overrides, encoding="utf-8") as fh:
            overrides = json.load(fh)
    previous = {}
    if args.previous:
        with open(args.previous, encoding="utf-8") as fh:
            previous = json.load(fh)

    register = Register()
    shapes = shape_index(inv)
    r2rml = r2rml_index(inv)
    replicas = overrides.get("replicas", {})
    lookup_classes = set(overrides.get("lookupEntities", []))

    classes = {c["iri"]: c for c in inv.get("classes", [])}
    dprops = inv.get("datatypeProperties", [])
    oprops = inv.get("objectProperties", [])
    reified = {r["iri"]: r for r in inv.get("reifiedRelations", [])}

    for note in inv.get("parserNotes", []):
        register.add(source="metadata", statement=f"input construct not interpreted: {note}",
                     expressible="no", candidate="assumed", resolution="deferred",
                     note="ontology-sources-guide.md § Parser limits")

    # ---- which classes become entities -------------------------------------
    props_by_class = {}
    for prop in dprops:
        for dom in prop.get("domain", []):
            props_by_class.setdefault(dom, []).append(prop)

    entity_classes = sorted(
        iri for iri in classes
        if props_by_class.get(iri) or iri in reified
    )
    not_covered = [
        {"from": iri, "why": "class carries no mapped property"}
        for iri in sorted(classes) if iri not in entity_classes
    ]

    taken_entities = set()
    name_of = {}
    for iri in entity_classes:
        name_of[iri] = normalize(iri, "entity", taken_entities, register)

    # ---- object properties: direction and junctions -------------------------
    relationships = {}          # entity name -> list of relationship dicts
    junctions = []
    edges = []

    for prop in oprops:
        domains = [d for d in prop.get("domain", []) if d in name_of]
        ranges = [r for r in prop.get("range", []) if r in name_of]
        if not domains or not ranges:
            register.add(source="metadata", from_iri=prop["iri"],
                         statement="object property with no mapped domain or range; not emitted",
                         expressible="no", candidate="assumed", resolution="deferred")
            continue
        if any(d in reified for d in domains):
            continue  # participants of a reified class are emitted with that entity
        kind = classify_cardinality(prop, shapes)
        for dom in domains:
            for rng in ranges:
                if kind == "many-to-many":
                    junctions.append((prop, dom, rng))
                    continue
                if kind == "one-to-many":
                    child, parent_cls = rng, dom
                else:
                    child, parent_cls = dom, rng
                if kind == "one-to-one":
                    register.add(source="convention", from_iri=prop["iri"],
                                 subject=f"{name_of[child]}.{local_name(prop['iri'])}",
                                 statement="one-to-one: the field was placed on the domain side; "
                                           "the choice is arbitrary",
                                 expressible="yes", locus=None, level=None,
                                 resolution="default-applied")
                relationships.setdefault(name_of[child], []).append(
                    {"prop": prop, "target": name_of[parent_cls], "cardinality": kind})
                edges.append((name_of[child], name_of[parent_cls]))

    # reified relation participants
    for iri, info in sorted(reified.items()):
        if iri not in name_of:
            continue
        by_iri = {p["iri"]: p for p in oprops}
        for part in info["participants"]:
            prop = by_iri.get(part)
            if not prop:
                continue
            for rng in prop.get("range", []):
                if rng in name_of:
                    relationships.setdefault(name_of[iri], []).append(
                        {"prop": prop, "target": name_of[rng], "cardinality": "many-to-one"})
                    edges.append((name_of[iri], name_of[rng]))

    # ---- junction entities --------------------------------------------------
    junction_entities = []
    for prop, dom, rng in sorted(junctions, key=lambda j: (j[0]["iri"], j[1], j[2])):
        jname = normalize(f"{name_of[dom]}{name_of[rng]}", "entity", taken_entities, register)
        junction_entities.append({
            "name": jname,
            "displayName": jname,
            "description": "",
            "provenance": {
                "from": sorted([dom, rng, prop["iri"]]),
                "derivation": "junction",
                "because": f"{local_name(prop['iri'])} is many-to-many; a RELATIONSHIP field is "
                           f"single-valued, so a bridge entity is the only representation",
            },
            "fields": [],
            "relationships": [
                {"name": normalize(dom, "field", set(), Register(), jname), "target": name_of[dom],
                 "cardinality": "many-to-one",
                 "provenance": {"from": [dom], "derivation": "direct"}},
                {"name": normalize(rng, "field", set(), Register(), jname), "target": name_of[rng],
                 "cardinality": "many-to-one",
                 "provenance": {"from": [rng], "derivation": "direct"}},
            ],
            "choiceSetFields": [],
        })
        edges.append((jname, name_of[dom]))
        edges.append((jname, name_of[rng]))
        register.add(source="domain", from_iri=prop["iri"], subject=jname,
                     statement="pair uniqueness on the junction cannot be stated: isUnique is "
                               "per field and there is no composite uniqueness",
                     expressible="no", locus=None, level=None,
                     candidate="transition", resolution="deferred",
                     note="entity-derivation-guide.md § Junctions")

    # ---- choice sets --------------------------------------------------------
    prev_sets = {cs["name"]: cs for cs in previous.get("choiceSets", [])}
    choice_sets = {}

    def choice_set_for(path_iri, values):
        name = pascal(local_name(path_iri)) or "Values"
        existing = choice_sets.get(name)
        if existing:
            return name
        prev = prev_sets.get(name, {})
        pinned = {v["name"]: v["numberId"] for v in prev.get("values", [])}
        nxt = prev.get("nextNumberId", 0)
        out_values = []
        for val in values:
            if val in pinned:
                out_values.append({"name": val, "displayName": val, "numberId": pinned[val]})
            else:
                out_values.append({"name": val, "displayName": val, "numberId": nxt})
                nxt += 1
        for val, num in sorted(pinned.items(), key=lambda kv: kv[1]):
            if val not in values:
                out_values.append({"name": val, "displayName": val, "numberId": num})
        choice_sets[name] = {
            "name": name, "displayName": name,
            "values": sorted(out_values, key=lambda v: v["numberId"]),
            "nextNumberId": nxt,
            "provenance": {"from": [path_iri], "derivation": "direct"},
        }
        return name

    # ---- entities -----------------------------------------------------------
    entities = []
    for iri in entity_classes:
        ename = name_of[iri]
        cls = classes[iri]
        is_replica = ename in replicas
        locus = "external" if is_replica else "uipath"
        taken_fields, fields, cs_fields = set(), [], []

        for prop in sorted(props_by_class.get(iri, []), key=lambda p: p["iri"]):
            fname = normalize(prop["iri"], "field", taken_fields, register, owner=ename)
            subject = f"{ename}.{fname}"
            shape = shapes.get(iri, {}).get(prop["iri"], {})

            if shape.get("in"):
                cs_name = choice_set_for(prop["iri"], shape["in"])
                cs_fields.append({"name": fname, "choiceSet": cs_name, "multiple": False,
                                  "provenance": {"from": [prop["iri"]], "derivation": "direct"}})
                register.add(source="domain", from_iri=prop["iri"], subject=subject,
                             statement=f"closed value set of {len(shape['in'])} values became a "
                                       f"choice set (default D4)",
                             expressible="yes", locus=locus, level=None,
                             candidate="state", resolution="default-applied")
                continue

            cli_type, extra = pick_type(prop, shape, register, subject)
            field = {"name": fname, "type": cli_type,
                     "provenance": {"from": [prop["iri"]], "derivation": "direct"}}
            field.update(extra)

            if shape.get("maxLength") and cli_type == "STRING":
                field["lengthLimit"] = min(int(shape["maxLength"]), 4000)
            if cli_type == "DECIMAL":
                for key, shape_key in (("minValue", "minInclusive"), ("maxValue", "maxInclusive")):
                    if shape.get(shape_key) is not None:
                        try:
                            field[key] = float(shape[shape_key])
                        except (TypeError, ValueError):
                            pass

            min_count = shape.get("minCount") or 0
            if min_count >= 1:
                field["isRequired"] = locus == "uipath"
                register.add(
                    source="process", from_iri=prop["iri"], subject=subject,
                    statement=f"sh:minCount {min_count}: mandatory in the domain",
                    expressible="yes", locus=locus, level=None,
                    candidate="state" if locus == "uipath" else "assumed",
                    resolution="default-applied" if locus == "uipath" else "override",
                    evidence={"replicaOf": replicas.get(ename)} if is_replica else {},
                    note=("isRequired left false: the entity is a replica and the system of "
                          "record holds the guarantee" if is_replica else
                          "isRequired set from the system-of-record default (D1); Phase 2 must "
                          "confirm records are written whole, not completed incrementally"))

            if any(prop["iri"] in key for key in cls.get("hasKey", [])):
                field["isUnique"] = True
            for key_group in cls.get("hasKey", []):
                if len(key_group) == 1 and key_group[0] == prop["iri"]:
                    field["isUnique"] = True
                elif len(key_group) > 1 and prop["iri"] in key_group:
                    register.add(source="domain", from_iri=iri, subject=subject,
                                 statement="composite key cannot be expressed: isUnique is per "
                                           "field",
                                 expressible="no", locus=locus, level=None,
                                 candidate="transition", resolution="deferred")

            if shape.get("pattern"):
                register.add(source="process", from_iri=prop["iri"], subject=subject,
                             statement=f"sh:pattern {shape['pattern']!r} must hold",
                             expressible="no", locus=locus, level=None,
                             candidate="transition", resolution="deferred",
                             note="no Data Fabric field option states a pattern")
            if shape.get("minLength"):
                register.add(source="process", from_iri=prop["iri"], subject=subject,
                             statement=f"sh:minLength {shape['minLength']} must hold",
                             expressible="no", locus=locus, level=None,
                             candidate="transition", resolution="deferred")
            for unsupported in shape.get("unsupported", []):
                register.add(source="process", from_iri=prop["iri"], subject=subject,
                             statement=f"sh:{unsupported} must hold",
                             expressible="no", locus=locus, level=None,
                             candidate="transition", resolution="deferred")

            prov = r2rml.get((iri, prop["iri"]))
            if prov:
                field["r2rml"] = prov
            fields.append(field)

        rels = []
        for rel in sorted(relationships.get(ename, []), key=lambda r: r["prop"]["iri"]):
            rname = normalize(rel["prop"]["iri"], "field", taken_fields, register, owner=ename)
            rels.append({"name": rname, "target": rel["target"],
                         "cardinality": rel["cardinality"],
                         "provenance": {"from": [rel["prop"]["iri"]], "derivation": "direct"}})

        chosen = overrides.get("displayFields", {}).get(ename)
        if not chosen:
            required_strings = [f["name"] for f in fields
                                if f["type"] == "STRING" and f.get("isRequired")]
            any_strings = [f["name"] for f in fields if f["type"] == "STRING"]
            chosen = (required_strings or any_strings or ["Id"])[0]
            register.add(source="domain", from_iri=iri, subject=ename,
                         statement=f"displayField defaulted to {chosen!r} (default D3)",
                         expressible="yes", locus=locus, level=None,
                         resolution="default-applied")

        if len([f for f in fields if f["type"] == "MULTILINE_MAX"]) > 10:
            raise DeriveError(f"{ename}: more than 10 MULTILINE_MAX fields; a split-forced "
                              f"decomposition is required and is not yet implemented")

        entities.append({
            "name": ename, "displayName": cls.get("label") or ename,
            "description": (cls.get("comment") or "")[:512],
            "displayField": chosen,
            "provenance": {"from": [iri],
                           "derivation": "direct",
                           **({"because": "reified relation class: it already is the junction"}
                              if iri in reified else {})},
            "fields": sorted(fields, key=lambda f: f["name"]),
            "relationships": sorted(rels, key=lambda r: r["name"]),
            "choiceSetFields": sorted(cs_fields, key=lambda c: c["name"]),
        })

        if is_replica:
            register.add(source="domain", from_iri=iri, subject=ename,
                         statement=f"entity is a replica of {replicas[ename]}; the system of "
                                   f"record holds every constraint on it",
                         expressible="yes", locus="external", level=None,
                         resolution="override")

    entities.extend(junction_entities)

    # ---- components and cycles ---------------------------------------------
    names = [e["name"] for e in entities]
    real_edges = sorted({(a, b) for a, b in edges if a != b and a in names and b in names})
    cycle = find_cycle(real_edges)
    if cycle:
        raise DeriveError("relationship cycle: " + " -> ".join(cycle) +
                          "; normalize the ontology further before modelling it")
    comp = components(names, real_edges)
    for entity in entities:
        entity["component"] = comp[entity["name"]]

    # ---- envelope: what Phase 2 may not propose -----------------------------
    envelope = []
    adjacency = {}
    for a, b in real_edges:
        adjacency.setdefault(a, set()).add(b)
    for start in sorted(adjacency):
        for mid in sorted(adjacency[start]):
            for end in sorted(adjacency.get(mid, ())):
                envelope.append({
                    "kind": "federated-view", "members": [start, mid, end],
                    "verdict": "impossible",
                    "why": f"{start}->{mid}->{end} is a depth-2 chain; a federated join graph is "
                           f"a depth-1 star"})
    tables = {}
    for entity in entities:
        for field in entity["fields"]:
            table = (field.get("r2rml") or {}).get("logicalTable")
            if table:
                tables.setdefault(table, set()).add(entity["name"])
    for table, members in sorted(tables.items()):
        if len(members) > 1:
            envelope.append({
                "kind": "consolidation", "members": sorted(members), "verdict": "candidate",
                "evidence": {"sharedLogicalTable": table},
                "why": "the source keeps these in one table; evidence only — whether this "
                       "automation reads them together is a Phase 2 question"})

    coverage = {}
    for entity in entities:
        for iri in entity["provenance"]["from"]:
            coverage.setdefault(iri, []).append(entity["name"])

    out = {
        "version": 1,
        "project": args.project,
        "scope": args.scope,
        "choiceSets": sorted(choice_sets.values(), key=lambda c: c["name"]),
        "entities": sorted(entities, key=lambda e: e["name"]),
        "register": register.finalize(),
        "coverage": {k: sorted(set(v)) for k, v in sorted(coverage.items())},
        "envelope": sorted(envelope, key=lambda e: (e["kind"], e["members"])),
        "notCovered": sorted(not_covered, key=lambda n: n["from"]),
    }

    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, sort_keys=True)
        fh.write("\n")

    deferred = sum(1 for r in out["register"] if r["resolution"] == "deferred")
    comps = len({e["component"] for e in out["entities"]})
    print(f"OK: {len(out['entities'])} entities in {comps} component(s), "
          f"{len(out['choiceSets'])} choice set(s), {len(out['register'])} register row(s) "
          f"({deferred} deferred), {len(out['notCovered'])} not covered -> {args.out}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except DeriveError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
