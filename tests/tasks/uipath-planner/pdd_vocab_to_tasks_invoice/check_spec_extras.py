#!/usr/bin/env python3
"""Score what check_tasks_entities.py does not: choice-set tasks and blocked VDO entity tasks.

Contract (coder_eval `run_command`, `score_from_stdout: true`): first stdout line = float in [0,1]; details follow.

    python3 check_spec_extras.py --golden golden.json --tasks <tasks file>

Components (weights):
  choicesets  0.5  each golden choice set has a `platform:*:choiceset:<name>` task (recall), and every entity task
                   whose body references a choice set is Blocked by a choice-set task
  blocked     0.5  each golden Federated (blocked) entity has its `platform:*:entity:<Entity>` task with
                   `Status: [!] blocked` and a `Blocked reason:` row
Stdlib only.
"""
import argparse
import json
import re
import sys
from pathlib import Path


def norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def parse(text):
    parts = re.split(r"^## Task\s+(T\d+)\s*[—-]+\s*", text, flags=re.M)
    out = []
    for i in range(1, len(parts), 2):
        body = parts[i + 1]
        def row(n):
            m = re.search(r"^\*\*%s:\*\*\s*(.+?)\s*$" % n, body, re.M | re.I)
            return m.group(1).strip() if m else ""
        out.append({"id": parts[i], "identity": row("Identity").strip("`"), "status": row("Status"),
                    "blocked": re.findall(r"T\d+", row("Blocked by")), "reason": row("Blocked reason"), "body": body})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--golden", required=True)
    ap.add_argument("--tasks", required=True)
    a = ap.parse_args()
    g = json.loads(Path(a.golden).read_text())
    p = Path(a.tasks)
    if not p.exists():
        print("0.0000"); print(f"[tasks] {p} not found"); return 0
    tasks = parse(p.read_text(errors="replace"))
    det = []
    cs_tasks = {}
    for t in tasks:
        m = re.search(r":choice-?set:([^:\s`]+)$", t["identity"], re.I)
        if m:
            cs_tasks[norm(m.group(1))] = t["id"]
    want = [norm(c) for c in g.get("choiceSets", [])]
    hit = sum(1 for c in want if c in cs_tasks)
    uses = [t for t in tasks if ":entity:" in t["identity"] and "CHOICE_SET" in t["body"]]
    edged = sum(1 for t in uses if set(t["blocked"]) & set(cs_tasks.values()))
    s_cs = 0.7 * (hit / len(want) if want else 1.0) + 0.3 * (edged / len(uses) if uses else 1.0)
    det.append(f"[choicesets] tasks {hit}/{len(want)} · entity tasks using a choice set blocked by one {edged}/{len(uses)}")
    vdos = [e for e in g["entities"] if e.get("status") == "blocked"]
    vh = 0.0
    for e in vdos:
        t = next((t for t in tasks if norm(t["identity"]).endswith("entity" + norm(e["name"]))), None)
        if not t:
            det.append(f"[blocked] {e['name']}: no entity task"); continue
        ok_status = "blocked" in t["status"].lower() or "[!]" in t["status"]
        ok_reason = bool(t["reason"])
        vh += 0.5 * ok_status + 0.5 * ok_reason
        det.append(f"[blocked] {e['name']}: status {'ok' if ok_status else t['status'] or '-'} · reason {'ok' if ok_reason else 'missing'}")
    s_bl = vh / len(vdos) if vdos else 1.0
    total = 0.5 * s_cs + 0.5 * s_bl
    print(f"{total:.4f}")
    for d in det:
        print(d)
    print(f"[components] choicesets {s_cs:.2f} · blocked {s_bl:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
