#!/usr/bin/env python3
"""IoBindingCase: run the case built from sdd.md once under debug and check
the values that moved between its tasks.

The Golden Expense API workflow echoes APIInput1 back as APIOutput1, so every
value the SDD wires through it is known in advance (caseInput defaults to
`case-seed`):

- Echo literal is sent `literal-seed`; Echo case variable `case-seed`; Echo prior
  output gets Echo literal's echo, `literal-seed`; Echo expression
  `case-seed-input-expression`; both NameToAge lookups get `case-seed`.
- renamedResult = `case-seed`, literalResult = `literal-assigned`,
  copiedResult = `case-seed`, computedResult = `literal-seed-computed`,
  metadataResult = the case's own id, as the instance itself reports it
  (`ExternalId`), else as the run's `CaseId` variable holds it. A tenant that
  puts the plan's identifier in the ids it mints gives `IOB-...`; Automation
  Suite 2.2610 gives a bare number, so the SDD's `IOB` prefix is read from the
  plan, not from the run. A run in which neither names the id fails: the
  value cannot be checked.

NameToAge asks api.agify.io, which has no age for `case-seed`, so its value is
not graded; the two tasks that consume it must receive a value, not the text of
an unresolved reference (null only when their source is null), and
customReferenceCopy must equal collisionCopy.

The run shows the value each task received, not how it was bound, so a literal
that spells the expected value passes these checks as the SDD's reference does.

Read from the debug instance (`uip maestro case instance variables-all`): each
task's runtime inputs and the case variables by the names the SDD gives. The
eight tasks must complete in the SDD's order. Static checks keep only what the
SDD states (the case identifier, task names, the resources and folders, run
once, no inline API project) and what any correct plan has (no unresolved `$xref`, unique task
output ids), plus the two agify-fed tasks binding their input to the producing
task's output, since a null upstream passes any input; they accept any other
binding, id or output-row layout.
"""

from __future__ import annotations

import glob
import json
import os
import re
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.case_run_evidence import (  # noqa: E402
    RunEvidence,
    assert_completed,
    execution_of,
    fail,
    _uip,
    leaf_values,
    read_run,
    since_iso,
    text_of,
)
from _shared.case_check import (  # noqa: E402
    _get_ci,
    assert_tasks_nested,
    find_tasks_of_type,
    read_caseplan,
    run_debug,
    task_is_skeleton,
)

DEBUG_TIMEOUT_S = 900
RESOURCE_NAME = "API Workflow"
GOLDEN_FOLDER = "Shared/uipath-maestro-case/CM-Golden-Expense-Reporting-106"
AGE_FOLDER = "Shared/uipath-maestro-case/NameToAgeFixed2"

# SDD order, the resource folder, the input field and the value it must receive
# (None: a value that depends on api.agify.io, checked only for being resolved).
CHAIN = (
    ("Echo literal", GOLDEN_FOLDER, "APIInput1", "literal-seed"),
    ("Echo case variable", GOLDEN_FOLDER, "APIInput1", "case-seed"),
    ("Echo prior output", GOLDEN_FOLDER, "APIInput1", "literal-seed"),
    ("Echo expression", GOLDEN_FOLDER, "APIInput1", "case-seed-input-expression"),
    ("Lookup exact same name", AGE_FOLDER, "name", "case-seed"),
    ("Lookup colliding same name", AGE_FOLDER, "name", "case-seed"),
    ("Consume colliding output", GOLDEN_FOLDER, "APIInput1", None),
    ("Consume custom output", GOLDEN_FOLDER, "APIInput1", None),
)
NAMED_OUTPUTS = {
    "renamedResult": "case-seed",
    "literalResult": "literal-assigned",
    "copiedResult": "case-seed",
    "computedResult": "literal-seed-computed",
}
# The task whose output each agify-fed task consumes: (producer, output name).
# That output is also where its input is read back from, and it may be null only when the producer's is.
CONSUMES = {
    "Consume colliding output": ("Lookup colliding same name", "estimatedAge"),
    "Consume custom output": ("Consume colliding output", "collisionCopy"),
}
CONSUMED_FIELD = "APIInput1"
VARS_PREFIX = "=vars."
CASE_ID_PREFIX = "IOB"
CASE_ID_TYPE = "constant"
METADATA_OUTPUT = "metadataResult"
UNRESOLVED = re.compile(r"(^=?vars\.|\$xref\(|^=js:|^<-)")


