#!/usr/bin/env python3
"""ProductCalc: run the agent's process once under `uip maestro bpmn debug`
from the grader's own sandbox and assert what the run did.

The grader runs the debug itself: Studio Web's host can refuse the agent's own
`bpmn debug` (`UnavailableInHost`) and its
testbench stubs RunProject, so the agent's saved evidence cannot be the gate.

Asserted on the run:
- it completed with no incidents;
- a script task completed in it (the multiplication really ran);
- the process variable the request names, `product`, reads back 42.

Static guard: no script or expression holds a literal 42 outside a comment.
It catches the plain `return 42`, not every way to spell the constant
(`40 + 2`, `0x2A`), so it is not proof the value was computed; the gate is the
run itself reading back `product` = 42.
"""

from __future__ import annotations

import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from _shared import bpmn_check  # noqa: E402
from _shared.bpmn_live import (  # noqa: E402
    BPMN_NS,
    UIPATH_NS,
    COMMENT,
    KEEP_LITERAL,
    CheckFailure,
    DebugRetry,
    debug_evidence,
    get_ci,
    import_exact,
    normalized_identifier,
    q,
    require_clean_run,
    root_scope,
    run_debug,
)

NAME = "ProductCalc"
OUTPUT = "product"
EXPECTED = 42
LIVE_RUN_DIR = Path("product-calc-live")
LITERAL = re.compile(r"(?<![\w.])42(?![\w.])")


def assert_not_hardcoded(root: ET.Element) -> None:
    texts = ["".join(s.itertext()) for s in root.iter(q(BPMN_NS, "script"))]
    for node in root.iter():
        if node.tag in (q(UIPATH_NS, "input"), q(UIPATH_NS, "output")):
            texts.extend([node.attrib.get("value", ""), node.attrib.get("source", ""), node.text or ""])
    hits = [t.strip() for t in texts if t and LITERAL.search(COMMENT.sub(KEEP_LITERAL, t))]
    if hits:
        raise CheckFailure(f"the answer 42 is written into the process as a literal: {hits[:3]}")


def completed_types(debug_data) -> set[str]:
    return {
        str(get_ci(item, "ElementType") or "")
        for item in get_ci(debug_data, "ElementExecutions", []) or []
        if isinstance(item, dict) and str(get_ci(item, "Status") or "").casefold() == "completed"
    }


def named_values(variables_data, name: str) -> list:
    """Every non-null runtime value of the process variable called `name`.

    Read through GlobalDefinitions (runtime key -> declared Name) first, then
    a Globals key that equals the name up to casing (`Product` for `product`).
    """
    scope = root_scope(variables_data)
    globals_ = get_ci(scope, "Globals", {}) or {}
    definitions = get_ci(scope, "GlobalDefinitions", {}) or {}
    wanted = normalized_identifier(name)
    keys = {
        key for key, definition in definitions.items()
        if normalized_identifier(get_ci(definition, "Name", "")) == wanted
    } | {key for key in globals_ if normalized_identifier(key) == wanted}
    return [globals_[key] for key in sorted(keys) if globals_.get(key) is not None]


def assert_product(variables_data) -> None:
    values = named_values(variables_data, OUTPUT)
    if not any(type(v) is not bool and str(v).strip() in ("42", "42.0") for v in values):
        raise CheckFailure(f"process variable {OUTPUT!r} is not {EXPECTED} after the run: {values!r}")


def main() -> None:
    bpmn_path = bpmn_check.locate_bpmn(f"{NAME}.bpmn", [LIVE_RUN_DIR])
    root = ET.parse(bpmn_path).getroot()
    assert_not_hardcoded(root)

    imported = import_exact(bpmn_path, bpmn_path.parent, LIVE_RUN_DIR / f"{NAME}LiveEval")
    # No side effects, so a transient CLI failure may be retried.
    debug_data, instance_id = run_debug(
        imported, {}, LIVE_RUN_DIR / "debug.log", timeout=300, retry=DebugRetry.TRANSIENT
    )
    evidence = debug_evidence(instance_id)
    require_clean_run(debug_data, evidence)

    if "ScriptTask" not in completed_types(debug_data):
        raise CheckFailure(f"no script task completed in the run: {sorted(completed_types(debug_data))}")
    print("OK: a script task completed in the run")

    assert_product(evidence.variables)
    print(f"OK: {OUTPUT} = {EXPECTED} after the run (instance {instance_id})")


if __name__ == "__main__":
    try:
        main()
    except CheckFailure as error:
        raise SystemExit(f"FAIL: {error}") from error
