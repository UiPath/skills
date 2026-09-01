#!/usr/bin/env python3
"""ContractExecution rebuild: deterministic dataflow and condition grader.

The case builder lowers SDD ``vars.$xref(stage, task, output)`` expressions to
``vars.<output-id>`` references, where task/stage/output IDs are minted per
build. This checker resolves those IDs back to logical names and verifies the
semantic contract that would otherwise need an LLM judge:

  - every stage holds exactly the SDD's task names
  - every generated task output has a unique id; an output the SDD routes to a
    case variable carries that variable in ``var``, every other output keeps
    ``var == id``
  - the four cross-task input bindings read the right upstream output, and no
    other input quietly consumes a task output
  - Scenario E (``custom: true``) outputs write exactly the SDD's fixed
    values - the three terminal ``finalOutcome`` literals plus the signature
    mock's persisted result
  - stage entry / exit, task entry, and case-exit condition sets match the
    SDD, including gate polarity: which decision literal routes where, and
    that the rejection lane negates the signature gate the executed lane
    asserts
  - behavior-bearing literals survive: api-workflow dispatch operations,
    per-phase SLA-handler ``phase`` values, agent ``analysisType``, the
    authority-policy JSON, action titles / priorities / labels, and
    ``caseId`` wiring to ``metadata.ExternalId``

Every expectation that names SDD content is parsed from the task's own
``fixtures/sdd.md`` at grade time, so re-sweeping the fixture updates agent
input and grader in one file.
"""

from __future__ import annotations

from collections import Counter
import json
import os
import re
import sys

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from _shared.case_check import find_stages, read_caseplan  # noqa: E402

EXPECTED_CASEPLAN = os.path.join("ContractExecution", "ContractExecution", "caseplan.json")
FIXTURE_SDD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "sdd.md")

CHECKING = "Checking the request"
COUNSEL = "Counsel review"
SENIOR = "Senior counsel review"
SIGNATURE = "Signature and filing"
EXECUTED = "Contract executed"
REJECTED = "Contract rejected"
WITHDRAWN = "Contract withdrawn"
INTERVENTION = "Overall SLA Intervention"

TASKS_BY_STAGE = {
    CHECKING: [
        "Validate Request Details",
        "Pull Counterparty Records",
        "Analyze Draft for Unusual Clauses",
        "Add More Documents",
        "Handle Checking SLA Breach",
    ],
    COUNSEL: [
        "Notify Assigned Counsel",
        "Counsel Decision",
        "Ask Business Team a Question",
        "Order Outside Opinion",
        "Handle Counsel SLA Breach",
    ],
    SENIOR: [
        "Run Policy and Authority Check",
        "Compare Historical Positions",
        "Pull In Finance Controller",
        "Senior Counsel Decision",
        "Handle Senior Counsel SLA Breach",
    ],
    SIGNATURE: [
        "Prepare and Send Signature Packet",
        "Wait for Signature Result",
        "Open Obligation Tracking",
        "Handle Signature SLA Breach",
    ],
    EXECUTED: [
        "Deliver Executed Copy",
        "File Contract",
        "Handle Executed Wrap Up SLA Breach",
    ],
    REJECTED: [
        "Notify Requester of Rejection",
        "Log Rejection Decision",
        "Handle Rejected Wrap Up SLA Breach",
    ],
    WITHDRAWN: [
        "Confirm Withdrawal",
        "Tidy Up Open Work",
        "Handle Withdrawn Wrap Up SLA Breach",
    ],
    INTERVENTION: ["Handle Overall SLA Breach", "General Counsel Review"],
}

COUNSEL_DECISION = (COUNSEL, "Counsel Decision")
SENIOR_DECISION = (SENIOR, "Senior Counsel Decision")
POLICY_CHECK = (SENIOR, "Run Policy and Authority Check")
WAIT_SIGNATURE = (SIGNATURE, "Wait for Signature Result")

