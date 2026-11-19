"""Unit tests for the EscalationJiraTicket effects grader.

The flow is cut down from what agents built on the 2026-11-17 nightly (manual
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
            "connectionId": "ac8506ff-65fd-4a7d-8698-c6a912134b11",
            "connectionFolderKey": "5da18ec0-7de1-4e57-aaf1-ddc8a369c199",
            "bodyParameters": {"fields.project.key": "CE", "fields.issuetype.id": "11457"},
        }
    },
}
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
    module.issues = {"CE-3481": {"summary": _summary(CASE, "Sev1"), "description": _adf(BODY)},
                     "CE-17": {"summary": "an older ticket"}}
    monkeypatch.setattr(module.jira_is, "connection_id", lambda: "conn")
    monkeypatch.setattr(module.jira_is, "get_issue", lambda conn, key: module.issues.get(key))
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
    grader.issues["CE-3482"] = {"summary": _summary(dup, "Sev3"), "description": _adf(BODY)}
    _check(grader, _payload())
    _check(grader, _payload(dup, key="CE-3482"), dup)
    assert (tmp_path / ".created_keys").read_text().split() == ["CE-3481", "CE-3482"]


def test_fails_when_the_key_is_not_in_jira(grader, tmp_path):
    with pytest.raises(SystemExit) as exc:
        _check(grader, _payload(key="CE-999999"))
    assert "reading CE-999999 back from Jira found no issue" in str(exc.value)
    assert (tmp_path / ".created_keys").read_text().split() == ["CE-999999"]


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
    (f"[TEST] [Sev1] {SUBJECT}", "lacks the case reference"),
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


def test_fails_when_engineering_needed_is_not_returned(grader):
    with pytest.raises(SystemExit) as exc:
        _check(grader, _payload(outputs={"engineeringRequired": None}))
    assert "(engineering needed)" in str(exc.value)


def test_main_opens_a_ticket_for_the_duplicate_too(grader, tmp_path, monkeypatch):
    dup = {**CASE, "name": "dup", "inputs": {**CASE["inputs"], "caseRef": "ESC-JIRA-1e90fee1-2",
                                             "tier": "Standard", "duplicate": True},
           "expected": {"severity": "Sev3", "engineering": False}}
    (tmp_path / "seed.json").write_text(json.dumps({"project_key": "CE", "cases": [CASE, dup]}))
    grader.issues["CE-3482"] = {"summary": _summary(dup, "Sev3"), "description": _adf(BODY)}
    payloads = iter([_payload(), _payload(dup, key="CE-3482")])
    fed = []

    def fake_debug(**kwargs):
        fed.append(kwargs["inputs"])
        return next(payloads)

    monkeypatch.setattr(grader, "run_debug", fake_debug)
    grader.main()
    assert [(f["customerTier"], f["isDuplicate"]) for f in fed] == [("Enterprise", False), ("Standard", True)]


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
    """A Studio Web build (2026-11-18, adhoc-2026-11-18_19-31-37) created the ticket
    with `uipath-atlassian-jira.insert-record` on the issue object, which completed."""
    node = {**CREATE_NODE, "type": "uipath.connector.uipath-atlassian-jira.insert-record",
            "inputs": {"detail": {**CREATE_NODE["inputs"]["detail"], "objectName": "issue", "endpoint": "/issue"}}}
    flow = _flow()
    flow["nodes"][1] = node
    (tmp_path / "EscalationJiraTicket" / "EscalationJiraTicket" / "EscalationJiraTicket.flow").write_text(json.dumps(flow))
    held = grader.check_case(flow, _payload(), CASE, "conn", "CE")
    assert held["ticket key"] == ["ticketKey"]
