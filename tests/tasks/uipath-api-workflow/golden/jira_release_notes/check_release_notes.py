#!/usr/bin/env python3
"""Golden scenario: run the agent's release-notes workflow on the fixture epics
(fixture.json) and check what it returns.

Right before running the workflow the grader adds one more closed ticket under the first
epic (GRADING_TICKET) and deletes it afterwards, so a workflow that hardcodes the notes for
what it read while authoring cannot pass. The prompt does not say how the epics are passed
in, so the epic keys are tried as a list, as one comma-separated string, and one epic per
run (outputs merged), as the workflow's declared input allows (`epic_plans`). Pass: the
output holds a list of notes with a summary and a description each, names every closed
ticket (by its marker word) and none of the tickets that are not closed. The output is
saved to OUTPUT_FILE for the task's llm_judge, which scores whether it looks like release
notes for a product feature.

INFRA (exit INFRA_EXIT): the fixture is not seeded, a fixture ticket changed status, the
grading-time ticket cannot be created, or a provider refused for load or quota. coder_eval
still scores INFRA as a failed criterion, so leave INFRA runs out of reported pass rates.
"""
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_shared"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import seed_jira_fixture as seed  # noqa: E402
from golden_connectors import (  # noqa: E402
    INFRA_EXIT, PROVIDER_REFUSAL, InfraError, connection_id, data, decode_json_string, declared_inputs, dicts_in,
    field, find_workflow, run_workflow, strings_in,
)

JIRA = "uipath-atlassian-jira"
FIXTURE = Path(__file__).resolve().parent / "fixture.json"
OUTPUT_FILE = Path("golden-output/release_notes.json")
GRADING_TICKET = {
    "status": "done",
    "summary": "Approve invoices from the Pelican inbox",
    "description": "Approvers see every invoice that waits for them in the new Pelican inbox and approve it in one click.",
    "markers": ["Pelican"],
}
BUDGET_SECONDS = 390
RUN_TIMEOUT = 150
SEARCH_ATTEMPTS = 6
SEARCH_PAUSE_SECONDS = 5
EPIC_INPUT = re.compile(r"epic|key|issue|ticket|parent", re.IGNORECASE)
SUMMARY_KEY = re.compile(r"summar|title|headline|name", re.IGNORECASE)
DESCRIPTION_KEY = re.compile(r"descr|detail|body|note|text|content", re.IGNORECASE)
CATEGORY ={"done": "done", "in_progress": "indeterminate", "todo": "new"}


def load_fixture(path=FIXTURE):
    fixture = json.loads(Path(path).read_text())
    issues = [item for epic in fixture.get("epics") or [] for item in [epic, *epic.get("children", [])]]
    unseeded = [item.get("summary") for item in issues if not item.get("key")]
    if not issues or unseeded:
        raise InfraError(f"fixture.json is not seeded ({len(unseeded)} of {len(issues)} issues have no key); "
                         "run seed_jira_fixture.py once")
    return fixture


def children(fixture):
    return [child for epic in fixture["epics"] for child in epic["children"]]


def status_drift(fixture, found):
    """Fixture tickets whose live status category differs from fixture.json, given an
    `issue_search_get` payload."""
    expected = {child["key"]: CATEGORY[child["status"]] for child in children(fixture)}
    drift = []
    for record in dicts_in(found):
        key = field(record, "key")
        category = field(field(field(field(record, "fields"), "status"), "statusCategory"), "key")
        if key in expected and category and str(category).lower() != expected[key]:
            drift.append(f"{key} is {category}, fixture.json says {expected[key]}")
    return drift


def check_fixture_statuses(fixture):
    """INFRA when someone moved a fixture ticket (reopened a closed one): the expected
    notes would be wrong. Best effort: a search that cannot run only warns."""
    keys = ", ".join(child["key"] for child in children(fixture))
    try:
        found = data("is", "resources", "run", "list", JIRA, "issue_search_get", "--connection-id",
                     connection_id(JIRA), "--query", json.dumps({"jql": f"key in ({keys})", "pageSize": 50}))
    except InfraError as exc:
        print(f"WARNING: could not verify the fixture's statuses ({exc})", file=sys.stderr)
        return
    drift = status_drift(fixture, found)
    if drift:
        raise InfraError("fixture tickets changed status: " + "; ".join(drift))


