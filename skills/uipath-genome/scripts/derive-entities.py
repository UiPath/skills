#!/usr/bin/env python3
"""Derive a Data Fabric entity set from an ontology-bundle inventory.

Usage:
  derive-entities.py --inventory <inventory.json> --project <EntityProject> --out entities.json
                     [--overrides <overrides.json>] [--previous <entities.json>]
                     [--scope tenant|folder]

Emits only what the inputs and the platform FORCE: `direct` entities and fields and
`junction` entities for many-to-many. Consolidation, decomposition and federated
views need a consumption pattern and are never emitted here — see
references/entity-derivation-guide.md.

Deterministic: given the same (inventory, overrides, previous, project, scope) the
output is byte identical. Keys are sorted and every list has a stable order.

--previous carries each choice set's proposed value order forward, so a re-run does
not renumber. The authoritative numbers are the server's, assigned when the open
items create the set; read them back with `uip df choice-sets list-values`.

--overrides is a JSON object; every key optional:
  { "systemsOfRecord": ["<EntityName>"],                     # D1: everything else
                                                             # is a replica
    "replicas":       { "<EntityName>": "<source system>" }, # names the source
    "folderScoped":   { "<EntityName>": "<folder>" },
    "displayFields":  { "<EntityName>": "<FieldName>" },
    "lookupEntities": ["<CLASS_IRI>"],
    "annotations": { "authoritativeSource": "<PREDICATE_IRI>",
                     "enforcementMode":     "<PREDICATE_IRI>" } }

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


# How two property shapes on the same path combine. SHACL conjoins them — every
# shape must be satisfied — so the merge takes the most restrictive of each bound,
# never the last one seen. Overwriting silently drops constraints.
MERGE_MAX = ("minCount", "minLength", "minInclusive")   # most restrictive = largest
MERGE_MIN = ("maxCount", "maxLength", "maxInclusive")   # most restrictive = smallest
MERGE_FIRST = ("datatype", "nodeKind", "class", "name", "severity")


def _numeric(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def merge_property_shapes(shapes):
    """Conjoin several property shapes on one path into one."""
    out = {"path": shapes[0].get("path"), "in": [], "patterns": [],
           "unsupported": [], "annotations": {}}
    for shape in shapes:
        for key in MERGE_FIRST:
            if out.get(key) is None and shape.get(key) is not None:
                out[key] = shape[key]
        for key in MERGE_MAX:
            new, old = _numeric(shape.get(key)), _numeric(out.get(key))
            if new is not None and (old is None or new > old):
                out[key] = shape[key]
        for key in MERGE_MIN:
            new, old = _numeric(shape.get(key)), _numeric(out.get(key))
            if new is not None and (old is None or new < old):
                out[key] = shape[key]
        if shape.get("pattern"):
            out["patterns"].append(shape["pattern"])
        if shape.get("in"):
            # Conjunction of two closed sets is their intersection. Disjoint sets
            # would intersect to nothing and the field would silently become a
            # plain STRING, so keep the first and flag the conflict instead.
            if not out["in"]:
                out["in"] = list(shape["in"])
            else:
                both = [v for v in out["in"] if v in shape["in"]]
                if both:
                    out["in"] = both
                else:
                    out.setdefault("inConflicts", []).append(list(shape["in"]))
        out["unsupported"] = sorted(set(out["unsupported"]) | set(shape.get("unsupported") or []))
        out["annotations"].update(shape.get("annotations") or {})
    for key in MERGE_MAX + MERGE_MIN:
        out.setdefault(key, None)
    out["pattern"] = out["patterns"][0] if out["patterns"] else None
    out.setdefault("inConflicts", [])
    return out


def is_deactivated(shape):
    return str(shape.get("deactivated") or "").lower() == "true"


def shape_index(inventory):
    """class IRI -> { property path -> merged, active property shape }

    A deactivated shape contributes nothing to validation, so it is excluded from
    the merge entirely — it is recorded separately so the register still gets its
    'documented, not enforced' row.
    """
    grouped = {}
    for shape in inventory.get("shapes", []):
        target = shape.get("targetClass")
        if not target:
            continue
        for prop in shape.get("properties", []):
            if prop.get("path"):
                grouped.setdefault(target, {}).setdefault(prop["path"], []).append(prop)
    out = {}
    for target, paths in grouped.items():
        for path, props in paths.items():
            active = [p for p in props if not is_deactivated(p)]
            merged = merge_property_shapes(active or props)
            # True only when EVERY shape on this path is deactivated. One active
            # shape beside a deactivated one keeps the path enforced.
            merged["allDeactivated"] = not active
            merged["deactivatedCount"] = len(props) - len(active)
            out.setdefault(target, {})[path] = merged
    return out


def relationship_constraints(prop, shape, subject, is_master, register, facts,
                             column, table):
    """Classify an OBJECT property's shape, the way a datatype property's is.

    Without this an `sh:minCount 1` on a relationship is parsed into the inventory
    and then dropped: no field option, no register row, and the open-item command
    ships without isRequired. Every SHACL shape becomes a register row — a
    relationship is not an exception.
    """
    if not shape:
        return {}
    locus = "uipath" if is_master else "external"
    level, may_require = verdict_for(column, facts, is_master)
    out = {}
    min_count = shape.get("minCount") or 0
    if min_count >= 1:
        out["isRequired"] = may_require if facts is not None else is_master
        register.add(
            source="process", from_iri=prop["iri"], subject=subject,
            statement=f"sh:minCount {min_count}: the relationship is mandatory in the domain",
            expressible="yes" if min_count == 1 else "no",
            locus=locus, level=None if facts is None else level,
            candidate=level or ("state" if is_master else "monitor"),
            resolution="decided" if facts is not None else
                       ("default-applied" if is_master else "override"),
            evidence={"table": table, "column": column} if facts is not None else {},
            note=level_note(level, column, table, not is_master, facts))
    for unsupported in shape.get("unsupported", []):
        register.add(source="process", from_iri=prop["iri"], subject=subject,
                     statement=f"sh:{unsupported} must hold on the relationship",
                     expressible="no", locus=locus, level=None,
                     candidate=level or ("monitor" if not is_master else "transition"),
                     resolution="deferred")
    return out


def shape_annotations(inventory):
    """class IRI -> the node shape's non-SHACL annotations"""
    return {s["targetClass"]: s.get("annotations", {})
            for s in inventory.get("shapes", []) if s.get("targetClass")}


