#!/usr/bin/env python3
"""Golden scenario: run the agent's expiring-contracts workflow against the seeded
Salesforce org and check which contracts it returns.

pre_run (_setup/sfdc_contracts.py seed) created contracts ending 5 and 25 days from today
and 45 days from today and 3 days ago. Right before running the workflow this grader adds
one more, ending GRADING_DAYS from today, so a workflow that hardcodes what it saw while
authoring cannot pass. Pass: every fixture contract ending in the next 30 days is in the
output and none of the others is. A contract counts as returned when its Id (15 or 18
characters), its ContractNumber or its fixture label appears anywhere in the output.

Declared inputs get plausible values (`inputs_for`): 30 for a day count, today for a date,
and reminders switched off where a flag allows it. When the agent leaves helper projects
beside it, the project graded is one whose required inputs these values cover, preferably
one that declares a list of contracts as an output (`pick_workflow`). A workflow whose
connector calls would write to Salesforce or send something (`side_effects`) is not run
unless such a flag switches that off: it fails, since the prompt rules that out while testing.

INFRA (exit INFRA_EXIT): the seed is missing, the grading-time contract cannot be created
or activated, a fixture contract is not Activated, the workflow reads Salesforce through a
connection other than the one the fixture was seeded through, or a provider refused the
run. coder_eval still scores INFRA as a failed criterion, so leave INFRA runs out of
reported pass rates.
"""
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
    INFRA_EXIT, PROVIDER_REFUSAL, InfraError, choose_workflow, declared_inputs, declared_outputs, needed_inputs,
    run_workflow, side_effects,
)

BUDGET_SECONDS = 270
RUN_TIMEOUT = 150
DAYS_INPUT = re.compile(r"day|window|within|ahead|horizon|next|range|period", re.IGNORECASE)
DATE_INPUT = re.compile(r"date|today|as_?of|from|start|reference", re.IGNORECASE)
DRY_RUN_INPUT = re.compile(r"dry.?run|preview|test.?mode", re.IGNORECASE)
SEND_INPUT = re.compile(r"send|notify|remind|email|mail|message|slack", re.IGNORECASE)
CONTRACTS_OUTPUT = re.compile(r"contract", re.IGNORECASE)
CONNECTION_ID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.IGNORECASE)


def inputs_for(declared, today):
    """Values for the declared inputs a grader can infer; the rest keep their defaults."""
    values = {}
    for name, spec in declared.items():
        kind = spec.get("type")
        if kind in ("integer", "number") and DAYS_INPUT.search(name):
            values[name] = fixture.WINDOW_DAYS
        elif kind == "string" and DATE_INPUT.search(name):
            values[name] = today.isoformat()
        elif kind == "boolean" and DRY_RUN_INPUT.search(name):
            values[name] = True
        elif kind == "boolean" and SEND_INPUT.search(name):
            values[name] = False
    return values


def pick_workflow(root=".", today=None):
    """The project to grade: one whose required inputs `inputs_for` fills, preferably one
    that declares a list of contracts as an output."""
    today = today or datetime.date.today()

    def fits(workflow):
        filled = inputs_for(declared_inputs(workflow), today)
        return all(name in filled for name in needed_inputs(workflow))

    def answers(workflow):
        return any(CONTRACTS_OUTPUT.search(name) and spec.get("type") == "array"
                   for name, spec in declared_outputs(workflow).items())

    return choose_workflow(fits, answers, root)


def is_inside(contract, today):
    """True or False for a contract whose EndDate is known, None otherwise."""
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
    """(passed, problems, inside count) for the workflow's raw output."""
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


def bound_connections(workflow):
    """The connection ids, lowercased, that the workflow's Salesforce activities bind. A
    placeholder or an expression is not a connection; such a workflow fails its run."""
    found = set()
    stack = [workflow]
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            bound = str(node.get("connectionId") or "")
            if str(node.get("connector") or "").lower() == fixture.CONNECTOR and CONNECTION_ID.fullmatch(bound):
                found.add(bound.lower())
            stack.extend(node.values())
        elif isinstance(node, list):
            stack.extend(node)
    return found


def prepare(today):
    """(the fixture's connection id, the fixture contracts), after adding the grading-time
    contract and reading every EndDate back. Raises FixtureError when that is not possible or
    a contract is not Activated."""
    state = fixture.load_state()
    state["contracts"].append(fixture.add_contract(state["connection_id"], state["account_id"], state["token"],
                                                   fixture.GRADING_DAYS, today))
    fixture.save_state(state)
    contracts = fixture.describe(state["connection_id"], state)
    fixture.save_state(state)
    unread = [c["label"] for c in contracts if not c.get("end_date")]
    if unread:
        raise fixture.FixtureError("EndDate not readable for " + ", ".join(unread))
    fixture.require_activated(contracts)
    return state["connection_id"], contracts


def run(workflow_path, inputs, deadline):
    """(raw output, None) or (None, error); one retry when time allows."""
    error = None
    for _ in range(2):
        remaining = deadline - time.monotonic()
        if remaining < 30:
            break
        ok, raw, error = run_workflow(workflow_path, inputs, timeout=int(min(RUN_TIMEOUT, remaining - 10)))
        if ok:
            return raw, None
        if error and PROVIDER_REFUSAL.search(error):
            raise InfraError(f"a provider refused the run: {error[:200]}")
    return None, error or "grading time budget used up"


def main(today=None):
    deadline = time.monotonic() + BUDGET_SECONDS
    today = today or datetime.date.today()
    try:
        connection, contracts = prepare(today)
    except (fixture.FixtureError, KeyError) as exc:
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
    foreign = sorted(bound_connections(workflow) - {str(connection).lower()})
    if foreign:
        print(f"INFRA: {shown} reads Salesforce through {', '.join(foreign)}, not {connection}, the connection "
              "the fixture was seeded through; this run says nothing about the workflow", file=sys.stderr)
        return INFRA_EXIT
    inputs = inputs_for(declared_inputs(workflow), today)
    effects = side_effects(workflow, fixture.CONNECTOR)
    if effects and not any(isinstance(value, bool) for value in inputs.values()):
        sys.exit(f"FAIL: {shown} would write to Salesforce or send something on every run ({'; '.join(effects)}) "
                 "and declares no input that turns that off, so it is not run: the prompt allows no emails, "
                 "messages or Salesforce changes while testing")

    try:
        raw, error = run(workflow_path, inputs, deadline)
    except InfraError as exc:
        print(f"INFRA: {exc}; this run says nothing about {shown}", file=sys.stderr)
        return INFRA_EXIT
    if error:
        sys.exit(f"FAIL: {shown} did not run with inputs {json.dumps(inputs)}: {error[:300]}")
    passed, problems, inside = verdict(contracts, raw, today)
    if not passed:
        sys.exit(f"FAIL: {shown}: {'; '.join(problems)} (inputs {json.dumps(inputs)})")
    print(f"OK: {shown}: returned all {inside} fixture contracts ending in the next 30 days and none of the others")
    return 0


if __name__ == "__main__":
    sys.exit(main())
