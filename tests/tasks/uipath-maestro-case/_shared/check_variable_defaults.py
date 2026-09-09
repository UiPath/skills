#!/usr/bin/env python3
"""Grade Step 12 Check 14 — every variable `default` is a string.

Regression guarded
------------------
The caseplan -> BPMN converter keeps only primitive attributes
(`bpmn-moddle.ts` `onlyPrimitiveVariableFields`):

    if (value === null || typeof value !== "object") { result[key] = value; }

So an object-valued `default` is **deleted without comment**. The emitted BPMN carries no `default`
attribute for that variable, the variable is null at runtime, and the first task bound to it dies
with `AGENT_STARTUP.INPUT_VALIDATION_ERROR / <input> Field required`.

Observed on a shipped build: 13 non-string defaults, all `jsonSchema`, all dicts. Twelve were empty
`{}`; one carried the real payload and killed the first agent task bound to it.

Nothing upstream catches it:
  * `uip maestro case validate` returns `Valid`
  * the FE's own Zod schema types this field `z.any()` and parses it clean
    (`UiPathVariablesJsonSchema.ts:12`) -- verified by safeParse against the failing artifact
  * only the serializer notices, and it does not report

`VariableTypes.ts` declares `default?: string`, which is the true contract but is compile-time only
and never sees agent-authored JSON. This checker enforces the serializer's *effective* contract.

Numbers and booleans survive serialization (`typeof 5 !== "object"`) but still violate the declared
string type, so they are reported too -- at WARN weight in the message, same exit code.

Exit 0 = pass, 1 = fail. Run from the sandbox root.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

SKIP = {".venv", "node_modules", ".npm-prefix", "dist"}
VARIABLE_ARRAYS = ("inputs", "outputs", "inputOutputs")


def find_caseplans(root: Path):
    for p in root.rglob("caseplan.json"):
        if SKIP.isdisjoint(p.parts):
            yield p


def offenders(case: dict):
    """Yield (array, id, type, python_type, repr) for every non-string default."""
    variables = case.get("variables") or {}
    for arr in VARIABLE_ARRAYS:
        for entry in variables.get(arr) or []:
            if not isinstance(entry, dict) or "default" not in entry:
                continue
            value = entry["default"]
            if isinstance(value, str):
                continue
            yield (
                arr,
                entry.get("id") or entry.get("name") or "<unnamed>",
                entry.get("type") or "<untyped>",
                type(value).__name__,
                json.dumps(value)[:70],
            )


def encoded(value) -> str:
    """What the entry should have said."""
    if isinstance(value, bool):
        return '"true"' if value else '"false"'
    if isinstance(value, (int, float)):
        return f'"{value}"'
    return json.dumps(json.dumps(value, separators=(",", ":")))


def main() -> int:
    root = Path.cwd()
    plans = list(find_caseplans(root))

    if not plans:
        print("PASS: no caseplan.json under the sandbox — nothing to check.")
        return 0

    total_bad = 0
    for plan in plans:
        rel = plan.relative_to(root)
        try:
            case = json.loads(plan.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            print(f"FAIL: {rel} unreadable/unparseable: {exc}")
            return 1

        bad = list(offenders(case))
        variables = case.get("variables") or {}
        counted = sum(
            1
            for arr in VARIABLE_ARRAYS
            for e in variables.get(arr) or []
            if isinstance(e, dict) and "default" in e
        )
        print(f"{rel}: {counted} default(s), {len(bad)} non-string")

        for arr, vid, vtype, pytype, shown in bad:
            total_bad += 1
            raw = None
            for e in variables.get(arr) or []:
                if isinstance(e, dict) and (e.get("id") == vid or e.get("name") == vid):
                    raw = e.get("default")
                    break
            fixed = encoded(raw)
            fatal = "DELETED at serialization" if isinstance(raw, (dict, list)) else "violates declared string type"
            print(f"  variables.{arr}[{vid}] type={vtype} default={pytype} -> {fatal}")
            print(f"     is:     {shown}")
            print(f"     should: {fixed}")

    if total_bad:
        print(
            f"\nFAIL: {total_bad} non-string variable default(s).\n"
            "  `default` is a JSON string on every variable, whatever its type. A non-primitive\n"
            "  value there is silently deleted by the BPMN serializer, leaving the variable null at\n"
            "  runtime; `uip maestro case validate` reports Valid regardless.\n"
            "  See global-vars/impl-json.md § `default` encoding."
        )
        return 1

    print("\nPASS: every variable default is a string.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
