#!/usr/bin/env python3
"""Score a Lane A tasks file for Data Fabric entity tasks and consumer bindings (Goal 1 v10, Phase N1).

Contract (coder_eval `run_command`, `score_from_stdout: true`): first stdout line = float in [0,1];
details follow; exit 0. `--strict` exits 1 below `--threshold` (default 0.6).

    python3 check_tasks_entities.py --golden golden.json [--tasks <file>] [--strict]

Components (weights) — reported one per line, never only the aggregate:
  entities       0.30  golden entities that have a `platform:*:entity:<Entity>` task (recall, core 0.7 /
                       reference 0.3), penalised for entity tasks matching no golden entity (precision)
  fields         0.10  per matched entity: field names in the task's fenced json create body vs golden (F1)
  types          0.05  per matched field: CLI type equals the golden type
  relationships  0.15  golden relationships present as a RELATIONSHIP field (matching the field name and
                       naming the referenced entity) OR as a `Blocked by` edge onto the referenced
                       entity's task
  bindings       0.30  per golden consumer: a task for that skill/project carries an `Entities:` row;
                       each golden entity present (0.6) with the right direction (0.4); extra bound
                       entities lower precision
  order          0.10  consumer tasks are `Blocked by` the tasks of every entity they bind; one
                       `solution:*:resources:Entity:<Entity>` task per entity, blocked by its entity task

The tasks file is parsed on `## Task T<N>` headings; `Identity`, `Status`, `Blocked by`, `Entities`
rows and the first fenced ```json block inside each task are read. Stdlib only.
"""
from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from pathlib import Path

W = {"entities": 0.30, "fields": 0.10, "types": 0.05, "relationships": 0.15, "bindings": 0.30, "order": 0.10}
DIRS = {"read": "read", "write": "write", "readwrite": "read-write", "read-write": "read-write", "rw": "read-write", "r": "read", "w": "write"}


def norm(s: str | None) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def find_tasks(explicit: str | None) -> Path | None:
    if explicit:
        p = Path(explicit); return p if p.exists() else None
    c = [Path(p) for p in glob.glob("**/*-tasks*.md", recursive=True) + glob.glob("**/tasks.md", recursive=True)]
    c = [p for p in c if "node_modules" not in p.parts]
    return sorted(c, key=lambda p: p.stat().st_mtime, reverse=True)[0] if c else None


def parse_tasks(text: str) -> list[dict]:
    parts = re.split(r"^## Task\s+(T\d+)\s*[—-]+\s*", text, flags=re.M)
    tasks = []
    for i in range(1, len(parts), 2):
        tid, body = parts[i], parts[i + 1]
        head = body.splitlines()[0] if body else ""
        skill = re.split(r"\s*[—-]+\s*", head)[0].strip().strip("`")
        def row(name):
            m = re.search(r"^\*\*%s:\*\*\s*(.+?)\s*$" % name, body, re.M | re.I)
            return m.group(1).strip() if m else ""
        ident = row("Identity").strip("`")
        blocked = [b.strip() for b in re.split(r"[,\s]+", row("Blocked by")) if re.fullmatch(r"T\d+", b.strip())]
        ents = row("Entities")
        bindings = {}
        if ents and norm(ents) != "none":
            for item in re.split(r";|\n", ents):
                m = re.match(r"\s*`?([A-Za-z][A-Za-z0-9_]*)`?\s*\(\s*([a-zA-Z\- ]+?)\s*\)", item)
                if m:
                    bindings[norm(m.group(1))] = DIRS.get(norm(m.group(2)), norm(m.group(2)))
        jm = re.search(r"```json\s*(\{.*?\})\s*```", body, re.S)
        bodyjson = None
        if jm:
            try: bodyjson = json.loads(jm.group(1))
            except Exception: bodyjson = None
        tasks.append({"id": tid, "skill": skill, "identity": ident, "blocked": blocked, "bindings": bindings, "body": bodyjson, "text": body})
    return tasks


def entity_name_from_identity(ident: str) -> str | None:
    m = re.match(r"^platform:[^:]+:entity:(.+)$", ident.strip())
    return m.group(1).strip() if m else None


def resource_entity_from_identity(ident: str) -> str | None:
    m = re.match(r"^solution:[^:]+:resources:Entity:(.+)$", ident.strip(), re.I)
    return m.group(1).strip() if m else None


