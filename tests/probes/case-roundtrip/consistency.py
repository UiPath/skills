"""Post-pull checks for one round trip (MST-15831): what 'consistent' means, fixed before
the first publish.

  entry-points  same entry points as before; each uniqueId unchanged; each filePath
                '...#<id>' names a trigger node in caseplan.json; its displayName matches
                that trigger's label (when the trigger has one)
  sidecar       any file the save added that names node ids must name exactly caseplan's
                node ids (no stale node, none missing)
  cli-editable  the designer's own converter round-trips the pulled caseplan.json with zero
                divergences (needs node and the vendored @uipath/case-schema; see simulate.cjs)

Run: python3 consistency.py <before_project_dir> <after_project_dir> [--case-schema <index.cjs>]
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))


def read(path):
    with open(path, encoding="utf-8-sig") as fh:
        return json.load(fh)


def entry_points(before: str, after: str) -> list[str]:
    problems = []
    a = {e["uniqueId"]: e for e in read(os.path.join(before, "entry-points.json"))["entryPoints"]}
    b_list = read(os.path.join(after, "entry-points.json"))["entryPoints"]
    b = {e.get("uniqueId"): e for e in b_list}
    if set(a) != set(b):
        problems.append(f"uniqueIds changed: before {sorted(a)}, after {sorted(b)}")
    plan = read(os.path.join(after, "caseplan.json"))
    triggers = {n["id"]: n for n in plan.get("nodes", []) if "trigger" in str(n.get("type", "")).lower()}
    for e in b_list:
        target = e.get("filePath", "").rsplit("#", 1)[-1]
        if target not in triggers:
            problems.append(f"entry point {e.get('uniqueId')} names #{target}, which is no trigger node")
            continue
        label = (triggers[target].get("data") or {}).get("label")
        if label and e.get("displayName") != label:
            problems.append(f"entry point {e.get('uniqueId')} displayName {e.get('displayName')!r} != trigger label {label!r}")
    return problems


def sidecar(before: str, after: str) -> list[str]:
    plan_ids = {n["id"] for n in read(os.path.join(after, "caseplan.json")).get("nodes", [])}
    problems = []
    for name in sorted(set(os.listdir(after)) - set(os.listdir(before))):
        try:
            doc = read(os.path.join(after, name))
        except (ValueError, IsADirectoryError, UnicodeDecodeError):
            continue
        text = json.dumps(doc)
        named = {i for i in plan_ids if i in text}
        if named and named != plan_ids:
            problems.append(f"{name} names {len(named)} of {len(plan_ids)} node ids; missing {sorted(plan_ids - named)}")
    return problems


def cli_editable(after: str, case_schema: str) -> list[str]:
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "caseplan.json")
        r = subprocess.run(["node", os.path.join(HERE, "simulate.cjs"), os.path.join(after, "caseplan.json"), out],
                           env={**os.environ, "CS": case_schema}, capture_output=True, text=True)
        if r.returncode != 0:
            return [f"converter failed: {r.stderr.strip()[-300:]}"]
        return [] if read(out) == read(os.path.join(after, "caseplan.json")) else \
            ["the designer's converter does not round-trip the pulled caseplan.json unchanged"]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("before")
    ap.add_argument("after")
    ap.add_argument("--case-schema")
    args = ap.parse_args(argv)
    report = {"entry-points": entry_points(args.before, args.after), "sidecar": sidecar(args.before, args.after)}
    if args.case_schema:
        report["cli-editable"] = cli_editable(args.after, args.case_schema)
    json.dump(report, sys.stdout, indent=1)
    print()
    return 1 if any(report.values()) else 0


if __name__ == "__main__":
    sys.exit(main())