# (stage, task) -> {case variable each extract output writes}. From the SDD's
# "-> <case variable>" Output Schema / Outputs rows.
EXPECTED_EXTRACT_VARS = {
    (CHECKING, "Validate Request Details"): {"requestIssues"},
    (CHECKING, "Pull Counterparty Records"): {"counterpartyProfile"},
    (CHECKING, "Add More Documents"): {"supportingDocuments"},
    COUNSEL_DECISION: {"rejectionReason", "rejectedBy"},
    (COUNSEL, "Order Outside Opinion"): {"outsideOpinion"},
    POLICY_CHECK: {"policyRiskFlags"},
    SENIOR_DECISION: {"rejectionReason", "rejectedBy"},
}

# (stage, task) -> {output var: fixed source}. Scenario E `custom: true` rows.
EXPECTED_CUSTOM_OUTPUTS = {
    WAIT_SIGNATURE: {
        "executedContract": "=vars.draftContract",
        "rejectionReason": "",
        "rejectedBy": "E-signature Platform mock",
    },
    (EXECUTED, "File Contract"): {"finalOutcome": "Executed"},
    (REJECTED, "Log Rejection Decision"): {"finalOutcome": "Rejected"},
    (WITHDRAWN, "Tidy Up Open Work"): {"finalOutcome": "Withdrawn"},
}

# (consumer, input) -> (producer output, reference form). "guarded:<prop>" is
# the null-safe dotted access `(vars.<id> || {}).<prop>`.
EXPECTED_SOURCES = {
    (COUNSEL_DECISION, "unusualClauses"): (
        (CHECKING, "Analyze Draft for Unusual Clauses", "analysisResult"),
        "guarded:unusualClauses",
    ),
    (SENIOR_DECISION, "authorityLevel"): (
        (*POLICY_CHECK, "response"),
        "guarded:authorityLevel",
    ),
    (SENIOR_DECISION, "historicalDeviationFlags"): (
        (SENIOR, "Compare Historical Positions", "analysisResult"),
        "guarded:deviationFlags",
    ),
    (SENIOR_DECISION, "financeOpinion"): (
        (SENIOR, "Pull In Finance Controller", "opinion"),
        "direct",
    ),
}

VAR_REF_RE = re.compile(r"\bvars\.([A-Za-z_][A-Za-z0-9_]*)")
EQUALS_GATE_RE = re.compile(
    r"^\s*=js:\s*vars\.([A-Za-z_][A-Za-z0-9_]*)\s*===\s*(['\"])(.+?)\2\s*$"
)
EXTERNAL_ID_RE = re.compile(r"^\s*=(?:js:)?\s*metadata\.ExternalId\s*$")
SIGNATURE_TOKENS = ("Declined", "Expired")
TASK_BLOCK_RE = re.compile(
    r"^#####\s+Task\s+\S+\s*:\s*(?P<name>.+?)\s*$(?P<body>.*?)(?=^#####\s|\n---\n|\Z)",
    re.MULTILINE | re.DOTALL,
)


def _fail(msg: str):
    sys.exit(f"FAIL: {msg}")


def _norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (value or "").lower())


def _read_plan() -> dict:
    if len(sys.argv) > 1:
        return read_caseplan(sys.argv[1])
    if os.path.exists(EXPECTED_CASEPLAN):
        return read_caseplan(EXPECTED_CASEPLAN)
    return read_caseplan()


# ── fixture parsing ────────────────────────────────────────────────────────


def _read_fixture() -> str:
    try:
        with open(FIXTURE_SDD, encoding="utf-8") as stream:
            return stream.read()
    except OSError as exc:
        _fail(f"cannot read fixture SDD {FIXTURE_SDD}: {exc}")


