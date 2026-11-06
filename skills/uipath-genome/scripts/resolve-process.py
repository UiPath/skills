#!/usr/bin/env python3
"""Parse a resolved process description into an access-pattern record.

Usage:
  resolve-process.py --process <process-resolved.md> --inventory <inventory.json>
                     --out access-patterns.json

The resolved description names the relational tables and columns the R2RML mapping
exposes — the only vocabulary that exists before any entity does. This tool reads
its `**Data:**` lines, checks every reference against the mapping, and emits what
the derivation needs to decide `locus`, `level` and the consolidation candidates.

It does NOT write the description. Resolving the raw process into the table
vocabulary is a judgement about the business; this is the deterministic half.

Grammar — one `**Data:**` line per step, clauses separated by `;`:

  creates <TABLE>
  writes  <TABLE>.<COLUMN>, ...
  reads   <TABLE>.<COLUMN>, ...
  deletes <TABLE>
  filters <TABLE> on <COLUMN>
  decides on <TABLE>.<COLUMN>          a branch turns on this value
  via <TABLE>.<COLUMN> -> <TABLE>.<COLUMN>    one join, one round trip

An optional `**Runs:**` line states the step's cadence.

Exit 0 on a parse; exit 1 with one line per reference the mapping does not carry.
See references/process-resolution-guide.md.
"""

import argparse
import json
import re
import sys

STEP_RE = re.compile(r"^\s*(\d+)\.\s+\*\*(.+?)\*\*")
DATA_RE = re.compile(r"\*\*Data:\*\*\s*(.*)$")
RUNS_RE = re.compile(r"\*\*Runs:\*\*\s*(.*)$")
REF_RE = re.compile(r"`([A-Za-z_][\w$]*)\.([A-Za-z_][\w$]*)`")
TABLE_RE = re.compile(r"`([A-Za-z_][\w$]*)`")
VIA_RE = re.compile(r"`([A-Za-z_][\w$]*)\.([A-Za-z_][\w$]*)`\s*->\s*"
                    r"`([A-Za-z_][\w$]*)\.([A-Za-z_][\w$]*)`")

VERBS = ("creates", "writes", "reads", "deletes", "filters", "decides on", "via")


class ResolveError(Exception):
    pass


def table_catalog(inventory):
    """table -> {columns, subjectClass}, from the R2RML mapping only."""
    out = {}
    for tmap in inventory.get("triplesMaps", []):
        table = tmap.get("logicalTable")
        if not table:
            continue
        entry = out.setdefault(table, {"columns": set(), "subjectClass": None})
        entry["subjectClass"] = entry["subjectClass"] or tmap.get("subjectClass")
        for pom in tmap.get("predicateObjectMaps", []):
            if pom.get("column"):
                entry["columns"].add(pom["column"])
            for jc in pom.get("joinConditions", []):
                if jc.get("child"):
                    entry["columns"].add(jc["child"])
        for pom in tmap.get("predicateObjectMaps", []):
            parent = pom.get("parentTriplesMap")
            for jc in pom.get("joinConditions", []):
                if parent and jc.get("parent"):
                    for other in inventory.get("triplesMaps", []):
                        if other.get("iri") == parent and other.get("logicalTable"):
                            out.setdefault(other["logicalTable"],
                                           {"columns": set(), "subjectClass":
                                            other.get("subjectClass")})
                            out[other["logicalTable"]]["columns"].add(jc["parent"])
    return out


def split_clauses(text):
    return [c.strip() for c in text.split(";") if c.strip()]


def parse_steps(markdown):
    """(number, name, data-text, runs-text) per step carrying a Data line."""
    steps, current, data, runs = [], None, [], None
    collecting = False
    for raw in markdown.splitlines():
        line = raw.rstrip()
        m = STEP_RE.match(line)
        if m:
            if current and data:
                steps.append((current[0], current[1], " ".join(data), runs))
            current, data, runs, collecting = (int(m.group(1)), m.group(2)), [], None, False
            continue
        if current is None:
            continue
        d = DATA_RE.search(line)
        if d:
            data.append(d.group(1).strip())
            collecting = True
            continue
        r = RUNS_RE.search(line)
        if r:
            runs = r.group(1).strip()
            collecting = False
            continue
        # A Data line may wrap. Keep collecting while the continuation is indented
        # prose and not a new bullet, a blockquote or a blank line.
        if collecting:
            stripped = line.strip()
            if not stripped or stripped.startswith((">", "#", "|", "-", "*")) \
                    or re.match(r"^\s*[a-z]\.\s", line):
                collecting = False
            else:
                data.append(stripped)
    if current and data:
        steps.append((current[0], current[1], " ".join(data), runs))
    return steps


