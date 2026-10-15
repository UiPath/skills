#!/usr/bin/env python3
"""The requested edit to the DevCon BillingDisputeResolution fixture is present.

One subcommand per task; `check_brownfield_preserved.py` grades everything the
edit was not supposed to touch.

Usage (from a task's run_command, cwd = sandbox root):
    python3 $REFERENCE_DIR/brownfield/check_brownfield_edit.py <edit> \\
        --original $REFERENCE_DIR/brownfield/fixture/<Sol>/<Project> --project <Sol>/<Project>

Exit 0 on pass; exit 1 with a `FAIL:` line.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _shared.check_brownfield_preserved import edge_key, load_project  # noqa: E402

OUT_VARIABLES = ("determination", "recommendedAction", "creditAmount", "rationale", "resolutionEmailBody")
WRITER_AGENT = "e6360c37-75b3-4315-b63e-afe9815dd65c"


def fail(message: str) -> int:
    print(f"FAIL: {message}")
    return 1


def new_nodes(original: dict, final: dict) -> list[dict]:
    original_ids = {n["id"] for n in original["nodes"]}
    return [n for n in final["nodes"] if n["id"] not in original_ids]


def label(node: dict) -> str:
    return str(node.get("display", {}).get("label") or node.get("label") or "")


def check_credit_cap(original: dict, final: dict, _agents: dict) -> int:
    scripts = [n for n in new_nodes(original, final) if n["type"] == "core.action.script"]
    capping = [n for n in scripts if "500" in str(n.get("inputs", {}).get("script", ""))]
    if not capping:
        return fail(f"no new Script node whose code caps at 500 (new scripts: {[n['id'] for n in scripts]})")
    edges = {edge_key(e) for e in final["edges"]}
    by_source: dict[str, set[str]] = {}
    for source, _port, target, _tport in edges:
        by_source.setdefault(source, set()).add(target)
    new_ids = {n["id"] for n in new_nodes(original, final)}
    frontier, seen = ["logCreditAmount"], set()
    while frontier:
        node = frontier.pop()
        for target in by_source.get(node, set()):
            if target in new_ids and target not in seen:
                seen.add(target)
                frontier.append(target)
    if not any(n["id"] in seen for n in capping):
        return fail("the capping Script is not downstream of logCreditAmount through new nodes only")
    if not any(target == "financialPosting" for node in seen for target in by_source.get(node, set())):
        return fail("no new node on the auto-resolve path continues to financialPosting")
    if any(s == "logCreditAmount" and t == "financialPosting" for s, _p, t, _tp in edges):
        return fail("logCreditAmount still connects straight to financialPosting")
    print(f"OK: {capping[0]['id']} caps the credit between logCreditAmount and financialPosting")
    return 0


def check_switch_route(original: dict, final: dict, _agents: dict) -> int:
    switch = next((n for n in final["nodes"] if n["id"] == "routeByAction"), None)
    if switch is None:
        return fail("routeByAction is gone")
    original_switch = next(n for n in original["nodes"] if n["id"] == "routeByAction")
    cases = switch.get("inputs", {}).get("cases", [])
    for case in original_switch["inputs"]["cases"]:
        if case not in cases:
            return fail(f"original switch case {case['id']!r} was changed or removed")
    added = [c for c in cases if c not in original_switch["inputs"]["cases"]]
    route = [c for c in added if "request_more_info" in str(c.get("expression", ""))]
    if len(route) != 1:
        return fail(f"expected one new case testing 'request_more_info', found {[c.get('id') for c in added]}")
    port = f"case-{route[0]['id']}"
    targets = [t for s, p, t, _tp in (edge_key(e) for e in final["edges"]) if s == "routeByAction" and p == port]
    ends = {n["id"]: n for n in new_nodes(original, final) if n["type"] == "core.control.end"}
    end = next((ends[t] for t in targets if t in ends), None)
    if end is None:
        return fail(f"{port} does not lead to a new End node (targets: {targets})")
    outputs = end.get("outputs", {})
    missing = [v for v in OUT_VARIABLES if not str(outputs.get(v, {}).get("source", "")).strip()]
    if missing:
        return fail(f"End node {end['id']!r} does not map {missing}")
    body = str(outputs["resolutionEmailBody"]["source"])
    if "resolutionWriter" in body or not re.search(r"['\"`]", body):
        return fail(f"resolutionEmailBody on {end['id']!r} is not a literal note: {body!r}")
    print(f"OK: {port} ends at {end['id']!r} ({label(end)!r}) with all five outputs mapped")
    return 0


def check_writer_prompt(_original: dict, _final: dict, agents: dict) -> int:
    writer = agents.get(WRITER_AGENT)
    if writer is None:
        return fail(f"writer agent project {WRITER_AGENT} is gone")
    system = " ".join(
        str(m.get("content", "")) for m in writer["agent"].get("messages", []) if m.get("role") == "system"
    )
    if not re.search(r"\b(5|five)\s+business\s+days\b", system, re.IGNORECASE):
        return fail("writer system prompt does not mention 5 business days")
    for kept in ("Billing Operations Team", "under 250 words", "invoice number"):
        if kept.lower() not in system.lower():
            return fail(f"writer system prompt lost an existing instruction ({kept!r})")
    print("OK: writer system prompt adds the 5-business-day line and keeps the rest")
    return 0


CHECKS = {
    "credit-cap": check_credit_cap,
    "switch-route": check_switch_route,
    "writer-prompt": check_writer_prompt,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("edit", choices=sorted(CHECKS))
    parser.add_argument("--original", required=True, type=Path)
    parser.add_argument("--project", required=True, type=Path)
    args = parser.parse_args(argv)
    original, _ = load_project(args.original)
    final, agents = load_project(args.project)
    return CHECKS[args.edit](original, final, agents)


if __name__ == "__main__":
    sys.exit(main())
