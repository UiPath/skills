#!/usr/bin/env python3
"""One-time setup for the Jira release-notes golden scenario: create the epics and child
tickets that fixture.json describes, through the run user's Jira connection, move each
child to its fixture status, and write the new keys back into fixture.json.

Run it once per Jira site, signed in (`uip login`) to the tenant the golden runs use,
then commit fixture.json:

    python3 tests/tasks/uipath-api-workflow/golden/jira_release_notes/seed_jira_fixture.py

It refuses to run while fixture.json holds any key, so it never creates a second set.
Keys are saved after every created issue: after a failure, delete the issues listed in
fixture.json and set their keys back to null before seeding again.

Overrides: JIRA_CONNECTION_ID, JIRA_PROJECT_KEY, JIRA_EPIC_TYPE_ID, JIRA_TASK_TYPE_ID.
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_shared"))
from golden_connectors import InfraError, connection_id, data, dicts_in, field  # noqa: E402

JIRA = "uipath-atlassian-jira"
FIXTURE = Path(__file__).resolve().parent / "fixture.json"
CATEGORY ={"done": "done", "in_progress": "indeterminate"}


def project_id(conn, key):
    listed = data("is", "resources", "run", "list", JIRA, "project", "--connection-id", conn)
    for record in dicts_in(listed):
        if str(field(record, "key") or "").lower() == key.lower() and field(record, "id"):
            return str(field(record, "id"))
    raise InfraError(f"the connected account sees no Jira project {key}")


def issue_type_id(conn, name, project):
    """The project-scoped issue type called `name`, else a global one. A site holds one
    type per project with the same name, so a global id is used only when the project has
    none of its own."""
    listed = data("is", "resources", "run", "list", JIRA, "issuetype", "--connection-id", conn)
    named = [record for record in dicts_in(listed)
             if str(field(record, "name") or "").lower() == name.lower() and field(record, "id")]
    scoped = [r for r in named if str(field(field(field(r, "scope"), "project"), "id") or "") == project]
    unscoped = [r for r in named if not field(r, "scope")]
    chosen = scoped or unscoped
    if not chosen:
        raise InfraError(f"project {project} has no '{name}' issue type; set JIRA_{name.upper()}_TYPE_ID")
    return str(field(chosen[0], "id"))


def adf(text):
    """`text` as an Atlassian Document Format paragraph, for sites whose create schema
    rejects a plain-string description."""
    return {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": [{"type": "text", "text": text}]}]}


def create_issue(conn, fields, description=None):
    def attempt(extra):
        created = data("is", "resources", "run", "create", JIRA, "curated_create_issue", "--connection-id", conn,
                       "--body", json.dumps({"fields": {**fields, **extra}}))
        key = field(created, "key")
        if not key:
            raise InfraError(f"Jira created an issue but returned no key: {json.dumps(created)[:200]}")
        return key

    if description is None:
        return attempt({})
    try:
        return attempt({"description": description})
    except InfraError as plain_error:
        try:
            return attempt({"description": adf(description)})
        except InfraError:
            raise plain_error


def transition(conn, key, category):
    """Move `key` to a status in `category`, preferring one named Closed for "done"
    (the scenario asks for closed tickets)."""
    query = json.dumps({"issueIdOrKey": key})
    listed = data("is", "resources", "run", "list", JIRA, "issue_transitions", "--connection-id", conn,
                  "--query", query)
    options = [record for record in dicts_in(listed) if field(record, "id") and isinstance(field(record, "to"), dict)]

    def category_of(option):
        return str(field(field(field(option, "to"), "statusCategory"), "key") or "").lower()

    wanted = [option for option in options if category_of(option) == category]
    wanted.sort(key=lambda option: str(field(field(option, "to"), "name") or "").lower() != "closed")
    if not wanted:
        names = sorted({str(field(field(option, "to"), "name")) for option in options})
        raise InfraError(f"{key}: no transition to a '{category}' status (available: {', '.join(names) or 'none'})")
    data("is", "resources", "run", "create", JIRA, "issue_transitions", "--connection-id", conn,
         "--query", query, "--body", json.dumps({"transition": {"id": str(field(wanted[0], "id"))}}))
    return str(field(field(wanted[0], "to"), "name"))


def delete_issue(conn, key):
    data("is", "resources", "run", "delete", JIRA, "issue", "--connection-id", conn,
         "--query", json.dumps({"issueId": key}), "--yes")


def save(fixture):
    FIXTURE.write_text(json.dumps(fixture, indent=2, ensure_ascii=False) + "\n")


def main():
    fixture = json.loads(FIXTURE.read_text())
    seeded = [item["key"] for epic in fixture["epics"] for item in [epic, *epic["children"]] if item.get("key")]
    if seeded:
        sys.exit(f"fixture.json already holds keys ({', '.join(seeded)}); it is seeded")
    project = os.environ.get("JIRA_PROJECT_KEY") or fixture["project_key"]
    try:
        conn = os.environ.get("JIRA_CONNECTION_ID") or connection_id(JIRA)
        pid = project_id(conn, project)
        epic_type = os.environ.get("JIRA_EPIC_TYPE_ID") or issue_type_id(conn, "Epic", pid)
        task_type = os.environ.get("JIRA_TASK_TYPE_ID") or issue_type_id(conn, "Task", pid)
        fixture["project_key"] = project
        fixture["task_type_id"] = task_type
        for epic in fixture["epics"]:
            epic["key"] = create_issue(conn, {"project": {"key": project}, "issuetype": {"id": epic_type},
                                              "summary": epic["summary"]})
            save(fixture)
            print(f"epic {epic['key']}: {epic['summary']}")
            for child in epic["children"]:
                child["key"] = create_issue(conn, {"project": {"key": project}, "issuetype": {"id": task_type},
                                                   "summary": child["summary"], "parent": {"key": epic["key"]}},
                                            description=child["description"])
                save(fixture)
                status = transition(conn, child["key"], CATEGORY[child["status"]]) if child["status"] in CATEGORY \
                    else "left as created"
                print(f"  {child['key']} ({child['status']} -> {status}): {child['summary']}")
    except InfraError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        print("fixture.json lists the issues created so far; delete them and reset their keys to null "
              "before seeding again", file=sys.stderr)
        return 1
    print(f"Seeded {FIXTURE.name}; commit it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
