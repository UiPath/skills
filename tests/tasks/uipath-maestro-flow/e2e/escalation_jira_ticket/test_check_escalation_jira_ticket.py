"""Unit tests for the EscalationJiraTicket effects grader.

The flow is cut down from what agents built in nightly runs (manual
trigger, the real `create-issue` node bound to the CE connection, End), with
input and output names a v3 agent might pick. The Create step's response has
the shape those runs returned (`id`, `key`, `self`). The Jira tenant is faked
at the `jira_is` boundary: `get_issue` returns the issue's `fields` like the
curated read does, or None when the key does not exist.
"""

from __future__ import annotations

import importlib.util
import json
import os
import runpy
import sys
import types

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REF = "ESC-JIRA-1e90fee1-1"
SUBJECT = "Production down: checkout API returning 500s"
BODY = "Critical outage since 09:15 UTC. All checkout requests fail with HTTP 500."
CASE = {
    "name": "enterprise-down-no-workaround-sev1",
    "inputs": {"senderEmail": "jane.doe@acmecorp.com", "senderDomain": "acmecorp.com", "subject": SUBJECT,
               "body": BODY, "tier": "Enterprise", "productionDown": True, "workaround": False,
               "attachments": False, "match": "single", "duplicate": False, "caseRef": REF},
    "expected": {"severity": "Sev1", "engineering": True},
}
CREATE_NODE = {
    "id": "openTicket",
    "type": "uipath.connector.uipath-atlassian-jira.create-issue",
    "inputs": {
        "detail": {
            "connector": "uipath-atlassian-jira",
            "endpoint": "/curated_create_issue",
            "connectionId": "00000000-0000-0000-0000-00000000a001",
            "connectionFolderKey": "5da18ec0-7de1-4e57-aaf1-ddc8a369c199",
            "bodyParameters": {"fields.project.key": "CE", "fields.issuetype.id": "11457"},
        }
    },
}
TASK = {"name": "Task", "id": "11457", "subtask": False, "hierarchyLevel": 0}
WORKSTREAM = {**TASK, "name": "Workstream", "id": "11456"}
INS = [("senderEmail", "string"), ("senderDomain", "string"), ("emailSubject", "string"),
       ("emailBody", "string"), ("customerTier", "string"), ("isProductionDown", "boolean"),
       ("hasWorkaround", "boolean"), ("hasAttachments", "boolean"), ("matchType", "string"),
       ("isDuplicate", "boolean"), ("caseReference", "string")]
OUTS = [("severity", "string"), ("engineeringRequired", "boolean"), ("caseRef", "string"),
        ("ticketKey", "string")]


def _flow(ins=INS) -> dict:
    return {
        "nodes": [{"id": "start", "type": "core.trigger.manual"}, CREATE_NODE,
                  {"id": "end", "type": "core.control.end"}],
        "edges": [],
        "variables": {"globals": [
            *({"id": i, "direction": "in", "type": t, "triggerNodeId": "start"} for i, t in ins),
            *({"id": o, "direction": "out", "type": t} for o, t in OUTS),
        ]},
    }


def _adf(text: str) -> dict:
    return {"type": "doc", "version": 1,
            "content": [{"type": "paragraph", "content": [{"type": "text", "text": text}]}]}


def _summary(case: dict, severity: str) -> str:
    return f"[TEST] [{severity}] {case['inputs']['caseRef']} {case['inputs']['subject']}"