def parse_fixture() -> dict:
    """Extract the per-task literals and the signature-gate property from the SDD."""
    sdd = _read_fixture()
    dispatch: dict[str, tuple[str, str]] = {}
    phases: dict[str, str] = {}
    envelopes: dict[str, dict[str, str]] = {}
    for match in TASK_BLOCK_RE.finditer(sdd):
        name = match.group("name").strip()
        body = match.group("body")
        operation = re.search(
            r"\*\*Dispatch / Operation:\*\*\s*(\w+)\s*=\s*\"([^\"]+)\"", body
        )
        if operation:
            dispatch[name] = (operation.group(1), operation.group(2))
        phase = re.search(r"^\|\s*phase\s*\|\s*string\s*\|\s*([^|\n]+?)\s*\|", body, re.M)
        if phase:
            phases[name] = phase.group(1)
        envelope = re.search(
            r"\*\*Priority:\*\*\s*(?P<priority>[^·\n]+?)\s*·\s*"
            r"\*\*Task Title:\*\*\s*(?P<title>[^·\n]+?)\s*·\s*"
            r"\*\*Labels:\*\*\s*(?P<labels>[^\n]+?)\s*$",
            body,
            re.M,
        )
        if envelope:
            envelopes[name] = {
                "priority": envelope.group("priority"),
                "taskTitle": envelope.group("title"),
                "labels": envelope.group("labels"),
            }

    if len(dispatch) < 19:
        _fail(f"fixture parse error: expected >=19 dispatch literals; got {len(dispatch)}")
    if len(phases) != 6:
        _fail(
            "fixture parse error: expected 6 per-phase SLA-handler `phase` literals; "
            f"got {sorted(phases)}"
        )
    if len(envelopes) != 7:
        _fail(f"fixture parse error: expected 7 action envelopes; got {sorted(envelopes)}")

    gate_props = set(
        re.findall(
            r"\$xref\('Signature and filing','Wait for Signature Result','response'\)"
            r"\.([A-Za-z_][A-Za-z0-9_]*)",
            sdd,
        )
    )
    if len(gate_props) != 1:
        _fail(
            "fixture parse error: expected exactly one signature-gate response property; "
            f"got {sorted(gate_props)}"
        )

    policy = re.search(
        r"^\|\s*authorityPolicy\s*\|\s*string\s*\|\s*(\{.*?\})\s*\|", sdd, re.M
    )
    if policy is None:
        _fail("fixture parse error: authorityPolicy literal not found")
    try:
        policy_json = json.loads(policy.group(1))
    except ValueError as exc:
        _fail(f"fixture parse error: authorityPolicy is not valid JSON: {exc}")

    return {
        "dispatch": dispatch,
        "phases": phases,
        "envelopes": envelopes,
        "gate_prop": gate_props.pop(),
        "authority_policy": policy_json,
    }


# ── plan indexing ──────────────────────────────────────────────────────────


def _stage_tasks(stage: dict) -> list[dict]:
    tasks: list[dict] = []
    for lane in ((stage.get("data") or {}).get("tasks") or []):
        if isinstance(lane, dict):
            tasks.append(lane)
        elif isinstance(lane, list):
            tasks.extend(task for task in lane if isinstance(task, dict))
    return tasks


def _case_variable_names(plan: dict) -> set[str]:
    variables = plan.get("variables") or {}
    names: set[str] = set()
    for section in ("inputs", "outputs", "inputOutputs"):
        for variable in variables.get(section) or []:
            name = variable.get("name")
            if isinstance(name, str) and name:
                names.add(name)
    if not names:
        _fail("caseplan declares no case variables; the SDD declares 21")
    return names


