#!/usr/bin/env python3
"""The requested edit to the DevCon BillingDisputeResolution fixture is present.

One subcommand per task, plus `merged`: the `.flow` came out of the skill's
decompile -> compile -> merge loop, not a hand edit.
`check_brownfield_preserved.py` grades everything the edit was not supposed to
touch. Scripts and expressions the agent wrote are run with `node` against stub
`$vars`, so the grade follows what the code returns, not how it is spelled.

Usage (from a task's run_command, cwd = sandbox root):
    python3 $REFERENCE_DIR/brownfield/check_brownfield_edit.py <edit> \\
        --original $REFERENCE_DIR/brownfield/fixture/<Sol>/<Project> --project <Sol>/<Project>

Exit 0 on pass; exit 1 with a `FAIL:` line.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _shared.check_brownfield_preserved import differing_keys, edge_key, load_project  # noqa: E402

OUT_VARIABLES = ("determination", "recommendedAction", "creditAmount", "rationale", "resolutionEmailBody")
WRITER_AGENT = "e6360c37-75b3-4315-b63e-afe9815dd65c"
CAP_CASES = ((120, 120), (500, 500), (750, 500), (10000, 500))
ACTIONS = ("escalate_to_manager", "auto_resolve", "reject", "request_more_info")
ANALYST_STUB = {"determination": "valid", "creditAmount": 42, "rationale": "stub rationale"}
JS_EXPRESSION = "jsExpression"
LITERAL = "literal"


class JsError(Exception):
    pass


def fail(message: str) -> int:
    print(f"FAIL: {message}")
    return 1


def run_js(body: str, scope: dict) -> object:
    if shutil.which("node") is None:
        raise JsError("node is not on PATH")
    program = (
        "const $vars = JSON.parse(process.argv[1]);"
        f"(async function () {{\n{body}\n}})()"
        ".then(r => process.stdout.write(JSON.stringify(r === undefined ? null : r)));"
    )
    try:
        proc = subprocess.run(
            ["node", "-e", program, json.dumps(scope)], capture_output=True, text=True, timeout=20
        )
    except subprocess.TimeoutExpired as exc:
        raise JsError("timed out") from exc
    if proc.returncode:
        errors = [line for line in proc.stderr.splitlines() if re.match(r"^\w*Error\b", line)]
        raise JsError(errors[0] if errors else f"node exited {proc.returncode}")
    return json.loads(proc.stdout or "null")


def unwrap_source(source: object) -> object:
    if not isinstance(source, dict):
        return source
    if source.get("type") == JS_EXPRESSION:
        return f"=js:{source.get('expression', '')}"
    if source.get("type") == LITERAL:
        return source.get("expression", "")
    return source


def evaluate_source(source: object, scope: dict) -> object:
    text = str(unwrap_source(source))
    if text.startswith("=js:"):
        return run_js(f"return ({text[4:]});", scope)
    if text.startswith("="):
        return run_js(f"return ({text[1:]});", scope)
    return text


def new_nodes(original: dict, final: dict) -> list[dict]:
    original_ids = {n["id"] for n in original["nodes"]}
    return [n for n in final["nodes"] if n["id"] not in original_ids]


def label(node: dict) -> str:
    return str(node.get("display", {}).get("label") or node.get("label") or "")


def caps_at_500(script: str) -> str | None:
    for given, expected in CAP_CASES:
        scope = {
            "disputeAnalyst": {"output": {**ANALYST_STUB, "creditAmount": given}},
            "logCreditAmount": {"output": {"creditAmount": given}},
        }
        try:
            result = run_js(script, scope)
        except JsError as exc:
            return f"creditAmount {given}: {exc}"
        value = result.get("creditAmount") if isinstance(result, dict) else None
        try:
            ok = abs(float(value) - expected) < 1e-9
        except (TypeError, ValueError):
            ok = False
        if not ok:
            return f"creditAmount {given} returned {json.dumps(result)}, expected {{creditAmount: {expected}}}"
    return None


def check_credit_cap(original: dict, final: dict, _original_agents: dict, _agents: dict) -> int:
    added = new_nodes(original, final)
    new_ids = {n["id"] for n in added}
    by_source: dict[str, set[str]] = {}
    edges = {edge_key(e) for e in final["edges"]}
    for source, _port, target, _tport in edges:
        by_source.setdefault(source, set()).add(target)
    frontier, seen = ["logCreditAmount"], set()
    while frontier:
        node = frontier.pop()
        for target in by_source.get(node, set()):
            if target in new_ids and target not in seen:
                seen.add(target)
                frontier.append(target)
    if any(s == "logCreditAmount" and t == "financialPosting" for s, _p, t, _tp in edges):
        return fail("logCreditAmount still connects straight to financialPosting")
    if not any(target == "financialPosting" for node in seen for target in by_source.get(node, set())):
        return fail("no new node downstream of logCreditAmount continues to financialPosting")
    scripts = [n for n in added if n["id"] in seen and n["type"] == "core.action.script"]
    if not scripts:
        return fail(f"no new Script node between logCreditAmount and financialPosting (new nodes on the path: {sorted(seen)})")
    problems = []
    for script in scripts:
        problem = caps_at_500(str(script.get("inputs", {}).get("script", "")))
        if problem is None:
            print(f"OK: {script['id']} returns min(creditAmount, 500) between logCreditAmount and financialPosting")
            return 0
        problems.append(f"{script['id']}: {problem}")
    return fail("no new Script on the path caps the credit at 500 (" + "; ".join(problems) + ")")


def case_hits(case: dict) -> list[str]:
    expression = str(case.get("expression", ""))
    source = expression if expression.startswith("=") else f"=js:{expression}"
    return [
        action
        for action in ACTIONS
        if evaluate_source(source, {"disputeAnalyst": {"output": {**ANALYST_STUB, "recommendedAction": action}}})
    ]


def check_switch_route(original: dict, final: dict, _original_agents: dict, _agents: dict) -> int:
    switch = next((n for n in final["nodes"] if n["id"] == "routeByAction"), None)
    if switch is None:
        return fail("routeByAction is gone")
    original_switch = next(n for n in original["nodes"] if n["id"] == "routeByAction")
    if label(switch) != label(original_switch):
        return fail(f"routeByAction's label changed: {label(original_switch)!r} -> {label(switch)!r}")
    cases = switch.get("inputs", {}).get("cases", [])
    by_id = {c.get("id"): c for c in cases}
    for case in original_switch["inputs"]["cases"]:
        kept = by_id.get(case["id"])
        try:
            same = kept is not None and kept.get("label") == case.get("label") and case_hits(kept) == case_hits(case)
        except JsError:
            same = False
        if not same:
            return fail(f"original switch case {case['id']!r} was changed or removed")
    original_ids = {c["id"] for c in original_switch["inputs"]["cases"]}
    added = [c for c in cases if c.get("id") not in original_ids]
    matches, notes = [], []
    for case in added:
        try:
            hits = case_hits(case)
        except JsError as exc:
            notes.append(f"{case.get('id')!r}: {exc}")
            continue
        if hits == ["request_more_info"]:
            matches.append(case)
        else:
            notes.append(f"{case.get('id')!r} matches {hits}")
    if len(matches) != 1:
        return fail(f"expected one new case that matches only request_more_info, found {len(matches)} ({'; '.join(notes) or 'no new cases'})")
    port = f"case-{matches[0]['id']}"
    targets = [t for s, p, t, _tp in (edge_key(e) for e in final["edges"]) if s == "routeByAction" and p == port]
    ends = {n["id"]: n for n in new_nodes(original, final) if n["type"] == "core.control.end"}
    end = next((ends[t] for t in targets if t in ends), None)
    if end is None:
        return fail(f"{port} does not lead to a new End node (targets: {targets})")
    outputs = end.get("outputs", {})
    missing = [v for v in OUT_VARIABLES if not str(unwrap_source(outputs.get(v, {}).get("source", ""))).strip()]
    if missing:
        return fail(f"End node {end['id']!r} does not map {missing}")
    reference = next(n for n in original["nodes"] if n["id"] == "returnRejection")["outputs"]
    scope = {"disputeAnalyst": {"output": {**ANALYST_STUB, "recommendedAction": "request_more_info"}}}
    try:
        for variable in OUT_VARIABLES[:-1]:
            got = evaluate_source(outputs[variable]["source"], scope)
            want = evaluate_source(reference[variable]["source"], scope)
            if got != want:
                return fail(f"End node {end['id']!r} maps {variable} to {got!r}; the other End nodes return {want!r}")
        body = evaluate_source(outputs["resolutionEmailBody"]["source"], scope)
    except JsError as exc:
        return fail(f"End node {end['id']!r} output does not evaluate: {exc}")
    if not isinstance(body, str) or not body.strip():
        return fail(f"resolutionEmailBody on {end['id']!r} is not a note: {body!r}")
    print(f"OK: {port} ends at {end['id']!r} ({label(end)!r}) with all five outputs mapped")
    return 0


def system_prompt(agent: dict) -> dict:
    return next((m for m in agent.get("messages", []) if m.get("role") == "system"), {})


def check_writer_prompt(_original: dict, _final: dict, original_agents: dict, agents: dict) -> int:
    writer = agents.get(WRITER_AGENT)
    if writer is None:
        return fail(f"writer agent project {WRITER_AGENT} is gone")
    before, after = original_agents[WRITER_AGENT]["agent"], writer["agent"]
    old, new = system_prompt(before), system_prompt(after)
    content = str(new.get("content", ""))
    if not re.search(r"\b(5|five)\s+business\s+days\b", content, re.IGNORECASE):
        return fail("writer system prompt does not mention 5 business days")
    if not re.search(r"next\s+statement", content, re.IGNORECASE):
        return fail("writer system prompt does not mention the next statement")
    kept = {line.strip() for line in content.splitlines()}
    lost = [line.strip() for line in str(old.get("content", "")).splitlines() if line.strip() and line.strip() not in kept]
    if lost:
        return fail(f"writer system prompt changed or dropped an existing line: {lost[0]!r}")
    tokens = new.get("contentTokens")
    if tokens is not None and "".join(str(t.get("rawString", "")) for t in tokens) != content:
        return fail("writer system prompt contentTokens rawString no longer matches content")
    if differing_keys({k: v for k, v in old.items() if k not in ("content", "contentTokens")},
                      {k: v for k, v in new.items() if k not in ("content", "contentTokens")}):
        return fail("writer system message changed outside content/contentTokens")
    if [m for m in before.get("messages", []) if m is not old] != [m for m in after.get("messages", []) if m is not new]:
        return fail("writer agent.json messages other than the system prompt changed")
    changed = [k for k in differing_keys(before, after) if k != "messages"]
    if changed:
        return fail(f"writer agent.json changed outside the system prompt ({', '.join(changed)})")
    print("OK: writer system prompt adds the 5-business-day line and keeps the rest")
    return 0


def check_merged(original: dict, final: dict, _original_agents: dict, _agents: dict) -> int:
    # merge takes every edge from the compiled source, which numbers them edge_0..edge_N
    # (builder-sdk FLOW_PARITY.md §6.2), so a surviving original edge id means a hand edit.
    # A tripwire, not proof (a hand edit can renumber too), and it inverts if merge ever keeps
    # original edge ids the way compile now keeps node ids (builder-sdk #1249, #1253).
    original_ids = {e["id"] for e in original["edges"]}
    kept = sorted(original_ids & {e.get("id") for e in final["edges"]})
    if kept:
        return fail(
            f"{len(kept)} of {len(original_ids)} original edge ids survive (e.g. {kept[0]!r}): the .flow was "
            "edited by hand, not written by `uip maestro flow merge`, which renumbers every edge. When the "
            "merge candidate changes something the task did not ask for, the skill's answer is to fix the "
            ".flow.ts and merge again, not to patch the .flow (uipath-maestro-flow references/brownfield.md, "
            "'Merge warnings: what the round trip changed')"
        )
    print("OK: the .flow was written by `uip maestro flow merge` (no original edge id survives)")
    return 0


CHECKS = {
    "credit-cap": check_credit_cap,
    "merged": check_merged,
    "switch-route": check_switch_route,
    "writer-prompt": check_writer_prompt,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("edit", choices=sorted(CHECKS))
    parser.add_argument("--original", required=True, type=Path)
    parser.add_argument("--project", required=True, type=Path)
    args = parser.parse_args(argv)
    original, original_agents = load_project(args.original)
    final, agents = load_project(args.project)
    return CHECKS[args.edit](original, final, original_agents, agents)


if __name__ == "__main__":
    sys.exit(main())