def score(golden: dict, tasks: list[dict], details: list[str]) -> float:
    gold = golden["entities"]; gmap = {norm(g["name"]): g for g in gold}
    # --- entities
    etasks = {}; unmatched = 0
    for t in tasks:
        n = entity_name_from_identity(t["identity"])
        if n is None: continue
        key = next((k for k in gmap if norm(n) == k or norm(n).endswith(k) or k.endswith(norm(n))), None)
        if key and key not in etasks: etasks[key] = t
        else: unmatched += 1
    core = [g for g in gold if g.get("tier", "core") == "core"]; ref = [g for g in gold if g.get("tier", "core") != "core"]
    rc = sum(1 for g in core if norm(g["name"]) in etasks) / len(core) if core else 1.0
    rr = sum(1 for g in ref if norm(g["name"]) in etasks) / len(ref) if ref else 1.0
    prec = len(etasks) / (len(etasks) + unmatched) if (etasks or unmatched) else 0.0
    s_ent = 0.8 * (0.7 * rc + 0.3 * rr) + 0.2 * prec
    details.append(f"[entities] core {sum(1 for g in core if norm(g['name']) in etasks)}/{len(core)} reference {sum(1 for g in ref if norm(g['name']) in etasks)}/{len(ref)} · unmatched entity tasks {unmatched}")
    if not etasks:
        details.append("[entities] no entity task matched a golden entity")
    # --- fields / types / relationships
    f1s = []; tmatch = ttot = 0; rel_hit = rel_tot = 0
    for k, t in etasks.items():
        g = gmap[k]; body = t["body"] or {}
        bfields = body.get("fields") if isinstance(body, dict) else None
        bfields = [f for f in (bfields or []) if isinstance(f, dict)]
        names = {norm(f.get("name")): f for f in bfields}
        gfields = {norm(f["name"]): f for f in g["fields"]}
        tp = len(names.keys() & gfields.keys())
        p = tp / len(names) if names else 0.0; r = tp / len(gfields) if gfields else 1.0
        f1s.append(2 * p * r / (p + r) if p + r else 0.0)
        for fn in names.keys() & gfields.keys():
            ttot += 1
            is_rel_field = any(norm(r["field"]) == fn for r in g.get("relationships") or [])
            if norm(names[fn].get("type")) == norm(gfields[fn]["type"]) or (norm(names[fn].get("type")) == "relationship" and is_rel_field):
                tmatch += 1
        for rel in g.get("relationships") or []:
            rel_tot += 1
            target = norm(rel["referenceEntity"])
            fld = names.get(norm(rel["field"])) or {}
            as_field = norm(fld.get("type")) == "relationship" and target in norm(json.dumps(fld))
            tgt_task = etasks.get(target)
            as_edge = bool(tgt_task) and tgt_task["id"] in t["blocked"]
            if as_field or as_edge: rel_hit += 1
            else: details.append(f"[relationships] {g['name']}.{rel['field']} → {rel['referenceEntity']}: no RELATIONSHIP field and no Blocked-by edge")
    s_fields = sum(f1s) / len(f1s) if f1s else 0.0
    s_types = tmatch / ttot if ttot else (1.0 if f1s and s_fields > 0 else 0.0)
    s_rel = rel_hit / rel_tot if rel_tot else 1.0
    details.append(f"[fields] mean F1 {s_fields:.2f} over {len(f1s)} entity bodies · [types] {tmatch}/{ttot} · [relationships] {rel_hit}/{rel_tot}")
    # --- bindings
    b_scores = []; b_prec_n = b_prec_d = 0; bound_pairs: list[tuple[dict, str]] = []
    for c in golden.get("consumers") or []:
        cands = [t for t in tasks if norm(t["skill"]) == norm(c["skill"]) or norm(c["project"]) in norm(t["identity"])]
        cands = [t for t in cands if t["bindings"] and not entity_name_from_identity(t["identity"]) and not resource_entity_from_identity(t["identity"])]
        want = {norm(k): v for k, v in c["entities"].items()}
        got: dict[str, str] = {}
        for t in cands:
            for e, d in t["bindings"].items():
                got.setdefault(e, d); bound_pairs.append((t, e))
        per = []
        for e, d in want.items():
            if e in got: per.append(0.6 + (0.4 if got[e] == d else 0.0))
            else: per.append(0.0)
        b_scores.append(sum(per) / len(per) if per else 1.0)
        b_prec_n += len(set(got) & set(want)); b_prec_d += len(got)
        details.append(f"[bindings] {c['project']} ({c['skill']}): {sum(1 for e in want if e in got)}/{len(want)} entities bound, directions right {sum(1 for e in want if got.get(e) == want[e])}/{len(want)}, extra {len(set(got) - set(want))}; tasks with Entities row: {len(cands)}")
    s_bind = (sum(b_scores) / len(b_scores)) if b_scores else 1.0
    if b_prec_d: s_bind = 0.85 * s_bind + 0.15 * (b_prec_n / b_prec_d)
    # --- order
    edge_hit = edge_tot = 0
    for t, e in bound_pairs:
        et = etasks.get(e)
        if et is None: continue
        edge_tot += 1
        if et["id"] in t["blocked"]: edge_hit += 1
    res_hit = 0
    for k, t in etasks.items():
        rt = next((x for x in tasks if resource_entity_from_identity(x["identity"]) and norm(resource_entity_from_identity(x["identity"])) == k), None)
        if rt and t["id"] in rt["blocked"]: res_hit += 1
    s_order = (0.6 * (edge_hit / edge_tot if edge_tot else 1.0)) + (0.4 * (res_hit / len(etasks) if etasks else 0.0))
    details.append(f"[order] consumer blocked-by edges {edge_hit}/{edge_tot} · resource tasks blocked by entity task {res_hit}/{len(etasks)}")
    total = (W["entities"] * s_ent + W["fields"] * s_fields + W["types"] * s_types + W["relationships"] * s_rel + W["bindings"] * s_bind + W["order"] * s_order)
    details.append(f"[components] entities {s_ent:.2f} · fields {s_fields:.2f} · types {s_types:.2f} · relationships {s_rel:.2f} · bindings {s_bind:.2f} · order {s_order:.2f}")
    return total


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--golden", required=True); ap.add_argument("--tasks"); ap.add_argument("--strict", action="store_true"); ap.add_argument("--threshold", type=float, default=0.6)
    a = ap.parse_args()
    golden = json.load(open(a.golden)); details: list[str] = []
    tf = find_tasks(a.tasks)
    if tf is None:
        print("0.0000"); print("[tasks] no *-tasks.md found"); return 1 if a.strict else 0
    tasks = parse_tasks(tf.read_text(errors="replace"))
    details.insert(0, f"[tasks] {tf} · {len(tasks)} tasks")
    s = max(0.0, min(1.0, score(golden, tasks, details))) if tasks else 0.0
    if not tasks: details.append("[tasks] no `## Task T<N>` sections")
    print(f"{s:.4f}")
    for d in details: print(d)
    return (0 if s >= a.threshold else 1) if a.strict else 0


if __name__ == "__main__":
    sys.exit(main())