def _index_plan(plan: dict):
    stages = find_stages(plan, include_exception=True)
    stage_by_key: dict[str, dict] = {}
    stage_id_to_key: dict[str, str] = {}
    for key in TASKS_BY_STAGE:
        matches = [s for s in stages if _norm((s.get("data") or {}).get("label")) == _norm(key)]
        if len(matches) != 1:
            _fail(
                f"expected one stage matching {key!r}; got "
                f"{[(s.get('data') or {}).get('label') for s in matches]}"
            )
        stage_by_key[key] = matches[0]
        stage_id = matches[0].get("id")
        if not isinstance(stage_id, str) or not stage_id:
            _fail(f"stage {key!r} has no id")
        stage_id_to_key[stage_id] = key

    task_by_logical: dict[tuple[str, str], dict] = {}
    task_id_to_logical: dict[str, tuple[str, str]] = {}
    for stage_key, expected_names in TASKS_BY_STAGE.items():
        tasks = _stage_tasks(stage_by_key[stage_key])
        actual = [task.get("displayName") for task in tasks]
        if Counter(actual) != Counter(expected_names):
            _fail(f"stage {stage_key!r} task names {actual!r} != expected {expected_names!r}")
        for task in tasks:
            logical = (stage_key, task["displayName"])
            task_by_logical[logical] = task
            task_id = task.get("id")
            if not isinstance(task_id, str) or not task_id:
                _fail(f"task {logical!r} has no id")
            if task_id in task_id_to_logical:
                _fail(f"duplicate task id {task_id!r}")
            task_id_to_logical[task_id] = logical

    case_variables = _case_variable_names(plan)
    output_by_logical: dict[tuple[str, str, str], dict] = {}
    output_id_to_logical: dict[str, tuple[str, str, str]] = {}
    extracts: dict[tuple[str, str], set[str]] = {}
    customs: dict[tuple[str, str], dict[str, object]] = {}
    for logical, task in task_by_logical.items():
        for output in (task.get("data") or {}).get("outputs") or []:
            name = output.get("name")
            if not isinstance(name, str) or not name:
                _fail(f"task {logical!r} has an output without a name")
            if output.get("custom") is True:
                variable = output.get("var")
                if not isinstance(variable, str) or not variable:
                    _fail(f"task {logical!r} custom output {name!r} has no var")
                customs.setdefault(logical, {})[variable] = output.get("source")
                continue
            output_id = output.get("id")
            if not isinstance(output_id, str) or not output_id:
                _fail(f"output {(*logical, name)!r} has no generated id")
            if output_id in output_id_to_logical:
                _fail(
                    f"duplicate generated output id {output_id!r} "
                    f"({(*logical, name)} vs {output_id_to_logical[output_id]}) - task "
                    "outputs are deduplicated by id alone, so a reused id silently "
                    "repoints every gate that reads it"
                )
            variable = output.get("var")
            if variable in case_variables and variable != output_id:
                extracts.setdefault(logical, set()).add(variable)
            elif variable == output_id:
                if output_id in case_variables:
                    extracts.setdefault(logical, set()).add(variable)
            else:
                _fail(
                    f"output {(*logical, name)!r} has id={output_id!r} and var={variable!r}: "
                    "a task output either keeps var == id or routes to a declared case "
                    "variable"
                )
            key = (*logical, name)
            if key in output_by_logical:
                _fail(f"duplicate logical output {key!r}")
            output_by_logical[key] = output
            output_id_to_logical[output_id] = key

    return {
        "stages": stage_by_key,
        "stage_ids": stage_id_to_key,
        "tasks": task_by_logical,
        "task_ids": task_id_to_logical,
        "outputs": output_by_logical,
        "output_ids": output_id_to_logical,
        "extracts": extracts,
        "customs": customs,
    }


# ── dataflow ───────────────────────────────────────────────────────────────


def _inputs(task: dict) -> dict[str, dict]:
    found: dict[str, dict] = {}
    for item in (task.get("data") or {}).get("inputs") or []:
        name = item.get("name")
        if not isinstance(name, str) or not name:
            _fail(f"task {task.get('displayName')!r} has an input without a name")
        if name in found:
            _fail(f"task {task.get('displayName')!r} has duplicate input {name!r}")
        found[name] = item
    return found


def _input_value(task: dict, name: str, where: str):
    item = _inputs(task).get(name)
    if item is None:
        _fail(f"{where}: task is missing input {name!r}")
    return item.get("value")


def _assert_reference(value, form: str, producer_id: str, where: str):
    if not isinstance(value, str):
        _fail(f"{where} must be an expression string; got {value!r}")
    escaped = re.escape(producer_id)
    if form == "direct":
        pattern = rf"^\s*=vars\.{escaped}\s*$"
    else:
        prop = re.escape(form.split(":", 1)[1])
        # Guard the OBJECT, not the property: `(vars.X || {}).prop`.
        pattern = (
            rf"^\s*=js:\s*\(\s*vars\.{escaped}\s*\|\|\s*\{{\s*\}}\s*\)\s*\.\s*{prop}\s*$"
        )
    if re.fullmatch(pattern, value) is None:
        _fail(
            f"{where} is wired as {value!r}; expected a {form!r} reference to producer "
            f"id {producer_id!r}"
        )


