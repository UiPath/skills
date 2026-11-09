#!/usr/bin/env python3
"""Derive a Data Fabric entity set from an ontology-bundle inventory.

Usage:
  derive-entities.py --inventory <inventory.json> --project <EntityProject> --out entities.json
                     [--overrides <overrides.json>] [--previous <entities.json>]
                     [--scope tenant|folder]

Emits only what the inputs and the platform FORCE. Entity identity is the R2RML
SUBJECT, not the class: two triples maps minting the same subject are one entity
(`consolidation`), one class minted under two subjects is two (`decomposition`).
Both are read off the mapping — they are never invented here, so a fold or a split
is a `target.r2rml` edit a reviewer sees as a diff. With no subject map, or none
carrying a template/column/constant, identity falls back to the class and the
derivation behaves exactly as a class-per-entity one.

`junction` entities are synthesized for many-to-many. Federated views are never
emitted: they need a consumption pattern. See references/entity-derivation-guide.md.

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


def normalize(iri, kind, taken, register, owner=None, literal=False):
    """kind is 'entity' or 'field'. Records a register row for any change.

    literal=True treats `iri` as an already-chosen name (an R2RML subject template's
    path segment) rather than an IRI to take the local name of.
    """
    raw = iri if literal else local_name(iri)
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


def parent_map_index(inventory):
    """(class IRI, predicate IRI) -> the subject key of the triples map it joins to.

    When a class is minted under several subjects, its range class alone cannot say
    which part a relationship points at. The mapping can: rr:parentTriplesMap names
    the exact map, and that map's subject key names the entity.
    """
    key_of_map = {tm["iri"]: tm.get("subjectKey") for tm in inventory.get("triplesMaps", [])}
    out, declaring = {}, {}
    for tmap in inventory.get("triplesMaps", []):
        cls = tmap.get("subjectClass")
        if not cls:
            continue
        for pom in tmap.get("predicateObjectMaps", []):
            if tmap.get("subjectKey"):
                declaring.setdefault((cls, pom["predicate"]), tmap["subjectKey"])
            parent = pom.get("parentTriplesMap")
            if parent and key_of_map.get(parent):
                out[(cls, pom["predicate"])] = key_of_map[parent]
    return out, declaring


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
    parent_key, declaring_key = parent_map_index(inv)
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

    # ---- entity identity: subject keys, not classes -------------------------
    # An entity is one *identifier*, not one class. R2RML states identity in the
    # subject map: two triples maps minting the same subject describe one record
    # (a fold), one class minted under two subjects describes two (a split). A
    # class is a type a record carries, and a record can carry two.
    #
    # With no subject map, or none carrying a template/column/constant, the group
    # key falls back to the class itself, so a bundle that never mentions subjects
    # derives exactly as it did before.
    maps_for_class = {}
    for tmap in inv.get("triplesMaps", []):
        if tmap.get("subjectClass") in classes:
            maps_for_class.setdefault(tmap["subjectClass"], []).append(tmap)

    group_members = {}          # gid -> set of class IRIs
    group_maps = {}             # gid -> list of triples maps
    groups_of_class = {}        # class IRI -> sorted list of gids
    for iri in entity_classes:
        tmaps = maps_for_class.get(iri, [])
        keyed = [tm for tm in tmaps if tm.get("subjectKey")]
        gids = sorted({tm["subjectKey"] for tm in keyed}) or [f"class:{iri}"]
        groups_of_class[iri] = gids
        for gid in gids:
            group_members.setdefault(gid, set()).add(iri)
        for tm in keyed:
            group_maps.setdefault(tm["subjectKey"], []).append(tm)
    group_ids = sorted(group_members)

    def key_name(gid):
        """A template's last literal path segment names the entity it mints."""
        if not gid.startswith("template:"):
            return None
        base = gid[len("template:"):].split("{")[0].rstrip("/#")
        seg = re.split(r"[/#]", base)[-1] if base else ""
        return pascal(seg) or None

    # The primary class of a group names it, supplies its label, comment and table,
    # and receives any relationship that points at a split class.
    group_primary = {}
    for gid in group_ids:
        members = sorted(group_members[gid])
        want = key_name(gid) if (len(members) > 1 or
                                 any(len(groups_of_class[m]) > 1 for m in members)) else None
        pick = next((m for m in members if pascal(local_name(m)) == want), None)
        group_primary[gid] = pick or members[0]

    taken_entities = set()
    name_of_group, name_of = {}, {}
    for gid in group_ids:
        members = sorted(group_members[gid])
        split = any(len(groups_of_class[m]) > 1 for m in members)
        proposed = key_name(gid) if (len(members) > 1 or split) else None
        if proposed:
            name_of_group[gid] = normalize(proposed, "entity", taken_entities, register,
                                           literal=True)
        else:
            name_of_group[gid] = normalize(group_primary[gid], "entity",
                                           taken_entities, register)
    for iri in entity_classes:
        # Incoming relationships point at the class's primary part.
        name_of[iri] = name_of_group[groups_of_class[iri][0]]

    for gid in group_ids:
        members = sorted(group_members[gid])
        if len(members) > 1:
            register.add(source="metadata", from_iri=gid[gid.index(":") + 1:],
                         subject=name_of_group[gid],
                         statement=f"{len(members)} classes share one R2RML subject, so they "
                                   f"are one record: {', '.join(local_name(m) for m in members)}",
                         expressible="yes", resolution="decided",
                         note="entity-derivation-guide.md § Identity is the subject")
    for iri in entity_classes:
        if len(groups_of_class[iri]) > 1:
            register.add(source="metadata", from_iri=iri, subject=local_name(iri),
                         statement=f"class is minted under {len(groups_of_class[iri])} distinct "
                                   f"R2RML subjects, so it is "
                                   f"{', '.join(name_of_group[g] for g in groups_of_class[iri])}; "
                                   f"relationships to it point at "
                                   f"{name_of_group[groups_of_class[iri][0]]}",
                         expressible="yes", resolution="decided",
                         note="entity-derivation-guide.md § Identity is the subject")

    # Which group carries which property: for a split class, the map that carries
    # the predicate owns it; a predicate no map carries falls to the primary group.
    props_by_group = {}
    for iri in entity_classes:
        gids = groups_of_class[iri]
        for prop in props_by_class.get(iri, []):
            if len(gids) == 1:
                props_by_group.setdefault(gids[0], []).append((iri, prop))
                continue
            # A split class's property belongs to every part whose map carries it —
            # both parts of a Party have a name, read from different columns. Only a
            # predicate no part carries falls back to the primary.
            carried = [gid for gid in gids
                       if any(pom.get("predicate") == prop["iri"]
                              for tm in group_maps.get(gid, [])
                              for pom in tm.get("predicateObjectMaps", []))]
            if not carried:
                carried = [gids[0]]
                register.add(source="metadata", from_iri=prop["iri"],
                             subject=f"{name_of_group[gids[0]]}."
                                     f"{pascal(local_name(prop['iri']))}",
                             statement="no subject map carries this predicate, so it was "
                                       "placed on the class's primary part",
                             expressible="yes", resolution="default-applied")
            for gid in carried:
                props_by_group.setdefault(gid, []).append((iri, prop))

    # Provenance per part: (group, class, predicate) -> the column that part reads.
    # The (class, predicate) index collapses a split class's two columns into one.
    r2rml_group = {}
    for tmap in inv.get("triplesMaps", []):
        cls = tmap.get("subjectClass")
        gid = tmap.get("subjectKey") or (f"class:{cls}" if cls else None)
        if not cls or not gid:
            continue
        for pom in tmap.get("predicateObjectMaps", []):
            if pom.get("column"):
                r2rml_group[(gid, cls, pom["predicate"])] = {
                    "logicalTable": tmap.get("logicalTable"), "column": pom["column"]}

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

    def part_name(cls_iri, prop_iri, via=None):
        """Which part of a split class a relationship end lands on.

        A range class alone cannot say which part a link points at once that class
        is minted under several subjects. The mapping can: rr:parentTriplesMap names
        the map, and its subject key names the entity. With nothing to go on, the
        class's primary part takes it, and the register says so.
        """
        gids = groups_of_class.get(cls_iri) or []
        if len(gids) <= 1:
            return name_of[cls_iri]
        key = parent_key.get((via, prop_iri)) if via else declaring_key.get((cls_iri, prop_iri))
        if key in gids:
            return name_of_group[key]
        register.add(source="metadata", from_iri=prop_iri, subject=name_of[cls_iri],
                     statement=f"{local_name(cls_iri)} is split across "
                               f"{len(gids)} entities and the mapping does not say which one "
                               f"this relationship touches; it was placed on the primary part",
                     expressible="yes", resolution="default-applied",
                     note="entity-derivation-guide.md § Identity is the subject")
        return name_of[cls_iri]

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
                # A fold makes the link between the folded classes a link from the
                # record to itself. It is not a self-reference the ontology asked
                # for (`Employee.manager`), it is the fold absorbing the join, so
                # the field is dropped rather than emitted pointing at its own row.
                child_name = part_name(child, prop["iri"])
                parent_name = part_name(parent_cls, prop["iri"], via=dom)
                if child != parent_cls and child_name == parent_name:
                    register.add(source="metadata", from_iri=prop["iri"],
                                 subject=child_name,
                                 statement=f"relationship "
                                           f"{local_name(child)}->{local_name(parent_cls)} "
                                           f"was absorbed: both classes are one record, so the "
                                           f"join it carried no longer exists",
                                 expressible="yes", resolution="decided",
                                 note="entity-derivation-guide.md § Identity is the subject")
                    continue
                relationships.setdefault(child_name, []).append(
                    {"prop": prop, "target": parent_name, "cardinality": kind,
                     "shape": shapes.get(dom, {}).get(prop["iri"], {})})
                edges.append((child_name, parent_name))

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
                    if rng != iri and name_of[rng] == name_of[iri]:
                        continue
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
    for gid in group_ids:
        members = sorted(group_members[gid])
        iri = group_primary[gid]
        ename = name_of_group[gid]
        cls = classes[iri]
        folded = len(members) > 1
        is_part = len(groups_of_class[iri]) > 1
        # D1: an entity is a replica unless this solution is named as its system of
        # record. The asymmetry of harm decides the direction — a constraint left
        # unenforced is recoverable, a wrongly required field rejects data the source
        # already accepted and cannot be ingested at all.
        group_tables = sorted({tm["logicalTable"] for tm in group_maps.get(gid, [])
                               if tm.get("logicalTable")})
        table = (group_tables[0] if group_tables else table_of_class.get(iri))
        if len(group_tables) > 1:
            register.add(source="metadata", subject=ename,
                         statement=f"the classes sharing this subject are mapped across "
                                   f"{len(group_tables)} tables ({', '.join(group_tables)}); "
                                   f"ownership and hop cost were read off {table!r}",
                         expressible="yes", resolution="default-applied",
                         evidence={"logicalTables": group_tables})
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

        for owner, prop in sorted(props_by_group.get(gid, []),
                                  key=lambda op: (op[1]["iri"], op[0])):
            fname = normalize(prop["iri"], "field", taken_fields, register, owner=ename)
            subject = f"{ename}.{fname}"
            shape = shapes.get(owner, {}).get(prop["iri"], {})

            # Constraints are classified for EVERY field kind before the field is
            # shaped. A choice-set field carries sh:minCount and sh:pattern like any
            # other, and skipping them here is how a constraint disappears silently.
            prov = (r2rml_group.get((gid, owner, prop["iri"]))
                    or r2rml.get((owner, prop["iri"])))
            column = (prov or {}).get("column")
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
            for key_group in classes[owner].get("hasKey", []):
                if len(key_group) > 1 and prop["iri"] in key_group:
                    register.add(source="domain", from_iri=owner, subject=subject,
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
            for key_group in classes[owner].get("hasKey", []):
                if len(key_group) == 1 and key_group[0] == prop["iri"]:
                    field["isUnique"] = True

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
            "provenance": {
                "from": members,
                "derivation": ("consolidation" if folded else
                               "decomposition" if is_part else "direct"),
                **({"because":
                    f"{len(members)} classes are minted under one R2RML subject "
                    f"({gid[gid.index(':') + 1:]}), so they are one record"} if folded else
                   {"because":
                    f"the class is minted under {len(groups_of_class[iri])} R2RML subjects; "
                    f"this part is {gid[gid.index(':') + 1:]}"} if is_part else
                   {"because": "reified relation class: it already is the junction"}
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
    # A federated entity is an UNDIRECTED star: one primary, every other source
    # joined directly to it, and the primary is a free choice. A join is symmetric,
    # so which side holds the foreign key is irrelevant. A set is therefore
    # federatable iff some member is adjacent to every other member — which makes
    # the maximal federatable sets exactly the closed neighbourhoods, and makes a
    # pair at distance >= 3 the minimal thing no federated entity can span.
    # A directed two-hop path A->B->C is NOT a counter-example: it is a star on B.
    undirected = {name: set() for name in names}
    for a, b in real_edges:
        undirected[a].add(b)
        undirected[b].add(a)
    stars = {centre: undirected[centre] | {centre}
             for centre in sorted(undirected) if len(undirected[centre]) >= 2}
    for centre, members in stars.items():
        # A star wholly inside another is not a separate option, it is a projection
        # of one. Reporting both buries the fact that one entity covers the model.
        if any(other > members for other in stars.values()):
            continue
        envelope.append({
            "kind": "federated-view", "members": sorted(members),
            "verdict": "possible", "primary": centre,
            "why": f"every other member joins directly to {centre}, so this is the "
                   f"largest federated entity centred on it"})

    def hops_from(root):
        seen, frontier, dist = {root}, [root], {root: 0}
        while frontier:
            nxt = []
            for node in frontier:
                for peer in undirected[node]:
                    if peer not in seen:
                        seen.add(peer)
                        dist[peer] = dist[node] + 1
                        nxt.append(peer)
            frontier = nxt
        return dist

    for a in sorted(undirected):
        reach = hops_from(a)
        for b in sorted(reach):
            if b > a and reach[b] >= 3:
                envelope.append({
                    "kind": "federated-view", "members": [a, b],
                    "verdict": "impossible",
                    "evidence": {"hops": reach[b]},
                    "why": f"{a} and {b} are {reach[b]} joins apart, so no member is adjacent "
                           f"to both; no federated entity can span them, whatever else "
                           f"is included"})
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
    # One table can realize several classes — that is the denormalized-source case
    # this whole analysis is about — so the inverse is a list, never a scalar.
    # Inverting the dict drops every class but the last and silently shrinks the
    # membership of every row below.
    classes_of_table = {}
    for cls_iri, tbl in table_of_class.items():
        if cls_iri in name_of:
            classes_of_table.setdefault(tbl, set()).add(cls_iri)

    def entities_on(tables):
        return sorted({name_of[c] for t in tables for c in classes_of_table.get(t, ())})

    for co in access.get("coReads", []):
        members = entities_on(co["tables"])
        if len(members) > 1:
            envelope.append({
                "kind": "consolidation", "members": members, "verdict": "candidate",
                "evidence": {"coReadInStep": co["step"], "tables": co["tables"]},
                "why": f"the process reads these together at step {co['step']}; whether "
                       f"the read pattern justifies a fold is a later phase's question"})
    step_of = {s["n"]: s for s in access.get("steps", [])}
    for hot in access.get("hotPaths", []):
        step = step_of.get(hot["step"], {})
        on_path = entities_on({t for v in step.get("traversals", [])
                               for t in (v["from"].split(".")[0], v["to"].split(".")[0])})
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