# ── Static: what the SDD states ─────────────────────────────────────────────


def one(items: list, what: str):
    if len(items) != 1:
        fail(f"expected exactly one {what}, got {len(items)}")
    return items[0]


def resolve_binding(plan: dict, reference: object, property_name: str) -> dict:
    prefix = "=bindings."
    if not isinstance(reference, str) or not reference.startswith(prefix):
        fail(f"task data.{property_name} is not a binding reference: {reference!r}")
    binding_id = reference[len(prefix):]
    return one(
        [b for b in plan.get("bindings") or [] if b.get("id") == binding_id],
        f"binding {binding_id!r}",
    )


def assert_resource(plan: dict, task: dict, folder: str) -> None:
    data = task.get("data") or {}
    name_binding = resolve_binding(plan, data.get("name"), "name")
    folder_binding = resolve_binding(plan, data.get("folderPath"), "folderPath")
    key = f"{folder}.{RESOURCE_NAME}"
    for binding in (name_binding, folder_binding):
        if binding.get("resourceKey") != key:
            fail(
                f"task {task.get('displayName')!r} binds {binding.get('resourceKey')!r}, "
                f"the SDD names {key!r}"
            )
    if name_binding.get("default") != RESOURCE_NAME or folder_binding.get("default") != folder:
        fail(
            f"task {task.get('displayName')!r} binds name={name_binding.get('default')!r} "
            f"folder={folder_binding.get('default')!r}, the SDD names {RESOURCE_NAME!r} in {folder!r}"
        )


def assert_no_inline_api_project() -> None:
    for manifest in glob.glob("**/*.uipx", recursive=True):
        with open(manifest, encoding="utf-8") as stream:
            solution = json.load(stream)
        api = [p for p in solution.get("Projects") or [] if str(p.get("Type", "")).lower() == "api"]
        if api:
            fail(f"{manifest} holds an inline API project instead of using the tenant's: {api}")


def assert_sdd_output_contract() -> None:
    """sdd.md's Outputs rows still use `->` or `x = expr`, as staged."""
    if not os.path.isfile("sdd.md"):
        fail("missing sdd.md")
    with open("sdd.md", encoding="utf-8") as stream:
        lines = stream.readlines()
    in_outputs = False
    for line_number, line in enumerate(lines, start=1):
        stripped = line.strip()
        if re.match(r"^\*\*Outputs:?\*\*$", stripped):
            in_outputs = True
            continue
        if in_outputs and stripped.startswith(("#", "**Inputs")):
            in_outputs = False
        if not in_outputs or not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) != 3:
            continue
        field, _type, binding = cells
        if field == "Field" or (field and set(field) <= {"-", ":"}):
            continue
        if binding.startswith("->") and field not in ("", "—") and binding[2:].strip():
            continue
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*\s*=(?!=)\s*(.+)$", binding) and field in ("", "—"):
            continue
        fail(f"sdd.md:{line_number} Outputs row was rewritten: {stripped}")


def _output_reference(task: dict, output_name: str) -> str:
    rows = (task.get("data") or {}).get("outputs") or []
    row = one([r for r in rows if r.get("name") == output_name], f"{output_name!r} output of {task.get('displayName')!r}")
    return VARS_PREFIX + str(row.get("id") or row.get("var"))


def assert_consumers_bound(tasks: list[dict]) -> None:
    """A null upstream passes any input at run time, so the binding is read from the plan."""
    by_name = {t.get("displayName"): t for t in tasks}
    for name, (producer, output_name) in CONSUMES.items():
        expected = _output_reference(by_name[producer], output_name)
        rows = (by_name[name].get("data") or {}).get("inputs") or []
        bound = [r.get("value") for r in rows if r.get("name") == CONSUMED_FIELD]
        if bound != [expected]:
            fail(f"task {name!r} must bind {CONSUMED_FIELD} to {expected!r}, got {bound!r}")


