#!/usr/bin/env python3
"""DevCon expense-approval (BPMN): HITL schema, decision capture, and wiring.

Ported from Flow `e2e/devcon_expense_approval.yaml`'s
``check_devcon_expense_approval.py``: same scenario (a script mocks expense
details, an Actions.HITL user task lets a manager approve/reject with an
optional reason, a downstream script logs the outcome), translated from a
JSON node/edge walk to an XML walk over the registry-driven Actions.HITL
``uipath:activity`` shell (see
skills/uipath-maestro-bpmn/references/registry-workflow.md and
skills/uipath-maestro-bpmn/SKILL.md's Actions.HITL routing rule).

Assertion map (Flow -> BPMN):
  F   check_devcon_expense_approval.py:58-60   exactly one HITL node   -> exactly one bpmn:userTask carrying Actions.HITL
  I                 locate/parse .bpmn                                       -> parse_bpmn("ExpenseApproval")
  DROPPED           typeVersion v1.x check (line 66-68)                      -> Actions.HITL exposes no schema-version field on the BPMN uipath:activity shell; the registry template governs the schema instead, so there is nothing to assert here
  F   check_devcon_expense_approval.py:71-74   HITL schema fields non-empty  -> HITL activity has >=1 context input (uipath:input) AND >=1 output mapping (uipath:output) with var=
  F   check_devcon_expense_approval.py:71,74   fields (outputs) must be typed -> at least one HITL output mapping carries a type= attribute
  DROPPED           outcomes[] non-empty (line 75-76)                        -> BPMN Actions.HITL has no discrete outcomes list; decision capture is graded directly below via a typed output field instead
  GUESS/F check_devcon_expense_approval.py:78-82   amount field type number  -> a context input naming/presenting "amount" references a declared vars.<id> whose <uipath:variables> type is numeric (number/integer/double); BPMN context inputs carry no type= of their own, so the type lives on the variable behind the vars.<id> reference (T: any numeric type spelling)
  F   check_devcon_expense_approval.py:84-96   decision boolean OR approve/reject outcome -> an HITL output field named approve/approved/decision, typed boolean OR string (T: BPMN has no outcomes list, so the "outcome-based" alternative becomes a string-typed decision output instead of named outcomes)
  F   check_devcon_expense_approval.py:98-105  text output field for the rejection reason -> an HITL output field typed text/string named reason/comment/explanation/justification/note
  F/T check_devcon_expense_approval.py:107-118 input bound to upstream script output (vars.<node>.output.<field> or =js:$vars...) -> T: a context input references a declared variable via vars.<id> (no .output. segment -- BPMN variables are flat, not node-scoped like Flow's $vars.<node>.output.<field>)
  DROPPED           outcome-<id> port-per-outcome wiring mechanics (lines 120-138) -> BPMN bpmn:userTask has a single completion path, not a per-outcome handle; both of Flow's outcome ports wired to the SAME downstream node anyway, so the faithful reduction is "the HITL task has an outgoing sequence flow" (kept below)
  F   check_devcon_expense_approval.py:127-138 HITL completion must be wired  -> the HITL userTask has >=1 outgoing bpmn:sequenceFlow
  F   check_devcon_expense_approval.py:140-147 downstream script reads HITL output via $vars.<hitl_id>.output -> T: some bpmn:scriptTask in the process references vars.<HITL output var id> (no .output. segment), in its <bpmn:script> source or its uipath:mapping input/output value

Checks performed:
  1. BPMN file exists and is well-formed XML.
  2. A bpmn:userTask carries the Actions.HITL uipath:activity shell.
  3. That task has a context input presenting data and a typed output mapping.
  4. A context input presents the amount, bound to a declared number-typed variable.
  5. An output field captures the manager's decision (boolean or string, name
     suggesting approve/approved/decision).
  6. An output field captures the optional rejection reason (text/string,
     name suggesting reason/comment/...).
  7. At least one context input is bound to a declared variable via vars.<id>
     (not a hardcoded literal).
  8. The HITL task has an outgoing sequence flow (completion is wired).
  9. Some scriptTask in the process reads one of the HITL's output variables
     via vars.<id>.
"""

from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _shared.bpmn_check import (  # noqa: E402
    NS,
    attr,
    elements,
    fail,
    has_uipath_extension,
    parse_bpmn,
    text_content,
)

AMOUNT_RE = re.compile(r"amount", re.IGNORECASE)
DECISION_NAME_RE = re.compile(r"approv|decision", re.IGNORECASE)
REASON_RE = re.compile(r"reason|comment|explanation|justification|note", re.IGNORECASE)
VAR_REF_RE = re.compile(r"vars\.([A-Za-z0-9_]+)")
NUMERIC_TYPES = {"number", "integer", "double", "int", "float"}
TEXT_TYPES = {"string", "text", "textarea"}
BOOLEAN_TYPES = {"boolean", "bool"}


def declared_var_types(root) -> dict[str, str]:
    types: dict[str, str] = {}
    for var in root.findall(".//uipath:variables/*", NS):
        ident = var.attrib.get("id") or var.attrib.get("name")
        if ident:
            types[ident] = (var.attrib.get("type") or "").lower()
    return types