def _assert_dataflow(plan: dict, index: dict, fixture: dict):
    tasks, outputs, output_ids = index["tasks"], index["outputs"], index["output_ids"]
    case_variables = _case_variable_names(plan)

    expected_ref_locations: set[tuple[tuple[str, str], str]] = set()
    for (consumer, input_name), (producer, form) in EXPECTED_SOURCES.items():
        output = outputs.get(producer)
        if output is None:
            _fail(f"required producer output missing: {producer!r}")
        value = _input_value(tasks[consumer], input_name, f"{consumer!r}")
        _assert_reference(
            value, form, output["id"], f"{consumer!r} input {input_name!r}"
        )
        expected_ref_locations.add((consumer, input_name))

    # No other input may consume a task output. `vars.<name>` where <name> is a
    # declared case variable is a case-variable read, not a task-output read.
    for logical, task in tasks.items():
        for input_name, item in _inputs(task).items():
            refs = set(VAR_REF_RE.findall(str(item.get("value") or "")))
            dangling = refs - set(output_ids) - case_variables
            if dangling:
                _fail(
                    f"unresolvable variable reference(s) {sorted(dangling)} in "
                    f"{logical!r} input {input_name!r}: neither a task output nor a "
                    "declared case variable"
                )
            task_output_refs = (refs & set(output_ids)) - case_variables
            if task_output_refs and (logical, input_name) not in expected_ref_locations:
                _fail(
                    f"unexpected task-output reference(s) {sorted(task_output_refs)} in "
                    f"{logical!r} input {input_name!r}"
                )

    if index["extracts"] != EXPECTED_EXTRACT_VARS:
        _fail(
            "task-output -> case-variable extractions differ from the SDD\n"
            f"  actual={ {k: sorted(v) for k, v in sorted(index['extracts'].items())} }\n"
            f"  expected={ {k: sorted(v) for k, v in sorted(EXPECTED_EXTRACT_VARS.items())} }"
        )
    if index["customs"] != EXPECTED_CUSTOM_OUTPUTS:
        _fail(
            "fixed-value (custom) outputs differ from the SDD\n"
            f"  actual={ {k: v for k, v in sorted(index['customs'].items())} }\n"
            f"  expected={ {k: v for k, v in sorted(EXPECTED_CUSTOM_OUTPUTS.items())} }"
        )
    _assert_literals(tasks, fixture)


def _assert_literals(tasks: dict, fixture: dict):
    for logical, task in tasks.items():
        name = logical[1]
        inputs = _inputs(task)

        dispatch = fixture["dispatch"].get(name)
        if dispatch is not None:
            field, expected = dispatch
            actual = _input_value(task, field, f"{logical!r}")
            if actual != expected:
                _fail(
                    f"{logical!r} dispatch input {field!r} must be {expected!r}; "
                    f"got {actual!r}"
                )

        phase = fixture["phases"].get(name)
        if phase is not None:
            actual = _input_value(task, "phase", f"{logical!r}")
            if actual != phase:
                _fail(f"{logical!r} input 'phase' must be {phase!r}; got {actual!r}")

        envelope = fixture["envelopes"].get(name)
        if envelope is not None:
            data = task.get("data") or {}
            for field, expected in envelope.items():
                if data.get(field) != expected:
                    _fail(
                        f"{logical!r} data.{field} must be {expected!r}; "
                        f"got {data.get(field)!r}"
                    )

        case_id = inputs.get("caseId")
        if case_id is not None and str(case_id.get("value") or ""):
            if EXTERNAL_ID_RE.fullmatch(str(case_id["value"])) is None:
                _fail(
                    f"{logical!r} input 'caseId' must reference metadata.ExternalId; "
                    f"got {case_id['value']!r}"
                )

    policy_value = _input_value(tasks[POLICY_CHECK], "authorityPolicy", f"{POLICY_CHECK!r}")
    try:
        policy = json.loads(policy_value) if isinstance(policy_value, str) else policy_value
    except ValueError as exc:
        _fail(f"{POLICY_CHECK!r} authorityPolicy is not valid JSON: {exc}")
    if policy != fixture["authority_policy"]:
        _fail(
            f"{POLICY_CHECK!r} authorityPolicy does not match fixtures/sdd.md\n"
            f"  actual={policy!r}\n  expected={fixture['authority_policy']!r}"
        )


