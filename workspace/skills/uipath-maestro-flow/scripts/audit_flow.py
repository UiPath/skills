#!/usr/bin/env python3
"""Audit a `.flow` file for the defects `uip maestro flow validate` does not catch, and
optionally repair the mechanical ones in the same call.

    audit_flow.py <FLOW> --json-out /tmp/findings.json     # report
    audit_flow.py <FLOW> --apply                           # repair what is mechanical, then re-audit
    audit_flow.py <FLOW> --fix-plan /tmp/fixes.json        # emit the repairs as a flow_edit plan

Checks: topology (ports, wiring rules), expressions (`=js:` contract), Jint constructs, resource
`bindings[]`, runtime gaps (error-handling shapes, layout sizes, variables.nodes[], HITL port, ids,
End-node output mappings). Exit 0 when no error-severity finding remains, 1 otherwise.

Mechanically repairable: MISSING_NODE_VARIABLE, MISSING_LAYOUT, LAYOUT_SIZE_MISMATCH,
MISSING_BINDING (when the definition supplies resource/resourceSubType), FLAG_WITHOUT_ERROR_EDGE,
ERROR_EDGE_WITHOUT_FLAG. Everything else needs a decision and is reported, never auto-changed.
"""
import argparse
import json
import sys

from _flow import bindings as B
from _flow import expressions as E
from _flow import jint as J
from _flow import lib as fl
from _flow import plan as P
from _flow import runtime_gaps as G
from _flow import topology as T

CHECKS = ("topology", "expressions", "jint", "bindings", "runtime-gaps")
FIXABLE = {"MISSING_NODE_VARIABLE", "MISSING_LAYOUT", "LAYOUT_SIZE_MISMATCH",
           "MISSING_BINDING", "FLAG_WITHOUT_ERROR_EDGE", "ERROR_EDGE_WITHOUT_FLAG"}


def collect_all(flow, only=None, reference_fields=False):
    runners = {
        "topology": lambda: T.collect(flow),
        "expressions": lambda: E.collect(flow),
        "jint": lambda: J.collect(flow),
        "bindings": lambda: B.collect(flow)[0],
        "runtime-gaps": lambda: G.collect(flow, reference_fields),
    }
    names = only or CHECKS
    out = {}
    for name in names:
        out[name] = sorted(runners[name](), key=lambda f: (f["severity"] != "error", f["code"],
                                                           f.get("node") or "", f["message"]))
    return out


def fix_ops(flow, findings):
    """Turn the mechanically-repairable findings into flow_edit plan ops."""
    ops, skipped = [], []
    _, missing_bindings = B.collect(flow)
    seen_bindings = False
    for name in findings:
        for f in findings[name]:
            code, nid = f["code"], f.get("node")
            if code not in FIXABLE:
                continue
            if code == "MISSING_NODE_VARIABLE":
                ops.append({"op": "add-node-variable", "node": nid, "outputId": "output"})
            elif code in ("MISSING_LAYOUT", "LAYOUT_SIZE_MISMATCH"):
                ntype = (fl.node_map(flow).get(nid) or {}).get("type", "")
                size = fl.expected_size(ntype)
                ops.append({"op": "set-layout", "node": nid, "width": size["width"], "height": size["height"]})
            elif code == "MISSING_BINDING":
                if seen_bindings:
                    continue
                complete = [e for e in missing_bindings if "resource" in e and "resourceSubType" in e]
                incomplete = [e["id"] for e in missing_bindings if e not in complete]
                if complete:
                    ops.append({"op": "add-bindings", "entries": complete})
                for eid in incomplete:
                    skipped.append("MISSING_BINDING %s — definition supplies no resource/resourceSubType; "
                                   "take the shape from the resource plugin's impl.md" % eid)
                seen_bindings = True
            elif code == "FLAG_WITHOUT_ERROR_EDGE":
                ops.append({"op": "set-error-flag", "node": nid, "value": False})
            elif code == "ERROR_EDGE_WITHOUT_FLAG":
                ops.append({"op": "set-error-flag", "node": nid, "value": True})
    # de-duplicate, keep order
    uniq = []
    for op in ops:
        if op not in uniq:
            uniq.append(op)
    return uniq, skipped


def summarize(findings, max_print):
    total_err = 0
    for name in findings:
        f = findings[name]
        errs = sum(1 for x in f if x["severity"] == "error")
        warns = sum(1 for x in f if x["severity"] == "warning")
        total_err += errs
        print("%-13s %d error(s), %d warning(s), %d info" % (name, errs, warns, len(f) - errs - warns))
        for x in f[:max_print]:
            print("    %-7s %-26s %-40s %s" % (x["severity"], x["code"], fl.location(x), x["message"]))
        if len(f) > max_print:
            print("    ... %d more (use --json-out to see all)" % (len(f) - max_print))
    return total_err


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("flow")
    p.add_argument("--json-out", help="write the full finding list here")
    p.add_argument("--max-print", type=int, default=10, help="findings printed per check (default 10)")
    p.add_argument("--reference-fields", action="store_true",
                   help="also list connector fields that look like connection-scoped reference ids")
    p.add_argument("--only", help="comma-separated subset: " + ",".join(CHECKS))
    p.add_argument("--fix-plan", help="write the mechanical repairs as a flow_edit plan and exit")
    p.add_argument("--apply", action="store_true", help="apply the mechanical repairs, then re-audit")
    args = p.parse_args(argv)

    only = None
    if args.only:
        only = [c.strip() for c in args.only.split(",")]
        unknown = set(only) - set(CHECKS)
        if unknown:
            fl.die("unknown check(s): %s" % ", ".join(sorted(unknown)))

    flow = fl.load(args.flow)
    findings = collect_all(flow, only, args.reference_fields)

    if args.fix_plan or args.apply:
        ops, skipped = fix_ops(flow, findings)
        if args.fix_plan:
            with open(args.fix_plan, "w") as fh:
                json.dump({"ops": ops}, fh, indent=2)
                fh.write("\n")
            print("%d mechanical repair op(s) -> %s" % (len(ops), args.fix_plan))
            for s in skipped:
                print("  needs a decision: %s" % s)
            print("apply with: flow_edit.py apply --flow %s --plan %s" % (args.flow, args.fix_plan))
            return 0 if ops else 1
        if not ops:
            print("no mechanical repair available")
        else:
            log = P.apply_ops(flow, ops)
            fl.save(args.flow, flow)
            print("repaired %d item(s):" % len(ops))
            for line in log:
                print("  " + line)
            for s in skipped:
                print("  needs a decision: %s" % s)
            flow = fl.load(args.flow)
            findings = collect_all(flow, only, args.reference_fields)
            print("re-audit after repair:")

    total_err = summarize(findings, args.max_print)
    if args.json_out:
        with open(args.json_out, "w") as fh:
            json.dump({"flow": args.flow, "checks": findings}, fh, indent=2)
            fh.write("\n")
        print("full findings: %s" % args.json_out)
    print("audit: %s" % ("FAIL (%d error(s))" % total_err if total_err else "clean"))
    return 1 if total_err else 0


if __name__ == "__main__":
    sys.exit(main())