def wait_until_searchable(conn, epic_key, key):
    """Jira's search index trails a write by a few seconds; wait until a search for the
    epic's children sees `key`. A connection that cannot search gets a fixed pause."""
    query = json.dumps({"jql": f"parent = {epic_key} AND key = {key}", "pageSize": 5})
    for _ in range(SEARCH_ATTEMPTS):
        try:
            found = data("is", "resources", "run", "list", JIRA, "issue_search_get", "--connection-id", conn,
                         "--query", query)
        except InfraError:
            time.sleep(2 * SEARCH_PAUSE_SECONDS)
            return
        if any(field(record, "key") == key for record in dicts_in(found)):
            return
        time.sleep(SEARCH_PAUSE_SECONDS)
    raise InfraError(f"{key} never showed up in a search for the children of {epic_key}")


def add_grading_ticket(fixture):
    """Create GRADING_TICKET closed under the first epic and add it to the fixture's
    children. Returns (connection id, key) for remove_grading_ticket."""
    conn = connection_id(JIRA)
    epic = fixture["epics"][0]
    project = fixture["project_key"]
    task_type = fixture.get("task_type_id") or seed.issue_type_id(conn, "Task", seed.project_id(conn, project))
    key = seed.create_issue(conn, {"project": {"key": project}, "issuetype": {"id": task_type},
                                   "summary": GRADING_TICKET["summary"], "parent": {"key": epic["key"]}},
                            description=GRADING_TICKET["description"])
    try:
        seed.transition(conn, key, "done")
        wait_until_searchable(conn, epic["key"], key)
    except InfraError:
        remove_grading_ticket(conn, key)
        raise
    epic["children"].append({**GRADING_TICKET, "key": key})
    return conn, key


def remove_grading_ticket(conn, key):
    try:
        seed.delete_issue(conn, key)
    except InfraError as exc:
        print(f"WARNING: could not delete the grading-time ticket {key} ({exc}); delete it by hand",
              file=sys.stderr)


def epic_plans(declared, epic_keys):
    """Ways to hand the epic keys to the workflow, most likely first. Each plan is the list
    of input sets to run, one run or one per epic, whose outputs are merged."""
    names = list(declared)
    target = next((name for name in names if EPIC_INPUT.search(name)), names[0] if len(names) == 1 else None)
    if target is None:
        return []
    kind = declared[target].get("type")
    as_list = [{target: list(epic_keys)}]
    as_text = [{target: ", ".join(epic_keys)}]
    one_each = [{target: key} for key in epic_keys]
    if kind == "array":
        return [as_list]
    if kind == "string":
        return [as_text, one_each] if len(epic_keys) > 1 else [one_each]
    return [as_list, as_text, one_each]


def lists_in(value):
    """Every list in `value` at any depth, looking inside strings that hold JSON."""
    if isinstance(value, str):
        decoded = decode_json_string(value)
        if decoded is not None:
            yield from lists_in(decoded)
    elif isinstance(value, dict):
        for item in value.values():
            yield from lists_in(item)
    elif isinstance(value, list):
        yield value
        for item in value:
            yield from lists_in(item)


def is_note(item):
    """An object with a non-empty summary-like string and a separate description-like one."""
    if not isinstance(item, dict):
        return False
    texts = [key for key, value in item.items() if isinstance(value, str) and value.strip()]
    summaries = [key for key in texts if SUMMARY_KEY.search(key)]
    descriptions = [key for key in texts if DESCRIPTION_KEY.search(key) and key not in summaries]
    return bool(summaries and descriptions)


def note_entries(raw):
    """The longest list of release notes anywhere in the output."""
    best = []
    for candidate in lists_in(raw):
        entries = [item for item in candidate if is_note(item)]
        if len(entries) > len(best):
            best = entries
    return best


def mentions(text, marker):
    return re.search(rf"(?<!\w){re.escape(marker.lower())}(?!\w)", text) is not None


