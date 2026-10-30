#!/usr/bin/env python3
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_shared"))
from golden_connectors import (  # noqa: E402
    INFRA_EXIT, PROVIDER_REFUSAL, InfraError, brief, choose_workflow, connection_id, connection_map, data,
    decode_json_string, declared_inputs, declared_outputs, dicts_in, field, run_workflow, side_effects, strings_in,
)

JIRA = "uipath-atlassian-jira"
FIXTURE = Path(__file__).resolve().parent / "fixture.json"
OUTPUT_FILE = Path("golden-output/release_notes.json")
BUDGET_SECONDS = 390
RUN_TIMEOUT = 150
EPIC_INPUT = re.compile(r"epic|key|issue|ticket|parent", re.IGNORECASE)
NOTES_OUTPUT = re.compile(r"note", re.IGNORECASE)
SUMMARY_KEY = re.compile(r"summar|title|headline|name", re.IGNORECASE)
DESCRIPTION_KEY = re.compile(r"descr|detail|body|note|text|content", re.IGNORECASE)
WORD_BREAK = r"[\s\-\u2010-\u2015]"
JUDGE_NOTES = 40
JUDGE_SUMMARY_CHARS = 300
JUDGE_DESCRIPTION_CHARS = 1500
CATEGORY = {"done": "done", "in_progress": "indeterminate", "todo": "new"}


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


def fixture_drift(fixture, found):
    expected = {child["key"]: (child, epic["key"]) for epic in fixture["epics"] for child in epic["children"]}
    drift, seen = [], set()
    for record in dicts_in(found):
        key = field(record, "key")
        if not isinstance(key, str) or key not in expected or key in seen:
            continue
        seen.add(key)
        child, epic_key = expected[key]
        fields = field(record, "fields")
        category = field(field(field(fields, "status"), "statusCategory"), "key")
        summary = field(fields, "summary")
        parent = field(field(fields, "parent"), "key")
        if category and str(category).lower() != CATEGORY[child["status"]]:
            drift.append(f"{key} is {category}, fixture.json says {CATEGORY[child['status']]}")
        if summary is not None and summary != child["summary"]:
            drift.append(f"{key} is titled {summary!r}, fixture.json says {child['summary']!r}")
        if parent is not None and parent != epic_key:
            drift.append(f"{key} is under {parent}, fixture.json says {epic_key}")
    return drift


def extra_children(fixture, found):
    epics = {epic["key"] for epic in fixture["epics"]}
    known = {child["key"] for child in children(fixture)}
    extra = set()
    for record in dicts_in(found):
        key = field(record, "key")
        parent = field(field(field(record, "fields"), "parent"), "key")
        if isinstance(key, str) and isinstance(parent, str) and parent in epics and key not in known:
            extra.add(key)
    return sorted(extra)


def check_fixture(fixture):
    epics = ", ".join(epic["key"] for epic in fixture["epics"])
    keys = ", ".join(child["key"] for child in children(fixture))
    query = {"jql": f"key in ({keys}) OR parent in ({epics})", "pageSize": 50}
    try:
        found = data("is", "resources", "run", "list", JIRA, "issue_search_get", "--connection-id",
                     connection_id(JIRA), "--query", json.dumps(query))
    except InfraError as exc:
        print(f"WARNING: could not verify the fixture tickets ({exc})", file=sys.stderr)
        return
    drift = fixture_drift(fixture, found)
    if drift:
        raise InfraError("fixture tickets changed: " + "; ".join(drift) + "; set them back as fixture.json says")
    extra = extra_children(fixture, found)
    if extra:
        print(f"WARNING: {', '.join(extra)} sit under the fixture epics but fixture.json does not list them; "
              "delete them if a run created them", file=sys.stderr)


def copied_tickets(workflow_text, fixture):
    text = workflow_text.lower()
    return [child["key"] for child in children(fixture)
            if re.search(rf"(?<!\w){re.escape(child['key'].lower())}(?!\d)", text)
            or child["summary"].lower() in text or child["description"].lower() in text]


