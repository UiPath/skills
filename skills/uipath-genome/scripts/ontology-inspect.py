#!/usr/bin/env python3
"""Parse an ontology bundle (OWL functional syntax, R2RML, SHACL) into one inventory JSON.

Usage:
  ontology-inspect.py --out <inventory.json>
                      [--ontology <file.ofn>] [--r2rml <file.ttl>] [--shacl <file.ttl>]

Every input is optional; the inventory records which were supplied under "inputs".
Output keys are sorted and ordering is stable, so two runs on unchanged input produce
byte-identical files.

Reads a documented subset, with no reasoning and no inference — asserted axioms only.
Every construct recognised as syntax but not interpreted produces a line in
"parserNotes". Limits are stated in references/ontology-sources-guide.md § Parser limits.

Exit 0 on a parse (including one with parserNotes); exit 1 with one line per failure.
"""

import argparse
import json
import re
import sys
from collections import namedtuple

Lit = namedtuple("Lit", "value datatype lang")

XSD = "http://www.w3.org/2001/XMLSchema#"
RDFS = "http://www.w3.org/2000/01/rdf-schema#"
RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
SH = "http://www.w3.org/ns/shacl#"
RR = "http://www.w3.org/ns/r2rml#"

DEFAULT_PREFIXES = {
    "xsd": XSD, "rdfs": RDFS, "rdf": RDF, "sh": SH, "rr": RR,
    "owl": "http://www.w3.org/2002/07/owl#",
    "skos": "http://www.w3.org/2004/02/skos/core#",
}


# --------------------------------------------------------------------------- #
# Turtle: tokenizer and parser (constrained subset -> triples)
# --------------------------------------------------------------------------- #

TOKEN_RE = re.compile(
    r"""
    (?P<ws>\s+)
  | (?P<comment>\#[^\n]*)
  | (?P<longstr>\"\"\"(?:[^\\]|\\.)*?\"\"\")
  | (?P<str>"(?:[^"\\\n]|\\.)*")
  | (?P<iri><[^>\s]*>)
  | (?P<directive>@prefix|@base|(?i:PREFIX|BASE)\b)
  | (?P<number>[+-]?\d+\.\d*(?:[eE][+-]?\d+)?|[+-]?\.?\d+(?:[eE][+-]?\d+)?)
  | (?P<pname>[A-Za-z_][\w.\-]*:[\w.\-%]*|:[\w.\-%]*)
  | (?P<akw>\ba\b)
  | (?P<boolean>\btrue\b|\bfalse\b)
  | (?P<punct>[.;,\[\]()^]{1,2})
    """,
    re.VERBOSE,
)


class TurtleError(Exception):
    pass


def tokenize_turtle(text):
    pos, out, n = 0, [], len(text)
    while pos < n:
        m = TOKEN_RE.match(text, pos)
        if not m:
            raise TurtleError(f"unexpected character {text[pos]!r} at offset {pos}")
        pos = m.end()
        kind = m.lastgroup
        if kind in ("ws", "comment"):
            continue
        val = m.group()
        if kind == "punct" and val == "^^":
            out.append(("dtmark", val))
        elif kind == "punct":
            for ch in val:
                out.append(("punct", ch))
        else:
            out.append((kind, val))
    return out


def _unescape(s):
    return (s.replace("\\n", "\n").replace("\\t", "\t").replace('\\"', '"')
             .replace("\\r", "\r").replace("\\\\", "\\"))