# ── conditions ─────────────────────────────────────────────────────────────


def _selected_tasks(rule: dict, task_ids: dict) -> tuple:
    ids = list(rule.get("selectedTasksIds") or [])
    if rule.get("selectedTaskId"):
        ids.append(rule["selectedTaskId"])
    logical = []
    for task_id in ids:
        if task_id not in task_ids:
            _fail(f"condition references unknown task id {task_id!r}")
        logical.append(task_ids[task_id])
    return tuple(sorted(logical))


def _selected_stages(rule: dict, stage_ids: dict) -> tuple:
    ids = list(rule.get("selectedStagesIds") or [])
    if rule.get("selectedStageId"):
        ids.append(rule["selectedStageId"])
    logical = []
    for stage_id in ids:
        if stage_id not in stage_ids:
            _fail(f"condition references unknown stage id {stage_id!r}")
        logical.append(stage_ids[stage_id])
    return tuple(sorted(logical))


def _signature_gate_forms(output_id: str, prop: str) -> dict[str, bool]:
    """Whitespace-free renderings of the signature gate -> negated?"""
    forms: dict[str, bool] = {}
    for first, second in (SIGNATURE_TOKENS, SIGNATURE_TOKENS[::-1]):
        for quote in ("'", '"'):
            guarded = f"String((vars.{output_id}||{{}}).{prop})"
            core = (
                f"({guarded}.indexOf({quote}{first}{quote})<0)"
                f"&&({guarded}.indexOf({quote}{second}{quote})<0)"
            )
            forms[core] = False
            forms[f"!({core})"] = True
    return forms


def _canonical_expression(expression, output_ids: dict, signature_forms: dict):
    if expression in (None, ""):
        return None
    if not isinstance(expression, str):
        return ("invalid", repr(expression))
    match = EQUALS_GATE_RE.fullmatch(expression)
    if match is not None:
        output_id, _, literal = match.groups()
        producer = output_ids.get(output_id)
        if producer is None:
            _fail(f"gate expression references unproduced variable {output_id!r}")
        return ("equals", producer, literal)
    stripped = re.sub(r"\s+", "", expression)
    if stripped.startswith("=js:"):
        negated = signature_forms.get(stripped[len("=js:"):])
        if negated is not None:
            return ("signature", negated)
    return ("raw", stripped)


def _signature(condition: dict, indexes, *, case_level: bool = False):
    stage_ids, task_ids, output_ids, signature_forms = indexes
    groups = condition.get("rules") or []
    if len(groups) != 1 or not isinstance(groups[0], list) or len(groups[0]) != 1:
        _fail(
            f"condition {condition.get('displayName')!r} must contain exactly one rule; "
            f"got {groups!r}"
        )
    rule = groups[0][0]
    marks = (
        condition.get("marksCaseComplete") if case_level else condition.get("marksStageComplete")
    )
    return (
        rule.get("rule"),
        _selected_stages(rule, stage_ids),
        _selected_tasks(rule, task_ids),
        _canonical_expression(rule.get("conditionExpression"), output_ids, signature_forms),
        None if case_level else condition.get("type"),
        marks,
    )


def _sig(rule, *, stages=(), tasks=(), expression=None, exit_type=None, marks=None):
    return (
        rule,
        tuple(sorted(stages)),
        tuple(sorted(tasks)),
        expression,
        exit_type,
        marks,
    )


def _assert_set(where: str, conditions: list, expected: list, indexes, *, case_level=False):
    actual = Counter(
        _signature(condition, indexes, case_level=case_level) for condition in conditions
    )
    wanted = Counter(expected)
    if actual != wanted:
        _fail(f"{where} conditions differ\n  actual={actual}\n  expected={wanted}")


