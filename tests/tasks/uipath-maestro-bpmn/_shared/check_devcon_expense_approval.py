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

Assertion map (Flow -> BPMN). One row per Flow assertion: the head line names the
Flow-side assertion, the `->` line its BPMN re-homing, and any further indented line
continues the row above.

  F    check_devcon_expense_approval.py:58-60 - exactly one HITL node
      -> exactly one bpmn:userTask carrying Actions.HITL
  I    locate/parse .bpmn
      -> parse_bpmn("ExpenseApproval")
  DROPPED  typeVersion v1.x check (line 66-68)
      -> Actions.HITL exposes no schema-version field on the BPMN uipath:activity shell; the
         registry template governs the schema instead, so there is nothing to assert here
  F    check_devcon_expense_approval.py:71-74 - HITL schema fields non-empty
      -> HITL activity has >=1 output mapping (uipath:output) with var=, AND (context input(s) OR a
         single merged-body HitlTaskArguments input)
  F    check_devcon_expense_approval.py:71,74 - fields (outputs) must be typed
      -> at least one HITL output mapping carries a type= attribute
  DROPPED  outcomes[] non-empty (line 75-76)
      -> BPMN Actions.HITL has no discrete outcomes list; decision capture is graded directly below
         via a typed output field / decisionField instead
  F(T) check_devcon_expense_approval.py:78-82 - amount field type number
      -> T: TWO accepted forms, per CI run 35500726138's real registry-template artifact vs. the
         older per-field hypothesis:
         (T1, per-field form) a context input naming/presenting "amount" references a declared
            vars.<id> whose <uipath:variables> type is numeric
         (T2, real Actions.HITL registry-template form --
            skills/uipath-maestro-bpmn/validator/bpmn-spec.json extensionTypes["Actions.HITL"]) the
            single <uipath:input name="HitlTaskArguments" type="json" target="bodyField"> JSON body
            has a key naming "amount" whose value is an `=vars.<V>.<field>` (or bare `=vars.<V>`)
            expression, resolved against either a numeric-typed declared variable V, or V's declared
            jsonSchema CDATA `properties.<field>.type == number|integer` (Var_Expense in the CI
            artifact)
  F(T) check_devcon_expense_approval.py:84-96 - decision boolean OR approve/reject outcome
      -> T1: an HITL output field named approve/approved/decision, typed boolean OR string
         T2 (recursive, CI runs 35500726138 + 35501830119): any HitlTaskArguments key at ANY depth
            matching approve/approved/decision whose value is a boolean literal, an `=`-expression
            resolving to a boolean-typed variable/schema property, or a bare string naming a field
            some downstream script actually dereferences (the original decisionField rule,
            generalized -- a stringly-typed literal like `"approved":"yes"` still fails, since "yes"
            is never dereferenced downstream)
         fallback: a declared jsonSchema variable (e.g. Var_LogResponse) names a matching
            boolean/string property
  F(T) check_devcon_expense_approval.py:98-105 - text output field for the rejection reason
      -> T1: an HITL output field typed text/string named reason/comment/...
         T2 (recursive): any HitlTaskArguments key at any depth matching
            reason/comment/explanation/justification/note whose value is any plain string (a literal
            default, empty allowed, or a field-name pointer -- both accepted unconditionally, unlike
            decision) or an `=`-expression resolving to string/text
         fallback: a declared jsonSchema variable names a matching text property
  F/T  check_devcon_expense_approval.py:107-118 - input bound to upstream script output
       (vars.<node>.output.<field> or =js:$vars...)
      -> T: T1 checks a context input, T2 checks any HitlTaskArguments body value at any depth;
         either references a declared variable via vars.<id> (no .output. segment -- BPMN variables
         are flat, not node-scoped like Flow's $vars.<node>.output.<field>)
  DROPPED  outcome-<id> port-per-outcome wiring mechanics (lines 120-138)
      -> BPMN bpmn:userTask has a single completion path, not a per-outcome handle; both of Flow's
         outcome ports wired to the SAME downstream node anyway, so the faithful reduction is "the
         HITL task has an outgoing sequence flow" (kept below)
  F    check_devcon_expense_approval.py:127-138 - HITL completion must be wired
      -> the HITL userTask has >=1 outgoing bpmn:sequenceFlow
  F    check_devcon_expense_approval.py:140-147 - downstream script reads HITL output via
       $vars.<hitl_id>.output
      -> T: some bpmn:scriptTask in the process references vars.<HITL output var id> (no .output.
         segment), in its <bpmn:script> source or its uipath:mapping input/output value -- this
         substring match already covers the real form's `vars.Var_ManagerDecision.approved` shape

Real registry-template shape confirmed against two CI artifacts:
run 35500726138 (ExpenseApprovalSolution/ExpenseApproval/ExpenseApproval.bpmn,
flat HitlTaskArguments keys, decisionField/rejectionReasonField pointers) and
run 35501830119 (ExpenseApproval/ExpenseApproval/ExpenseApproval.bpmn -- grade
that copy, not the stray ExpenseApprovalSolution/ scaffold alongside it in
that artifact -- form fields nested one level down under `fields`, decision
and reason expressed as boolean/string literal defaults instead of pointer
keys). Both match skills/uipath-maestro-bpmn/validator/bpmn-spec.json's
Actions.HITL extensionType: `contextFields` are fixed app-identity metadata
(appId, appVersion, actions, key, taskTitle) -- NOT the reviewer-facing form
fields. Form fields live at any depth inside the ONE `HitlTaskArguments` JSON
body, and the single `<uipath:output type="Actions.HITL" var="...">` is
opaquely typed; downstream code reads its fields as `vars.<var>.<field>`.
Platform note (recorded, not graded here): `uip maestro bpmn validate` can
only pass this shape with a real Action App binding -- see the task
description.

Checks performed:
  1. BPMN file exists and is well-formed XML.
  2. Exactly one bpmn:userTask carries the Actions.HITL uipath:activity shell.
  3. That task has some input mapping (context inputs or a merged-body
     HitlTaskArguments input) and a typed output mapping.
  4. The amount is presented, resolving to a declared number-typed variable
     either directly or through a jsonSchema property.
  5. The manager's decision is captured (boolean literal, boolean-typed
     expression, or a genuinely-dereferenced field-name pointer, at any depth
     in HitlTaskArguments; OR a matching jsonSchema property).
  6. The optional rejection reason is captured (any string value at any depth
     in HitlTaskArguments, or a string-typed expression; OR a matching
     jsonSchema property).
  7. At least one input value (context input or HitlTaskArguments body field,
     at any depth) is bound to a declared variable via vars.<id> (not a
     hardcoded literal).
  8. The HITL task has an outgoing sequence flow (completion is wired).
  9. Some scriptTask in the process reads one of the HITL's output variables
     via vars.<id>.