class TurtleParser:
    """Subject predicate-object lists, `;` and `,`, blank-node lists `[ ]`, collections `( )`."""

    def __init__(self, tokens, notes):
        self.t, self.i, self.notes = tokens, 0, notes
        self.prefixes = dict(DEFAULT_PREFIXES)
        self.triples = []
        self._bnode = 0

    def peek(self):
        return self.t[self.i] if self.i < len(self.t) else (None, None)

    def next(self):
        tok = self.peek()
        self.i += 1
        return tok

    def expect(self, value):
        kind, val = self.next()
        if val != value:
            raise TurtleError(f"expected {value!r}, got {val!r}")

    def fresh_bnode(self):
        self._bnode += 1
        return f"_:b{self._bnode}"

    def expand(self, pname):
        prefix, _, local = pname.partition(":")
        base = self.prefixes.get(prefix)
        if base is None:
            self.notes.append(f"turtle: unknown prefix {prefix or '(default)'}: in {pname}")
            return pname
        return base + local

    def parse(self):
        while self.i < len(self.t):
            kind, val = self.peek()
            if kind == "directive":
                self.directive()
            else:
                self.statement()
        return self.triples

    def directive(self):
        _, val = self.next()
        low = val.lower()
        if low in ("@prefix", "prefix"):
            _, pname = self.next()
            _, iri = self.next()
            self.prefixes[pname.rstrip(":")] = iri[1:-1]
        else:
            self.next()
            self.notes.append("turtle: @base is not supported; IRIs left unresolved")
        if self.peek()[1] == ".":
            self.next()

    def term(self):
        kind, val = self.next()
        if kind == "iri":
            return val[1:-1]
        if kind == "pname":
            return self.expand(val)
        if kind in ("str", "longstr"):
            raw = val[3:-3] if kind == "longstr" else val[1:-1]
            text, dt, lang = _unescape(raw), None, None
            if self.peek()[0] == "dtmark":
                self.next()
                dt = self.term()
            elif self.peek()[1] and str(self.peek()[1]).startswith("@"):
                lang = self.next()[1][1:]
            return Lit(text, dt, lang)
        if kind == "number":
            dt = XSD + ("decimal" if ("." in val or "e" in val.lower()) else "integer")
            return Lit(val, dt, None)
        if kind == "boolean":
            return Lit(val, XSD + "boolean", None)
        if kind == "akw":
            return RDF + "type"
        if val == "[":
            node = self.fresh_bnode()
            if self.peek()[1] == "]":
                self.next()
                return node
            self.predicate_object_list(node)
            self.expect("]")
            return node
        if val == "(":
            items = []
            while self.peek()[1] != ")":
                if self.peek()[0] is None:
                    raise TurtleError("unterminated collection")
                items.append(self.term())
            self.next()
            head = RDF + "nil"
            for item in reversed(items):
                node = self.fresh_bnode()
                self.triples.append((node, RDF + "first", item))
                self.triples.append((node, RDF + "rest", head))
                head = node
            return head
        raise TurtleError(f"unexpected token {val!r}")

    def predicate_object_list(self, subject):
        while True:
            kind, val = self.peek()
            if kind is None or val in ("]", "."):
                return
            pred = self.term()
            while True:
                obj = self.term()
                self.triples.append((subject, pred, obj))
                if self.peek()[1] == ",":
                    self.next()
                    continue
                break
            if self.peek()[1] == ";":
                self.next()
                while self.peek()[1] == ";":
                    self.next()
                continue
            return

    def statement(self):
        subject = self.term()
        self.predicate_object_list(subject)
        if self.peek()[1] == ".":
            self.next()


def parse_turtle(path, notes):
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    parser = TurtleParser(tokenize_turtle(text), notes)
    return parser.parse()


# --------------------------------------------------------------------------- #
# Triple helpers
# --------------------------------------------------------------------------- #

def objects(triples, s, p):
    return [o for (ts, tp, o) in triples if ts == s and tp == p]


def one(triples, s, p):
    vals = objects(triples, s, p)
    return vals[0] if vals else None


def subjects(triples, p, o):
    return [s for (s, tp, to) in triples if tp == p and to == o]


def lit_value(term):
    return term.value if isinstance(term, Lit) else term


def collection(triples, head):
    out = []
    seen = set()
    while head and head != RDF + "nil" and head not in seen:
        seen.add(head)
        first = one(triples, head, RDF + "first")
        if first is None:
            break
        out.append(first)
        head = one(triples, head, RDF + "rest")
    return out


# --------------------------------------------------------------------------- #
# OWL functional syntax
# --------------------------------------------------------------------------- #

OFN_PREFIX_RE = re.compile(r"Prefix\(\s*([A-Za-z_][\w.\-]*)?:\s*=\s*<([^>]*)>\s*\)")