def first_annotation(annotations, predicate_iri):
    if not predicate_iri:
        return None
    values = annotations.get(predicate_iri) or []
    return values[0] if values else None


def level_note(level, column, table, is_replica, facts):
    """Say why the verdict is what it is, in the process's own terms."""
    if facts is None:
        return ("isRequired left false: the entity is a replica and the system of "
                "record holds the guarantee" if is_replica else
                "isRequired set from the system-of-record default; no process "
                "description was resolved, so the write sites are unknown")
    if level == "state":
        return (f"`{table}.{column}` is set when the row is created, so the schema "
                f"can hold the constraint")
    if level == "transition":
        return (f"`{table}.{column}` is written only after the row exists, so the "
                f"record is legitimately incomplete first; enforce on the write, "
                f"not on the schema")
    if level == "monitor":
        return (f"a branch turns on `{table}.{column}` and the system of record owns "
                f"it: surface a violation, do not block")
    return (f"nothing in the process writes or branches on "
            f"`{table}.{column or '?'}`; the value is carried, not judged")


def verdict_for(column, table_facts, is_master):
    """(level, isRequired-eligible) from the access pattern — genome's own call.

    Whether a constraint is enforced, surfaced or trusted is derived here, never
    read out of the bundle. A shape that pre-states it has already made the
    decision this pipeline exists to make.

      ours + set at creation          -> state      the schema can hold it
      ours + written only later       -> transition the record exists incomplete
      ours + never written            -> assumed    nothing here sets it
      theirs + a branch turns on it   -> monitor    a bad value changes behaviour
      theirs + only carried           -> assumed    the source of record owes it
    """
    if table_facts is None:
        return (None, False)
    if is_master:
        if column and column in table_facts.get("columnsCreatedWith", []):
            return ("state", True)
        if column and column in table_facts.get("columnsWritten", []):
            return ("transition", False)
        return ("assumed", False)
    if column and column in table_facts.get("decidedOn", []):
        return ("monitor", False)
    return ("assumed", False)


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
    """Directed cycle over edges [(child, parent)], self-loops already removed.

    Iterative: a recursive walk overflows on the long chains real ontologies have.
    """
    graph = {}
    for a, b in edges:
        graph.setdefault(a, set()).add(b)
    WHITE, GREY, BLACK = 0, 1, 2
    colour = {}

    for root in sorted(graph):
        if colour.get(root, WHITE) != WHITE:
            continue
        stack = [(root, iter(sorted(graph.get(root, ()))))]
        path = [root]
        colour[root] = GREY
        while stack:
            node, children = stack[-1]
            nxt = next(children, None)
            if nxt is None:
                colour[node] = BLACK
                stack.pop()
                path.pop()
                continue
            state = colour.get(nxt, WHITE)
            if state == GREY:
                return path[path.index(nxt):] + [nxt]
            if state == WHITE:
                colour[nxt] = GREY
                path.append(nxt)
                stack.append((nxt, iter(sorted(graph.get(nxt, ())))))
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--inventory", required=True)
    ap.add_argument("--project", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--overrides")
    ap.add_argument("--previous")
    ap.add_argument("--access-patterns", dest="access_patterns")
    ap.add_argument("--scope", default="tenant", choices=("tenant", "folder"))
    args = ap.parse_args()

    def load(path, what):
        try:
            with open(path, encoding="utf-8") as fh:
                return json.load(fh)
        except (OSError, json.JSONDecodeError) as exc:
            raise DeriveError(f"{what} {path}: {exc}")

    inv = load(args.inventory, "--inventory")
    overrides = load(args.overrides, "--overrides") if args.overrides else {}
    previous = load(args.previous, "--previous") if args.previous else {}
    access = load(args.access_patterns, "--access-patterns") if args.access_patterns else {}
    unknown = sorted(set(overrides) - {"systemsOfRecord", "replicas", "folderScoped",
                                       "displayFields", "lookupEntities", "annotations"})
    if unknown:
        raise DeriveError(f"--overrides {args.overrides}: unknown key(s) "
                          f"{', '.join(unknown)}; a typo here is silently ignored otherwise")

    register = Register()
    shapes = shape_index(inv)
    node_annotations = shape_annotations(inv)
    r2rml = r2rml_index(inv)
    replicas = dict(overrides.get("replicas", {}))
    annotation_map = overrides.get("annotations", {})
    source_predicate = annotation_map.get("authoritativeSource")
    mode_predicate = annotation_map.get("enforcementMode")
    systems_of_record = set(overrides.get("systemsOfRecord", []))
    # The resolved process description decides ownership: a table it only reads is
    # a replica, one it creates or writes is ours, and a class the mapping does not
    # carry at all exists nowhere else, so nothing but this solution can own it.
    table_of_class = {tm["subjectClass"]: tm["logicalTable"]
                      for tm in inv.get("triplesMaps", [])
                      if tm.get("subjectClass") and tm.get("logicalTable")}
    access_tables = access.get("tables", {})
    declared_sources = {}   # class IRI -> the system named in the shapes

    classes = {c["iri"]: c for c in inv.get("classes", [])}
    dprops = list(inv.get("datatypeProperties", []))
    oprops = list(inv.get("objectProperties", []))
    reified = {r["iri"]: r for r in inv.get("reifiedRelations", [])}

    # A bundle is any ONE of the three inputs. Classes and properties the OWL
    # does not declare, but the shapes or the mappings name, are synthesised
    # here so a SHACL-only or R2RML-only bundle still yields a model.
    def ensure_class(iri, whence):
        if iri and iri not in classes:
            classes[iri] = {"iri": iri, "label": None, "comment": None,
                            "superClasses": [], "hasKey": []}
            register.add(source="metadata", from_iri=iri, subject=local_name(iri),
                         statement=f"class not declared in the ontology; taken from {whence}",
                         expressible="yes", resolution="default-applied")

    known_d = {p["iri"] for p in dprops}
    known_o = {p["iri"] for p in oprops}

    for shape in inv.get("shapes", []):
        target = shape.get("targetClass")
        ensure_class(target, "a SHACL node shape")
        if not target:
            register.add(source="metadata", from_iri=shape.get("iri"),
                         statement=f"node shape with no sh:targetClass; its "
                                   f"{len(shape.get('properties') or [])} property shape(s) "
                                   f"could not be attached to an entity",
                         expressible="no", candidate="assumed", resolution="deferred")
            continue
        for ps in shape.get("properties", []):
            path = ps.get("path")
            if not path or path in known_d or path in known_o:
                continue
            if ps.get("class"):
                oprops.append({"iri": path, "label": ps.get("name"), "domain": [target],
                               "range": [ps["class"]], "functional": ps.get("maxCount") == 1,
                               "inverseFunctional": False})
                known_o.add(path)
                ensure_class(ps["class"], "a SHACL sh:class")
            else:
                dprops.append({"iri": path, "label": ps.get("name"), "domain": [target],
                               "range": ps.get("datatype"), "functional": True})
                known_d.add(path)

    for tmap in inv.get("triplesMaps", []):
        subject_class = tmap.get("subjectClass")
        ensure_class(subject_class, "an R2RML subject map")
        if not subject_class:
            continue
        for pom in tmap.get("predicateObjectMaps", []):
            pred = pom.get("predicate")
            if not pred or pred in known_d or pred in known_o or not pom.get("column"):
                continue
            dprops.append({"iri": pred, "label": None, "domain": [subject_class],
                           "range": None, "functional": True})
            known_d.add(pred)

    for note in inv.get("parserNotes", []):
        register.add(source="metadata", statement=f"input construct not interpreted: {note}",
                     expressible="no", candidate="assumed", resolution="deferred",
                     note="ontology-sources-guide.md § Parser limits")

    # ---- which classes become entities -------------------------------------
    props_by_class = {}
    for prop in dprops:
        for dom in prop.get("domain", []):
            props_by_class.setdefault(dom, []).append(prop)

    linked = set()
    for prop in oprops:
        linked.update(prop.get("domain") or [])
        linked.update(prop.get("range") or [])
    entity_classes = sorted(
        iri for iri in classes
        if props_by_class.get(iri) or iri in reified or iri in linked
    )
    not_covered = [
        {"from": iri, "why": "class carries no mapped property and no relationship"}
        for iri in sorted(classes) if iri not in entity_classes
    ]
    # S2-10: a datatype property with no domain, or a domain no class declares,
    # reaches no entity. Say so rather than letting it disappear.
    placed = {iri for cls in entity_classes for p in props_by_class.get(cls, [])
              for iri in [p["iri"]]}
    not_covered += [{"from": p["iri"], "why": "datatype property with no mapped domain"}
                    for p in dprops if p["iri"] not in placed]

    taken_entities = set()
    name_of = {}
    for iri in entity_classes:
        name_of[iri] = normalize(iri, "entity", taken_entities, register)

    # A shape that names an authoritative source declares the entity a replica.
    # A declared answer beats the D1 default; an override beats both, and the
    # disagreement is recorded rather than silently resolved.
    for iri in entity_classes:
        declared = first_annotation(node_annotations.get(iri, {}), source_predicate)
        if not declared:
            continue
        declared_sources[iri] = declared
        ename = name_of[iri]
        if ename in systems_of_record:
            register.add(source="domain", from_iri=iri, subject=ename,
                         statement=f"the shapes name {declared!r} as the authoritative source, "
                                   f"but the overrides claim this solution as the system of "
                                   f"record; the override wins and its constraints are enforced",
                         expressible="yes", locus="uipath", level=None,
                         resolution="override")
        else:
            replicas.setdefault(ename, declared)
            register.add(source="domain", from_iri=iri, subject=ename,
                         statement=f"the shapes name {declared!r} as the authoritative source, "
                                   f"so this entity is a replica of it",
                         expressible="yes", locus="external", level=None,
                         resolution="override")

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
        # A reified class's participants are emitted with that entity, but the
        # property may have other domains too — filter, do not bail.
        domains = [d for d in domains if d not in reified]
        if not domains:
            continue
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
                    {"prop": prop, "target": name_of[parent_cls], "cardinality": kind,
                     "shape": shapes.get(dom, {}).get(prop["iri"], {})})
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
                        {"prop": prop, "target": name_of[rng],
                         "cardinality": "many-to-one",
                         "shape": shapes.get(iri, {}).get(prop["iri"], {})})
                    edges.append((name_of[iri], name_of[rng]))

    # ---- junction entities --------------------------------------------------
    junction_entities = []
    for prop, dom, rng in sorted(junctions, key=lambda j: (j[0]["iri"], j[1], j[2])):
        jname = normalize(f"{name_of[dom]}{name_of[rng]}", "entity", taken_entities, register)
        jtaken = set()
        dom_field = normalize(dom, "field", jtaken, register, owner=jname)
        rng_field = normalize(rng, "field", jtaken, register, owner=jname)
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
            "displayField": None,
            "fields": [],
            "relationships": [
                {"name": dom_field, "target": name_of[dom], "cardinality": "many-to-one",
                 "isRequired": True,
                 "provenance": {"from": [dom], "derivation": "direct"}},
                {"name": rng_field, "target": name_of[rng], "cardinality": "many-to-one",
                 "isRequired": True,
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
    choice_set_of_path = {}          # path IRI -> set name, so one property = one set
    taken_sets = set()

    def choice_set_for(path_iri, values):
        if path_iri in choice_set_of_path:
            return choice_set_of_path[path_iri]
        base = pascal(local_name(path_iri)) or "Values"
        name, n = base, 2
        while name.lower() in taken_sets:
            name = f"{base}{n}"
            n += 1
        taken_sets.add(name.lower())
        choice_set_of_path[path_iri] = name
        if name != base:
            register.add(source="convention", from_iri=path_iri, subject=name,
                         statement=f"choice-set name {base!r} already taken by another "
                                   f"property; this set is {name!r}",
                         expressible="yes", resolution="default-applied")
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
        # D1: an entity is a replica unless this solution is named as its system of
        # record. The asymmetry of harm decides the direction — a constraint left
        # unenforced is recoverable, a wrongly required field rejects data the source
        # already accepted and cannot be ingested at all.
        table = table_of_class.get(iri)
        facts = access_tables.get(table) if table else None
        if ename in systems_of_record:
            is_master, why = True, "named under systemsOfRecord"
        elif access_tables and table is None:
            is_master, why = True, ("no relational table realizes this class, so it "
                                    "exists nowhere but here")
        elif facts is not None:
            is_master = not facts["readOnly"]
            why = (f"the process writes `{table}` at step(s) "
                   f"{', '.join(map(str, facts['writtenIn']))}" if is_master else
                   f"the process only reads `{table}`")
        else:
            is_master, why = False, "no process description was resolved (default D1)"
        is_replica = not is_master
        locus = "uipath" if is_master else "external"
        register.add(source="process" if facts is not None or access_tables else "domain",
                     from_iri=iri, subject=ename,
                     statement=("this solution is the system of record: " + why
                                if is_master else "this entity is a replica: " + why),
                     expressible="yes", locus=locus, level=None,
                     resolution="decided" if (access_tables and
                                              ename not in systems_of_record)
                     else ("override" if ename in systems_of_record
                           else "default-applied"),
                     evidence={"table": table} if table else {})
        taken_fields, fields, cs_fields = set(), [], []

        for prop in sorted(props_by_class.get(iri, []), key=lambda p: p["iri"]):
            fname = normalize(prop["iri"], "field", taken_fields, register, owner=ename)
            subject = f"{ename}.{fname}"
            shape = shapes.get(iri, {}).get(prop["iri"], {})

            # Constraints are classified for EVERY field kind before the field is
            # shaped. A choice-set field carries sh:minCount and sh:pattern like any
            # other, and skipping them here is how a constraint disappears silently.
            column = (r2rml.get((iri, prop["iri"])) or {}).get("column")
            level, may_require = verdict_for(column, facts, is_master)
            deactivated = bool(shape.get("allDeactivated"))
            field_locus = "none" if deactivated else locus
            # An inexpressible constraint cannot be enforced by the schema, so its
            # candidate is an operation, a surfaced finding, or trust. For a replica
            # the default is to surface rather than block: rejecting data the system
            # of record accepted creates divergence, not a catch.
            soft = level or ("monitor" if field_locus == "external" else "transition")
            hard = level or ("state" if field_locus == "uipath" else "monitor")
            # expressible: no forecloses state, including when the shapes declare
            # `authoritative`. A constraint the schema cannot hold is enforced by an
            # operation, surfaced, or trusted — never by the schema.
            if soft == "state":
                soft = "transition"
            resolution = ("override" if deactivated else
                          "decided" if level else None)

            # A deactivated shape is excluded from the merge so it cannot weaken an
            # active one, but it is still something the business wrote down. Record
            # it, or a deliberate decision becomes indistinguishable from an omission.
            if shape.get("deactivatedCount"):
                register.add(
                    source="domain", from_iri=prop["iri"], subject=subject,
                    statement=(f"{shape['deactivatedCount']} shape(s) on this path are "
                               f"deactivated: documented, deliberately not enforced"),
                    expressible="yes", locus="none" if deactivated else locus,
                    level="assumed", candidate="assumed", resolution="override",
                    note=("every shape on this path is deactivated" if deactivated else
                          "an active shape on the same path still applies"))

            required = None
            min_count = shape.get("minCount") or 0
            if min_count > 1:
                register.add(source="process", from_iri=prop["iri"], subject=subject,
                             statement=f"sh:minCount {min_count}: at least {min_count} values "
                                       f"required; no Data Fabric option states a lower bound "
                                       f"above one",
                             expressible="no", locus=field_locus, level=None,
                             candidate=soft, resolution=resolution or "deferred")
            if min_count >= 1:
                required = (may_require and not deactivated) if facts is not None \
                    else (field_locus == "uipath" and not deactivated)
                register.add(
                    source="process", from_iri=prop["iri"], subject=subject,
                    statement=f"sh:minCount {min_count}: mandatory in the domain",
                    expressible="yes" if min_count == 1 else "no", locus=field_locus,
                    level=None if facts is None else level,
                    candidate=hard,
                    resolution=resolution or ("default-applied" if field_locus == "uipath"
                                              else "override"),
                    evidence=({"table": table, "column": column} if facts is not None
                              else {"replicaOf": replicas.get(ename)} if is_replica else {}),
                    note=level_note(level, column, table, is_replica, facts))
            statements = [f"sh:pattern {p!r} must hold" for p in shape.get("patterns") or []]
            if shape.get("minLength"):
                statements.append(f"sh:minLength {shape['minLength']} must hold")
            for statement in statements:
                register.add(source="process", from_iri=prop["iri"], subject=subject,
                             statement=statement, expressible="no", locus=field_locus,
                             level=None, candidate=soft,
                             resolution=resolution or "deferred",
                             note="no Data Fabric field option states this")
            for unsupported in shape.get("unsupported", []):
                register.add(source="process", from_iri=prop["iri"], subject=subject,
                             statement=f"sh:{unsupported} must hold",
                             expressible="no", locus=field_locus,
                             level=None, candidate=soft,
                             resolution=resolution or "deferred")
            for key_group in cls.get("hasKey", []):
                if len(key_group) > 1 and prop["iri"] in key_group:
                    register.add(source="domain", from_iri=iri, subject=subject,
                                 statement="composite key cannot be expressed: isUnique is per "
                                           "field",
                                 expressible="no", locus=locus, level=None,
                                 candidate="transition", resolution="deferred")

            if shape.get("in"):
                cs_name = choice_set_for(prop["iri"], shape["in"])
                entry = {"name": fname, "choiceSet": cs_name, "multiple": False,
                         "provenance": {"from": [prop["iri"]], "derivation": "direct"}}
                if required is not None:
                    entry["isRequired"] = required
                if shape.get("maxLength"):
                    register.add(source="metadata", from_iri=prop["iri"], subject=subject,
                                 statement=f"sh:maxLength {shape['maxLength']} is not expressible "
                                           f"on a choice-set field; the value set bounds it",
                                 expressible="no", locus=locus, level=None,
                                 candidate="assumed", resolution="default-applied")
                cs_fields.append(entry)
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

            # A bound beyond STRING's reach widens the type rather than being
            # silently narrowed to 4000 — a narrowed bound is a different constraint
            # from the one the bundle stated, and it would leave no trace.
            if shape.get("maxLength") and cli_type == "STRING":
                limit = int(shape["maxLength"])
                if limit > 10000:
                    field["type"], cli_type = "MULTILINE_MAX", "MULTILINE_MAX"
                    field["lengthLimit"] = min(limit * 2, 131072)
                    register.add(source="metadata", from_iri=prop["iri"], subject=subject,
                                 statement=f"sh:maxLength {limit} exceeds MULTILINE_TEXT's "
                                           f"10000; emitted MULTILINE_MAX, whose limit counts "
                                           f"UTF-16 bytes, not characters",
                                 expressible="yes", locus=locus, level=None,
                                 resolution="default-applied")
                elif limit > 4000:
                    field["type"], cli_type = "MULTILINE_TEXT", "MULTILINE_TEXT"
                    field["lengthLimit"] = limit
                    register.add(source="metadata", from_iri=prop["iri"], subject=subject,
                                 statement=f"sh:maxLength {limit} exceeds STRING's 4000; "
                                           f"emitted MULTILINE_TEXT",
                                 expressible="yes", locus=locus, level=None,
                                 resolution="default-applied")
                else:
                    field["lengthLimit"] = limit
            if cli_type == "DECIMAL":
                for key, shape_key in (("minValue", "minInclusive"), ("maxValue", "maxInclusive")):
                    if shape.get(shape_key) is not None:
                        try:
                            field[key] = float(shape[shape_key])
                        except (TypeError, ValueError):
                            pass

            if required is not None:
                field["isRequired"] = required
            for key_group in cls.get("hasKey", []):
                if len(key_group) == 1 and key_group[0] == prop["iri"]:
                    field["isUnique"] = True

            prov = r2rml.get((iri, prop["iri"]))
            if prov:
                field["r2rml"] = prov
            fields.append(field)

        rels = []
        for rel in sorted(relationships.get(ename, []), key=lambda r: r["prop"]["iri"]):
            rname = normalize(rel["prop"]["iri"], "field", taken_fields, register, owner=ename)
            entry = {"name": rname, "target": rel["target"],
                     "cardinality": rel["cardinality"],
                     "provenance": {"from": [rel["prop"]["iri"]], "derivation": "direct"}}
            rel_col = (r2rml.get((iri, rel["prop"]["iri"])) or {}).get("column")
            entry.update(relationship_constraints(
                rel["prop"], rel.get("shape") or {}, f"{ename}.{rname}", is_master,
                register, facts, rel_col, table))
            rels.append(entry)

        # Lowest-sorting, so the pick does not depend on construction order. Never
        # falls back to Id: the display field decides what renders in every picker,
        # and the platform requires that choice to be confirmed, not defaulted to a
        # UUID. With no candidate the entity carries none and the open item asks.
        chosen = overrides.get("displayFields", {}).get(ename)
        if not chosen:
            required_strings = sorted(f["name"] for f in fields
                                      if f["type"] == "STRING" and f.get("isRequired"))
            any_strings = sorted(f["name"] for f in fields if f["type"] == "STRING")
            candidates = required_strings or any_strings
            chosen = candidates[0] if candidates else None
            register.add(
                source="domain", from_iri=iri, subject=ename,
                statement=(f"displayField proposed as {chosen!r} (default D3)" if chosen else
                           "no STRING field to propose as displayField"),
                expressible="yes", locus=locus, level=None,
                resolution="default-applied" if chosen else "deferred",
                note="a proposal only: the platform requires the display field to be "
                     "confirmed, since it decides what renders in every picker")

        if len([f for f in fields if f["type"] == "MULTILINE_MAX"]) > 10:
            raise DeriveError(
                f"{ename}: {len([f for f in fields if f['type'] == 'MULTILINE_MAX'])} "
                f"MULTILINE_MAX fields exceeds the platform cap of 10. Splitting the entity "
                f"is a decomposition this mode does not make; reduce the bundle's long-text "
                f"properties or split the class in the ontology.")

        comment = cls.get("comment") or ""
        if len(comment) > 512:
            register.add(source="metadata", from_iri=iri, subject=ename,
                         statement=f"rdfs:comment truncated from {len(comment)} to 512 "
                                   f"characters, the Data Fabric description cap",
                         expressible="yes", resolution="default-applied")
        entities.append({
            "name": ename, "displayName": cls.get("label") or ename,
            "description": comment[:512],
            "displayField": chosen,
            "provenance": {"from": [iri],
                           "derivation": "direct",
                           **({"because": "reified relation class: it already is the junction"}
                              if iri in reified else {})},
            "fields": sorted(fields, key=lambda f: f["name"]),
            "relationships": sorted(rels, key=lambda r: r["name"]),
            "choiceSetFields": sorted(cs_fields, key=lambda c: c["name"]),
        })

        if is_replica and ename in replicas:
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
                       "automation reads them together is a later phase's question"})
    # A co-read is this process's evidence, not the source's layout: two tables
    # fetched in one step are a real candidate, and the step says so.
    class_of_table = {v: k for k, v in table_of_class.items()}
    for co in access.get("coReads", []):
        members = sorted({name_of[class_of_table[t]] for t in co["tables"]
                          if class_of_table.get(t) in name_of})
        if len(members) > 1:
            envelope.append({
                "kind": "consolidation", "members": members, "verdict": "candidate",
                "evidence": {"coReadInStep": co["step"], "tables": co["tables"]},
                "why": f"the process reads these together at step {co['step']}; whether "
                       f"the read pattern justifies a fold is a later phase's question"})
    step_of = {s["n"]: s for s in access.get("steps", [])}
    for hot in access.get("hotPaths", []):
        step = step_of.get(hot["step"], {})
        on_path = sorted({name_of[class_of_table[t]]
                          for v in step.get("traversals", [])
                          for t in (v["from"].split(".")[0], v["to"].split(".")[0])
                          if class_of_table.get(t) in name_of})
        envelope.append({
            "kind": "hot-path", "members": on_path, "verdict": "evidence",
            "evidence": {"step": hot["step"], "hops": hot["hops"], "runs": hot["runs"]},
            "why": f"step {hot['step']} traverses {hot['hops']} join(s)"
                   f"{' at ' + hot['runs'] if hot['runs'] else ''}; each hop is a "
                   f"round trip, because native entities have no query-time join"})

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