def split_via(clause):
    """Peel any `via A.B -> C.D` off a clause.

    A traversal attaches to the clause it qualifies — `reads X via A.B -> C.D` —
    so a verb-prefix test alone reads the join columns as more values the step
    needs, inflating the read set and losing the hop.
    """
    traversals, rest = [], clause
    while True:
        m = re.search(r"\bvia\s+" + VIA_RE.pattern, rest)
        if not m:
            return rest.strip(), traversals
        traversals.append(m)
        rest = (rest[:m.start()] + " " + rest[m.end():])


def parse_clause(clause, catalog, step_no, failures):
    """-> (verb, payload). Validates every reference against the catalog."""
    low = clause.lower()
    verb = next((v for v in VERBS if low.startswith(v)), None)
    if verb is None:
        failures.append(f"step {step_no}: clause does not start with a known verb: "
                        f"{clause!r}; expected one of {', '.join(VERBS)}")
        return None, None
    body = clause[len(verb):].strip()

    def check(table, column=None):
        if table not in catalog:
            failures.append(f"step {step_no}: table {table!r} is not in the R2RML "
                            f"mapping; the mapping carries "
                            f"{', '.join(sorted(catalog)) or '(none)'}")
            return False
        if column and column not in catalog[table]["columns"]:
            failures.append(f"step {step_no}: column {table}.{column} is not in the "
                            f"R2RML mapping; {table} carries "
                            f"{', '.join(sorted(catalog[table]['columns'])) or '(none)'}")
            return False
        return True

    if verb == "via":
        m = VIA_RE.search(body)
        if not m:
            failures.append(f"step {step_no}: a via clause reads "
                            f"`TABLE.COLUMN` -> `TABLE.COLUMN`: {clause!r}")
            return None, None
        ok = check(m.group(1), m.group(2)) and check(m.group(3), m.group(4))
        return ("via", {"from": f"{m.group(1)}.{m.group(2)}",
                        "to": f"{m.group(3)}.{m.group(4)}"}) if ok else (None, None)

    if verb in ("creates", "deletes"):
        tables = [t for t in TABLE_RE.findall(body) if check(t)]
        return verb, tables

    if verb == "filters":
        m = re.search(r"`([A-Za-z_][\w$]*)`\s+on\s+`([A-Za-z_][\w$]*)`", body)
        if not m:
            failures.append(f"step {step_no}: a filters clause reads "
                            f"`TABLE` on `COLUMN`: {clause!r}")
            return None, None
        if not check(m.group(1), m.group(2)):
            return None, None
        return "filters", [{"table": m.group(1), "column": m.group(2)}]

    refs = [{"table": t, "column": c} for t, c in REF_RE.findall(body) if check(t, c)]
    if not refs:
        failures.append(f"step {step_no}: {verb} names no `TABLE.COLUMN`: {clause!r}")
        return None, None
    return ("decides" if verb == "decides on" else verb), refs


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--process", required=True)
    ap.add_argument("--inventory", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    def load(path, what, text=False):
        try:
            with open(path, encoding="utf-8") as fh:
                return fh.read() if text else json.load(fh)
        except (OSError, json.JSONDecodeError) as exc:
            raise ResolveError(f"{what} {path}: {exc}")

    inventory = load(args.inventory, "--inventory")
    markdown = load(args.process, "--process", text=True)
    catalog = table_catalog(inventory)
    if not catalog:
        raise ResolveError("the inventory carries no R2RML logical table; a resolved "
                           "process description has no vocabulary to name")

    failures, steps = [], []
    for number, name, data, runs in parse_steps(markdown):
        rec = {"n": number, "name": name, "creates": [], "deletes": [], "writes": [],
               "reads": [], "filters": [], "decides": [], "traversals": [],
               "runs": runs}
        for raw_clause in split_clauses(data):
            clause, vias = split_via(raw_clause)
            for m in vias:
                ok = True
                for tbl, col in ((m.group(1), m.group(2)), (m.group(3), m.group(4))):
                    if tbl not in catalog:
                        failures.append(f"step {number}: table {tbl!r} is not in the "
                                        f"R2RML mapping")
                        ok = False
                    elif col not in catalog[tbl]["columns"]:
                        failures.append(f"step {number}: column {tbl}.{col} is not in "
                                        f"the R2RML mapping")
                        ok = False
                if ok:
                    rec["traversals"].append(
                        {"from": f"{m.group(1)}.{m.group(2)}",
                         "to": f"{m.group(3)}.{m.group(4)}"})
            if not clause:
                continue
            verb, payload = parse_clause(clause, catalog, number, failures)
            if verb is None:
                continue
            if verb == "via":
                rec["traversals"].append(payload)
            else:
                rec[verb].extend(payload)
        rec["hops"] = len(rec["traversals"])
        steps.append(rec)

    if failures:
        for line in failures:
            print(f"FAIL: {line}", file=sys.stderr)
        return 1
    if not steps:
        raise ResolveError(f"{args.process} carries no numbered step with a "
                           f"**Data:** line")

    tables = {}
    for t in sorted(catalog):
        tables[t] = {"subjectClass": catalog[t]["subjectClass"],
                     "created": False, "written": False, "readOnly": True,
                     "createdIn": [], "writtenIn": [], "readIn": [], "deletedIn": [],
                     "columnsCreatedWith": [], "columnsWritten": [],
                     "columnsRead": [], "decidedOn": []}
    for s in steps:
        for t in s["creates"]:
            tables[t]["created"] = True
            tables[t]["createdIn"].append(s["n"])
            tables[t]["columnsCreatedWith"] += [
                w["column"] for w in s["writes"] if w["table"] == t]
        for t in s["deletes"]:
            tables[t]["deletedIn"].append(s["n"])
        for w in s["writes"]:
            tables[w["table"]]["written"] = True
            if s["n"] not in tables[w["table"]]["writtenIn"]:
                tables[w["table"]]["writtenIn"].append(s["n"])
            tables[w["table"]]["columnsWritten"].append(w["column"])
        for r in s["reads"] + s["filters"]:
            if s["n"] not in tables[r["table"]]["readIn"]:
                tables[r["table"]]["readIn"].append(s["n"])
            tables[r["table"]]["columnsRead"].append(r["column"])
        for d in s["decides"]:
            tables[d["table"]]["decidedOn"].append(d["column"])
    for t in tables.values():
        t["readOnly"] = not (t["created"] or t["written"] or t["deletedIn"])
        for key in ("columnsCreatedWith", "columnsWritten", "columnsRead", "decidedOn"):
            t[key] = sorted(set(t[key]))

    co_reads = []
    for s in steps:
        touched = sorted({r["table"] for r in s["reads"] + s["filters"]}
                         | {t for t in (v["to"].split(".")[0] for v in s["traversals"])})
        if len(touched) > 1:
            co_reads.append({"tables": touched, "step": s["n"]})

    hot = [{"step": s["n"], "hops": s["hops"], "runs": s["runs"]}
           for s in steps if s["hops"] >= 1]

    out = {"process": args.process, "steps": steps,
           "tables": dict(sorted(tables.items())),
           "coReads": co_reads, "hotPaths": hot}
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, sort_keys=True)
        fh.write("\n")

    owned = sorted(t for t, v in tables.items() if not v["readOnly"])
    replicas = sorted(t for t, v in tables.items() if v["readOnly"])
    print(f"OK: {len(steps)} step(s); {len(owned)} table(s) written "
          f"({', '.join(owned) or 'none'}), {len(replicas)} read-only "
          f"({', '.join(replicas) or 'none'}); {len(co_reads)} co-read(s), "
          f"{len(hot)} traversing step(s) -> {args.out}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ResolveError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