def strip_ofn_comments(text):
    """Drop `#` comments, but never a `#` inside an <IRI> or a "literal".

    Naive line splitting on `#` truncates `Prefix(:=<http://…/p2p#>)` and leaves an
    unbalanced paren, which silently swallows the rest of the file.
    """
    out, in_iri, in_str, i, n = [], False, False, 0, len(text)
    while i < n:
        ch = text[i]
        if in_str:
            out.append(ch)
            if ch == "\\" and i + 1 < n:
                out.append(text[i + 1])
                i += 2
                continue
            if ch == '"':
                in_str = False
        elif in_iri:
            out.append(ch)
            if ch == ">":
                in_iri = False
        elif ch == '"':
            in_str = True
            out.append(ch)
        elif ch == "<":
            in_iri = True
            out.append(ch)
        elif ch == "#":
            while i < n and text[i] != "\n":
                i += 1
            continue
        else:
            out.append(ch)
        i += 1
    return "".join(out)


def top_level_exprs(text):
    """Yield (name, body) for each balanced Name(...) at nesting depth 0."""
    i, n = 0, len(text)
    while i < n:
        m = re.compile(r"([A-Za-z][A-Za-z0-9]*)\(").search(text, i)
        if not m:
            return
        name, depth, j, in_str = m.group(1), 1, m.end(), False
        while j < n and depth:
            ch = text[j]
            if in_str:
                if ch == "\\":
                    j += 1
                elif ch == '"':
                    in_str = False
            elif ch == '"':
                in_str = True
            elif ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            j += 1
        yield name, text[m.end():j - 1]
        i = j


def split_args(body):
    """Split on top-level whitespace, respecting parens, angle brackets and quotes."""
    out, buf, depth, in_str, in_iri = [], [], 0, False, False
    for ch in body:
        if in_str:
            buf.append(ch)
            if ch == '"':
                in_str = False
            continue
        if in_iri:
            buf.append(ch)
            if ch == ">":
                in_iri = False
            continue
        if ch == '"':
            in_str = True
            buf.append(ch)
        elif ch == "<":
            in_iri = True
            buf.append(ch)
        elif ch == "(":
            depth += 1
            buf.append(ch)
        elif ch == ")":
            depth -= 1
            buf.append(ch)
        elif ch.isspace() and depth == 0:
            if buf:
                out.append("".join(buf))
                buf = []
        else:
            buf.append(ch)
    if buf:
        out.append("".join(buf))
    return out