def blob(el) -> str:
    """Every string an element might carry a value/reference in: attributes
    the skill uses for HITL/script wiring (name, value, source, var), plus
    text/CDATA content."""
    parts = [
        el.attrib.get("name") or "",
        el.attrib.get("value") or "",
        el.attrib.get("source") or "",
        el.attrib.get("var") or "",
        text_content(el),
    ]
    return " ".join(parts)


def var_ref(text: str) -> str | None:
    match = VAR_REF_RE.search(text)
    return match.group(1) if match else None


def main() -> None:
    path, root = parse_bpmn("ExpenseApproval")

    hitl_tasks = [t for t in elements(root, "userTask") if has_uipath_extension(t, "Actions.HITL")]
    if len(hitl_tasks) != 1:
        fail(
            "expected exactly one bpmn:userTask carrying an Actions.HITL uipath:activity shell, "
            f"found {len(hitl_tasks)}"
        )
    hitl = hitl_tasks[0]
    hitl_id = attr(hitl, "id")

    context_inputs = hitl.findall(
        "bpmn:extensionElements/uipath:activity/uipath:context/uipath:input", NS
    ) + hitl.findall("bpmn:extensionElements/uipath:activity/uipath:input", NS)
    if not context_inputs:
        fail("HITL activity has no input mapping presenting context to the reviewer")

    outputs = [
        o
        for o in hitl.findall("bpmn:extensionElements/uipath:activity/uipath:output", NS)
        if o.attrib.get("var")
    ]
    if not outputs:
        fail("HITL activity has no output mapping (var=) capturing the reviewer's returned fields")
    if not any(o.attrib.get("type") for o in outputs):
        fail("HITL output mappings are untyped (no type= on any captured field)")

    declared = declared_var_types(root)

    # -- amount field must present a number-typed value --------------------
    amount_inputs = [inp for inp in context_inputs if AMOUNT_RE.search(blob(inp))]
    if not amount_inputs:
        fail("HITL has no context input presenting the expense amount to the reviewer")
    amount_ok = False
    for inp in amount_inputs:
        ref = var_ref(blob(inp))
        if ref and declared.get(ref) in NUMERIC_TYPES:
            amount_ok = True
            break
    if not amount_ok:
        fail(
            "amount context input must reference a number-typed declared "
            "variable via vars.<id> (found types: "
            f"{[declared.get(var_ref(blob(i))) for i in amount_inputs]})"
        )

    # -- decision capture: boolean OR string output naming the decision ----
    decision_outputs = [o for o in outputs if DECISION_NAME_RE.search(blob(o))]
    if not decision_outputs:
        fail(
            "HITL has no output field capturing the manager's decision "
            "(name/var containing approve/approved/decision)"
        )
    if not any((o.attrib.get("type") or "").lower() in (BOOLEAN_TYPES | TEXT_TYPES) for o in decision_outputs):
        fail("decision output field must be typed boolean or string/text")

    # -- rejection reason: text output field --------------------------------
    reason_outputs = [
        o
        for o in outputs
        if (o.attrib.get("type") or "").lower() in TEXT_TYPES and REASON_RE.search(blob(o))
    ]
    if not reason_outputs:
        fail("HITL has no text output field for the rejection reason (e.g. reason, comment)")

    # -- at least one context input bound to a declared variable -----------
    def bound_to_declared(inp) -> bool:
        ref = var_ref(blob(inp))
        return ref is not None and ref in declared

    if not any(bound_to_declared(inp) for inp in context_inputs):
        fail(
            "HITL context inputs must be bound to a declared process variable "
            "via vars.<id> (upstream script output), not a hardcoded literal"
        )

    # -- HITL completion must be wired to something downstream -------------
    flows = elements(root, "sequenceFlow")
    outgoing = [f for f in flows if attr(f, "sourceRef") == hitl_id]
    if not outgoing:
        fail(f"HITL task {hitl_id} has no outgoing sequence flow (completion not wired)")

    # -- downstream script reads the HITL's output variable(s) -------------
    hitl_out_vars = {o.attrib.get("var") for o in outputs if o.attrib.get("var")}

    def script_reads(task, var_id: str) -> bool:
        needle = f"vars.{var_id}"
        script = task.find("bpmn:script", NS)
        if script is not None and needle in text_content(script):
            return True
        for el in task.findall(".//uipath:input", NS) + task.findall(".//uipath:output", NS):
            if needle in blob(el):
                return True
        return False

    scripts = elements(root, "scriptTask")
    if not scripts:
        fail("no bpmn:scriptTask found to log the HITL outcome downstream")
    consumed = any(any(script_reads(s, v) for v in hitl_out_vars) for s in scripts)
    if not consumed:
        fail(
            "no scriptTask reads the HITL output via vars.<id> for any of "
            f"{sorted(hitl_out_vars)}"
        )

    print(
        f"OK: {path} HITL {hitl_id} presents typed context, captures decision + "
        "reason as declared variables, is wired downstream, and its output is "
        "read by a logging scriptTask"
    )


if __name__ == "__main__":
    main()