"""

from __future__ import annotations

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _shared.bpmn_check import (  # noqa: E402
    declared_variable_elements,
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
_VARS_EXPR = re.compile(r"^vars\.([A-Za-z0-9_]+)(?:\.([A-Za-z0-9_]+))?$")
NUMERIC_TYPES = {"number", "integer", "double", "int", "float"}
TEXT_TYPES = {"string", "text", "textarea"}
BOOLEAN_TYPES = {"boolean", "bool"}


def declared_var_types(root) -> dict[str, str]:
    types: dict[str, str] = {}
    for var in declared_variable_elements(root):
        ident = var.attrib.get("id") or var.attrib.get("name")
        if ident:
            types[ident] = (var.attrib.get("type") or "").lower()
    return types


def declared_var_schemas(root) -> dict[str, dict]:
    """id -> parsed JSON schema, for every declared variable whose type is
    jsonSchema and whose CDATA parses as JSON (e.g. Var_Expense in the real
    Actions.HITL registry-template artifact)."""
    schemas: dict[str, dict] = {}
    for var in declared_variable_elements(root):
        ident = var.attrib.get("id")
        if not ident or (var.attrib.get("type") or "").lower() != "jsonschema":
            continue
        text = text_content(var).strip()
        if not text:
            continue
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            schemas[ident] = parsed
    return schemas


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


def _vars_match(expr) -> re.Match | None:
    if not isinstance(expr, str):
        return None
    text = expr.strip()
    if text.startswith("="):
        text = text[1:]
    return _VARS_EXPR.match(text)


def expr_var_ref(expr) -> str | None:
    """The base variable id an `=vars.<id>` or `=vars.<id>.<field>` value
    expression references, or None."""
    match = _vars_match(expr)
    return match.group(1) if match else None


def resolve_expr_type(expr, declared_types: dict[str, str], declared_schemas: dict[str, dict]) -> str | None:
    """The declared type behind a value expression: directly from
    <uipath:variables> for a bare `=vars.<id>`, or from a jsonSchema
    variable's `properties.<field>.type` for `=vars.<id>.<field>`."""
    match = _vars_match(expr)
    if not match:
        return None
    var_id, field = match.groups()
    if field is None:
        return declared_types.get(var_id)
    schema = declared_schemas.get(var_id) or {}
    prop = (schema.get("properties") or {}).get(field)
    if not isinstance(prop, dict):
        return None
    return (prop.get("type") or "").lower() or None