def epic_input(declared):
    names = list(declared)
    return next((name for name in names if EPIC_INPUT.search(name)), names[0] if len(names) == 1 else None)


def pick_workflow(root="."):
    return choose_workflow(lambda workflow: epic_input(declared_inputs(workflow)) is not None,
                           lambda workflow: any(NOTES_OUTPUT.search(name) for name in declared_outputs(workflow)),
                           root)


def epic_plans(declared, epic_keys):
    target = epic_input(declared)
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
    if not isinstance(item, dict):
        return False
    texts = [key for key, value in item.items() if isinstance(value, str) and value.strip()]
    summaries = [key for key in texts if SUMMARY_KEY.search(key)]
    descriptions = [key for key in texts if DESCRIPTION_KEY.search(key) and key not in summaries]
    return bool(summaries and descriptions)


def note_entries(raw):
    best = []
    for candidate in lists_in(raw):
        entries = [item for item in candidate if is_note(item)]
        if len(entries) > len(best):
            best = entries
    return best


def mentions(text, marker):
    words = [re.escape(word) for word in re.split(f"{WORD_BREAK}+", marker.lower()) if word]
    if not words:
        return False
    joined = f"{WORD_BREAK}*".join(words)
    return re.search(rf"(?<!\w){joined}(?!\w)", text) is not None


def names(ticket, text):
    key = re.escape(str(ticket.get("key") or "").lower())
    if key and re.search(rf"(?<!\w){key}(?!\d)", text):
        return True
    return any(mentions(text, marker) for marker in ticket["markers"])


def verdict(raw, fixture):
    entries = note_entries(raw)
    text = "\n".join(strings_in(raw)).lower()
    closed = [child for child in children(fixture) if child["status"] == "done"]
    others = [child for child in children(fixture) if child["status"] != "done"]
    missing = [child["key"] for child in closed if not names(child, text)]
    leaked = [child["key"] for child in others if names(child, text)]
    problems = []
    if not entries:
        problems.append("no list of release notes with a summary and a description")
    if missing:
        problems.append(f"closed tickets missing: {', '.join(missing)}")
    if leaked:
        problems.append(f"tickets that are not closed included: {', '.join(leaked)}")
    return not problems, problems, len(entries)


def first_epic_verdict(raw, fixture):
    _, problems, _ = verdict(raw, {**fixture, "epics": fixture["epics"][:1]})
    text = "\n".join(strings_in(raw)).lower()
    foreign = [child["key"] for epic in fixture["epics"][1:] for child in epic["children"] if names(child, text)]
    if foreign:
        problems.append(f"tickets of another epic included: {', '.join(foreign)}")
    return not problems, problems


def judged_notes(raw, fixture):
    notes = []
    for entry in note_entries(raw):
        text = "\n".join(strings_in(entry)).lower()
        tickets = [child["key"] for child in children(fixture) if names(child, text)]
        if not tickets:
            continue
        texts = [(key, value) for key, value in entry.items() if isinstance(value, str) and value.strip()]
        summary = next(value for key, value in texts if SUMMARY_KEY.search(key))
        description = next(value for key, value in texts if DESCRIPTION_KEY.search(key) and not SUMMARY_KEY.search(key))
        notes.append({"summary": summary[:JUDGE_SUMMARY_CHARS], "description": description[:JUDGE_DESCRIPTION_CHARS],
                      "tickets": tickets})
        if len(notes) == JUDGE_NOTES:
            break
    return notes


def write_for_judge(raw, fixture, error=None, path=OUTPUT_FILE):
    def ticket(child):
        return {"key": child["key"], "summary": child["summary"], "description": child["description"]}

    payload = {
        "release_notes": None if raw is None else judged_notes(raw, fixture),
        "closed_tickets": [ticket(child) for child in children(fixture) if child["status"] == "done"],
        "tickets_to_leave_out": [ticket(child) for child in children(fixture) if child["status"] != "done"],
    }
    if error:
        payload["run_error"] = str(error)[:JUDGE_SUMMARY_CHARS]
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))