class OfnReader:
    HANDLED = {
        "Prefix", "Ontology", "Declaration", "SubClassOf",
        "ObjectPropertyDomain", "ObjectPropertyRange",
        "DataPropertyDomain", "DataPropertyRange",
        "FunctionalObjectProperty", "InverseFunctionalObjectProperty",
        "FunctionalDataProperty", "HasKey", "AnnotationAssertion",
    }

    def __init__(self, notes):
        self.notes = notes
        self.prefixes = dict(DEFAULT_PREFIXES)
        self.classes, self.dprops, self.oprops = {}, {}, {}
        self.cardinalities = []

    def expand(self, token):
        token = token.strip()
        if token.startswith("<") and token.endswith(">"):
            return token[1:-1]
        if ":" in token:
            prefix, _, local = token.partition(":")
            base = self.prefixes.get(prefix)
            if base is None:
                self.notes.append(f"ofn: unknown prefix {prefix or '(default)'}: in {token}")
                return token
            return base + local
        return token

    def klass(self, iri):
        return self.classes.setdefault(
            iri, {"iri": iri, "label": None, "comment": None, "superClasses": [], "hasKey": []})

    def dprop(self, iri):
        return self.dprops.setdefault(
            iri, {"iri": iri, "label": None, "domain": [], "range": None, "functional": False})

    def oprop(self, iri):
        return self.oprops.setdefault(
            iri, {"iri": iri, "label": None, "domain": [], "range": [],
                  "functional": False, "inverseFunctional": False})

    def read(self, path):
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        for m in OFN_PREFIX_RE.finditer(text):
            self.prefixes[(m.group(1) or "")] = m.group(2)
        text = strip_ofn_comments(text)
        for name, body in top_level_exprs(text):
            if name == "Ontology":
                for inner_name, inner_body in top_level_exprs(body):
                    self.axiom(inner_name, inner_body)
                break
        else:
            for name, body in top_level_exprs(text):
                self.axiom(name, body)

    def axiom(self, name, body):
        if name in ("Prefix", "Ontology", "Import", "Annotation"):
            return
        args = split_args(body)
        if name == "Declaration":
            for inner, inner_body in top_level_exprs(body):
                iri = self.expand(inner_body.strip())
                if inner == "Class":
                    self.klass(iri)
                elif inner == "DataProperty":
                    self.dprop(iri)
                elif inner == "ObjectProperty":
                    self.oprop(iri)
                else:
                    self.notes.append(f"ofn: Declaration({inner}) not interpreted")
            return
        if name == "SubClassOf" and len(args) == 2:
            sub, sup = args
            if "(" not in sup:
                self.klass(self.expand(sub))["superClasses"].append(self.expand(sup))
            else:
                self.restriction(self.expand(sub), sup)
            return
        if name in ("ObjectPropertyDomain", "ObjectPropertyRange") and len(args) == 2:
            prop, cls = self.expand(args[0]), args[1]
            if "(" in cls:
                self.notes.append(f"ofn: {name} with a class expression not interpreted")
                return
            key = "domain" if name.endswith("Domain") else "range"
            self.oprop(prop)[key].append(self.expand(cls))
            return
        if name == "DataPropertyDomain" and len(args) == 2:
            self.dprop(self.expand(args[0]))["domain"].append(self.expand(args[1]))
            return
        if name == "DataPropertyRange" and len(args) == 2:
            if "(" in args[1]:
                self.notes.append("ofn: DataPropertyRange with a data range not interpreted")
                return
            self.dprop(self.expand(args[0]))["range"] = self.expand(args[1])
            return
        if name == "FunctionalObjectProperty" and args:
            self.oprop(self.expand(args[0]))["functional"] = True
            return
        if name == "InverseFunctionalObjectProperty" and args:
            self.oprop(self.expand(args[0]))["inverseFunctional"] = True
            return
        if name == "FunctionalDataProperty" and args:
            self.dprop(self.expand(args[0]))["functional"] = True
            return
        if name == "HasKey":
            cls, rest = args[0], args[1:]
            props = []
            for group in rest:
                inner = group.strip()
                if inner.startswith("(") and inner.endswith(")"):
                    inner = inner[1:-1]
                props.extend(self.expand(tok) for tok in split_args(inner) if tok.strip())
            if props:
                self.klass(self.expand(cls))["hasKey"].append(sorted(props))
            return
        if name == "AnnotationAssertion" and len(args) >= 3:
            prop, subject, value = self.expand(args[0]), self.expand(args[1]), args[2]
            text = value.strip()
            if text.startswith('"'):
                text = _unescape(text[1:text.rindex('"')])
            target = (self.classes.get(subject) or self.dprops.get(subject)
                      or self.oprops.get(subject))
            if target is None:
                return
            if prop == RDFS + "label":
                target["label"] = text
            elif prop == RDFS + "comment" and "comment" in target:
                target["comment"] = text
            return
        self.notes.append(f"ofn: {name} not interpreted")

    def restriction(self, cls, expr):
        for inner, inner_body in top_level_exprs(expr):
            if inner not in ("ObjectMinCardinality", "ObjectMaxCardinality",
                             "DataMinCardinality", "DataMaxCardinality",
                             "ObjectExactCardinality", "DataExactCardinality"):
                self.notes.append(f"ofn: SubClassOf with {inner} not interpreted")
                continue
            parts = split_args(inner_body)
            if len(parts) < 2 or not parts[0].isdigit():
                self.notes.append(f"ofn: {inner} with a non-integer cardinality not interpreted")
                continue
            self.cardinalities.append({
                "onClass": cls, "property": self.expand(parts[1]),
                "kind": inner, "value": int(parts[0])})
            return


# --------------------------------------------------------------------------- #
# SHACL and R2RML extraction
# --------------------------------------------------------------------------- #