@pytest.fixture
def grader(tmp_path, monkeypatch):
    project = tmp_path / "EscalationJiraTicket" / "EscalationJiraTicket"
    project.mkdir(parents=True)
    (project / "project.uiproj").write_text(json.dumps({"Name": "EscalationJiraTicket", "ProjectType": "Flow"}))
    (project / "EscalationJiraTicket.flow").write_text(json.dumps(_flow()))
    monkeypatch.chdir(tmp_path)
    spec = importlib.util.spec_from_file_location(
        "check_escalation_jira_ticket", os.path.join(HERE, "check_escalation_jira_ticket.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.issues = {"CE-3481": {"summary": _summary(CASE, "Sev1"), "description": _adf(BODY), "issuetype": TASK},
                     "CE-17": {"summary": "an older ticket"}}
    monkeypatch.setattr(module.jira_is, "connection_id", lambda: "conn")
    monkeypatch.setattr(module.jira_is, "get_issue", lambda conn, key: module.issues.get(key))
    monkeypatch.setattr(module.jira_is, "issue_absent", lambda conn, key: key not in module.issues)
    return module


def _payload(case=CASE, *, key="CE-3481", outputs=None, executed=("start", "openTicket", "end")):
    globals_ = {"severity": case["expected"]["severity"], "engineeringRequired": case["expected"]["engineering"],
                "caseRef": case["inputs"]["caseRef"], "ticketKey": key,
                "start.output.caseReference": case["inputs"]["caseRef"],
                "openTicket.output": {"id": "52114", "key": key, "self": f"https://x/rest/api/3/issue/{key}"}}
    globals_.update(outputs or {})
    return {
        "finalStatus": "Completed",
        "elementExecutions": [{"elementId": i, "status": "Completed"} for i in executed],
        "variables": {"globals": globals_},
    }


def _check(grader, payload, case=CASE):
    return grader.check_case(_flow(), payload, case, "conn", "CE")


def test_seeded_values_map_onto_the_agents_inputs(grader):
    assert grader.feed(_flow(), CASE) == {
        "senderEmail": "jane.doe@acmecorp.com", "senderDomain": "acmecorp.com", "emailSubject": SUBJECT,
        "emailBody": BODY, "customerTier": "Enterprise", "isProductionDown": True, "hasWorkaround": False,
        "hasAttachments": False, "matchType": "single", "isDuplicate": False, "caseReference": REF,
    }


def test_a_flow_without_a_subject_input_fails_naming_its_inputs(grader):
    with pytest.raises(SystemExit) as exc:
        grader.feed(_flow([(i, t) for i, t in INS if i != "emailSubject"]), CASE)
    assert "could not map subject onto inputs ['senderEmail'" in str(exc.value)


def test_passes_and_records_the_key(grader, tmp_path):
    holders = _check(grader, _payload())
    assert holders == {"ticket key": ["ticketKey"], "severity": ["severity"],
                       "engineering needed": ["engineeringRequired"], "case reference": ["caseRef"]}
    assert (tmp_path / ".created_keys").read_text().split() == ["CE-3481"]


def test_keys_from_every_case_are_kept_for_teardown(grader, tmp_path):
    dup = {**CASE, "name": "dup", "inputs": {**CASE["inputs"], "caseRef": "ESC-JIRA-1e90fee1-2",
                                             "tier": "Standard", "duplicate": True},
           "expected": {"severity": "Sev3", "engineering": False}}
    grader.issues["CE-3482"] = {"summary": _summary(dup, "Sev3"), "description": _adf(BODY), "issuetype": TASK}
    _check(grader, _payload())
    _check(grader, _payload(dup, key="CE-3482"), dup)
    assert (tmp_path / ".created_keys").read_text().split() == ["CE-3481", "CE-3482"]


def test_fails_when_the_key_is_not_in_jira(grader, tmp_path):
    with pytest.raises(SystemExit) as exc:
        _check(grader, _payload(key="CE-999999"))
    assert "no CE key the Jira steps returned (['CE-999999']) reads back" in str(exc.value)
    assert not (tmp_path / ".created_keys").exists()


def test_only_the_ticket_carrying_the_case_ref_is_recorded_for_teardown(grader, tmp_path):
    """A flow that searches CE for duplicates returns other runs' keys; teardown
    must not delete those from the shared project."""
    insert = {**CREATE_NODE, "id": "openTicket", "type": "uipath.connector.uipath-atlassian-jira.insert-record",
              "inputs": {"detail": {**CREATE_NODE["inputs"]["detail"], "objectName": "issue", "endpoint": "/issue"}}}
    search = {**CREATE_NODE, "id": "findDuplicates", "type": "uipath.connector.uipath-atlassian-jira.search-issues",
              "inputs": {"detail": {**CREATE_NODE["inputs"]["detail"], "endpoint": "/search"}}}
    flow = _flow()
    flow["nodes"][1:2] = [search, insert]
    (tmp_path / "EscalationJiraTicket" / "EscalationJiraTicket" / "EscalationJiraTicket.flow").write_text(json.dumps(flow))
    payload = _payload(executed=("start", "findDuplicates", "openTicket", "end"))
    payload["variables"]["globals"]["findDuplicates.output"] = {
        "issues": [{"id": "10017", "key": "CE-17", "self": "https://x/rest/api/3/issue/CE-17"}]}
    held = grader.check_case(flow, payload, CASE, "conn", "CE")
    assert held["ticket key"] == ["ticketKey"]
    assert (tmp_path / ".created_keys").read_text().split() == ["CE-3481"]


def test_fails_when_the_returned_key_is_not_the_one_the_create_step_made(grader):
    payload = _payload()
    payload["variables"]["globals"]["ticketKey"] = "CE-17"
    with pytest.raises(SystemExit) as exc:
        _check(grader, payload)
    assert "no declared output is the created key ['CE-3481'] (ticket key)" in str(exc.value)


def test_fails_when_the_create_step_did_not_run(grader):
    with pytest.raises(SystemExit) as exc:
        _check(grader, _payload(executed=("start", "end")))
    assert "no Jira step completed" in str(exc.value)


@pytest.mark.parametrize("summary,why", [
    (f"[Sev1] {REF} {SUBJECT}", "does not start with '[TEST]'"),
    (f"[TEST] {REF} {SUBJECT}", "lacks the severity"),
    (f"[TEST] [Sev1] {SUBJECT}", "whose title carries the case reference"),
    (f"[TEST] {REF} [Sev1] {SUBJECT}", "in that order"),
])
def test_fails_when_the_title_is_not_in_the_asked_format(grader, summary, why):
    grader.issues["CE-3481"]["summary"] = summary
    with pytest.raises(SystemExit) as exc:
        _check(grader, _payload())
    assert why in str(exc.value)


def test_fails_when_the_description_is_not_the_email_body(grader):
    grader.issues["CE-3481"]["description"] = _adf("Escalation from jane.doe@acmecorp.com")
    with pytest.raises(SystemExit) as exc:
        _check(grader, _payload())
    assert "does not hold the email body" in str(exc.value)


def test_a_plain_text_description_counts(grader):
    grader.issues["CE-3481"]["description"] = f"Customer wrote:\n{BODY}"
    _check(grader, _payload())


@pytest.mark.parametrize("issuetype", [{"name": "Bug"}, {"name": "Story"}, None])
def test_fails_when_the_ticket_is_not_a_task(grader, issuetype):
    grader.issues["CE-3481"]["issuetype"] = issuetype
    with pytest.raises(SystemExit) as exc:
        _check(grader, _payload())
    assert "is not a Task" in str(exc.value)


def test_a_wrong_type_ticket_with_the_case_ref_is_still_journaled(grader, tmp_path):
    grader.issues["CE-3481"]["issuetype"] = WORKSTREAM
    with pytest.raises(SystemExit) as exc:
        _check(grader, _payload())
    assert "is not a Task (issue type 'Workstream')" in str(exc.value)
    assert (tmp_path / ".created_keys").read_text().split() == ["CE-3481"]


def test_a_missing_description_fails_as_not_holding_the_body(grader):
    del grader.issues["CE-3481"]["description"]
    with pytest.raises(SystemExit) as exc:
        _check(grader, _payload())
    assert "does not hold the email body" in str(exc.value)


def test_one_failed_read_is_retried(grader, monkeypatch, tmp_path):
    reads = []

    def flaky(conn, key):
        reads.append(key)
        if len(reads) == 1:
            raise RuntimeError("uip is resources run get returned invalid JSON")
        return grader.issues.get(key)

    monkeypatch.setattr(grader.jira_is, "get_issue", flaky)
    _check(grader, _payload())
    assert (tmp_path / ".created_keys").read_text().split() == ["CE-3481"]


@pytest.mark.parametrize("failure", ["raises", "returns_none"])
def test_a_persistent_read_error_is_a_grader_error_and_journals_nothing(grader, monkeypatch, tmp_path, capsys, failure):
    def broken(conn, key):
        if failure == "raises":
            raise RuntimeError("uip is resources run get returned invalid JSON")

    monkeypatch.setattr(grader.jira_is, "get_issue", broken)
    monkeypatch.setattr(grader.jira_is, "issue_absent", lambda conn, key: False)
    with pytest.raises(SystemExit) as exc:
        _check(grader, _payload())
    assert exc.value.code == grader.io.GRADER_ERROR_EXIT
    err = capsys.readouterr().err
    assert "GRADER ERROR" in err and "CE-3481" in err
    assert not (tmp_path / ".created_keys").exists()


def test_an_unread_key_beside_an_owned_one_is_noted_not_journaled(grader, monkeypatch, tmp_path, capsys):
    grader.issues["CE-3490"] = {"summary": _summary(CASE, "Sev1")}
    real = grader.jira_is.get_issue

    def read(conn, key):
        if key == "CE-3490":
            raise RuntimeError("invalid JSON")
        return real(conn, key)

    monkeypatch.setattr(grader.jira_is, "get_issue", read)
    monkeypatch.setattr(grader.jira_is, "issue_absent", lambda conn, key: False)
    payload = _payload()
    payload["variables"]["globals"]["openTicket.output"] = {"key": "CE-3481", "other": "CE-3490"}
    _check(grader, payload)
    out = capsys.readouterr().out
    assert "NOTE" in out and "CE-3490" in out
    assert (tmp_path / ".created_keys").read_text().split() == ["CE-3481"]


def test_a_partial_output_key_that_cannot_be_read_is_noted_not_journaled(grader, monkeypatch, tmp_path, capsys):
    def broken(conn, key):
        raise RuntimeError("invalid JSON")

    monkeypatch.setattr(grader.jira_is, "get_issue", broken)
    monkeypatch.setattr(grader.jira_is, "issue_absent", lambda conn, key: False)
    monkeypatch.setattr(grader, "get_last_debug_raw", lambda: "created CE-3481")
    assert grader._record_partial(SystemExit(1), "conn", REF, "CE") == []
    out = capsys.readouterr().out
    assert "NOTE" in out and "CE-3481" in out
    assert not (tmp_path / ".created_keys").exists()


def test_fails_when_engineering_needed_is_not_returned(grader):
    with pytest.raises(SystemExit) as exc:
        _check(grader, _payload(outputs={"engineeringRequired": None}))
    assert "(engineering needed)" in str(exc.value)


def test_main_opens_a_ticket_for_the_duplicate_too(grader, tmp_path, monkeypatch):
    dup = {**CASE, "name": "dup", "inputs": {**CASE["inputs"], "caseRef": "ESC-JIRA-1e90fee1-2",
                                             "tier": "Standard", "duplicate": True},
           "expected": {"severity": "Sev3", "engineering": False}}
    (tmp_path / "seed.json").write_text(json.dumps({"project_key": "CE", "cases": [CASE, dup]}))
    grader.issues["CE-3482"] = {"summary": _summary(dup, "Sev3"), "description": _adf(BODY), "issuetype": TASK}
    payloads = iter([_payload(), _payload(dup, key="CE-3482")])
    fed = []

    def fake_debug(**kwargs):
        fed.append(kwargs["inputs"])
        return next(payloads)

    monkeypatch.setattr(grader, "run_debug", fake_debug)
    grader.main()
    assert [(f["customerTier"], f["isDuplicate"]) for f in fed] == [("Enterprise", False), ("Standard", True)]


def test_main_fails_when_no_one_output_holds_the_result_in_every_case(grader, tmp_path, monkeypatch):
    dup = {**CASE, "name": "dup", "inputs": {**CASE["inputs"], "caseRef": "ESC-JIRA-1e90fee1-2"}}
    (tmp_path / "seed.json").write_text(json.dumps({"project_key": "CE", "cases": [CASE, dup]}))
    names = iter(["constantA", "constantB"])
    monkeypatch.setattr(grader, "run_debug", lambda **kw: _payload())
    monkeypatch.setattr(grader, "check_case", lambda *a, **kw: {"severity": [next(names)]})
    with pytest.raises(SystemExit) as exc:
        grader.main()
    assert "no single output holds the severity in every case" in str(exc.value)


def test_tickets_from_every_debug_attempt_are_recorded(grader, tmp_path, monkeypatch):
    (tmp_path / "seed.json").write_text(json.dumps({"project_key": "CE", "cases": [CASE]}))
    grader.issues["CE-9001"] = {"summary": _summary(CASE, "Sev1"), "description": _adf(BODY), "issuetype": TASK}
    grader.issues["CE-9002"] = {"summary": _summary(CASE, "Sev1"), "description": _adf(BODY), "issuetype": TASK}
    monkeypatch.setattr(grader, "get_debug_attempt_raws", lambda: ["created CE-9001", "created CE-9002"])
    monkeypatch.setattr(grader, "run_debug", lambda **kw: _payload())
    grader.main()
    assert set((tmp_path / ".created_keys").read_text().split()) == {"CE-9001", "CE-9002", "CE-3481"}


def test_seed_preflights_jira_and_expects_v3_severities(tmp_path, monkeypatch):
    calls = []
    stub = types.SimpleNamespace(
        PROJECT_KEY="CE",
        connection_id=lambda: calls.append("connection") or "conn",
        issuetype_id=lambda conn: calls.append("issuetype") or "11457",
    )
    monkeypatch.setitem(sys.modules, "jira_is", stub)
    monkeypatch.chdir(tmp_path)
    runpy.run_path(os.path.join(HERE, "_setup", "seed.py"))
    seed = json.loads((tmp_path / "seed.json").read_text())
    assert calls == ["connection", "issuetype"]
    got = {(c["inputs"]["tier"], c["inputs"]["duplicate"]): (c["expected"]["severity"], c["expected"]["engineering"])
           for c in seed["cases"]}
    assert got == {("Enterprise", False): ("Sev1", True), ("Standard", True): ("Sev3", False)}
    assert all(c["inputs"]["productionDown"] and not c["inputs"]["workaround"] for c in seed["cases"])


def test_seed_ends_the_run_when_jira_is_unreachable(tmp_path, monkeypatch):
    def forbidden(conn):
        raise RuntimeError("uip is resources run list project failed: 403 Forbidden")

    stub = types.SimpleNamespace(PROJECT_KEY="CE", connection_id=lambda: "conn", issuetype_id=forbidden)
    monkeypatch.setitem(sys.modules, "jira_is", stub)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(RuntimeError, match="403"):
        runpy.run_path(os.path.join(HERE, "_setup", "seed.py"))
    assert not (tmp_path / "seed.json").exists()


def test_a_ticket_created_by_the_generic_insert_record_op_counts(grader, tmp_path):
    """A Studio Web build may create the ticket with
    `uipath-atlassian-jira.insert-record` on the issue object."""
    node = {**CREATE_NODE, "type": "uipath.connector.uipath-atlassian-jira.insert-record",
            "inputs": {"detail": {**CREATE_NODE["inputs"]["detail"], "objectName": "issue", "endpoint": "/issue"}}}
    flow = _flow()
    flow["nodes"][1] = node
    (tmp_path / "EscalationJiraTicket" / "EscalationJiraTicket" / "EscalationJiraTicket.flow").write_text(json.dumps(flow))
    held = grader.check_case(flow, _payload(), CASE, "conn", "CE")
    assert held["ticket key"] == ["ticketKey"]
