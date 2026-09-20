#!/usr/bin/env python3
"""Check source semantics for the simulated HITL tasks (BPMN).

Ported from Flow `_shared/check_simulated_hitl.py`. Flow's schema-carrying
"HITL quickform" node with `inputs.schema.{fields,outcomes}` has no BPMN
equivalent: an Actions.HITL `bpmn:userTask` presents context via
`uipath:context/uipath:input` elements and captures reviewer-entered data via
`uipath:output` elements (`var=`, `type=`) bound to declared process
variables (see `skills/uipath-maestro-bpmn/references/registry-workflow.md`
and the CI-proven `_shared/check_devcon_expense_approval.py`,
`_shared/check_quality_schema_design.py`,
`_shared/check_smoke_completed_wired.py`). Every mode below re-homes the same
Flow assertion onto that shape; nothing is added beyond what Flow asserted.

Two valid BPMN shapes, both accepted (T tolerance)
---------------------------------------------------
CI run 35500726138 (`e2e/devcon_expense_approval`, same Actions.HITL
construct) showed the eval agent legitimately following the registry
template instead of hand-authoring per-field outputs. The
`Actions.HITL` `xmlTemplate` (`validator/bpmn-spec.json`,
`extensionTypes["Actions.HITL"]`) has a FIXED context (`appId`, `appVersion`,
`actions`, `key`, `taskTitle`), exactly ONE
`<uipath:input name="HitlTaskArguments" type="json" target="bodyField">` body
holding every field's value/expression, and exactly ONE
`<uipath:output name="Process response" type="Actions.HITL" var="...">`
(opaque -- the registry explicitly forbids coercing this to a concrete type).
Individual field *types* live on the variable(s) referenced from that body
(flat `type=` or nested `properties.<field>.type` in a `jsonSchema`
variable's CDATA), and the decision/reason are read downstream as
`vars.<responseVar>.<field>` -- often through a local script alias
(`var d = vars.X; ...d.field`) rather than one literal dotted token -- or
declared in a *different* downstream variable's JSON Schema (e.g. a logging
step's output shape). Real artifact:
`ci-35500726138/.../ExpenseApproval.bpmn`.

  Form 1 (per-field, hand-authored) -- context input per field, typed
  `uipath:output` per field.
  Form 2 (template, registry-driven) -- fixed context, one JSON body input,
  one opaque response output; field identity/typing resolved indirectly.

Every mode below tries Form 1 first, then Form 2, and passes if either
succeeds -- never requiring both.

Assertion map (Flow -> BPMN), citing check_simulated_hitl.py (Flow) lines:

  quick-form
    F check_simulated_hitl.py:38-53   inline HITL quick-form node exists      -> >=1 bpmn:userTask carrying Actions.HITL (BPMN's Actions.HITL IS the inline
                                                                                  form; there is no separate "quick" vs "form" node type to distinguish,
                                                                                  and this holds for both Form 1 and Form 2)

  schema
    F check_simulated_hitl.py:67-69   an input-direction (read-only) field    -> >=1 uipath:context/uipath:input presenting data to the reviewer (Form 1's
                                                                                  own field inputs, or Form 2's fixed context -- both are >=1 input)
    F check_simulated_hitl.py:70-71   an output/inOut (fill-in) field         -> >=1 uipath:output (var=) capturing reviewer-entered data (Form 1's typed
                                                                                  per-field outputs, or Form 2's single opaque response output)
    T check_simulated_hitl.py:72-74   "approve"+"reject" present in the       -> "approve"+"reject" present in the serialized uipath:activity subtree
                                       dumped schema JSON                        (context inputs + outputs + taskTitle + Form 2's HitlTaskArguments body),
                                                                                  OR in a conditionExpression/script that references the response
                                                                                  variable (T: BPMN has no discrete outcomes list, so the same
                                                                                  substring-presence check runs over the whole activity payload, widened
                                                                                  to the response variable's downstream consumers for Form 2 where the
                                                                                  node itself may only carry an indirection key like "decisionField")

  priority
    F check_simulated_hitl.py:78-83   "high" present anywhere in the dumped   -> "high" present anywhere in the serialized HITL userTask element (I:
                                       JSON of the whole HITL node               ET.tostring of the element replaces json.dumps of the node dict; this
                                                                                  already covers Form 2's body JSON since it's a descendant of the
                                                                                  userTask -- unchanged by the two-form tolerance)

  outcome-wiring
    F check_simulated_hitl.py:116-117 zero-outcome path: "completed" handle   -> HITL userTask has >=1 outgoing bpmn:sequenceFlow (T/DROPPED: BPMN
                                       must be wired                             Actions.HITL has one completion path, not per-outcome ports, so
    DROPPED check_simulated_hitl.py:98-115 per-outcome outcome-<id> handle       "every outcome gets its own wired port" collapses to "the task's single
                                       wiring, outcome-completed placeholder      completion path is wired" -- the same reduction
                                       rule                                       check_devcon_expense_approval.py and check_smoke_completed_wired.py
                                                                                  already use for this exact construct; form-agnostic, unchanged.

  expense
    I check_simulated_hitl.py:136-139 locate/parse the artifact, edges exist  -> parse_bpmn(), sequenceFlow elements always present in a well-formed .bpmn
    F check_simulated_hitl.py:141-142 exactly 1 HITL node                     -> exactly 1 bpmn:userTask carrying Actions.HITL
    F check_simulated_hitl.py:148-149 HITL needs fields                      -> HITL activity has >=1 context input
    F check_simulated_hitl.py:150-155 amount must be a number field          -> Form 1: a context input naming/presenting "amount" references a flat
                                                                                  numeric declared vars.<id>. T/Form 2: a HitlTaskArguments-style body-JSON
                                                                                  key naming/presenting "amount" holds an `=vars.<id>.<field>` expression
                                                                                  whose <field> resolves to "number" in that variable's own JSON Schema
                                                                                  (BPMN context inputs carry no type= of their own, so the type lives on
                                                                                  the variable -- possibly nested -- behind the vars.<id> reference)
    F check_simulated_hitl.py:156-174 decision: boolean field OR             -> Form 1: a typed HITL output field named approve/approved/decision,
                                       approve/reject outcomes                    boolean OR string typed. T/Form 2: a body-JSON key named
                                                                                  approve*/decision* (or its literal string VALUE, an indirection naming
                                                                                  the response field, e.g. "decisionField":"approved") is actually
                                                                                  dereferenced downstream off the response var (vars.<respVar>, tolerating
                                                                                  a local script alias) and, wherever any declared JSON-Schema variable
                                                                                  documents that field name, it is boolean or string typed (BPMN has no
                                                                                  outcomes list, so "named outcomes" becomes a string/boolean-typed
                                                                                  decision field read off the opaque response instead)
    F check_simulated_hitl.py:175-185 text output field for rejection reason -> same Form 1/Form 2 split as decision, with REASON_RE and text typing
    F check_simulated_hitl.py:186     outcome wiring (see outcome-wiring)    -> HITL userTask has >=1 outgoing sequence flow
    F check_simulated_hitl.py:187-194 downstream core.action.script reads    -> T: some bpmn:scriptTask references vars.<HITL output var id> (no
                                       $vars.<hitl_id>.output                     .output segment -- BPMN variables are flat, not node-scoped) in its
                                                                                  <bpmn:script> source or a nested uipath:input/output value; unaffected
                                                                                  by the two-form tolerance since it only needs the base var id, and a
                                                                                  local script alias still contains that literal substring once
                                                                                  (`var d = vars.X;`)

Checks performed, per mode, against the discovered .bpmn (no name hint --
the simulated dialog never pins a specific file to check, mirroring Flow's
`find_flow_file()` with no name argument):
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

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
VAR_REF_RE = re.compile(r"vars\.([A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)*)")
NUMERIC_TYPES = {"number", "integer", "double", "int", "float"}
TEXT_TYPES = {"string", "text", "textarea"}
BOOLEAN_TYPES = {"boolean", "bool"}


def hitl_tasks(root: ET.Element) -> list[ET.Element]:
    return [t for t in elements(root, "userTask") if has_uipath_extension(t, "Actions.HITL")]


def activity_element(task: ET.Element) -> ET.Element | None:
    ext = task.find("bpmn:extensionElements", NS)
    if ext is None:
        return None
    return ext.find("uipath:activity", NS)


def context_inputs(task: ET.Element) -> list[ET.Element]:
    """Form 1's per-field context inputs AND Form 2's fixed context inputs,
    plus any direct child input of uipath:activity (Form 2's single
    HitlTaskArguments body lands here too -- callers that care about the
    difference filter on a leading '{' in the text, see amount_ok below)."""
    return task.findall(
        "bpmn:extensionElements/uipath:activity/uipath:context/uipath:input", NS
    ) + task.findall("bpmn:extensionElements/uipath:activity/uipath:input", NS)


def activity_outputs(task: ET.Element) -> list[ET.Element]:
    return task.findall("bpmn:extensionElements/uipath:activity/uipath:output", NS)


def declared_var_types(root: ET.Element) -> dict[str, str]:
    types: dict[str, str] = {}
    for var in root.findall(".//uipath:variables/*", NS):
        ident = var.attrib.get("id") or var.attrib.get("name")
        if ident:
            types[ident] = (var.attrib.get("type") or "").lower()
    return types


def declared_variable_element(root: ET.Element, ident: str) -> ET.Element | None:
    for var in root.findall(".//uipath:variables/*", NS):
        if (var.attrib.get("id") or var.attrib.get("name")) == ident:
            return var
    return None


def parse_schema_properties(var_el: ET.Element) -> dict[str, str]:
    """properties.<name>.type from a jsonSchema-typed variable's CDATA,
    lowercased. Empty on any non-schema type or parse failure."""
    type_ = (var_el.attrib.get("type") or "").lower().replace("-", "").replace("_", "")
    if "jsonschema" not in type_:
        return {}
    text = (var_el.text or "").strip()
    if not text:
        return {}
    try:
        schema = json.loads(text)
    except (ValueError, TypeError):
        return {}
    props = schema.get("properties") if isinstance(schema, dict) else None
    if not isinstance(props, dict):
        return {}
    return {
        str(name).lower(): spec["type"].lower()
        for name, spec in props.items()
        if isinstance(spec, dict) and isinstance(spec.get("type"), str)
    }


def declared_schema_properties(root: ET.Element) -> dict[str, str]:
    """property-name -> type, merged across every declared jsonSchema
    variable in the document (T: Form 2's field type may be declared on a
    DIFFERENT variable than the one directly referenced -- e.g. a downstream
    logging step's output shape -- rather than on the referenced variable
    itself)."""
    merged: dict[str, str] = {}
    for var_el in root.findall(".//uipath:variables/*", NS):
        for name, type_ in parse_schema_properties(var_el).items():
            merged.setdefault(name, type_)
    return merged


def resolve_ref_type(
    root: ET.Element, ref: str | None, flat_types: dict[str, str], schema_props: dict[str, str]
) -> str:
    """ref is 'Var_X' (Form 1: flat-typed variable) or 'Var_X.field...'
    (Form 2: a property nested in Var_X's own JSON Schema, or -- failing that
    -- any declared JSON-Schema variable's matching property name)."""
    if not ref:
        return ""
    base, _, rest = ref.partition(".")
    if not rest:
        return flat_types.get(base, "")
    field = rest.split(".")[0].lower()
    base_el = declared_variable_element(root, base)
    if base_el is not None:
        local = parse_schema_properties(base_el)
        if field in local:
            return local[field]
    return schema_props.get(field, "")


def blob(el: ET.Element) -> str:
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


def find_body_json(task: ET.Element) -> dict | None:
    """Form 2's single HitlTaskArguments-style body: a direct uipath:input
    child of uipath:activity, target=bodyField or type=json, whose CDATA
    parses as a JSON object."""
    activity = activity_element(task)
    if activity is None:
        return None
    for inp in activity.findall("uipath:input", NS):
        target = inp.attrib.get("target", "")
        type_ = (inp.attrib.get("type") or "").lower()
        if target != "bodyField" and type_ != "json":
            continue
        text = (inp.text or "").strip()
        if not text:
            continue
        try:
            data = json.loads(text)
        except (ValueError, TypeError):
            continue
        if isinstance(data, dict):
            return data
    return None


def downstream_field_reference(root: ET.Element, var_name: str, field_name: str) -> bool:
    """True if some scriptTask or sequenceFlow (conditionExpression)
    references vars.<var_name> AND accesses a `.field_name` member somewhere
    in that same element's serialized text/attributes. Tolerates a local JS
    alias (`var d = vars.X; ...d.field`) instead of requiring the literal
    dotted `vars.X.field` in one token, which is how real generated code
    reads an opaque Actions.HITL response (see module docstring)."""
    needle_var = f"vars.{var_name}"
    field_re = re.compile(rf"\.{re.escape(field_name)}\b", re.IGNORECASE)
    for el in elements(root, "scriptTask") + elements(root, "sequenceFlow"):
        text = ET.tostring(el, encoding="unicode")
        if needle_var in text and field_re.search(text):
            return True
    return False


def require_hitl(root: ET.Element) -> list[ET.Element]:
    tasks = hitl_tasks(root)
    if not tasks:
        fail("need a bpmn:userTask carrying an Actions.HITL uipath:activity shell")
    return tasks


def check_quick_form(root: ET.Element) -> None:
    require_hitl(root)
    print("OK: BPMN contains an inline Actions.HITL user task")


def approve_reject_present(root: ET.Element, task: ET.Element, outputs: list[ET.Element]) -> bool:
    activity = activity_element(task)
    scope = activity if activity is not None else task
    rendered = ET.tostring(scope, encoding="unicode").lower()
    if "approve" in rendered and "reject" in rendered:
        return True
    # Form 2 fallback: the node itself may only carry an indirection key
    # (e.g. "decisionField":"approved"); look at what consumes the response
    # variable downstream instead.
    resp_vars = {o.attrib.get("var") for o in outputs if o.attrib.get("var")}
    if not resp_vars:
        return False
    relevant: list[str] = []
    for cond in root.findall(".//bpmn:conditionExpression", NS):
        text = cond.text or ""
        if any(f"vars.{v}" in text for v in resp_vars):
            relevant.append(text)
    for script in root.findall(".//bpmn:script", NS):
        text = text_content(script)
        if any(f"vars.{v}" in text for v in resp_vars):
            relevant.append(text)
    combined = " ".join(relevant).lower()
    return "approve" in combined and "reject" in combined


def check_schema(root: ET.Element) -> None:
    tasks = require_hitl(root)
    task = tasks[0]
    inputs = context_inputs(task)
    if not inputs:
        fail("need an input mapping presenting read-only context to the reviewer")
    outputs = [o for o in activity_outputs(task) if o.attrib.get("var")]
    if not outputs:
        fail("need an output mapping (var=) capturing the reviewer's fill-in data")
    if not approve_reject_present(root, task, outputs):
        fail(
            "need Approve and Reject represented in the HITL activity (title, action, or "
            "output naming/value) or in a downstream condition/script keyed off the response "
            "variable"
        )
    print("OK: HITL activity has input/output mappings and Approve/Reject represented")


def check_priority(root: ET.Element) -> None:
    tasks = require_hitl(root)
    if "high" not in ET.tostring(tasks[0], encoding="unicode").lower():
        fail("priority should be High")
    print("OK: HITL priority is High")


def check_outcome_wiring(root: ET.Element) -> None:
    tasks = require_hitl(root)
    flows = elements(root, "sequenceFlow")
    for task in tasks:
        tid = attr(task, "id")
        outgoing = [f for f in flows if attr(f, "sourceRef") == tid]
        if not outgoing:
            fail(f"HITL task {tid} has no outgoing sequence flow (completion not wired)")
    ids = ", ".join(attr(t, "id") for t in tasks)
    print(f"OK: every HITL task's completion is wired to a downstream step ({ids})")


def amount_ok(
    root: ET.Element, task: ET.Element, flat_types: dict[str, str], schema_props: dict[str, str]
) -> bool:
    # Form 1: a plain context input naming/presenting "amount", bound to a
    # numeric variable (flat, or nested through the referenced var's own
    # JSON Schema).
    for inp in context_inputs(task):
        text = (inp.text or "").strip()
        if text.startswith("{"):
            continue  # Form 2's JSON body -- handled below, scoped per-key
        if AMOUNT_RE.search(blob(inp)):
            ref = var_ref(blob(inp))
            if ref and resolve_ref_type(root, ref, flat_types, schema_props) in NUMERIC_TYPES:
                return True
    # Form 2: a HitlTaskArguments-style body-JSON key naming/presenting
    # "amount" whose value is an expression referencing a numeric field.
    body = find_body_json(task) or {}
    for key, value in body.items():
        if AMOUNT_RE.search(key) and isinstance(value, str):
            ref = var_ref(value)
            if ref and resolve_ref_type(root, ref, flat_types, schema_props) in NUMERIC_TYPES:
                return True
    return False


def _field_ok(
    root: ET.Element,
    task: ET.Element,
    outputs: list[ET.Element],
    name_re: re.Pattern,
    accepted_types: set[str],
) -> bool:
    """Shared Form 1 / Form 2 logic for the decision and reason fields."""
    # Form 1: an explicit typed HITL output field.
    matches = [o for o in outputs if name_re.search(blob(o))]
    if matches and any((o.attrib.get("type") or "").lower() in accepted_types for o in matches):
        return True

    # Form 2: a body-JSON key names (directly, or via a literal string value
    # that is an indirection naming the response field) the field on the
    # single opaque response output; the field must actually be dereferenced
    # downstream off that response variable, and if any declared JSON-Schema
    # variable documents the field's type, it must be an accepted type.
    resp_vars = {o.attrib.get("var") for o in outputs if o.attrib.get("var")}
    if not resp_vars:
        return False
    body = find_body_json(task) or {}
    candidate_fields: set[str] = set()
    for key, value in body.items():
        if name_re.search(key):
            candidate_fields.add(key)
            if isinstance(value, str) and value and not value.startswith("="):
                candidate_fields.add(value)
    if not candidate_fields:
        return False
    schema_props = declared_schema_properties(root)
    for var in resp_vars:
        for field in candidate_fields:
            if downstream_field_reference(root, var, field):
                field_type = schema_props.get(field.lower(), "")
                if field_type == "" or field_type in accepted_types:
                    return True
    return False


def decision_ok(root: ET.Element, task: ET.Element, outputs: list[ET.Element]) -> bool:
    return _field_ok(root, task, outputs, DECISION_NAME_RE, BOOLEAN_TYPES | TEXT_TYPES)


def reason_ok(root: ET.Element, task: ET.Element, outputs: list[ET.Element]) -> bool:
    return _field_ok(root, task, outputs, REASON_RE, TEXT_TYPES)


def check_expense(root: ET.Element) -> None:
    tasks = hitl_tasks(root)
    if len(tasks) != 1:
        fail(f"need exactly 1 HITL user task carrying Actions.HITL, found {len(tasks)}")
    hitl = tasks[0]
    hitl_id = attr(hitl, "id")

    inputs = context_inputs(hitl)
    if not inputs:
        fail("HITL activity has no input mapping presenting context to the reviewer")

    outputs = [o for o in activity_outputs(hitl) if o.attrib.get("var")]
    if not outputs:
        fail("HITL activity has no output mapping (var=) capturing the reviewer's returned fields")

    flat_types = declared_var_types(root)
    schema_props = declared_schema_properties(root)

    # -- amount field must present a number-typed value ---------------------
    if not amount_ok(root, hitl, flat_types, schema_props):
        fail(
            "HITL has no context input (or body field) presenting the expense amount bound to "
            "a number-typed declared variable"
        )

    # -- decision capture: boolean OR string output naming the decision -----
    if not decision_ok(root, hitl, outputs):
        fail("need a boolean decision field or approve/reject outcomes")

    # -- rejection reason: text output field ---------------------------------
    if not reason_ok(root, hitl, outputs):
        fail("need a text reason output field")

    # -- outcome wiring: HITL completion must be wired -----------------------
    flows = elements(root, "sequenceFlow")
    if not [f for f in flows if attr(f, "sourceRef") == hitl_id]:
        fail(f"HITL task {hitl_id} has no outgoing sequence flow (completion not wired)")

    # -- downstream script reads the HITL's output variable(s) --------------
    hitl_out_vars = {o.attrib.get("var") for o in outputs if o.attrib.get("var")}

    def script_reads(task: ET.Element, var_id: str) -> bool:
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
        fail("downstream script must read HITL output via vars.<id> (no scriptTask found)")
    if not any(any(script_reads(s, v) for v in hitl_out_vars) for s in scripts):
        fail(f"downstream script must read HITL output via vars.<id> for one of {sorted(hitl_out_vars)}")

    print("OK: expense HITL schema, routing, and downstream output access are correct")


CHECKS = {
    "expense": check_expense,
    "outcome-wiring": check_outcome_wiring,
    "priority": check_priority,
    "quick-form": check_quick_form,
    "schema": check_schema,
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("check", choices=sorted(CHECKS))
    args = parser.parse_args()
    _path, root = parse_bpmn()
    CHECKS[args.check](root)


if __name__ == "__main__":
    main()