def hitl_body_input(hitl):
    """The single merged-body <uipath:input> the real Actions.HITL registry
    template emits (name="HitlTaskArguments", target="bodyField"), or None
    when the task uses the older per-field context/output form instead."""
    for inp in hitl.findall("bpmn:extensionElements/uipath:activity/uipath:input", NS):
        if inp.attrib.get("name") == "HitlTaskArguments" or inp.attrib.get("target") == "bodyField":
            return inp
    return None


def parse_body_json(inp) -> dict:
    text = text_content(inp).strip()
    if not text:
        fail("HitlTaskArguments body input is empty")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        fail(f"HitlTaskArguments body is not valid JSON: {exc}")
    if not isinstance(data, dict):
        fail("HitlTaskArguments body must be a JSON object")
    return data


def schema_property_matches(declared_schemas: dict[str, dict], name_re: re.Pattern, type_set: set[str]) -> bool:
    for schema in declared_schemas.values():
        for pname, pinfo in (schema.get("properties") or {}).items():
            if not isinstance(pinfo, dict):
                continue
            if name_re.search(pname) and (pinfo.get("type") or "").lower() in type_set:
                return True
    return False


def iter_keys_at_any_depth(obj):
    """Yield every (key, value) pair anywhere in a nested JSON structure of
    dicts/lists -- CI run 35501830119 nested the form fields one level down
    (`HitlTaskArguments.fields.approved`), so a top-level-only scan misses
    them entirely."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield key, value
            yield from iter_keys_at_any_depth(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from iter_keys_at_any_depth(item)


def field_dereferenced_downstream(scripts, field_name: str) -> bool:
    """Whether some downstream scriptTask's text plausibly reads
    ``field_name`` off the HITL response (``response.approved``,
    ``decision.approved``, ``response["approved"]``, ...). Deliberately loose
    -- a dotted/bracket property-access substring, not full dataflow tracing
    -- matching this file's existing script_reads() style."""
    if not field_name:
        return False
    needles = (f".{field_name}", f'"{field_name}"', f"'{field_name}'")
    return any(needle in text_content(task) for task in scripts for needle in needles)


def decision_value_ok(value, declared_types, declared_schemas, scripts) -> bool:
    """A decision-matching key's value is acceptable as: a boolean literal
    (`fields.approved: false`); an `=`-expression resolving to a
    boolean-typed variable/schema property; or (the original decisionField
    rule, generalized) a bare string naming a field that some downstream
    script actually dereferences -- NOT any bare string, so a stringly-typed
    literal decision (`"approved": "yes"`) still fails."""
    if isinstance(value, bool):
        return True
    if not isinstance(value, str):
        return False
    if _vars_match(value) is not None:
        return resolve_expr_type(value, declared_types, declared_schemas) in BOOLEAN_TYPES
    return field_dereferenced_downstream(scripts, value.strip())