def assert_case_identifier(plan: dict) -> None:
    """The plan carries the SDD's case identifier (a constant prefix), whatever the ids the tenant mints from it."""
    metadata = plan.get("metadata") or {}
    identifier, kind = metadata.get("caseIdentifier"), metadata.get("caseIdentifierType")
    if identifier != CASE_ID_PREFIX or kind != CASE_ID_TYPE:
        fail(
            f"the plan's case identifier is {identifier!r} (type {kind!r}), "
            f"the SDD names the prefix {CASE_ID_PREFIX!r} (type {CASE_ID_TYPE!r})"
        )


def check_plan(plan: dict) -> list[dict]:
    """The eight SDD tasks in SDD order, after the static checks."""
    assert_tasks_nested(plan)
    assert_case_identifier(plan)
    tasks = find_tasks_of_type(plan, "api-workflow")
    names = [name for name, *_ in CHAIN]
    extra = sorted(str(t.get("displayName")) for t in tasks if t.get("displayName") not in names)
    if len(tasks) != len(CHAIN) or extra:
        fail(f"expected the SDD's {len(CHAIN)} api-workflow tasks, got {len(tasks)} (unexpected: {extra})")
    chain = []
    for name, folder, _field, _value in CHAIN:
        task = one([t for t in tasks if t.get("displayName") == name], f"api-workflow task {name!r}")
        if task_is_skeleton(task):
            fail(f"task {name!r} is an unresolved skeleton")
        if task.get("shouldRunOnlyOnce") is not True:
            fail(f"task {name!r} must run only once, as the SDD says")
        assert_resource(plan, task, folder)
        chain.append(task)
    if "$xref(" in json.dumps(plan):
        fail("the plan still holds an unresolved $xref marker")
    output_ids = [
        row.get("id") for t in tasks for row in (t.get("data") or {}).get("outputs") or [] if row.get("id")
    ]
    duplicates = sorted({i for i in output_ids if output_ids.count(i) > 1})
    if duplicates:
        fail(f"task output ids collide: {duplicates}")
    assert_consumers_bound(tasks)
    return chain


# ── Runtime: what the run did ───────────────────────────────────────────────


