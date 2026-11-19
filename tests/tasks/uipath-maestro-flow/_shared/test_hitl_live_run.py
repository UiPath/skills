"""Offline tests for the HITL live-run graders.

A fake `uip` on PATH plays the tenant: `maestro flow debug` logs the lines the
real CLI logs (maestro-tool 1.204: `Personal folder — key: …, id: …`,
`Debug session started — jobKey: …`, `Debug instance created — instanceId: …`)
and waits for the task; `tasks list|data get|complete|assign`, `login status`
and `debug-instance status|variables` answer in the real envelope shapes (the
`TaskList` row fields are those `uip tasks list` returns on the codereval
tenant; `tasks data get` prints the whole task record with the form under
`Data`; an app task sits in the app's folder, not the personal folder;
completing a task nobody is assigned fails with "This action is no longer
assigned to you" until `tasks assign`). A scenario's `on_reject` gives what a
run answered with Reject executes and returns.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
import time

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
        R = S.get("on_reject", {}) if "reject" in st["action"].lower() else {}
        out({"instanceId": INST, "jobKey": JOB, "finalStatus": "Completed",
             "elementExecutions": [{"elementId": e, "status": "Completed"} for e in R.get("executed", S["executed"])],
             "variables": {"globals": fill(R.get("globals", S["globals"]), st["inputs"])}}, code="FlowDebug")
    st = state()
    inputs = st.get("inputs", {})
    R = S.get("on_reject", {}) if "reject" in str(st.get("action", "")).lower() else {}
    if args[:2] == ["login", "status"]:
        out({"UserId": "a9da509e-82c6-4393-8e49-cedd00f5103c", "UserEmail": "bot@example.test"})
    TASK_PATH = S.get("task_folder_path")  # None: the run's personal folder
    TASK_FOLDER = 3278005 if TASK_PATH else 42
    def task_row():
        return {"Id": 200, "Status": "Completed" if st.get("action") else "Unassigned",
                "Type": S.get("task_type", "AppTask"), "Title": S.get("title", "Review"),
                "FolderId": TASK_FOLDER, "IsCompleted": bool(st.get("action")),
                "CreatorJobKey": JOB if S.get("job_link", True) else "00000000-0000-0000-0000-000000000000",
                "WaitJobKey": None, "AssignedToUserKey": None}
    if args[:2] == ["tasks", "list"]:
        path = args[args.index("--folder-path") + 1] if "--folder-path" in args else None
        fid = args[args.index("--folder-id") + 1] if "--folder-id" in args else None
        rows = []
        if fid in (None, "42") and not path:
            rows.append({"Id": 100, "Status": "Pending", "Type": "AppTask", "Title": "Someone else's task",
                         "FolderId": 42, "CreatorJobKey": "00000000-0000-0000-0000-000000000000"})
            if S.get("foreign_newer"):
                rows.append({"Id": 300, "Status": "Pending", "Type": S.get("task_type", "AppTask"),
                             "Title": "Another run's task", "FolderId": 42,
                             "CreatorJobKey": "d4e5f6a7-0000-0000-0000-000000000009"})
        in_scope = (fid is None and path is None) or (path == TASK_PATH if path else fid == str(TASK_FOLDER))
        if inputs and in_scope:
            rows.append(task_row())
        out(rows, code="TaskList")
    if args[:3] == ["tasks", "data", "get"]:
        if args[3] == "300" and S.get("foreign_newer"):
            out({"Status": "Pending", "Id": 300, "Data": fill(S["task_data"], dict(inputs, **S["foreign_newer"]))},
                code="TaskData")
        if args[3] != "200":
            out({"Status": "Pending", "Id": int(args[3]), "Data": {"other": "x"}}, code="TaskData")
        record = dict(task_row(), Action=None, TaskSource={"SourceName": "Maestro", "SourceId": JOB},
                      OrganizationUnitFullyQualifiedName=TASK_PATH or "bot's workspace",
                      Data=fill(S["task_data"], inputs))
        out(record, code="TaskData")
    if args[:2] in (["tasks", "assign"], ["tasks", "reassign"]):
        st["assigned"] = True
        json.dump(st, open(STATE, "w"))
        out({"success": True})
    if args[:2] == ["tasks", "complete"]:
        action = args[args.index("--action") + 1]
        if not st.get("assigned"):
            print(json.dumps({"Result": "Failure", "Message": "Error completing task '200'",
                              "Instructions": "This action is no longer assigned to you"}))
            sys.exit(1)
        if args[2] != "200" or args[args.index("--folder-id") + 1] != str(TASK_FOLDER):
            out(None, result="Failure", rc=1)
        if action not in S.get("accept_actions", [action]):
            out(None, result="Failure", rc=1)
        st["action"] = action
        st["data"] = json.loads(args[args.index("--data") + 1])
        json.dump(st, open(STATE, "w"))
        with open(STATE + ".log", "a") as log:
            log.write(json.dumps(st) + "\n")
        out({"success": True}, code="TaskCompleted")
    if args[:3] == ["maestro", "flow", "debug-instance"]:
        verb = args[3]
        if verb == "status":
            done = bool(st.get("action"))
            out({"status": S.get("final_status", "Completed") if done else "Running",
                 "elementExecutions": [{"elementId": e, "status": "Completed"}
                                       for e in R.get("executed", S["executed"])] if done else []})
        if verb == "variables":
            out({"globals": fill(R.get("globals", S["globals"]), inputs)})
        if verb == "cancel":
            st["cancelled"] = True
            json.dump(st, open(STATE, "w"))
            out({"success": True})
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
        {"id": "postToSap", "type": "core.action.script",
         "inputs": {"script": 'return { sapDocumentNumber: "SAP-" + $vars.start.output.invoiceNumber };'}},
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
    # Action Center shows field `invoicenumber` as `Invoicenumber`
    "task_data": {"Invoicenumber": "{invoiceNumber}", "Vendorname": "{vendorName}", "Totalamount": 4870.25, "Currency": "{currency}"},
    "task_type": "QuickFormTask",
    "on_reject": {"executed": ["start", "financeApproval", "end2"],
                  "globals": {"invoiceNumber": "{invoiceNumber}", "status": "rejected", "sapDocumentNumber": ""}},
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


POST_EXPENSE = {"id": "postExpense", "type": "core.action.script",
                "inputs": {"script": 'return { sapDocumentNumber: "SAPEXP-" + $vars.start.output.expenseId };'}}


def expense_flow(hitl: dict = APP_HITL) -> dict:
    """The fixture's start -> postExpense -> end, with the review and a
    decision on its outcome put in front of the posting."""
    return {
        "nodes": [
            {"id": "start", "type": "core.trigger.manual"},
            hitl,
            {"id": "isApproved", "type": "core.logic.decision",
             "inputs": {"expression": f"$vars.{hitl['id']}.status === 'approve'"}},
            POST_EXPENSE,
            {"id": "end", "type": "core.control.end"},
            {"id": "endRejected", "type": "core.control.end"},
        ],
        "edges": [
            {"sourceNodeId": "start", "sourcePort": "output", "targetNodeId": hitl["id"]},
            {"sourceNodeId": hitl["id"], "sourcePort": "completed", "targetNodeId": "isApproved"},
            {"sourceNodeId": "isApproved", "sourcePort": "true", "targetNodeId": "postExpense"},
            {"sourceNodeId": "isApproved", "sourcePort": "false", "targetNodeId": "endRejected"},
            {"sourceNodeId": "postExpense", "sourcePort": "success", "targetNodeId": "end"},
        ],
    }


GOOD_EXPENSE = {
    "executed": ["start", "managerReview", "isApproved", "postExpense", "end"],
    "globals": {"status": "posted", "sapDocumentNumber": "SAPEXP-{expenseId}"},
    "task_data": {"Content": "Expense {expenseId}: {employeeName}, USD {amount}, {description}", "Comment": ""},
    "task_type": "AppTask",
    "accept_actions": ["approve", "reject"],
    "on_reject": {"executed": ["start", "managerReview", "isApproved", "endRejected"],
                  "globals": {"status": "rejected"}},
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


def completions(tmp_path) -> list[dict]:
    """The state after each task completion, in order: one per debug run."""
    log = tmp_path / "state.json.log"
    return [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []


# ── invoice approval ────────────────────────────────────────────────────────

def test_invoice_approval_passes_when_the_task_shows_the_invoice_and_approve_posts(tmp_path):
    r = run_check(tmp_path, "check_hitl_invoice_approval_run.py", invoice_flow(), GOOD_INVOICE)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "OK: Action Center task 200" in r.stdout
    approved, rejected = completions(tmp_path)
    assert approved["action"] == "Approve"
    assert approved["data"] == {
        "Invoicenumber": approved["inputs"]["invoiceNumber"],
        "Vendorname": "Northwind Office Supplies",
        "Totalamount": 4870.25,
        "Currency": "EUR",
        "Comments": "Approved by the eval grader",
    }
    assert rejected["action"] == "Reject"
    assert rejected["data"]["Comments"] == "Rejected by the eval grader"
    assert rejected["inputs"]["invoiceNumber"] != approved["inputs"]["invoiceNumber"]


def test_invoice_approval_fails_when_the_task_hides_the_vendor(tmp_path):
    scenario = dict(GOOD_INVOICE, task_data={"Invoicenumber": "{invoiceNumber}", "Totalamount": 4870.25, "Currency": "EUR"})
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


def test_invoice_approval_only_warns_when_a_prep_step_before_the_approval_builds_the_number(tmp_path):
    flow = invoice_flow()
    flow["edges"] = [
        {"sourceNodeId": "start", "sourcePort": "output", "targetNodeId": "postToSap"},
        {"sourceNodeId": "postToSap", "sourcePort": "success", "targetNodeId": "financeApproval"},
        {"sourceNodeId": "financeApproval", "sourcePort": "outcome-approve", "targetNodeId": "end"},
        {"sourceNodeId": "financeApproval", "sourcePort": "outcome-reject", "targetNodeId": "end2"},
    ]
    scenario = dict(GOOD_INVOICE, executed=["start", "postToSap", "financeApproval", "end"],
                    on_reject={"executed": ["start", "postToSap", "financeApproval", "end2"],
                               "globals": {"status": "rejected", "sapDocumentNumber": ""}})
    r = run_check(tmp_path, "check_hitl_invoice_approval_run.py", flow, scenario)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "WARN: the SAP step(s) ['postToSap'] can run without" in r.stdout


def test_invoice_approval_fails_when_a_rejection_still_posts(tmp_path):
    scenario = dict(GOOD_INVOICE, on_reject={"executed": ["start", "financeApproval", "postToSap", "end"],
                                             "globals": {"status": "rejected", "sapDocumentNumber": ""}})
    r = run_check(tmp_path, "check_hitl_invoice_approval_run.py", invoice_flow(), scenario)
    assert r.returncode != 0
    assert "reachable only from Approve ran after a rejection: ['postToSap']" in r.stdout + r.stderr


def shared_posting_flow() -> dict:
    flow = invoice_flow()
    flow["edges"] = [
        {"sourceNodeId": "start", "sourcePort": "output", "targetNodeId": "financeApproval"},
        {"sourceNodeId": "financeApproval", "sourcePort": "outcome-approve", "targetNodeId": "postToSap"},
        {"sourceNodeId": "financeApproval", "sourcePort": "outcome-reject", "targetNodeId": "postToSap"},
        {"sourceNodeId": "postToSap", "sourcePort": "success", "targetNodeId": "end"},
    ]
    return flow


def test_invoice_approval_passes_when_the_reject_branch_returns_an_empty_document_number(tmp_path):
    reject_end = {"id": "end2", "type": "core.control.end", "outputs": {"sapDocumentNumber": {
        "var": "sapDocumentNumber",
        "source": {"type": "jsExpression", "expression": "$vars.notifyRejected.output.sapDocumentNumber"}}}}
    reject_step = {"id": "notifyRejected", "type": "core.action.script",
                   "inputs": {"script": 'return { sapDocumentNumber: "" };'}}
    flow = invoice_flow(reject_step=True)
    flow["nodes"] = [{"end2": reject_end, "notifyRejected": reject_step}.get(n["id"], n) for n in flow["nodes"]]
    scenario = dict(GOOD_INVOICE, on_reject={"executed": ["start", "financeApproval", "notifyRejected", "end2"],
                                             "globals": {"status": "rejected", "sapDocumentNumber": ""}})
    r = run_check(tmp_path, "check_hitl_invoice_approval_run.py", flow, scenario)
    assert r.returncode == 0, r.stdout + r.stderr


def test_invoice_approval_passes_when_a_shared_step_ran_on_a_rejection_with_rejected_outputs(tmp_path):
    scenario = dict(GOOD_INVOICE, on_reject={"executed": ["start", "financeApproval", "postToSap", "end"],
                                             "globals": {"status": "rejected", "sapDocumentNumber": ""}})
    r = run_check(tmp_path, "check_hitl_invoice_approval_run.py", shared_posting_flow(), scenario)
    assert r.returncode == 0, r.stdout + r.stderr


def test_invoice_approval_fails_when_a_rejection_posts_through_a_shared_step(tmp_path):
    scenario = dict(GOOD_INVOICE, on_reject={"executed": ["start", "financeApproval", "postToSap", "end"],
                                             "globals": {"status": "rejected", "sapDocumentNumber": "SAP-{invoiceNumber}"}})
    r = run_check(tmp_path, "check_hitl_invoice_approval_run.py", shared_posting_flow(), scenario)
    assert r.returncode != 0
    assert "must be empty after a rejection" in r.stdout + r.stderr


def test_invoice_approval_passes_with_one_script_that_sets_both_outputs_on_either_decision(tmp_path):
    script = ('const approved = $vars.financeApproval.output.decision === "approve"; '
              'return { status: approved ? "posted" : "rejected", '
              'sapDocumentNumber: approved ? "SAP-" + $vars.start.output.invoiceNumber : "" };')
    flow = shared_posting_flow()
    flow["nodes"] = [dict(n, inputs={"script": script}) if n["id"] == "postToSap" else n for n in flow["nodes"]]
    scenario = dict(GOOD_INVOICE, on_reject={"executed": ["start", "financeApproval", "postToSap", "end"],
                                             "globals": {"status": "rejected", "sapDocumentNumber": ""}})
    r = run_check(tmp_path, "check_hitl_invoice_approval_run.py", flow, scenario)
    assert r.returncode == 0, r.stdout + r.stderr


def assembled_marker_flow(posting: dict, end_expression: str, edges: list[dict]) -> dict:
    return {
        "nodes": [
            {"id": "start", "type": "core.trigger.manual"},
            INVOICE_HITL,
            posting,
            {"id": "end", "type": "core.control.end",
             "outputs": {"sapDocumentNumber": {"var": "sapDocumentNumber",
                                               "source": {"type": "jsExpression", "expression": end_expression}}}},
            {"id": "end2", "type": "core.control.end"},
        ],
        "edges": edges,
    }


POST_FIRST = [
    {"sourceNodeId": "start", "sourcePort": "output", "targetNodeId": "postToSap"},
    {"sourceNodeId": "postToSap", "sourcePort": "success", "targetNodeId": "financeApproval"},
    {"sourceNodeId": "financeApproval", "sourcePort": "outcome-approve", "targetNodeId": "end"},
    {"sourceNodeId": "financeApproval", "sourcePort": "outcome-reject", "targetNodeId": "end2"},
]


@pytest.mark.parametrize("globals_,why", [
    ({"status": "posted", "sapDocumentNumber": ""}, "expected 'rejected'"),
    ({"status": "rejected", "sapDocumentNumber": "SAP-{invoiceNumber}"}, "must be empty after a rejection"),
])
def test_invoice_approval_fails_when_a_rejection_returns_the_wrong_outputs(tmp_path, globals_, why):
    scenario = dict(GOOD_INVOICE, on_reject={"executed": ["start", "financeApproval", "end2"], "globals": globals_})
    r = run_check(tmp_path, "check_hitl_invoice_approval_run.py", invoice_flow(), scenario)
    assert r.returncode != 0
    assert why in r.stdout + r.stderr


def test_invoice_approval_picks_its_own_task_over_a_newer_one_for_another_invoice(tmp_path):
    scenario = dict(GOOD_INVOICE, job_link=False, foreign_newer={"invoiceNumber": "INV-0THERRUN"})
    r = run_check(tmp_path, "check_hitl_invoice_approval_run.py", invoice_flow(), scenario)
    assert r.returncode == 0, r.stdout + r.stderr
    assert [c["action"] for c in completions(tmp_path)] == ["Approve", "Reject"]


def test_invoice_approval_cancels_a_run_that_did_not_complete(tmp_path):
    scenario = dict(GOOD_INVOICE, cli="suspend", final_status="Faulted")
    r = run_check(tmp_path, "check_hitl_invoice_approval_run.py", invoice_flow(), scenario)
    assert r.returncode != 0
    assert "did not complete" in r.stdout + r.stderr
    assert state_of(tmp_path).get("cancelled") is True


# ── expense app task ────────────────────────────────────────────────────────

def test_expense_app_task_passes_when_the_app_task_shows_the_expense(tmp_path):
    r = run_check(tmp_path, "check_hitl_expense_apptask_run.py", expense_flow(), GOOD_EXPENSE, "run")
    assert r.returncode == 0, r.stdout + r.stderr
    st, rejected = completions(tmp_path)
    assert st["action"] == "approve"
    assert set(st["data"]) == {"Content", "Comment"}
    assert st["data"]["Comment"] == "Approved by the eval grader"
    assert st["inputs"]["expenseId"] in st["data"]["Content"]
    assert rejected["action"] == "reject"


def test_expense_app_task_is_found_and_completed_in_the_app_folder(tmp_path):
    scenario = dict(GOOD_EXPENSE, task_folder_path="Shared/uipath-agents/ExpenseReviewSol")
    r = run_check(tmp_path, "check_hitl_expense_apptask_run.py", expense_flow(), scenario, "run")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "OK: app task 200" in r.stdout
    assert [c["action"] for c in completions(tmp_path)] == ["approve", "reject"]


def test_expense_app_task_fails_when_the_content_lacks_the_employee(tmp_path):
    scenario = dict(GOOD_EXPENSE, task_data={"Content": "Expense {expenseId}, {amount}"})
    r = run_check(tmp_path, "check_hitl_expense_apptask_run.py", expense_flow(), scenario, "run")
    assert r.returncode != 0
    assert "employee" in r.stdout + r.stderr


def test_expense_app_task_fails_when_the_content_lacks_the_description(tmp_path):
    scenario = dict(GOOD_EXPENSE, task_data={"Content": "Expense {expenseId}: {employeeName}, USD {amount}"})
    r = run_check(tmp_path, "check_hitl_expense_apptask_run.py", expense_flow(), scenario, "run")
    assert r.returncode != 0
    assert "description" in r.stdout + r.stderr


def test_expense_app_task_fails_when_posting_does_not_run(tmp_path):
    scenario = dict(GOOD_EXPENSE, executed=["start", "managerReview", "end"])
    r = run_check(tmp_path, "check_hitl_expense_apptask_run.py", expense_flow(), scenario, "run")
    assert r.returncode != 0
    assert "posting step" in r.stdout + r.stderr


def test_expense_app_task_fails_when_posting_runs_before_the_review(tmp_path):
    flow = expense_flow()
    flow["edges"] = [
        {"sourceNodeId": "start", "sourcePort": "output", "targetNodeId": "postExpense"},
        {"sourceNodeId": "postExpense", "sourcePort": "success", "targetNodeId": "managerReview"},
        {"sourceNodeId": "managerReview", "sourcePort": "completed", "targetNodeId": "end"},
    ]
    scenario = dict(GOOD_EXPENSE, executed=["start", "postExpense", "managerReview", "end"],
                    on_reject={"executed": ["start", "postExpense", "managerReview", "end"],
                               "globals": {"status": "rejected"}})
    r = run_check(tmp_path, "check_hitl_expense_apptask_run.py", flow, scenario, "run")
    assert r.returncode != 0
    assert "can run without the manager's review" in r.stdout + r.stderr


def test_expense_app_task_fails_when_a_rejection_still_posts(tmp_path):
    scenario = dict(GOOD_EXPENSE, on_reject={"executed": ["start", "managerReview", "isApproved", "postExpense", "end"],
                                             "globals": {"status": "rejected"}})
    r = run_check(tmp_path, "check_hitl_expense_apptask_run.py", expense_flow(), scenario, "run")
    assert r.returncode != 0
    assert "ran after a rejection" in r.stdout + r.stderr


def test_expense_app_task_fails_when_a_rejection_is_not_reported_rejected(tmp_path):
    scenario = dict(GOOD_EXPENSE, on_reject={"executed": ["start", "managerReview", "isApproved", "endRejected"],
                                             "globals": {"status": "posted"}})
    r = run_check(tmp_path, "check_hitl_expense_apptask_run.py", expense_flow(), scenario, "run")
    assert r.returncode != 0
    assert "expected 'rejected'" in r.stdout + r.stderr


def test_expense_app_task_cancels_a_run_that_did_not_complete(tmp_path):
    scenario = dict(GOOD_EXPENSE, cli="suspend", final_status="Faulted")
    r = run_check(tmp_path, "check_hitl_expense_apptask_run.py", expense_flow(), scenario, "run")
    assert r.returncode != 0
    assert "did not complete" in r.stdout + r.stderr
    assert state_of(tmp_path).get("cancelled") is True


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

class _FakeRun:
    def __init__(self, ids):
        self.ids = ids
        self.proc = type("P", (), {"poll": lambda self: None})()

    def refresh_ids(self):
        return self.ids


def _fake_clock(monkeypatch):
    now = [0.0]
    monkeypatch.setattr(live.time, "monotonic", lambda: now[0])
    monkeypatch.setattr(live.time, "sleep", lambda seconds: now.__setitem__(0, now[0] + seconds))
    return now


@pytest.mark.parametrize("known", [{"job_key": "job-1"}, {"instance_id": "inst-1"}])
def test_wait_for_ids_returns_once_the_run_is_named_without_a_folder(monkeypatch, known):
    now = _fake_clock(monkeypatch)
    ids = live.wait_for_ids(_FakeRun(live.RunIds(**known)), 600.0)
    assert ids.folder_id is None
    assert live.FOLDER_GRACE_SECONDS <= now[0] < live.FOLDER_GRACE_SECONDS + 10


def test_wait_for_ids_keeps_waiting_while_nothing_is_named(monkeypatch):
    now = _fake_clock(monkeypatch)
    live.wait_for_ids(_FakeRun(live.RunIds()), 600.0)
    assert now[0] >= 600.0


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


def test_find_run_task_finds_a_task_listed_only_tenant_wide_by_its_job_key():
    job = "52c347d7-d166-49f8-8480-f6fb55763afd"
    row = {"Id": 102190311, "Status": "Unassigned", "Type": "AppTask", "FolderId": 3278005,
           "CreatorJobKey": job, "AssignedToUserKey": None}

    def lister(folder_id, *, as_admin=False, folder_path=None):
        return [row] if folder_id is None and folder_path is None else []

    ids = live.RunIds(folder_id="2863967", job_key=job)
    task, notes = live.find_run_task(
        ids, lambda *_: False, time.monotonic() + 120, None,
        lister=lister, data_reader=lambda *_: {"Content": "x"}, sleep=lambda _s: None,
    )
    assert task is not None, notes
    assert (task.task_id, task.folder_id) == ("102190311", "3278005")


def test_task_data_is_the_form_inside_the_record_tasks_data_get_prints():
    record = {"Status": "Unassigned", "Action": None, "Type": "QuickFormTask", "FolderId": 2863967,
              "CreatorJobKey": "74b5add8-f7d6-4649-8709-1d1c013e5ead", "Id": 102190245,
              "Data": {"InvoiceNumber": "INV-1001", "VendorName": "Contoso Supplies",
                       "TotalAmount": 1250.5, "Currency": "USD"}}
    assert live.form_data(record) == record["Data"]


def test_node_folder_paths_reads_the_app_folder():
    assert live.node_folder_paths(APP_HITL) == ["Shared/uipath-agents/ExpenseReviewSol"]
    assert live.node_folder_paths(INVOICE_HITL) == []


def test_row_job_keys_ignore_the_empty_guid():
    row = {"CreatorJobKey": "00000000-0000-0000-0000-000000000000", "TaskSource": {"SourceId": "ABC"}}
    assert live.row_job_keys(row) == {"abc"}


def test_bounded_calls_return_within_the_minimum_when_uip_hangs(tmp_path, monkeypatch):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    hung = bin_dir / "uip"
    hung.write_text("#!/bin/sh\nsleep 30\n")
    hung.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setattr(live, "MIN_CALL_SECONDS", 1)
    live.bound_calls_by(time.monotonic() - 100)
    try:
        started = time.monotonic()
        assert live.uip_json(["tasks", "list"]) is None
        assert time.monotonic() - started < 5
    finally:
        live.bound_calls_by(None)


def test_find_run_task_stops_reading_tasks_at_the_deadline():
    rows = [{"Id": 7, "Status": "Unassigned", "Type": "AppTask", "FolderId": 42,
             "CreatorJobKey": "00000000-0000-0000-0000-000000000000"}]
    reads = []

    def reader(task_id, folder):
        reads.append(task_id)
        return {}

    ids = live.RunIds(folder_id="42", job_key="52c347d7-d166-49f8-8480-f6fb55763afd")
    task, _notes = live.find_run_task(
        ids, lambda *_: True, time.monotonic() - 1, None,
        lister=lambda *_a, **_k: rows, data_reader=reader, sleep=lambda _s: None,
    )
    assert task is None
    assert reads == []


def test_find_run_task_rereads_a_task_whose_first_read_failed():
    rows = [{"Id": 7, "Status": "Unassigned", "Type": "AppTask", "FolderId": 42,
             "CreatorJobKey": "00000000-0000-0000-0000-000000000000"}]
    reads = iter([None, {"token": "run-1"}])

    ids = live.RunIds(folder_id="42", job_key="52c347d7-d166-49f8-8480-f6fb55763afd")
    task, notes = live.find_run_task(
        ids, lambda _row, bundle: bundle["data"] == {"token": "run-1"}, time.monotonic() + live.TASK_POLL_SECONDS + 5, None,
        lister=lambda *_a, **_k: rows, data_reader=lambda *_: next(reads), sleep=lambda _s: None,
    )
    assert task is not None, notes
    assert task.task_id == "7"


class FakeProc:
    def __init__(self, running: bool):
        self.running = running
        self.killed = False

    def poll(self):
        return None if self.running else 0

    def kill(self):
        self.killed = True
        self.running = False

    def wait(self, timeout=None):
        return 0


def fake_debug_run(tmp_path, running: bool) -> live.DebugRun:
    out_dir = tmp_path / "hitl-debug-x"
    out_dir.mkdir()
    stdout_path, stderr_path = str(out_dir / "stdout.json"), str(out_dir / "stderr.log")
    return live.DebugRun(
        FakeProc(running), stdout_path, stderr_path,
        stdout_file=open(stdout_path, "w"), stderr_file=open(stderr_path, "w"), out_dir=str(out_dir),
    )


@pytest.mark.parametrize("running", [True, False])
def test_stop_closes_the_log_handles(tmp_path, running):
    run = fake_debug_run(tmp_path, running)
    run.stop()
    assert run.proc.killed is running
    assert run.stdout_file.closed and run.stderr_file.closed
    run.stop()


def test_finish_removes_the_temp_dir_and_keeps_stop_idempotent(tmp_path):
    run = fake_debug_run(tmp_path, True)
    run.finish()
    assert run.proc.killed
    assert run.stdout_file.closed and run.stderr_file.closed
    assert not os.path.exists(run.out_dir)
    assert run.stdout() == "" and run.stderr() == ""
    run.finish()


def test_invoice_completion_data_leaves_booleans_unapproved_on_a_rejection():
    import check_hitl_invoice_approval_run as invoice

    hitl = {"inputs": {"schema": {"fields": [
        {"id": "comments", "type": "text", "direction": "output"},
        {"id": "escalate", "type": "boolean", "direction": "output"},
    ]}}}
    approved = invoice.completion_data(hitl, {}, "ok", invoice.Decision.APPROVE)
    rejected = invoice.completion_data(hitl, {}, "no", invoice.Decision.REJECT)
    assert approved == {"Comments": "ok", "Escalate": True}
    assert rejected == {"Comments": "no", "Escalate": False}


def test_a_missing_uip_leaves_no_debug_dir_behind(tmp_path, monkeypatch):
    scratch = tmp_path / "tmp"
    scratch.mkdir()
    monkeypatch.setattr("tempfile.tempdir", str(scratch))
    monkeypatch.setenv("PATH", str(tmp_path / "empty"))
    with pytest.raises(FileNotFoundError):
        live.start_debug(str(tmp_path), {}, 30)
    assert list(scratch.iterdir()) == []


def test_each_graded_run_records_its_token_for_cleanup(tmp_path):
    r = run_check(tmp_path, "check_hitl_invoice_approval_run.py", invoice_flow(), GOOD_INVOICE)
    assert r.returncode == 0, r.stdout + r.stderr
    lines = (tmp_path / "Sol" / live.TOKENS_FILE).read_text().splitlines()
    tokens = [line.split()[0] for line in lines if len(line.split()) == 1]
    with_instance = [line.split() for line in lines if len(line.split()) == 2]
    assert len(tokens) == 2 and all(t.startswith("INV-") for t in tokens)
    assert [t for t, _ in with_instance] == tokens and all(i == "c3d4e5f6-0000-0000-0000-000000000001" for _, i in with_instance)


class _LateInstanceRun:
    """A debug whose log names the job key first and the instance id only later."""

    def __init__(self):
        self.ids = live.RunIds(folder_id="42", job_key="job-1")
        self.proc = type("Proc", (), {"poll": lambda self: 0})()

    def stdout(self):
        return ""

    def stderr(self):
        return ""

    def refresh_ids(self):
        return self.ids

    def finish(self):
        pass


def test_an_instance_id_that_arrives_after_the_job_key_is_still_recorded(tmp_path, monkeypatch):
    run = _LateInstanceRun()

    def find_run_task(ids, matches, deadline, run_, **kwargs):
        run_.ids.instance_id = "inst-9"
        return None, ["no task"]

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(live, "start_debug", lambda *a, **k: run)
    monkeypatch.setattr(live, "wait_for_ids", lambda r, d: r.refresh_ids())
    monkeypatch.setattr(live, "find_run_task", find_run_task)
    monkeypatch.setattr(live, "cancel", lambda r: None)
    with pytest.raises(SystemExit):
        live.run_with_task(str(tmp_path), {}, "TOK-1", {}, [], lambda t: None, lambda t: {}, "task")
    assert (tmp_path / live.TOKENS_FILE).read_text().splitlines() == ["TOK-1", "TOK-1 inst-9"]
