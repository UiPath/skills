#!/usr/bin/env python3
"""Score the SDD's `### Data Fabric entities` table against a golden (Goal 1, planner half).

Two contracts in one script:
  default        prints a float in [0,1] on the first stdout line, details after; exit 0 always
                 (coder_eval `run_command` with `score_from_stdout: true`)
  --strict       exit 0 when score >= --threshold (default 0.6), else 1 (like check_sdd.py)

    python3 check_sdd_entities.py --golden golden.json [--sdd <file>] [--strict]

What is scored (weights):
  entities   0.35  golden entities found as table rows (recall), penalised for rows that match no
                   golden entity (precision); tier-weighted like check_vdo (core 0.7 / reference 0.3)
  class      0.15  row class equals golden class (Federated for every BIRD table)
  connector  0.15  connector key in the row is on the CEP federated allow-list and equals a live
                   variant's key in the golden
  object     0.15  external object equals a live variant's object name
  fields     0.10  source fields listed in the row vs golden fields (F1); backticked `field → TYPE`,
                   backticked `field`, or a plain comma-separated list
  joins      0.10  `field → Entity.field` pairs vs golden foreign keys (either direction)

The table is parsed from the first `### Data Fabric entities` heading to the next heading; rows
are split on `|`; `[SME REVIEW]` / `[DEFAULT]` cells count as unresolved (no credit, no penalty on
precision). Stdlib only.
"""
from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from pathlib import Path

W = {"entities": 0.35, "class": 0.15, "connector": 0.15, "object": 0.15, "fields": 0.10, "joins": 0.10}
CEP_CONNECTORS = {
    "uipath-salesforce-sfdc", "uipath-snowflake-snowflake", "uipath-servicenow-servicenow",
    "uipath-uipath-jdbc", "uipath-coupa-coupa", "uipath-sap-c4cv2",
    "uipath-microsoft-azureactivedirectory", "uipath-microsoft-dynamicscrm",
    "uipath-workday-workdayrest", "uipath-workday-workday", "uipath-microsoft-onedrive",
    "uipath-zendesk-zendesk", "data-service",
}
UNRESOLVED = re.compile(r"\[(SME REVIEW|DEFAULT)\]", re.I)
HEADING = re.compile(r"^#{2,4}\s+(?:[\d.]+\s+)?Data Fabric entities\s*$", re.M | re.I)   # "### 3.2 Data Fabric entities" too


def norm(s: str | None) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def find_sdd(explicit: str | None) -> Path | None:
    if explicit:
        p = Path(explicit)
        return p if p.exists() else None
    cands = [Path(p) for p in glob.glob("**/*-sdd*.md", recursive=True)] + [Path(p) for p in glob.glob("**/*SDD*.md", recursive=True)]
    cands = [c for c in cands if "node_modules" not in c.parts]
    return sorted(cands, key=lambda p: p.stat().st_mtime, reverse=True)[0] if cands else None


def parse_table(text: str) -> list[dict]:
    m = HEADING.search(text)
    if not m:
        return []
    body = text[m.end():]
    nxt = re.search(r"^#{1,4}\s", body, re.M)
    body = body[: nxt.start()] if nxt else body
    rows = []
    header: list[str] | None = None
    for line in body.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if header is None:
            header = [norm(c) for c in cells]
            continue
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
            continue
        if len(cells) < 3:
            continue
        row = dict(zip(header, cells))
        # tolerate header wording variants
        def col(*names):
            for n in names:
                for h, v in row.items():
                    if n in h:
                        return v
            return ""
        rows.append({
            "entity": col("entity"),
            "class": col("class", "direction"),
            # tolerate planners that write the connection instead of the connector key
            "connector": col("connector", "systemofrecord", "sourceconnection", "connection", "system"),
            "object": col("externalobject", "sourcetable", "sourceobject", "object", "table"),
            "fields": col("fields"),
            "joins": col("joins", "relationships"),
            "consumers": col("consumers"),
        })
    for r in rows:
        if norm(r["class"]) in ("readonly", "read-only", "readonlyview"):
            r["class"] = "Federated"                          # a read-only view is a federated entity
    return [r for r in rows if r["entity"] and not r["entity"].startswith("<")]


# Connection names → connector keys, for tables that name the connection instead of the key.
CONNECTION_TO_KEY = {
    "birdadminsqlserver": "uipath-uipath-jdbc", "adminredshift": "uipath-uipath-jdbc",
    "sureshc": "uipath-snowflake-snowflake", "ven03565": "uipath-servicenow-servicenow",
}


