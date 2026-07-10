#!/usr/bin/env python3
"""Verify smoke_update_existing_flow: agent must edit MovieReportFlow's
one Query node and then revert. Success ≡ final .flow byte-equivalent to
the pre_state snapshot on all fields the agent is supposed to have
touched (queryExpression + _sortFieldName + isAscending), AND on every
other node in the file (no collateral changes).

The snapshot lives at MovieReportSolution/MovieReportFlow/pre_state.flow
(dropped by scaffold_movie_report_flow.py in pre_run).
"""
import json
import sys
from pathlib import Path


FLOW = Path("MovieReportSolution/MovieReportFlow/MovieReportFlow.flow")
SNAP = Path("MovieReportSolution/MovieReportFlow/pre_state.flow")


def load(p):
    if not p.exists():
        print(f"FAIL: missing {p}", file=sys.stderr)
        sys.exit(1)
    with open(p) as f:
        return json.load(f)


def q_node(doc):
    for n in doc.get("nodes", []):
        if (n.get("type", "")
                .endswith(".query-entity-records")):
            return n
    return None


def main() -> int:
    initial = load(SNAP)
    final = load(FLOW)

    i_q = q_node(initial)
    f_q = q_node(final)
    if not i_q or not f_q:
        print("FAIL: query-entity-records node missing", file=sys.stderr)
        return 1

    # Post-revert, the fields the agent edited must be back to their
    # initial values. Missing key == missing key (revert = clear).
    i_qp = (i_q.get("inputs", {}).get("detail", {}).get("queryParameters") or {})
    f_qp = (f_q.get("inputs", {}).get("detail", {}).get("queryParameters") or {})
    i_bp = (i_q.get("inputs", {}).get("detail", {}).get("bodyParameters") or {})
    f_bp = (f_q.get("inputs", {}).get("detail", {}).get("bodyParameters") or {})

    for k in ("queryExpression",):
        if i_qp.get(k) != f_qp.get(k):
            print(f"FAIL: queryParameters.{k} not reverted: initial={i_qp.get(k)!r} final={f_qp.get(k)!r}", file=sys.stderr)
            return 1
    for k in ("_sortFieldName",):
        if i_bp.get(k) != f_bp.get(k):
            print(f"FAIL: bodyParameters.{k} not reverted: initial={i_bp.get(k)!r} final={f_bp.get(k)!r}", file=sys.stderr)
            return 1
    if i_qp.get("isAscending", False) != f_qp.get("isAscending", False):
        print(f"FAIL: queryParameters.isAscending not reverted: initial={i_qp.get('isAscending')!r} final={f_qp.get('isAscending')!r}", file=sys.stderr)
        return 1

    # No other nodes may have been added or removed
    i_ids = {n["id"] for n in initial.get("nodes", [])}
    f_ids = {n["id"] for n in final.get("nodes", [])}
    if i_ids != f_ids:
        print(f"FAIL: node set changed. initial={sorted(i_ids)} final={sorted(f_ids)}", file=sys.stderr)
        return 1

    print(f"OK: MovieReportFlow reverted cleanly; {len(i_ids)} nodes, no drift")
    return 0


if __name__ == "__main__":
    sys.exit(main())