def run_plan(workflow_path, plan, deadline):
    outputs = []
    for inputs in plan:
        remaining = deadline - time.monotonic()
        if remaining < 30:
            return None, "grading time budget used up"
        ok, raw, error = run_workflow(workflow_path, inputs, timeout=int(min(RUN_TIMEOUT, remaining - 10)))
        if not ok:
            if error and PROVIDER_REFUSAL.search(error):
                raise InfraError("a provider refused the run")
            return None, brief(error)
        outputs.append(raw)
    return outputs, None


def first_epic_inputs(plan, epic_key):
    target, value = next(iter(plan[0].items()))
    return {target: [epic_key] if isinstance(value, list) else epic_key}


def grade(workflow_path, plans, fixture, deadline):
    tried, best = [], None
    first_key = fixture["epics"][0]["key"]
    for plan in plans:
        outputs, error = run_plan(workflow_path, plan, deadline)
        shown = json.dumps(plan)[:160]
        if error:
            tried.append(f"{shown} -> {error}")
            continue
        raw = outputs[0] if len(outputs) == 1 else outputs
        passed, problems, count = verdict(raw, fixture)
        if passed:
            alone = outputs
            if len(plan) == 1:
                alone, error = run_plan(workflow_path, [first_epic_inputs(plan, first_key)], deadline)
            if error:
                return False, f"the run on {first_key} alone failed: {error} (inputs {shown})", raw
            passed, problems = first_epic_verdict(alone[0], fixture)
            if not passed:
                return False, f"on {first_key} alone: {'; '.join(problems)} (inputs {shown})", raw
            return True, (f"{count} release notes cover every closed ticket and nothing else, and {first_key} "
                          f"alone gets only its own (inputs {shown})"), raw
        best = best or (f"{'; '.join(problems)} (inputs {shown})", raw)
        tried.append(f"{shown} -> {'; '.join(problems)}")
    if best is None:
        return False, "no input shape ran: " + " | ".join(tried), None
    return False, best[0], best[1]


def main():
    deadline = time.monotonic() + BUDGET_SECONDS
    try:
        fixture = load_fixture()
        check_fixture(fixture)
        connections = connection_map()
    except InfraError as exc:
        print(f"INFRA: {exc}; this run says nothing about the workflow", file=sys.stderr)
        return INFRA_EXIT

    workflow_path = pick_workflow()
    if workflow_path is None:
        write_for_judge(None, fixture, "no Workflow.json inside a project folder")
        sys.exit("FAIL: no Workflow.json inside a project folder")
    shown = workflow_path.relative_to(Path.cwd().resolve())
    try:
        text = workflow_path.read_text()
        workflow = json.loads(text)
    except (OSError, ValueError) as exc:
        write_for_judge(None, fixture, f"{shown} is not readable JSON")
        sys.exit(f"FAIL: {shown} is not readable JSON: {exc}")
    copied = copied_tickets(text, fixture)
    if copied:
        write_for_judge(None, fixture, f"{shown} holds fixture ticket text")
        sys.exit(f"FAIL: {shown} holds the key, summary or description of {', '.join(copied)}: "
                 "notes copied in while authoring")
    effects = side_effects(workflow, JIRA, connections)
    if effects:
        write_for_judge(None, fixture, f"{shown} would change Jira or send something")
        sys.exit(f"FAIL: {shown} would change Jira or send something on every run ({'; '.join(effects)}), so it "
                 "is not run: release notes only read Jira, and the fixture tickets are shared")
    plans = epic_plans(declared_inputs(workflow), [epic["key"] for epic in fixture["epics"]])
    if not plans:
        write_for_judge(None, fixture, f"{shown} declares no input for the epic keys")
        sys.exit(f"FAIL: {shown} declares no input for the epic keys")

    try:
        passed, message, raw = grade(workflow_path, plans, fixture, deadline)
    except InfraError as exc:
        print(f"INFRA: {exc}; this run says nothing about {shown}", file=sys.stderr)
        return INFRA_EXIT
    write_for_judge(raw, fixture, None if raw is not None else message)
    if not passed:
        sys.exit(f"FAIL: {shown}: {message}")
    print(f"OK: {shown}: {message}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
