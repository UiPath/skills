#!/usr/bin/env python3
"""Assert connector field-name fidelity in a built caseplan.json.

The authority is the LIVE connector contract, fetched with `uip maestro case
spec` at grade time: `.Data.Inputs.*[].Name` for request fields,
`.Data.Outputs.ResponseFields[].Name` for response fields, and
`.Data.Filter.Fields[].Name` for filterable fields. Expectations are NOT
hardcoded here — a connector version bump changes the contract, and a frozen
golden would go stale silently (the failure mode the cm_golden fixture header
warns about).

Each authority `Name` is a dotted LEAF PATH. Top-level property names are the
ordered de-duplicated FIRST segments; nested levels are the later segments,
reached through `properties` / `items` / `$ref`. Array markers (`[*]`) are part
of the key.

Checks, in order:
  1. inputs[].body keys           -> Inputs.*[].Name          (written -> authority)
  2. payload output properties    -> ResponseFields[].Name    (set equality, Error excluded)
  3. definitions keys             -> the $ref value targeting each one
  4. compiled trigger filter      -> Filter.Fields[].Name     (names appear verbatim)
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys

CASEPLAN = "ConnectorNaming/ConnectorNaming/caseplan.json"
ERROR_OUTPUT_NAMES = {"error"}
ENVELOPE_BODY_KEYS = {"parameters", "filters"}
FAILURES: list[str] = []


def fail(msg: str) -> None:
    FAILURES.append(msg)


def ci(obj, *keys):
    """Case-insensitive nested get — the caseplan is camelCase, the spec PascalCase."""
    for key in keys:
        if not isinstance(obj, dict):
            return None
        for actual in obj:
            if actual.lower() == key.lower():
                obj = obj[actual]
                break
        else:
            return None
    return obj


def norm(name: str) -> str:
    """Compare ignoring case and underscores — used only to PAIR a written key
    with its authority segment, never to accept one as correct."""
    return re.sub(r"[_\s]", "", name or "").lower()


def spec(kind: str, type_id: str, connection_id: str) -> dict:
    out = subprocess.run(
        ["uip", "maestro", "case", "spec", "--type", kind,
         "--activity-type-id", type_id, "--connection-id", connection_id,
         "--skip-case-shape", "--output", "json"],
        capture_output=True, text=True, timeout=120,
    ).stdout
    try:
        payload = json.loads(out)
    except json.JSONDecodeError:
        fail(f"case spec --type {kind} {type_id} returned non-JSON")
        return {}
    if payload.get("Result") not in (None, "Success"):
        fail(f"case spec --type {kind} {type_id} failed: {payload.get('Message')}")
        return {}
    return payload.get("Data") or {}


def authority_names(data: dict, section: str) -> list[str]:
    if section == "outputs":
        entries = ci(data, "Outputs", "ResponseFields") or []
    elif section == "filter":
        entries = ci(data, "Filter", "Fields") or []
    else:
        entries = []
        for sink_value in (ci(data, "Inputs") or {}).values():
            if isinstance(sink_value, list):
                entries.extend(sink_value)
    return [ci(e, "Name") for e in entries if isinstance(e, dict) and ci(e, "Name")]


def top_level(names: list[str]) -> list[str]:
    out: list[str] = []
    for n in names:
        seg = n.split(".")[0]
        if seg not in out:
            out.append(seg)
    return out


def connector_nodes(plan: dict):
    """Yield (displayName, connectorKey, block) for every connector task."""
    def walk(node):
        if isinstance(node, dict):
            if node.get("type") in ("execute-connector-activity", "wait-for-connector"):
                block = node.get("data") or {}
                ck = next((c.get("value") for c in (block.get("context") or [])
                           if c.get("name") == "connectorKey"), None)
                yield node.get("displayName"), ck, block
            for v in node.values():
                yield from walk(v)
        elif isinstance(node, list):
            for v in node:
                yield from walk(v)
    yield from walk(plan)


def check_inputs(label: str, block: dict, auth: list[str]) -> None:
    """Written -> authority only. An authority name with no written key is an
    unused optional parameter, not a mismatch."""
    segs = {norm(s): s for s in top_level(auth)}
    for entry in block.get("inputs") or []:
        body = entry.get("body")
        if not isinstance(body, dict):
            continue
        for written in body:
            # structural envelope keys a trigger input body carries, not contract fields:
            # `parameters` holds eventParameters, `filters` holds the compiled JMESPath
            if written in ENVELOPE_BODY_KEYS:
                continue
            want = segs.get(norm(written))
            if want is None:
                fail(f"{label}: input key {written!r} matches no field in the connector contract")
            elif written != want:
                fail(f"{label}: input key {written!r} should be {want!r} (byte-exact contract name)")


def check_outputs(label: str, block: dict, auth: list[str]) -> None:
    expected = top_level(auth)
    for entry in block.get("outputs") or []:
        name = str(entry.get("name") or "")
        if name.lower() in ERROR_OUTPUT_NAMES:
            continue  # fixed platform envelope; ResponseFields never describes it
        props = ci(entry.get("body") or {}, "properties")
        if not isinstance(props, dict) or not props:
            continue
        written = list(props.keys())
        if set(written) != set(expected):
            missing = [e for e in expected if e not in written]
            extra = [w for w in written if w not in expected]
            fail(f"{label}: output {name!r} property names do not match the contract; "
                 f"missing={missing[:8]} unexpected={extra[:8]}")


def check_definitions(label: str, block: dict) -> None:
    raw = json.dumps(block)
    refs = set(re.findall(r'"\$ref"\s*:\s*"#/definitions/([^"]+)"', raw))
    if not refs:
        return
    defs: set[str] = set()

    def walk(node):
        if isinstance(node, dict):
            for k, v in node.items():
                if k.lower() == "definitions" and isinstance(v, dict):
                    defs.update(v.keys())
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
    walk(block)
    dangling = sorted(r for r in refs if r not in defs)
    if dangling:
        fail(f"{label}: {len(dangling)} $ref target(s) resolve to no definitions key "
             f"(the definitions keys were renamed): {dangling[:6]}")


def check_filter(label: str, block: dict, auth: list[str]) -> None:
    """Filter field names compile into a JMESPath expression — a third sink
    where a renamed field silently matches nothing at runtime."""
    raw = json.dumps(block)
    exprs = re.findall(r'"(?:expression|filterExpression)"\s*:\s*"([^"]+)"', raw)
    if not exprs:
        return
    blob = " ".join(exprs)
    by_norm = {norm(a): a for a in auth}
    for token in set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*(?:\[\*\])?(?:\.[A-Za-z0-9_]+)*", blob)):
        want = by_norm.get(norm(token))
        if want and token != want:
            fail(f"{label}: compiled filter references {token!r}; the contract field is {want!r}")


def main() -> int:
    path = sys.argv[1] if len(sys.argv) > 1 else CASEPLAN
    if not os.path.exists(path):
        print(f"FAIL: {path} not found")
        return 1
    plan = json.load(open(path))

    seen = 0
    for label, connector_key, block in connector_nodes(plan):
        # connection id is context[name="resourceKey"]; the activity type id is
        # buried in the metadata config blob as uiPathActivityTypeId
        ctx = {c.get("name"): c.get("value") for c in (block.get("context") or [])}
        conn = ctx.get("resourceKey") or block.get("connectionId")
        found = re.findall(r'"uiPathActivityTypeId"\s*:\s*\\?"?([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})',
                           json.dumps(block))
        type_id = block.get("typeId") or (found[0] if found else None)
        if not type_id or not conn:
            fail(f"{label}: cannot locate typeId/connectionId on the node to fetch its contract")
            continue
        kind = "trigger" if block.get("serviceType") == "Intsvc.WaitForEvent" else "activity"
        data = spec(kind, str(type_id), str(conn))
        if not data:
            continue
        seen += 1
        check_inputs(label, block, authority_names(data, "inputs"))
        check_outputs(label, block, authority_names(data, "outputs"))
        check_definitions(label, block)
        check_filter(label, block, authority_names(data, "filter"))

    if seen < 2:
        fail(f"expected 2 connector tasks with resolvable contracts, graded {seen}")

    for f in FAILURES:
        print("FAIL:", f)
    if FAILURES:
        return 1
    print(f"PASS: connector field names match the live contract on {seen} connector task(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
