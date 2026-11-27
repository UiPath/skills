#!/usr/bin/env python3
"""Grade a draft-mode Case skeleton: blank labelled boxes, real stages and rules, no built task.

Usage (cwd = sandbox root):
    check_draft_skeleton.py [--trigger any|manual|timer] [--routed] [--min-stages N] [--min-boxes N]

The plan is found like every other Case grader finds it, so a Studio Web layout
passes too. A skeleton passes when:
  - it has one trigger, of the requested kind when `--trigger` names one;
  - it has at least `--min-stages` (default 2) stages, each with an entry condition;
  - every task is blank (an empty `data` block) with a `<Action> [<Kind>]` name,
    and there are at least `--min-boxes` (default 3) of them;
  - `--routed`: a stage entry condition carries an expression and an outcome name;
  - `uip maestro case validate --strict` reports Valid.
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_shared"))
from draft_case import (  # noqa: E402
    BOX_LABEL, fail, is_blank, label_of, load_plan, stage_label, stages, tasks, trigger_kinds, validate,
)


def routed_conditions(doc: dict) -> list[dict]:
    """Stage entry conditions whose rule carries an expression."""
    found = []
    for stage in stages(doc):
        for cond in (stage.get("data") or {}).get("entryConditions") or []:
            rules = [r for group in cond.get("rules") or [] for r in group if isinstance(r, dict)]
            if any(r.get("conditionExpression") for r in rules):
                found.append(cond)
    return found


def problems(doc: dict, trigger: str = "any", routed: bool = False, min_stages: int = 2, min_boxes: int = 3) -> list[str]:
    out = []
    kinds = trigger_kinds(doc)
    if len(kinds) != 1 or (trigger != "any" and kinds[0] != trigger):
        out.append(f"expected one trigger{'' if trigger == 'any' else ' of kind ' + trigger}, found {kinds}")

    found_stages = stages(doc)
    if len(found_stages) < min_stages:
        out.append(f"expected >= {min_stages} stages, found {len(found_stages)}")
    no_entry = [stage_label(s) for s in found_stages if not (s.get("data") or {}).get("entryConditions")]
    if no_entry:
        out.append(f"stages without an entry condition: {no_entry}")

    found = [task for _, task in tasks(doc)]
    built = [f"{label_of(t)} ({t.get('type')})" for t in found if not is_blank(t)]
    if built:
        out.append(f"skeleton has built tasks: {built}")
    if len(found) < min_boxes:
        out.append(f"expected >= {min_boxes} blank boxes, found {len(found)}")
    bad = [label_of(t) for t in found if not BOX_LABEL.fullmatch(label_of(t))]
    if bad:
        out.append(f"boxes without an '<Action> [<Kind>]' name (optional `→ <variable>`): {bad}")

    if routed:
        conds = routed_conditions(doc)
        if not conds:
            out.append("no stage entry condition routes on an expression")
        unnamed = [c.get("id") for c in conds if not str(c.get("displayName") or "").strip()]
        if unnamed:
            out.append(f"routed entry conditions without an outcome name: {unnamed}")
    return out


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trigger", default="any", choices=["any", "manual", "timer"])
    ap.add_argument("--routed", action="store_true")
    ap.add_argument("--min-stages", type=int, default=2)
    ap.add_argument("--min-boxes", type=int, default=3)
    args = ap.parse_args(argv)

    path, doc = load_plan()
    found = problems(doc, args.trigger, args.routed, args.min_stages, args.min_boxes)
    if found:
        return fail("; ".join(found))
    print(f"Skeleton OK: {len(tasks(doc))} blank boxes in {path}", flush=True)
    return validate(path)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
