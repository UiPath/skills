#!/usr/bin/env python3
"""Score the SDD's `### Data model` table against a golden read from the PDD's data model.

    python3 check_sdd_data_model.py --golden golden.json [--sdd <file>]

Prints a float in [0,1] on the first stdout line, details after; exit 0 always (coder_eval `run_command` with
`score_from_stdout: true`).

What is scored (weights):
  objects    0.30  golden business objects found as table rows (F1 on names)
  source     0.20  per found object: the source of record names the golden system and none of the connection or
                   object names the PDD gave beside it (the SDD names the system only)
  fields     0.25  per found object: field names (F1); `Object.field` and `field` both count
  links      0.15  per golden link: the row's Links cell names the field and the target object, and says to-one
  read-only  0.10  found rows of a federated object with no Written by

The table is the first one under a `### Data model` heading, up to the next heading. Stdlib only.
"""
from __future__ import annotations

import argparse
import glob
import json
import re
from pathlib import Path

W = {"objects": 0.30, "source": 0.20, "fields": 0.25, "links": 0.15, "read-only": 0.10}
HEADING = re.compile(r"^#{2,4}\s+(?:[\d.]+\s+)?Data model\s*$", re.M | re.I)
UNSET = re.compile(r"^\s*(?:[-—–]|none|n/a)?\s*$", re.I)


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def find_sdd(explicit: str | None) -> Path | None:
    if explicit:
        p = Path(explicit)
        return p if p.exists() else None
    found = [Path(p) for p in glob.glob("**/*-sdd*.md", recursive=True) if "node_modules" not in p]
    return max(found, key=lambda p: p.stat().st_mtime) if found else None


def cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def parse_table(text: str) -> list[dict]:
    m = HEADING.search(text)
    if not m:
        return []
    block = re.split(r"^#{1,4}\s", text[m.end():], maxsplit=1, flags=re.M)[0]
    rows = [l for l in block.splitlines() if l.strip().startswith("|")]
    if len(rows) < 2:
        return []
    header = [norm(c) for c in cells(rows[0])]

    def col(*names):
        return next((i for i, h in enumerate(header) if h in names), None)

    ix = {k: col(*v) for k, v in {
        "entity": ("entity", "businessobject", "object"), "source": ("sourceofrecord",), "fields": ("fields",),
        "links": ("links",), "written": ("writtenby",)}.items()}
    out = []
    for line in rows[2:]:
        c = cells(line)
        get = lambda k: c[ix[k]] if ix[k] is not None and ix[k] < len(c) else ""
        out.append({k: get(k) for k in ix})
    return out


def f1(found: set, want: set) -> float:
    if not found or not want:
        return 0.0
    hit = len(found & want)
    if not hit:
        return 0.0
    p, r = hit / len(found), hit / len(want)
    return 2 * p * r / (p + r)


def field_names(cell: str) -> set[str]:
    names = set()
    for part in re.split(r"[,;]|<br\s*/?>", cell):
        name = part.split(":")[0].strip().strip("`*").split(".")[-1]
        if name:
            names.add(norm(name))
    return names


def score(sdd_text: str, golden: dict) -> tuple[float, list[str]]:
    rows = parse_table(sdd_text)
    notes = [f"rows parsed: {len(rows)}"]
    if not rows:
        return 0.0, notes + ["no `### Data model` table"]
    by_name = {norm(r["entity"].strip("`*")): r for r in rows if r["entity"]}
    want = {norm(o["name"]): o for o in golden["objects"]}
    found = {k: by_name[k] for k in want if k in by_name}
    parts = {"objects": f1(set(by_name), set(want))}

    system = norm(golden["sourceOfRecord"]["system"])
    banned = [norm(b) for b in golden["sourceOfRecord"]["mustNotName"]]
    ok_source = [k for k, r in found.items() if system in norm(r["source"]) and not any(b in norm(r["source"]) for b in banned)]
    parts["source"] = len(ok_source) / len(want)

    parts["fields"] = sum(f1(field_names(found[k]["fields"]), {norm(f["name"]) for f in want[k]["fields"]}) for k in found) / len(want)

    links = [(k, l) for k, o in want.items() for l in o["links"]]
    def link_ok(k, l):
        cell = found[k]["links"] if k in found else ""
        return any(norm(l["field"]) in norm(p) and norm(l["target"]) in norm(p) and "toone" in norm(p)
                   for p in re.split(r"[,;]|<br\s*/?>", cell))
    parts["links"] = sum(link_ok(k, l) for k, l in links) / len(links) if links else 1.0

    parts["read-only"] = (sum(bool(UNSET.match(r["written"])) for r in found.values()) / len(found)) if found else 0.0

    total = sum(W[k] * v for k, v in parts.items())
    notes += [f"{k}: {v:.2f} (x{W[k]})" for k, v in parts.items()]
    missing = sorted(set(want) - set(found))
    if missing:
        notes.append(f"objects missing: {missing}")
    bad = sorted(set(found) - set(ok_source))
    if bad:
        notes.append(f"source of record not the system alone: {[found[k]['source'] for k in bad]}")
    return round(total, 4), notes


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--golden", required=True)
    ap.add_argument("--sdd")
    a = ap.parse_args()
    golden = json.loads(Path(a.golden).read_text(encoding="utf-8"))
    sdd = find_sdd(a.sdd)
    if not sdd:
        print("0.0\nno SDD file found")
        return
    total, notes = score(sdd.read_text(encoding="utf-8"), golden)
    print(total)
    print("\n".join(notes))


if __name__ == "__main__":
    main()