SH_SCALARS = {
    "datatype": "datatype", "minCount": "minCount", "maxCount": "maxCount",
    "maxLength": "maxLength", "minLength": "minLength", "pattern": "pattern",
    "minInclusive": "minInclusive", "maxInclusive": "maxInclusive",
    "nodeKind": "nodeKind", "class": "class", "name": "name",
    # enforcement metadata: SHACL's own way of saying "documented, not enforced"
    # and "surface, do not block" — read before any locus default is applied.
    "severity": "severity", "deactivated": "deactivated",
}
SH_KNOWN = set(SH_SCALARS) | {"path", "in", "property", "targetClass",
                              "message", "description", "order", "group"}


def annotations_on(triples, node):
    """Predicates outside the SHACL namespace, carried as-is.

    The authoritative-source and enforcement-mode predicates are not standardized —
    every bundle names them in its own vocabulary — so they are recorded rather than
    interpreted, and the derivation is told which IRIs to read.
    """
    out = {}
    for (s, p, o) in triples:
        if s == node and not p.startswith(SH) and p != RDF + "type":
            out.setdefault(p, []).append(lit_value(o))
    return {k: sorted(set(map(str, v))) for k, v in sorted(out.items())}


def extract_shapes(triples, notes):
    shapes = []
    shape_nodes = sorted(set(subjects(triples, RDF + "type", SH + "NodeShape")))
    for node in shape_nodes:
        props = []
        for pnode in objects(triples, node, SH + "property"):
            path = one(triples, pnode, SH + "path")
            entry = {"path": path if isinstance(path, str) else None,
                     "in": [], "unsupported": []}
            for key, out_key in SH_SCALARS.items():
                val = one(triples, pnode, SH + key)
                entry[out_key] = lit_value(val) if val is not None else None
            in_head = one(triples, pnode, SH + "in")
            if in_head:
                entry["in"] = [lit_value(v) for v in collection(triples, in_head)]
            for (_s, p, _o) in [t for t in triples if t[0] == pnode]:
                if p.startswith(SH) and p[len(SH):] not in SH_KNOWN:
                    name = p[len(SH):]
                    if name not in entry["unsupported"]:
                        entry["unsupported"].append(name)
                        notes.append(f"shacl: sh:{name} not interpreted on {path}")
            for key in ("minCount", "maxCount", "maxLength", "minLength"):
                if entry[key] is not None:
                    try:
                        entry[key] = int(entry[key])
                    except (TypeError, ValueError):
                        notes.append(f"shacl: non-integer sh:{key} on {path}")
                        entry[key] = None
            entry["unsupported"].sort()
            entry["annotations"] = annotations_on(triples, pnode)
            props.append(entry)
        target = one(triples, node, SH + "targetClass")
        shapes.append({
            "iri": node,
            "targetClass": target if isinstance(target, str) else None,
            "annotations": annotations_on(triples, node),
            "properties": sorted(props, key=lambda p: (p["path"] or "")),
        })
    return shapes


def extract_triples_maps(triples, notes):
    maps = []
    nodes = set(subjects(triples, RDF + "type", RR + "TriplesMap"))
    nodes |= {s for (s, p, _o) in triples if p == RR + "logicalTable"}
    for node in sorted(n for n in nodes if isinstance(n, str)):
        table = sql = None
        lt = one(triples, node, RR + "logicalTable")
        if lt is not None:
            table = lit_value(one(triples, lt, RR + "tableName"))
            sql = lit_value(one(triples, lt, RR + "sqlQuery"))
        subject_class = None
        sm = one(triples, node, RR + "subjectMap")
        if sm is not None:
            cls = one(triples, sm, RR + "class")
            subject_class = cls if isinstance(cls, str) else None
        poms = []
        for pom in objects(triples, node, RR + "predicateObjectMap"):
            predicate = one(triples, pom, RR + "predicate")
            om = one(triples, pom, RR + "objectMap")
            column = parent = None
            joins = []
            if om is not None:
                column = lit_value(one(triples, om, RR + "column"))
                parent_map = one(triples, om, RR + "parentTriplesMap")
                parent = parent_map if isinstance(parent_map, str) else None
                for jc in objects(triples, om, RR + "joinCondition"):
                    joins.append({
                        "child": lit_value(one(triples, jc, RR + "child")),
                        "parent": lit_value(one(triples, jc, RR + "parent"))})
            if predicate is None:
                notes.append(f"r2rml: predicateObjectMap without rr:predicate on {node}")
                continue
            poms.append({
                "predicate": predicate if isinstance(predicate, str) else lit_value(predicate),
                "column": column, "parentTriplesMap": parent,
                "joinConditions": sorted(joins, key=lambda j: (j["child"] or ""))})
        if sql:
            notes.append(f"r2rml: {node} uses rr:sqlQuery; column types are not derivable")
        maps.append({
            "iri": node, "logicalTable": table, "sqlQuery": sql,
            "subjectClass": subject_class,
            "predicateObjectMaps": sorted(poms, key=lambda p: p["predicate"] or "")})
    return maps


