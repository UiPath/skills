#!/usr/bin/env python3
import datetime
import json
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "_shared"))
sys.path.insert(0, str(HERE / "_setup"))
import sfdc_contracts as fixture  # noqa: E402
from golden_connectors import (  # noqa: E402
    INFRA_EXIT, PROVIDER_REFUSAL, InfraError, brief, choose_workflow, connection_map, declared_inputs, declared_outputs,
    needed_inputs, run_workflow, side_effect_tasks,
)
from switches import switch_off  # noqa: E402

BUDGET_SECONDS = 270
RUN_TIMEOUT = 150
DAYS_INPUT = re.compile(r"day|window|within|ahead|horizon|next|range|period", re.IGNORECASE)
DATE_INPUT = re.compile(r"date|today|as_?of|from|start|reference", re.IGNORECASE)
CONTRACTS_OUTPUT = re.compile(r"contract", re.IGNORECASE)


def inputs_for(declared, today):
    values = {}
    for name, spec in declared.items():
        kind = spec.get("type")
        if kind in ("integer", "number") and DAYS_INPUT.search(name):
            values[name] = fixture.WINDOW_DAYS
        elif kind == "string" and DATE_INPUT.search(name):
            values[name] = today.isoformat()
    return values


def booleans(declared):
    return [name for name, spec in declared.items() if spec.get("type") == "boolean"]


def run_inputs(workflow, today, connections):
    declared = declared_inputs(workflow)
    flags = booleans(declared)
    effects = side_effect_tasks(workflow, fixture.CONNECTOR, connections)
    inputs, left = switch_off(workflow, effects, inputs_for(declared, today), flags)
    inputs.update((name, False) for name in needed_inputs(workflow) if name in flags and name not in inputs)
    return inputs, left


def pick_workflow(root=".", today=None):
    today = today or datetime.date.today()

    def fits(workflow):
        declared = declared_inputs(workflow)
        covered = set(inputs_for(declared, today)) | set(booleans(declared))
        return all(name in covered for name in needed_inputs(workflow))

    def answers(workflow):
        return any(CONTRACTS_OUTPUT.search(name) and spec.get("type") == "array"
                   for name, spec in declared_outputs(workflow).items())

    return choose_workflow(fits, answers, root)


def is_inside(contract, today):
    end = contract.get("end_date")
    if not end:
        return None
    end = datetime.date.fromisoformat(str(end)[:10])
    return today <= end <= today + datetime.timedelta(days=fixture.WINDOW_DAYS)


def returned(contract, text):
    if contract["id"][:15] in text:
        return True
    number = contract.get("number")
    if number and re.search(rf"(?<!\d){re.escape(str(number))}(?!\d)", text):
        return True
    return contract["label"] in text


def verdict(contracts, raw, today):
    text = json.dumps(raw, ensure_ascii=False)
    inside = [c for c in contracts if is_inside(c, today)]
    outside = [c for c in contracts if is_inside(c, today) is False]
    missing = [c["label"] for c in inside if not returned(c, text)]
    leaked = [c["label"] for c in outside if returned(c, text)]
    problems = []
    if missing:
        problems.append("expiring contracts missing: " + ", ".join(missing))
    if leaked:
        problems.append("contracts outside the next 30 days returned: " + ", ".join(leaked))
    return not problems, problems, len(inside)


def bound_connections(workflow, connections):
    found = set()
    stack = [workflow]
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            bound = str(node.get("connectionId") or "").lower()
            if connections.get(bound) == fixture.CONNECTOR:
                found.add(bound)
            stack.extend(node.values())
        elif isinstance(node, list):
            stack.extend(node)
    return found


def prepare(today):
    state = fixture.load_state()
    connection, account_id, _ = fixture.verify_fixture(state)
    state["contracts"].append(fixture.add_contract(connection, account_id, state["token"],
                                                   fixture.GRADING_DAYS, today))
    fixture.save_state(state)
    contracts = fixture.describe(connection, state)
    fixture.save_state(state)
    unread = [c["label"] for c in contracts if not c.get("end_date")]
    if unread:
        raise fixture.FixtureError("EndDate not readable for " + ", ".join(unread))
    fixture.require_activated(contracts)
    return connection, contracts


def run(workflow_path, inputs, deadline):
    error = None
    for _ in range(2):
        remaining = deadline - time.monotonic()
        if remaining < 30:
            break
        ok, raw, error = run_workflow(workflow_path, inputs, timeout=int(min(RUN_TIMEOUT, remaining - 10)))
        if ok:
            return raw, None
        if error and PROVIDER_REFUSAL.search(error):
            raise InfraError("a provider refused the run")
        if error == "run timed out":
            break
    return None, error or "grading time budget used up"


def main(today=None):
    deadline = time.monotonic() + BUDGET_SECONDS
    today = today or datetime.date.today()
    try:
        connection, contracts = prepare(today)
        connections = connection_map()
    except (fixture.FixtureError, KeyError, InfraError) as exc:
        print(f"INFRA: {exc}; this run says nothing about the workflow", file=sys.stderr)
        return INFRA_EXIT

    workflow_path = pick_workflow(today=today)
    if workflow_path is None:
        sys.exit("FAIL: no Workflow.json inside a project folder")
    shown = workflow_path.relative_to(Path.cwd().resolve())
    try:
        workflow = json.loads(workflow_path.read_text())
    except (OSError, ValueError) as exc:
        sys.exit(f"FAIL: {shown} is not readable JSON: {exc}")
    foreign = sorted(bound_connections(workflow, connections) - {str(connection).lower()})
    if foreign:
        print(f"INFRA: {shown} reads Salesforce through {', '.join(foreign)}, not {connection}, the connection "
              "the fixture was seeded through; this run says nothing about the workflow", file=sys.stderr)
        return INFRA_EXIT
    inputs, effects = run_inputs(workflow, today, connections)
    if effects:
        sys.exit(f"FAIL: {shown} would write to Salesforce or send something ({'; '.join(effects)}), and no values "
                 "of the boolean inputs its If conditions read as $workflow.input.<name> keep that from running, so "
                 "it is not run: the prompt allows no emails, messages or Salesforce changes while testing")

    try:
        raw, error = run(workflow_path, inputs, deadline)
    except InfraError as exc:
        print(f"INFRA: {exc}; this run says nothing about {shown}", file=sys.stderr)
        return INFRA_EXIT
    if error:
        sys.exit(f"FAIL: {shown} did not run with inputs {json.dumps(inputs)}: {brief(error)}")
    passed, problems, inside = verdict(contracts, raw, today)
    if not passed:
        sys.exit(f"FAIL: {shown}: {'; '.join(problems)} (inputs {json.dumps(inputs)})")
    print(f"OK: {shown}: returned all {inside} fixture contracts ending in the next 30 days and none of the others")
    return 0


if __name__ == "__main__":
    sys.exit(main())
