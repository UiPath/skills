"""Offline tests for the HITL live-run graders.

A fake `uip` on PATH plays the tenant: `maestro flow debug` logs the lines the
real CLI logs (maestro-tool 1.204: `Personal folder — key: …, id: …`,
`Debug session started — jobKey: …`, `Debug instance created — instanceId: …`)
and waits for the task; `tasks list|data get|complete|assign`, `login status`
and `debug-instance status|variables` answer in the real envelope shapes (the
`TaskList` row fields are those `uip tasks list` returned on the codereval
tenant, nightly 2026-11-18_04-23-44, skill-tasks-e2e-fetch-tasks).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import hitl_live_run as live  # noqa: E402

FAKE_UIP = textwrap.dedent(
    r'''
    #!/usr/bin/env python3
    import json, os, sys, time
    S = json.load(open(os.environ["FAKE_UIP_SCENARIO"]))
    STATE = os.environ["FAKE_UIP_STATE"]
    args = [a for a in sys.argv[1:]]
    def out(data, code="Ok", result="Success", rc=0):
        print(json.dumps({"Result": result, "Code": code, "Data": data})); sys.exit(rc)
    def state():
        return json.load(open(STATE)) if os.path.exists(STATE) else {}
    def fill(v, inputs):
        if isinstance(v, str):
            for k, x in inputs.items():
                v = v.replace("{" + k + "}", str(x))
            return v
        if isinstance(v, dict):
            return {k: fill(x, inputs) for k, x in v.items()}
        if isinstance(v, list):
            return [fill(x, inputs) for x in v]
        return v
    JOB, INST = "b2c3d4e5-0000-0000-0000-000000000001", "c3d4e5f6-0000-0000-0000-000000000001"
    if args[:3] == ["maestro", "flow", "debug"]:
        inputs = json.loads(args[args.index("--inputs") + 1])
        json.dump({"inputs": inputs}, open(STATE, "w"))
        sys.stderr.write("[info] Personal folder — key: 11111111-2222-3333-4444-555555555555, id: 42\n")
        sys.stderr.write(f"[info] Debug session started — jobKey: {JOB}\n")
        sys.stderr.write(f"[info] Debug instance created — instanceId: {INST}\n")
        sys.stderr.flush()
        if S.get("cli") == "suspend":
            time.sleep(1)
            out({"instanceId": INST, "jobKey": JOB, "finalStatus": "Suspended"}, result="Failure", rc=1)
        for _ in range(300):
            if state().get("action"):
                break
            time.sleep(0.2)
        st = state()
        out({"instanceId": INST, "jobKey": JOB, "finalStatus": "Completed",
             "elementExecutions": [{"elementId": e, "status": "Completed"} for e in S["executed"]],
             "variables": {"globals": fill(S["globals"], st["inputs"])}}, code="FlowDebug")
    st = state()
    inputs = st.get("inputs", {})
    if args[:2] == ["login", "status"]:
        out({"UserId": "a9da509e-82c6-4393-8e49-cedd00f5103c", "UserEmail": "bot@example.test"})
    if args[:2] == ["tasks", "list"]:
        rows = [{"Id": 100, "Status": "Pending", "Type": "AppTask", "Title": "Someone else's task",
                 "FolderId": 42, "CreatorJobKey": "00000000-0000-0000-0000-000000000000"}]
        if inputs:
            rows.append({"Id": 200, "Status": "Completed" if st.get("action") else "Unassigned",
                         "Type": S.get("task_type", "AppTask"), "Title": S.get("title", "Review"),
                         "FolderId": 42, "IsCompleted": bool(st.get("action")),
                         "CreatorJobKey": JOB if S.get("job_link", True) else "00000000-0000-0000-0000-000000000000",
                         "WaitJobKey": None, "AssignedToUserKey": None})
        out(rows, code="TaskList")
    if args[:3] == ["tasks", "data", "get"]:
        out(fill(S["task_data"], inputs) if args[3] == "200" else {"other": "x"}, code="TaskData")
    if args[:2] in (["tasks", "assign"], ["tasks", "reassign"]):
        out({"success": True})
    if args[:2] == ["tasks", "complete"]:
        action = args[args.index("--action") + 1]
        if action not in S.get("accept_actions", [action]):
            out(None, result="Failure", rc=1)
        st["action"] = action
        st["data"] = json.loads(args[args.index("--data") + 1])
        json.dump(st, open(STATE, "w"))
        out({"success": True}, code="TaskCompleted")
    if args[:3] == ["maestro", "flow", "debug-instance"]:
        verb = args[3]
        if verb == "status":
            done = bool(st.get("action"))
            out({"status": "Completed" if done else "Running",
                 "elementExecutions": [{"elementId": e, "status": "Completed"} for e in S["executed"]] if done else []})
        if verb == "variables":
            out({"globals": fill(S["globals"], inputs)})
        out([])
    out(None, result="Failure", rc=1)
    '''
).lstrip()

INVOICE_HITL = {
    "id": "financeApproval",
    "type": "uipath.human-in-the-loop.quick-form",
    "typeVersion": "1.0",
    "inputs": {
        "schema": {
            "fields": [
                {"id": "invoicenumber", "direction": "input", "type": "string", "binding": "vars.start.output.invoiceNumber"},
                {"id": "vendorname", "direction": "input", "type": "string", "binding": "vars.start.output.vendorName"},
                {"id": "totalamount", "direction": "input", "type": "number", "binding": "vars.start.output.totalAmount"},
                {"id": "currency", "direction": "input", "type": "string", "binding": "vars.start.output.currency"},
                {"id": "comments", "direction": "output", "type": "string"},
            ],
            "outcomes": [
                {"id": "approve", "name": "Approve", "type": "string", "isPrimary": True, "action": "Continue"},
                {"id": "reject", "name": "Reject", "type": "string", "isPrimary": False, "action": "Continue"},
            ],
        }
    },
}


def invoice_flow(reject_step: bool = False) -> dict:
    nodes = [
        {"id": "start", "type": "core.trigger.manual"},
        INVOICE_HITL,
        {"id": "postToSap", "type": "core.action.script", "inputs": {"script": "return {}"}},
        {"id": "end", "type": "core.control.end"},
        {"id": "end2", "type": "core.control.end"},
    ]
    edges = [
        {"sourceNodeId": "start", "sourcePort": "output", "targetNodeId": "financeApproval"},
        {"sourceNodeId": "financeApproval", "sourcePort": "outcome-approve", "targetNodeId": "postToSap"},
        {"sourceNodeId": "postToSap", "sourcePort": "success", "targetNodeId": "end"},
    ]
    if reject_step:
        nodes.append({"id": "notifyRejected", "type": "core.action.script", "inputs": {"script": "return {}"}})
        edges += [
            {"sourceNodeId": "financeApproval", "sourcePort": "outcome-reject", "targetNodeId": "notifyRejected"},
            {"sourceNodeId": "notifyRejected", "sourcePort": "success", "targetNodeId": "end2"},
        ]
    else:
        edges.append({"sourceNodeId": "financeApproval", "sourcePort": "outcome-reject", "targetNodeId": "end2"})
    return {"nodes": nodes, "edges": edges}


GOOD_INVOICE = {
    "executed": ["start", "financeApproval", "postToSap", "end"],
    "globals": {"invoiceNumber": "{invoiceNumber}", "status": "posted", "sapDocumentNumber": "SAP-{invoiceNumber}"},
    "task_data": {"invoicenumber": "{invoiceNumber}", "vendorname": "{vendorName}", "totalamount": 4870.25, "currency": "{currency}"},
    "task_type": "AppTask",
}

APP_HITL = {
    "id": "managerReview",
    "type": "uipath.human-in-the-loop.coded-action-app",
    "typeVersion": "1.0",
    "inputs": {
        "app": {"name": "ExpenseReviewApp", "key": "a30ac44f-8ebf-4124-9746-abc93a5ae17d",
                "folderPath": "Shared/uipath-agents/ExpenseReviewSol"},
        "appInputBindings": {"Content": "=js:`${$vars.start.output.expenseId} ...`"},
    },
}


def expense_flow(hitl: dict = APP_HITL) -> dict:
    return {
        "nodes": [
            {"id": "start", "type": "core.trigger.manual"},
            hitl,
            {"id": "postExpense", "type": "core.action.script",
             "inputs": {"script": 'return { sapDocumentNumber: "SAPEXP-" + $vars.start.output.expenseId };'}},
            {"id": "end", "type": "core.control.end"},
        ],
        "edges": [
            {"sourceNodeId": "start", "sourcePort": "output", "targetNodeId": hitl["id"]},
            {"sourceNodeId": hitl["id"], "sourcePort": "completed", "targetNodeId": "postExpense"},
            {"sourceNodeId": "postExpense", "sourcePort": "success", "targetNodeId": "end"},
        ],
    }


GOOD_EXPENSE = {
    "executed": ["start", "managerReview", "postExpense", "end"],
    "globals": {"status": "posted", "sapDocumentNumber": "SAPEXP-{expenseId}"},
    "task_data": {"Content": "Expense {expenseId}: {employeeName}, USD {amount}, {description}", "Comment": ""},
    "task_type": "AppTask",
    "accept_actions": ["approve"],
}


def run_check(tmp_path, script: str, flow: dict, scenario: dict, *args: str) -> subprocess.CompletedProcess:
    project = tmp_path / "Sol" / "Proj"
    project.mkdir(parents=True)
    (project / "project.uiproj").write_text(json.dumps({"Name": "Proj", "ProjectType": "Flow"}))
    (project / "Proj.flow").write_text(json.dumps(flow))
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake = bin_dir / "uip"
    fake.write_text(FAKE_UIP)
    fake.chmod(0o755)
    (tmp_path / "scenario.json").write_text(json.dumps(scenario))
    env = dict(os.environ)
    env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
    env["FAKE_UIP_SCENARIO"] = str(tmp_path / "scenario.json")
    env["FAKE_UIP_STATE"] = str(tmp_path / "state.json")
    return subprocess.run(
        [sys.executable, os.path.join(HERE, script), *args],
        cwd=tmp_path / "Sol",
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )


def state_of(tmp_path) -> dict:
    return json.loads((tmp_path / "state.json").read_text())


# ── invoice approval ────────────────────────────────────────────────────────

def test_invoice_approval_passes_when_the_task_shows_the_invoice_and_approve_posts(tmp_path):
    r = run_check(tmp_path, "check_hitl_invoice_approval_run.py", invoice_flow(), GOOD_INVOICE)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "OK: Action Center task 200" in r.stdout
    st = state_of(tmp_path)
    assert st["action"] == "Approve"
    assert st["data"]["comments"] == "Approved by the eval grader"
    assert st["data"]["invoicenumber"] == st["inputs"]["invoiceNumber"]


def test_invoice_approval_fails_when_the_task_hides_the_vendor(tmp_path):
    scenario = dict(GOOD_INVOICE, task_data={"invoicenumber": "{invoiceNumber}", "totalamount": 4870.25, "currency": "EUR"})
    r = run_check(tmp_path, "check_hitl_invoice_approval_run.py", invoice_flow(), scenario)
    assert r.returncode != 0
    assert "does not show the finance manager vendor" in r.stdout + r.stderr


def test_invoice_approval_fails_when_a_reject_only_step_runs(tmp_path):
    scenario = dict(GOOD_INVOICE, executed=["start", "financeApproval", "notifyRejected", "postToSap", "end"])
    r = run_check(tmp_path, "check_hitl_invoice_approval_run.py", invoice_flow(reject_step=True), scenario)
    assert r.returncode != 0
    assert "reachable only from Reject ran" in r.stdout + r.stderr


def test_invoice_approval_fails_when_nothing_on_the_approve_path_runs(tmp_path):
    scenario = dict(GOOD_INVOICE, executed=["start", "financeApproval", "end2"])
    r = run_check(tmp_path, "check_hitl_invoice_approval_run.py", invoice_flow(), scenario)
    assert r.returncode != 0
    assert "no step on the Approve path" in r.stdout + r.stderr


def test_invoice_approval_fails_on_a_wrong_document_number(tmp_path):
    scenario = dict(GOOD_INVOICE, globals={"status": "posted", "sapDocumentNumber": "5100012345"})
    r = run_check(tmp_path, "check_hitl_invoice_approval_run.py", invoice_flow(), scenario)
    assert r.returncode != 0
    assert "sapDocumentNumber" in r.stdout + r.stderr


def test_invoice_approval_follows_the_instance_when_the_cli_returns_suspended(tmp_path):
    scenario = dict(GOOD_INVOICE, cli="suspend")
    r = run_check(tmp_path, "check_hitl_invoice_approval_run.py", invoice_flow(), scenario)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "followed instance" in r.stdout


def test_invoice_approval_finds_the_task_by_its_data_without_a_job_key(tmp_path):
    scenario = dict(GOOD_INVOICE, job_link=False)
    r = run_check(tmp_path, "check_hitl_invoice_approval_run.py", invoice_flow(), scenario)
    assert r.returncode == 0, r.stdout + r.stderr


# ── expense app task ────────────────────────────────────────────────────────

def test_expense_app_task_passes_when_the_app_task_shows_the_expense(tmp_path):
    r = run_check(tmp_path, "check_hitl_expense_apptask_run.py", expense_flow(), GOOD_EXPENSE, "run")
    assert r.returncode == 0, r.stdout + r.stderr
    st = state_of(tmp_path)
    assert st["action"] == "approve"
    assert st["data"]["Comment"] == "Approved by the eval grader"
    assert st["inputs"]["expenseId"] in st["data"]["Content"]


def test_expense_app_task_fails_when_the_content_lacks_the_employee(tmp_path):
    scenario = dict(GOOD_EXPENSE, task_data={"Content": "Expense {expenseId}, {amount}"})
    r = run_check(tmp_path, "check_hitl_expense_apptask_run.py", expense_flow(), scenario, "run")
    assert r.returncode != 0
    assert "employee" in r.stdout + r.stderr


def test_expense_app_task_fails_when_posting_does_not_run(tmp_path):
    scenario = dict(GOOD_EXPENSE, executed=["start", "managerReview", "end"])
    r = run_check(tmp_path, "check_hitl_expense_apptask_run.py", expense_flow(), scenario, "run")
    assert r.returncode != 0
    assert "posting step" in r.stdout + r.stderr


def test_expense_structure_refuses_a_quick_form_substitute(tmp_path):
    quick = {"id": "managerReview", "type": "uipath.human-in-the-loop.quick-form",
             "inputs": {"schema": {"fields": [{"id": "note", "label": "ExpenseReviewApp"}]}}}
    r = run_check(tmp_path, "check_hitl_expense_apptask_run.py", expense_flow(quick), GOOD_EXPENSE, "structure")
    assert r.returncode != 0
    assert "backed by the deployed ExpenseReviewApp" in r.stdout + r.stderr


def test_expense_structure_accepts_the_app_by_key_alone(tmp_path):
    by_key = dict(APP_HITL, inputs={"app": {"key": "a30ac44f-8ebf-4124-9746-abc93a5ae17d"}})
    r = run_check(tmp_path, "check_hitl_expense_apptask_run.py", expense_flow(by_key), GOOD_EXPENSE, "structure")
    assert r.returncode == 0, r.stdout + r.stderr


# ── pure helpers ────────────────────────────────────────────────────────────

def test_run_ids_read_the_cli_log_lines():
    ids = live.RunIds()
    ids.read(
        "[info] Personal folder — key: 0a1b2c3d-0000-4000-8000-000000000001, id: 2815972\n"
        "[info] Debug session started — jobKey: 0a1b2c3d-0000-4000-8000-000000000002\n"
        "[info] Debug instance created — instanceId: 0a1b2c3d-0000-4000-8000-000000000003\n"
    )
    assert (ids.folder_id, ids.job_key, ids.instance_id) == (
        "2815972",
        "0a1b2c3d-0000-4000-8000-000000000002",
        "0a1b2c3d-0000-4000-8000-000000000003",
    )


@pytest.mark.parametrize("value", [4870.25, "4870.25", "EUR 4,870.25", {"x": ["4870.250"]}])
def test_has_amount_reads_numbers_and_text(value):
    assert live.has_amount(value, 4870.25)


@pytest.mark.parametrize("value", [4870, "4870.2", "48702.5", True])
def test_has_amount_rejects_other_amounts(value):
    assert not live.has_amount(value, 4870.25)


def test_row_job_keys_ignore_the_empty_guid():
    row = {"CreatorJobKey": "00000000-0000-0000-0000-000000000000", "TaskSource": {"SourceId": "ABC"}}
    assert live.row_job_keys(row) == {"abc"}