def verdict(raw, fixture):
    """(passed, problems, number of notes) for one merged workflow output."""
    entries = note_entries(raw)
    text = "\n".join(strings_in(raw)).lower()
    closed = [child for child in children(fixture) if child["status"] == "done"]
    others = [child for child in children(fixture) if child["status"] != "done"]
    missing = [child["key"] for child in closed if not any(mentions(text, m) for m in child["markers"])]
    leaked = [child["key"] for child in others if any(mentions(text, m) for m in child["markers"])]
    problems = []
    if not entries:
        problems.append("no list of release notes with a summary and a description")
    if missing:
        problems.append(f"closed tickets missing: {', '.join(missing)}")
    if leaked:
        problems.append(f"tickets that are not closed included: {', '.join(leaked)}")
    return not problems, problems, len(entries)


def write_for_judge(raw, fixture, error=None, path=OUTPUT_FILE):
    def ticket(child):
        return {"key": child["key"], "summary": child["summary"], "description": child["description"]}

    payload = {
        "workflow_output": raw,
        "closed_tickets": [ticket(child) for child in children(fixture) if child["status"] == "done"],
        "tickets_to_leave_out": [ticket(child) for child in children(fixture) if child["status"] != "done"],
    }
    if error:
        payload["run_error"] = error
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))


def run_plan(workflow_path, plan, deadline):
    """(merged raw output, None) or (None, error) for one plan."""
    outputs = []
    for inputs in plan:
        remaining = deadline - time.monotonic()
        if remaining < 30:
            return None, "grading time budget used up"
        ok, raw, error = run_workflow(workflow_path, inputs, timeout=int(min(RUN_TIMEOUT, remaining - 10)))
        if not ok:
            if error and PROVIDER_REFUSAL.search(error):
                raise InfraError(f"a provider refused the run: {error[:200]}")
            return None, error
        outputs.append(raw)
    return (outputs[0] if len(outputs) == 1 else outputs), None


def grade(workflow_path, plans, fixture, deadline):
    """(passed, message, raw output of the plan reported)."""
    tried, best = [], None
    for plan in plans:
        raw, error = run_plan(workflow_path, plan, deadline)
        shown = json.dumps(plan)[:160]
        if error:
            tried.append(f"{shown} -> {error[:160]}")
            continue
        passed, problems, count = verdict(raw, fixture)
        if passed:
            return True, f"{count} release notes cover every closed ticket and nothing else (inputs {shown})", raw
        best = best or (f"{'; '.join(problems)} (inputs {shown})", raw)
        tried.append(f"{shown} -> {'; '.join(problems)}")
    if best is None:
        return False, "no input shape ran: " + " | ".join(tried), None
    return False, best[0], best[1]


def main():
    deadline = time.monotonic() + BUDGET_SECONDS
    try:
        fixture = load_fixture()
        check_fixture_statuses(fixture)
    except InfraError as exc:
        print(f"INFRA: {exc}; this run says nothing about the workflow", file=sys.stderr)
        return INFRA_EXIT

    workflow_path = find_workflow()
    if workflow_path is None:
        write_for_judge(None, fixture, "no Workflow.json inside a project folder")
        sys.exit("FAIL: no Workflow.json inside a project folder")
    shown = workflow_path.relative_to(Path.cwd().resolve())
    try:
        workflow = json.loads(workflow_path.read_text())
    except (OSError, ValueError) as exc:
        write_for_judge(None, fixture, f"{shown} is not readable JSON")
        sys.exit(f"FAIL: {shown} is not readable JSON: {exc}")
    plans = epic_plans(declared_inputs(workflow), [epic["key"] for epic in fixture["epics"]])
    if not plans:
        write_for_judge(None, fixture, f"{shown} declares no input for the epic keys")
        sys.exit(f"FAIL: {shown} declares no input for the epic keys")

    try:
        conn, grading_key = add_grading_ticket(fixture)
    except InfraError as exc:
        print(f"INFRA: the grading-time ticket was not created: {exc}", file=sys.stderr)
        return INFRA_EXIT
    try:
        passed, message, raw = grade(workflow_path, plans, fixture, deadline)
    except InfraError as exc:
        print(f"INFRA: {exc}; this run says nothing about {shown}", file=sys.stderr)
        return INFRA_EXIT
    finally:
        remove_grading_ticket(conn, grading_key)
    write_for_judge(raw, fixture, None if raw is not None else message)
    if not passed:
        sys.exit(f"FAIL: {shown}: {message}")
    print(f"OK: {shown}: {message}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