def reason_value_ok(value, declared_types, declared_schemas) -> bool:
    """A reason-matching key's value is acceptable as: any plain string
    (a literal default, including empty -- `fields.rejectionReason: ""` -- or
    a field-name pointer, both accepted unconditionally per the task's own
    tolerance for the reason field); or an `=`-expression resolving to a
    string/text-typed variable/schema property."""
    if not isinstance(value, str):
        return False
    if _vars_match(value) is None:
        return True
    return resolve_expr_type(value, declared_types, declared_schemas) in TEXT_TYPES


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

    declared_types = declared_var_types(root)
    declared_schemas = declared_var_schemas(root)
    scripts = elements(root, "scriptTask")

    body_input = hitl_body_input(hitl)

    if body_input is not None:
        # -- T2: real Actions.HITL registry-template form -------------------
        # Form fields live as keys of the single merged HitlTaskArguments
        # JSON body, not as separate context inputs / typed outputs (see
        # skills/uipath-maestro-bpmn/validator/bpmn-spec.json). Walked
        # recursively: CI run 35501830119 nested them one level down under a
        # "fields" object instead of putting them at the top level.
        body = parse_body_json(body_input)
        entries = [(k, v) for k, v in iter_keys_at_any_depth(body) if isinstance(k, str)]

        amount_entries = [(k, v) for k, v in entries if AMOUNT_RE.search(k)]
        if not amount_entries:
            fail("HitlTaskArguments body has no key presenting the expense amount")
        checked_types = []
        amount_ok = False
        for _key, value in amount_entries:
            resolved = resolve_expr_type(value, declared_types, declared_schemas)
            checked_types.append(resolved)
            if resolved in NUMERIC_TYPES:
                amount_ok = True
                break
        if not amount_ok:
            fail(
                "amount field in HitlTaskArguments body must resolve to a "
                "number-typed variable or jsonSchema property via "
                f"vars.<id>[.field] (found types: {checked_types})"
            )

        decision_entries = [(k, v) for k, v in entries if DECISION_NAME_RE.search(k)]
        decision_ok = any(
            decision_value_ok(v, declared_types, declared_schemas, scripts) for _k, v in decision_entries
        ) or schema_property_matches(declared_schemas, DECISION_NAME_RE, BOOLEAN_TYPES | TEXT_TYPES)
        if not decision_ok:
            fail(
                "HitlTaskArguments has no key (at any depth) matching "
                "approve/approved/decision whose value is a boolean literal, a "
                "boolean-typed expression, or a string naming a field a "
                "downstream script actually dereferences, and no declared "
                "jsonSchema variable names a matching boolean/string property "
                f"(checked keys: {[k for k, _v in decision_entries]})"
            )

        reason_entries = [(k, v) for k, v in entries if REASON_RE.search(k)]
        reason_ok = any(
            reason_value_ok(v, declared_types, declared_schemas) for _k, v in reason_entries
        ) or schema_property_matches(declared_schemas, REASON_RE, TEXT_TYPES)
        if not reason_ok:
            fail(
                "HitlTaskArguments has no key (at any depth) matching "
                "reason/comment/explanation/justification/note with a string "
                "value, and no declared jsonSchema variable names a matching "
                f"text property (checked keys: {[k for k, _v in reason_entries]})"
            )

        bound_any = any(
            expr_var_ref(v) is not None and (expr_var_ref(v) in declared_types or expr_var_ref(v) in declared_schemas)
            for _k, v in entries
            if isinstance(v, str)
        )
        if not bound_any:
            fail(
                "HitlTaskArguments body has no field bound to a declared "
                "process variable via vars.<id> (upstream script output), "
                "not a hardcoded literal"
            )
    else:
        # -- T1: older per-field context-input / typed-output form ----------
        amount_inputs = [inp for inp in context_inputs if AMOUNT_RE.search(blob(inp))]
        if not amount_inputs:
            fail("HITL has no context input presenting the expense amount to the reviewer")
        amount_ok = False
        for inp in amount_inputs:
            ref = var_ref(blob(inp))
            if ref and declared_types.get(ref) in NUMERIC_TYPES:
                amount_ok = True
                break
        if not amount_ok:
            fail(
                "amount context input must reference a number-typed declared "
                "variable via vars.<id> (found types: "
                f"{[declared_types.get(var_ref(blob(i))) for i in amount_inputs]})"
            )

        decision_outputs = [o for o in outputs if DECISION_NAME_RE.search(blob(o))]
        if not decision_outputs:
            fail(
                "HITL has no output field capturing the manager's decision "
                "(name/var containing approve/approved/decision)"
            )
        if not any((o.attrib.get("type") or "").lower() in (BOOLEAN_TYPES | TEXT_TYPES) for o in decision_outputs):
            fail("decision output field must be typed boolean or string/text")

        reason_outputs = [
            o
            for o in outputs
            if (o.attrib.get("type") or "").lower() in TEXT_TYPES and REASON_RE.search(blob(o))
        ]
        if not reason_outputs:
            fail("HITL has no text output field for the rejection reason (e.g. reason, comment)")

        def bound_to_declared(inp) -> bool:
            ref = var_ref(blob(inp))
            return ref is not None and ref in declared_types

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