def _instant(stamp: object) -> datetime | None:
    match = re.match(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(\.\d+)?", str(stamp or ""))
    if not match:
        return None
    fraction = (match.group(2) or ".0")[1:7].ljust(6, "0")
    return datetime.fromisoformat(f"{match.group(1)}.{fraction}")


def check_order(payload: dict, chain: list[dict]) -> None:
    for earlier, later in zip(chain, chain[1:]):
        done = _instant(_get_ci(execution_of(payload, str(earlier.get("id"))) or {}, "completedAt"))
        began = _instant(_get_ci(execution_of(payload, str(later.get("id"))) or {}, "startedAt"))
        if done and began and began < done:
            fail(
                f"task {later.get('displayName')!r} started before {earlier.get('displayName')!r} "
                "completed; the SDD runs them one after another"
            )


def _empty(value: object) -> bool:
    """The null or NaN that agify's empty answer turns into along the chain."""
    return value is None or (isinstance(value, float) and value != value)


def _upstream(evidence: RunEvidence, chain: list[dict], source: str | None, field: str) -> object:
    """``field`` as the source task returned it, else as the case variable holds it."""
    if source is not None:
        task = next(t for t, (name, *_) in zip(chain, CHAIN) if name == source)
        returned = list(leaf_values(evidence.task_io_or_empty(str(task.get("id")))[1], field))
        if returned:
            return returned[0]
    return evidence.value(field) if evidence.has(field) else None


def check_inputs(evidence: RunEvidence, chain: list[dict]) -> None:
    for task, (name, _folder, field, expected) in zip(chain, CHAIN):
        inputs, _ = evidence.task_io(str(task.get("id")))
        values = list(leaf_values(inputs, field))
        if expected is None and (not values or _empty(values[0])):
            upstream = _upstream(evidence, chain, *CONSUMES[name])
            if _empty(upstream):
                continue  # agify's empty answer may reach the task as no value at all
            fail(f"task {name!r} ran without a {field} input although its source holds {upstream!r}")
        if not values:
            fail(f"task {name!r} ran without a {field} input: {text_of(inputs)[:300]}")
        value = values[0]
        if expected is not None and value != expected:
            fail(f"task {name!r} received {field}={value!r}, expected {expected!r}")
        if isinstance(value, str) and UNRESOLVED.search(value.strip()):
            fail(f"task {name!r} received the text {value!r} instead of the value it refers to")


def instance_external_id(payload: dict, folder_key: str | None) -> str | None:
    """The id the tenant gave this case, read from the instance itself; None when it reports none.

    ``folder_key`` is the one ``read_run`` already resolved, so the instance is
    not looked up in the list a second time. A failed read fails the check: it
    is not an instance without an id.
    """
    instance_id = str(_get_ci(payload, "instanceId", "InstanceId") or "")
    if not instance_id or not folder_key:
        return None
    data = _uip(
        ["maestro", "case", "instance", "get", instance_id, "--folder-key", folder_key],
        "uip maestro case instance get",
    )
    value = _get_ci(data, "ExternalId") if isinstance(data, dict) else None
    return str(value) if value else None


def check_metadata(evidence: RunEvidence, external_id: str | None) -> None:
    """metadataResult is the case's own id."""
    metadata = evidence.value(METADATA_OUTPUT)
    # The instance's own ExternalId is the authority; the run's CaseId variable stands in for it.
    case_id = external_id or (evidence.value("caseId") if evidence.has("caseId") else None)
    if not case_id:
        # A prefix would be a guess: it passes any `IOB-…` value and fails a tenant that mints a bare id.
        fail(
            f"the run names no case id (no ExternalId on the instance, no CaseId variable), "
            f"so {METADATA_OUTPUT} ({metadata!r}) cannot be checked"
        )
    # The SDD declares metadataResult a string: the number 17980423 is not the id "17980423".
    if not isinstance(metadata, str) or metadata != str(case_id):
        fail(f"{METADATA_OUTPUT} is {metadata!r}, expected the case's id {str(case_id)!r} as a string")


def check_outputs(evidence: RunEvidence, chain: list[dict], external_id: str | None = None) -> None:
    for name, expected in NAMED_OUTPUTS.items():
        actual = evidence.value(name)
        if actual != expected:
            fail(f"{name} is {actual!r} after the run, expected {expected!r}")
    check_metadata(evidence, external_id)
    collision = evidence.value("collisionCopy")
    custom = evidence.value("customReferenceCopy")
    age = _upstream(evidence, chain, *CONSUMES["Consume colliding output"])
    if not _same_number(custom, collision, age):
        fail(f"customReferenceCopy is {custom!r}, expected collisionCopy's {collision!r}")


def _same_number(a: object, b: object, age: object) -> bool:
    """Equal, or both the NaN / null that `null + 0` chains produce from a null age."""
    if _empty(a) and _empty(b):
        return _empty(age)
    return a == b


def check_run(payload: dict, evidence: RunEvidence, chain: list[dict], external_id: str | None = None) -> None:
    for task in chain:
        assert_completed(payload, task)
    check_order(payload, chain)
    check_inputs(evidence, chain)
    check_outputs(evidence, chain, external_id)


def main() -> None:
    assert_sdd_output_contract()
    plan = read_caseplan()
    chain = check_plan(plan)
    assert_no_inline_api_project()
    since = since_iso()
    payload = run_debug(timeout=DEBUG_TIMEOUT_S)
    evidence = read_run(payload, since)
    check_run(payload, evidence, chain, instance_external_id(payload, evidence.folder_key))
    print(
        "OK: debug Completed; the eight SDD tasks completed in order, each received the "
        "value its SDD binding names, and renamedResult, literalResult, copiedResult, "
        "computedResult, metadataResult and customReferenceCopy hold the expected values"
    )


if __name__ == "__main__":
    main()