def score(golden: dict, rows: list[dict], details: list[str]) -> float:
    gold = golden["entities"]
    gmap = {norm(g["name"]): g for g in gold}
    matched: dict[str, dict] = {}
    unmatched = 0
    for r in rows:
        key = next((gn for gn in gmap if norm(r["entity"]) == gn or norm(r["entity"]).endswith(gn) or norm(r["object"]).endswith(gn)), None)
        if key and key not in matched:
            matched[key] = r
        else:
            unmatched += 1
    core = [g for g in gold if g["tier"] == "core"]; ref = [g for g in gold if g["tier"] != "core"]
    rec_core = sum(1 for g in core if norm(g["name"]) in matched) / len(core) if core else 1.0
    rec_ref = sum(1 for g in ref if norm(g["name"]) in matched) / len(ref) if ref else 1.0
    prec = len(matched) / (len(matched) + unmatched) if (matched or unmatched) else 0.0
    s_entities = 0.7 * rec_core + 0.3 * rec_ref
    s_entities = 0.8 * s_entities + 0.2 * prec
    details.append(f"[entities] core {sum(1 for g in core if norm(g['name']) in matched)}/{len(core)} reference {sum(1 for g in ref if norm(g['name']) in matched)}/{len(ref)} unmatched rows {unmatched}")
    if not matched:
        details.append("[entities] no golden entity matched — nothing else to score")
        return W["entities"] * s_entities

    n = len(matched); cls = conn = obj = 0; f1s = []; hit_j = 0; agent_j = 0
    gjoins = {(norm(g["name"]), norm(j["relatedEntity"]), norm(j["joinField"]), norm(j["relatedJoinField"])) for g in gold for j in g["joins"]}
    for gn, r in matched.items():
        g = gmap[gn]
        cls_cell = norm(re.split(r"[·(/,\-]|\breuse\b", r["class"], maxsplit=1)[0]) if r["class"] else ""
        if cls_cell == norm(g["class"]) or norm(r["class"]).startswith(norm(g["class"])):
            cls += 1
        keys = re.findall(r"(uipath-[a-z0-9-]+|data-service)", r["connector"])
        key = keys[0] if keys else None
        if key is None:                                      # a connection name instead of a key
            for token in re.findall(r"`([^`]+)`", r["connector"]) + [r["connector"]]:
                if norm(token) in CONNECTION_TO_KEY:
                    key = CONNECTION_TO_KEY[norm(token)]
                    break
        if norm(r["class"]) in ("readonly", "read-only") and not norm(r["class"]).startswith("federated"):
            r["class"] = "Federated"                          # a read-only view is a federated entity
        live_keys = {k.split("|")[0] for k in (g.get("live") or {})}
        if key and key in CEP_CONNECTORS and (not live_keys or key in live_keys):
            conn += 1
        elif not UNRESOLVED.search(r["connector"]):
            details.append(f"[connector] {g['name']}: {r['connector'][:60]!r} not an allow-listed live key {sorted(live_keys)}")
        objs = [norm(x) for x in re.findall(r"`([^`]+)`", r["object"])] or [norm(r["object"].split("·")[0])]
        live = g.get("live") or {}
        live_objs = {norm(v.get("externalObjectName")) for v in live.values()}
        live_names = {norm(v.get("entityName")) for v in live.values()}
        # Credit the connector object name, or — when the planner reuses a deployed federated entity
        # under its estate-reuse rule — that entity's own name in the Entity column.
        if any(o in live_objs for o in objs) or norm(r["entity"]) in live_names or (not live_objs and any(o.endswith(gn) for o in objs)):
            obj += 1
        elif not UNRESOLVED.search(r["object"]):
            details.append(f"[object] {g['name']}: {r['object'][:60]!r} not a live object")
        gfields = {norm(f["sourceField"]) for f in g["fields"]}
        afields = ({norm(x) for x in re.findall(r"`([A-Za-z0-9_ .-]+?)\s*(?:→|->)", r["fields"])}
                   or {norm(x) for x in re.findall(r"`([A-Za-z0-9_.-]+)`", r["fields"])}
                   # a plain comma-separated list without backticks (a compressed table still names the fields)
                   or {norm(re.split(r"\s*(?:→|->|:)\s*", x.strip())[0]) for x in r["fields"].split(",") if x.strip()})
        afields = {a for a in afields if a}
        tp = len(afields & gfields)
        p = tp / len(afields) if afields else 0.0; rc = tp / len(gfields) if gfields else 1.0
        f1s.append(2 * p * rc / (p + rc) if p + rc else 0.0)
        for m in re.finditer(r"`?([A-Za-z0-9_]+)`?\s*(?:→|->)\s*`?([A-Za-z0-9_]+)\.([A-Za-z0-9_]+)`?", r["joins"]):
            agent_j += 1
            jf, rel, rjf = m.groups()
            rel_n = next((x for x in gmap if norm(rel) == x or norm(rel).endswith(x) or x.endswith(norm(rel))), norm(rel))
            k = (gn, rel_n, norm(jf), norm(rjf)); rk = (rel_n, gn, norm(rjf), norm(jf))
            if k in gjoins or rk in gjoins:
                hit_j += 1
    j_rec = hit_j / len(gjoins) if gjoins else 1.0
    j_prec = hit_j / agent_j if agent_j else (1.0 if not gjoins else 0.0)
    details.append(f"[class] {cls}/{n} · [connector] {conn}/{n} · [object] {obj}/{n} · [fields] mean F1 {sum(f1s)/n:.2f} · [joins] recall {hit_j}/{len(gjoins)} precision {hit_j}/{agent_j}")
    return (W["entities"] * s_entities + W["class"] * cls / n + W["connector"] * conn / n + W["object"] * obj / n
            + W["fields"] * (sum(f1s) / n) + W["joins"] * (0.7 * j_rec + 0.3 * j_prec))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--golden", required=True)
    ap.add_argument("--sdd")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--threshold", type=float, default=0.6)
    args = ap.parse_args()
    details: list[str] = []
    golden = json.load(open(args.golden))
    sdd = find_sdd(args.sdd)
    if sdd is None:
        print("0.0000"); print("[sdd] no *-sdd.md found"); return 1 if args.strict else 0
    rows = parse_table(sdd.read_text(errors="replace"))
    details.insert(0, f"[sdd] {sdd} · {len(rows)} entity rows")
    if not rows:
        details.append("[sdd] no `### Data Fabric entities` table with rows")
        s = 0.0
    else:
        s = max(0.0, min(1.0, score(golden, rows, details)))
    print(f"{s:.4f}")
    for d in details:
        print(d)
    return (0 if s >= args.threshold else 1) if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