def _assert_conditions(plan: dict, index: dict, fixture: dict):
    outputs, task_ids, stage_ids = index["outputs"], index["task_ids"], index["stage_ids"]
    signature_output = outputs.get((*WAIT_SIGNATURE, "response"))
    if signature_output is None:
        _fail(f"{WAIT_SIGNATURE!r} must expose a 'response' output for the signature gates")
    signature_forms = _signature_gate_forms(signature_output["id"], fixture["gate_prop"])
    indexes = (stage_ids, task_ids, index["output_ids"], signature_forms)

    counsel_decision = (*COUNSEL_DECISION, "decision")
    senior_decision = (*SENIOR_DECISION, "decision")
    for logical in (counsel_decision, senior_decision):
        if logical not in outputs:
            _fail(
                f"{logical[:2]!r} must expose a 'decision' output - every routing gate off "
                "this stage reads it"
            )

    def counsel(literal):
        return ("equals", counsel_decision, literal)

    def senior(literal):
        return ("equals", senior_decision, literal)

    expected_entries = {
        CHECKING: [
            _sig("case-entered"),
            _sig(
                "selected-stage-exited",
                stages=(COUNSEL,),
                expression=counsel("Return for corrections"),
            ),
        ],
        COUNSEL: [_sig("selected-stage-completed", stages=(CHECKING,))],
        SENIOR: [
            _sig(
                "selected-stage-completed", stages=(COUNSEL,), expression=counsel("Approve")
            )
        ],
        SIGNATURE: [
            _sig(
                "selected-stage-completed",
                stages=(SENIOR,),
                expression=senior("Send to signature"),
            )
        ],
        EXECUTED: [
            _sig(
                "selected-stage-completed",
                stages=(SIGNATURE,),
                expression=("signature", False),
            )
        ],
        REJECTED: [
            _sig("selected-stage-exited", stages=(COUNSEL,), expression=counsel("Reject")),
            _sig("selected-stage-exited", stages=(SENIOR,), expression=senior("Reject")),
            _sig(
                "selected-stage-exited",
                stages=(SIGNATURE,),
                expression=("signature", True),
            ),
        ],
        WITHDRAWN: [_sig("wait-for-connector")],
        INTERVENTION: [_sig("sla-status-change")],
    }
    exit_only_complete = _sig("required-tasks-completed", exit_type="exit-only", marks=True)
    expected_exits = {
        CHECKING: [exit_only_complete],
        COUNSEL: [
            _sig(
                "required-tasks-completed",
                expression=counsel("Approve"),
                exit_type="exit-only",
                marks=True,
            ),
            _sig(
                "selected-tasks-completed",
                tasks=(COUNSEL_DECISION,),
                expression=counsel("Return for corrections"),
                exit_type="exit-only",
                marks=False,
            ),
            _sig(
                "selected-tasks-completed",
                tasks=(COUNSEL_DECISION,),
                expression=counsel("Reject"),
                exit_type="exit-only",
                marks=False,
            ),
        ],
        SENIOR: [
            _sig(
                "required-tasks-completed",
                expression=senior("Send to signature"),
                exit_type="exit-only",
                marks=True,
            ),
            _sig(
                "selected-tasks-completed",
                tasks=(SENIOR_DECISION,),
                expression=senior("Reject"),
                exit_type="exit-only",
                marks=False,
            ),
        ],
        SIGNATURE: [
            _sig(
                "required-tasks-completed",
                expression=("signature", False),
                exit_type="exit-only",
                marks=True,
            ),
            _sig(
                "selected-tasks-completed",
                tasks=(WAIT_SIGNATURE,),
                expression=("signature", True),
                exit_type="exit-only",
                marks=False,
            ),
        ],
        EXECUTED: [exit_only_complete],
        REJECTED: [exit_only_complete],
        WITHDRAWN: [exit_only_complete],
        INTERVENTION: [
            _sig("required-tasks-completed", exit_type="return-to-origin", marks=True)
        ],
    }
    for stage_key, stage in index["stages"].items():
        data = stage.get("data") or {}
        _assert_set(
            f"stage {stage_key!r} entry",
            data.get("entryConditions") or [],
            expected_entries[stage_key],
            indexes,
        )
        _assert_set(
            f"stage {stage_key!r} exit",
            data.get("exitConditions") or [],
            expected_exits[stage_key],
            indexes,
        )

    sla_triggered = _sig("sla-status-change")
    sequential = _sig("runs-sequentially")
    on_entry = _sig("current-stage-entered")
    adhoc = _sig("adhoc")
    expected_task_entries = {
        (CHECKING, "Validate Request Details"): [on_entry],
        (CHECKING, "Pull Counterparty Records"): [on_entry],
        (CHECKING, "Analyze Draft for Unusual Clauses"): [on_entry],
        (CHECKING, "Add More Documents"): [adhoc],
        (CHECKING, "Handle Checking SLA Breach"): [sla_triggered],
        (COUNSEL, "Notify Assigned Counsel"): [sequential],
        COUNSEL_DECISION: [sequential],
        (COUNSEL, "Ask Business Team a Question"): [adhoc],
        (COUNSEL, "Order Outside Opinion"): [adhoc],
        (COUNSEL, "Handle Counsel SLA Breach"): [sla_triggered],
        POLICY_CHECK: [on_entry],
        (SENIOR, "Compare Historical Positions"): [adhoc],
        (SENIOR, "Pull In Finance Controller"): [adhoc],
        SENIOR_DECISION: [_sig("selected-tasks-completed", tasks=(POLICY_CHECK,))],
        (SENIOR, "Handle Senior Counsel SLA Breach"): [sla_triggered],
        (SIGNATURE, "Prepare and Send Signature Packet"): [sequential],
        WAIT_SIGNATURE: [sequential],
        (SIGNATURE, "Open Obligation Tracking"): [adhoc],
        (SIGNATURE, "Handle Signature SLA Breach"): [sla_triggered],
        (EXECUTED, "Deliver Executed Copy"): [sequential],
        (EXECUTED, "File Contract"): [sequential],
        (EXECUTED, "Handle Executed Wrap Up SLA Breach"): [sla_triggered],
        (REJECTED, "Notify Requester of Rejection"): [sequential],
        (REJECTED, "Log Rejection Decision"): [sequential],
        (REJECTED, "Handle Rejected Wrap Up SLA Breach"): [sla_triggered],
        (WITHDRAWN, "Confirm Withdrawal"): [sequential],
        (WITHDRAWN, "Tidy Up Open Work"): [sequential],
        (WITHDRAWN, "Handle Withdrawn Wrap Up SLA Breach"): [sla_triggered],
        (INTERVENTION, "Handle Overall SLA Breach"): [sequential],
        (INTERVENTION, "General Counsel Review"): [sequential],
    }
    for logical, task in index["tasks"].items():
        _assert_set(
            f"task {logical!r} entry",
            task.get("entryConditions") or [],
            expected_task_entries[logical],
            indexes,
        )
        _assert_set(f"task {logical!r} exit", task.get("exitConditions") or [], [], indexes)

    _assert_set(
        "case exit",
        (plan.get("metadata") or {}).get("caseExitRules") or [],
        [
            _sig("required-stages-completed", marks=True),
            _sig("selected-stage-completed", stages=(REJECTED,), marks=False),
            _sig("selected-stage-completed", stages=(WITHDRAWN,), marks=False),
        ],
        indexes,
        case_level=True,
    )


def main():
    plan = _read_plan()
    fixture = parse_fixture()
    index = _index_plan(plan)
    _assert_dataflow(plan, index, fixture)
    _assert_conditions(plan, index, fixture)

    print(
        "OK: ContractExecution caseplan deterministically matches the SDD's task "
        "layout, producer/consumer dataflow, extract and fixed-value outputs, "
        "behavior-bearing literals, and normalized stage/task/case conditions "
        "including decision and signature gate polarity"
    )


if __name__ == "__main__":
    main()