def detect_reified(classes, oprops, dprops):
    """A class is a reified relation when it has >=2 functional object properties
    whose ranges differ, those are its only object properties, and it has no hasKey."""
    by_domain = {}
    for prop in oprops.values():
        for dom in prop["domain"]:
            by_domain.setdefault(dom, []).append(prop)
    out = []
    for iri, cls in classes.items():
        props = by_domain.get(iri, [])
        if len(props) < 2 or cls["hasKey"]:
            continue
        if not all(p["functional"] for p in props):
            continue
        ranges = {r for p in props for r in p["range"]}
        if len(ranges) < 2:
            continue
        attrs = sorted(p["iri"] for p in dprops.values() if iri in p["domain"])
        out.append({"iri": iri,
                    "participants": sorted(p["iri"] for p in props),
                    "attributes": attrs})
    return sorted(out, key=lambda r: r["iri"])


# --------------------------------------------------------------------------- #

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ontology")
    ap.add_argument("--r2rml")
    ap.add_argument("--shacl")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    if not any((args.ontology, args.r2rml, args.shacl)):
        print("FAIL: give at least one of --ontology, --r2rml, --shacl", file=sys.stderr)
        return 1

    notes, failures = [], []
    reader = OfnReader(notes)
    if args.ontology:
        try:
            reader.read(args.ontology)
        except (OSError, TurtleError) as exc:
            failures.append(f"ontology: {exc}")

    shapes, maps = [], []
    if args.shacl:
        try:
            shapes = extract_shapes(parse_turtle(args.shacl, notes), notes)
        except (OSError, TurtleError) as exc:
            failures.append(f"shacl: {exc}")
    if args.r2rml:
        try:
            maps = extract_triples_maps(parse_turtle(args.r2rml, notes), notes)
        except (OSError, TurtleError) as exc:
            failures.append(f"r2rml: {exc}")

    if failures:
        for line in failures:
            print(f"FAIL: {line}", file=sys.stderr)
        return 1

    inventory = {
        "inputs": {"ontology": args.ontology, "r2rml": args.r2rml, "shacl": args.shacl},
        "prefixes": dict(sorted(reader.prefixes.items())),
        "classes": sorted(
            ({**c, "superClasses": sorted(set(c["superClasses"])),
              "hasKey": sorted(c["hasKey"])} for c in reader.classes.values()),
            key=lambda c: c["iri"]),
        "datatypeProperties": sorted(
            ({**p, "domain": sorted(set(p["domain"]))} for p in reader.dprops.values()),
            key=lambda p: p["iri"]),
        "objectProperties": sorted(
            ({**p, "domain": sorted(set(p["domain"])), "range": sorted(set(p["range"]))}
             for p in reader.oprops.values()),
            key=lambda p: p["iri"]),
        "cardinalities": sorted(reader.cardinalities,
                                key=lambda c: (c["onClass"], c["property"], c["kind"])),
        "reifiedRelations": detect_reified(reader.classes, reader.oprops, reader.dprops),
        "shapes": shapes,
        "triplesMaps": maps,
        "parserNotes": sorted(set(notes)),
    }

    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(inventory, fh, indent=2, sort_keys=True)
        fh.write("\n")

    print(f"OK: {len(inventory['classes'])} classes, "
          f"{len(inventory['datatypeProperties'])} datatype properties, "
          f"{len(inventory['objectProperties'])} object properties, "
          f"{len(inventory['reifiedRelations'])} reified relations, "
          f"{len(inventory['shapes'])} shapes, {len(inventory['triplesMaps'])} triples maps, "
          f"{len(inventory['parserNotes'])} parser notes -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
