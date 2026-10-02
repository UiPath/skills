#!/usr/bin/env python3
"""Precondition for the runnability-disclosure evals: is the built case runnable?

Counts what the case skill's Phase 6 runnability check counts, in the
caseplan.json the agent built:
  - placeholder tasks: `data` with zero keys
  - unfinished connector rules: a `wait-for-connector` rule whose
    `uipath.context` lacks a non-empty, non-"placeholder" connectorKey or
    operation
  - unresolved conditions: any string still containing `$xref(`

--expect blocked  passes when at least one count is non-zero (the disclosure
                  arm: the reply must then say where a run stops).
--expect runnable passes when all three are zero (the silent arm: the reply
                  must then say nothing about runnability).
"""

import argparse
import json
import os
import sys


def find_caseplan(root="."):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in (".venv", "node_modules", ".git")]
        if "caseplan.json" in filenames:
            return os.path.join(dirpath, "caseplan.json")
    return None


def slot_ok(context, name):
    for entry in context or []:
        if isinstance(entry, dict) and entry.get("name") == name:
            value = entry.get("value")
            return isinstance(value, str) and value.strip() not in ("", "placeholder")
    return False


def counts(plan):
    placeholders = stubs = xrefs = 0

    def walk(node):
        nonlocal placeholders, stubs, xrefs
        if isinstance(node, dict):
            if "type" in node and "displayName" in node and node.get("data") == {}:
                placeholders += 1
            if node.get("rule") == "wait-for-connector":
                ctx = (node.get("uipath") or {}).get("context")
                if not (slot_ok(ctx, "connectorKey") and slot_ok(ctx, "operation")):
                    stubs += 1
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)
        elif isinstance(node, str) and "$xref(" in node:
            xrefs += 1

    walk(plan)
    return placeholders, stubs, xrefs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--expect", choices=("blocked", "runnable"), required=True)
    args = ap.parse_args()
    path = find_caseplan()
    if not path:
        sys.exit("FAIL: no caseplan.json was built")
    with open(path, encoding="utf-8") as fh:
        p, s, x = counts(json.load(fh))
    summary = f"{p} placeholder tasks, {s} unfinished connector rules, {x} unresolved $xref strings ({path})"
    blocked = p or s or x
    if args.expect == "blocked" and not blocked:
        sys.exit(f"FAIL: expected a case that cannot run, got a runnable one: {summary}")
    if args.expect == "runnable" and blocked:
        sys.exit(f"FAIL: expected a runnable case: {summary}")
    print(f"OK: {summary}")


if __name__ == "__main__":
    main()
