#!/usr/bin/env python3
"""SupplierOnboarding — run the case for real, one route at a time, and assert where it landed.

The case parks on required action tasks, so `uip maestro case debug` alone never reaches a terminal status: it uploads, starts the instance, polls, and gives up. This script starts that debug run and drives the gates alongside it, then reads the case's own variables to check the route it took.

Usage: drive_case.py [--route default|reject|sendback]

Every gate is completed as the identity that is already authenticated. The script never assigns work to a group and never names a user: it reads the running identity from `uip login status` and assigns each task to that person alone. Nothing reaches anybody else's Action Center queue.

`uip maestro case debug` abandons a run after roughly 600 seconds with no progress, and the instance is cancelled after that. So the loop stays continuous: complete a task, send the stage message if one is pending, pick up the next task, with no idle gap.

Only some exits need a stage message. An exit-only condition carries its own exitToStageId and routes by itself; a wait-for-user condition parks on a selection element and waits to be told. So after each gate the loop watches for whichever comes first: a selection waiting, the next gate's task, or the case finishing.

Two lookups are deliberately narrow. `uip tasks list` is tenant-wide, so a title match alone picks up leftovers from earlier runs; tasks are filtered by an id watermark captured before this run started. And the stage-selection element from the previous pass stays in the execution list, so a message is sent only once its element is InProgress -- testing for presence fires it too early and the platform drops it.
"""

from __future__ import annotations

import argparse
import atexit
import datetime
import json
import re
import subprocess
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
from _shared.case_check import find_project_dir, find_solution_dir  # noqa: E402

# The folder that owns the case instance; the stage-selection message is addressed to it.
# Read off the instance rather than pinned: the case is published into whatever folder the
# run's own solution lands in, and a pinned key sends every folder-scoped call to a folder
# that may not exist — which the CLI answers with a 404 the callers cannot tell from an
# empty result.
CASE_FOLDER_KEY = ""

WITHDRAWN = "Application withdrawn"
CHECKING = "Checking the application"
BUYER = "Buyer review"
COMPLIANCE = "Compliance and risk review"
SETUP = "Setting up the supplier"
ONBOARDED = "Supplier onboarded"
REJECTED = "Application rejected"

# Where a completed stage goes when the case asks which stage is next.
NEXT_STAGE = {CHECKING: BUYER, BUYER: COMPLIANCE, COMPLIANCE: SETUP, SETUP: ONBOARDED}

# Each step names the task by its SDD name and the decision to send. What Action Center shows is
# that task's own taskTitle, which the build writes freely, so it is looked up rather than assumed.
# A route may redirect one stage's selection somewhere other than the forward stage. The
# withdrawal stage is reachable only this way: its entry rule is `user-selected-stage`, so
# nothing routes into it automatically.
SELECT_OVERRIDE = {
    "withdraw": {CHECKING: WITHDRAWN},
}

ROUTES = {
    # Nothing is completed until the intake phase misses its own deadline. The escalation task that
    # opens is answered, then the phase's own task is completed as well, which is the evidence that
    # the escalation ran alongside the phase's work rather than replacing it. The breach is driven
    # separately, because what it waits for is a clock rather than a sequence; the buyer decline
    # after it is the shortest way to a disposition.
    "sla": [
        ("Record buyer review decision", "reject"),
    ],
    # The buyer declines. The shortest route to a terminal stage, and the cheapest proof that a
    # human decision actually reaches the guard that reads it.
    "reject": [
        ("Validate application details", "approve"),
        ("Record buyer review decision", "reject"),
    ],
    # The supplier withdraws while the application is still under review. The only route that
    # reaches the withdrawal stage, and the only runtime evidence that a review stage offers
    # the choice at all.
    "withdraw": [
        ("Validate application details", "approve"),
    ],
    # The buyer sends it back, then approves on the second pass. The only route that walks
    # backwards, so it is the only one that proves a stage can be re-entered.
    "sendback": [
        ("Validate application details", "approve"),
        ("Record buyer review decision", "sendback"),
        ("Validate application details", "approve"),
        ("Record buyer review decision", "approve"),
        ("Record compliance review decision", "approve"),
    ],
}

# The intake escalation writes its own revised-date variable, and it is the only escalation the
# case authors. The SDD declares this one variable; nothing else carries a revised date.
REVISED_DATE = {
    CHECKING: "ApplicationCheckRevisedDate",
}

# The case's own variable names, as the SDD declares them. `instance variables` returns Globals
# PascalCased, so `buyerDecision` reads back as `BuyerDecision`.
BUYER_DECISION = "BuyerDecision"
COMPLIANCE_DECISION = "ComplianceDecision"

FINISHED = {"Completed", "Successful", "Faulted", "Cancelled"}

# The intake phase's deadline is 16 minutes, so its escalation cannot open before then. Waiting is
# the whole point of that route, and the budget has to clear the deadline with room for the platform
# to notice it, so it is set well above the deadline rather than at it.
BREACH_TIMEOUT = 1500

# A solution's first upload registers the solution and its process before any instance exists, so
# the first route of a fresh build waits longer here than later ones. Measured: a re-uploaded
# solution surfaces its instance inside a minute, a brand new one took over five.
INSTANCE_TIMEOUT = 600

POLL_SLEEP = 10
GATE_TIMEOUT = 420
# Long enough to outlast the slowest route. The sla route spends its first sixteen minutes
# waiting for a deadline to pass, so the debug wait has to clear that plus the work after it.
DEBUG_TIMEOUT = 2100


# The running `case debug` session, so every exit path can end it. A route that fails
# after starting debug used to leave it alive: `fail` exits through `sys.exit`, which the
# one `finally` in `main` sits after, and the next route's `case debug` then never created
# an instance — three routes, one instance, two 600s timeouts.
_DEBUG_SESSION: list = []


# The instance this route started, so it can be cancelled however the route ends. A case
# left `Running` holds the project: the next route's `case debug` then produced no instance
# and no output at all, and waited out its whole timeout. Killing the debug process is not
# enough, because the instance outlives it.
_OWN_INSTANCE: list = []


def _end_debug_session() -> None:
    for instance_id, folder in _OWN_INSTANCE:
        try:
            subprocess.run(
                ["uip", "maestro", "case", "instance", "cancel", instance_id,
                 "-f", folder, "--comment", "route finished", "--output", "json"],
                capture_output=True, text=True, timeout=60,
            )
        except (OSError, subprocess.SubprocessError):
            pass
    _OWN_INSTANCE.clear()
    for proc in _DEBUG_SESSION:
        if proc.poll() is None:
            proc.kill()
    _DEBUG_SESSION.clear()


atexit.register(_end_debug_session)


def fail(msg: str):
    print(f"FAIL: {msg}")
    sys.exit(1)


def envelope(args: list[str], *, timeout: int = 120) -> dict:
    """The whole uip response envelope, so callers can read Result as well as Data."""
    try:
        proc = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"Result": "Failure", "Message": f"timed out after {timeout}s"}
    out = proc.stdout
    start = out.find("{")
    if start < 0:
        return {"Result": "Failure", "Message": (proc.stderr or out)[:400]}
    try:
        reply = json.loads(out[start:])
    except json.JSONDecodeError:
        return {"Result": "Failure", "Message": out[:400]}
    # A failing verb answers with a one-line Message and puts the HTTP status, endpoint, response
    # body and trace id in Instructions. Carrying both, plus stderr, is the difference between
    # "Error completing task" and a reason.
    if reply.get("Result") != "Success" and (proc.stderr or "").strip():
        reply.setdefault("Stderr", proc.stderr.strip()[:600])
    return reply


def run(args: list[str], *, timeout: int = 120) -> dict:
    return envelope(args, timeout=timeout).get("Data") or {}


def run_list_checked(args: list[str], *, timeout: int = 120) -> list:
    """`run_list`, but a failed CLI call raises instead of reading as an empty result.

    A polling loop cannot tell "no task yet" from "the call failed" when both answer with an
    empty list, so a broken lookup burns the whole gate budget and then reports the wrong cause.
    """
    reply = envelope(args, timeout=timeout)
    if reply.get("Result") != "Success":
        raise RuntimeError(
            f"`{' '.join(args[:3])}` failed: {reply.get('Message') or reply.get('Code') or reply}")
    return _rows_of(reply.get("Data") or {})


def _rows_of(data) -> list:
    if isinstance(data, list):
        return data
    for key in ("ElementExecutions", "value", "Items"):
        if isinstance(data.get(key), list):
            return data[key]
    return next((v for v in data.values() if isinstance(v, list)), [])


def run_list(args: list[str], *, timeout: int = 120) -> list:
    """The rows a uip list command returned. Some verbs answer with a bare list; `instance element-executions` wraps its rows in a named field beside the instance's own metadata, so a known key wins and any list-valued field is the fallback."""
    return _rows_of(run(args, timeout=timeout))


def current_identity() -> str:
    data = run(["uip", "login", "status", "--output", "json"])
    who = data.get("UserEmail") or data.get("Identity")
    if not who:
        fail("could not resolve the authenticated identity from `uip login status`")
    return who


def task_watermark() -> int:
    """Highest task id that exists before this run, so later lookups ignore older runs."""
    ids = [int(r["Id"]) for r in run_list(["uip", "tasks", "list", "--output", "json"]) if r.get("Id")]
    return max(ids) if ids else 0


def instance_ids() -> dict:
    """Every case instance the tenant currently lists, keyed by id, valued by folder key."""
    return {
        r["InstanceId"]: (r.get("FolderKey") or "")
        for r in run_list(["uip", "maestro", "case", "instance", "list", "--output", "json"])
        if r.get("InstanceId")
    }


def appeared_since(before: dict) -> str:
    """The instance that exists now and did not before `case debug` was started.

    A set difference against a snapshot, rather than anything read off an instance's own
    fields. A debug instance carries nothing that says which case it is: the create call
    writes `PackageKey`, `ProcessKey` and `PackageVersion` as `Guid.Empty`, an empty display
    name, and `PackageId` as the Studio Web project's guid. `case debug` prints nothing
    before the instance exists either. Two suites debugging at the same moment is the one
    case this cannot resolve, and it says so rather than driving whichever came first.
    """
    fresh = {k: v for k, v in instance_ids().items() if k not in before}
    if not fresh:
        return ""
    global CASE_FOLDER_KEY
    if len(fresh) > 1:
        fail(
            f"{len(fresh)} case instances appeared while this route was starting "
            f"({sorted(fresh)}); another suite is debugging into this tenant at the same "
            "moment and no field says which one is ours"
        )
    instance_id, folder = next(iter(fresh.items()))
    CASE_FOLDER_KEY = folder
    return instance_id


def pending_task(watermark: int, title: str, done: set = frozenset(), instance_id: str = ""):
    """The open Action Center task with this exact title, belonging to this run's own case.

    `uip tasks list` is tenant-wide, so three filters stack. `CreatorJobKey` is the instance that
    raised the task, which is what keeps concurrent runs of this same task from completing each
    other's gates; the id watermark drops anything that existed before this run; and ids already
    driven are skipped, because a route that revisits a stage sees the same title twice and a
    just-completed task can still read as open for a moment.
    """
    for row in run_list_checked(["uip", "tasks", "list", "--output", "json"]):
        if not row.get("Id") or int(row["Id"]) <= watermark:
            continue
        if str(row["Id"]) in done or row.get("Status") == "Completed":
            continue
        if (row.get("Title") or "") != title:
            continue
        if instance_id and row.get("CreatorJobKey") != instance_id:
            continue
        return row
    return None


def explain_missing_gate(watermark: int, title: str, done: set, instance_id: str) -> None:
    """Say why every task carrying this title was passed over.

    "never appeared" is the one failure this script cannot diagnose after the fact: post_run
    deletes the solution, and with it the instance the task hung off. Naming the filter that
    rejected each candidate is what separates a task the case never raised from a task the
    lookup threw away.
    """
    rows = [r for r in run_list(["uip", "tasks", "list", "--output", "json"])
            if (r.get("Title") or "") == title]
    print(f"  watermark {watermark}, instance {instance_id}, {len(rows)} task(s) carry this title")
    for row in sorted(rows, key=lambda r: int(r.get("Id") or 0))[-6:]:
        tid = int(row.get("Id") or 0)
        if tid <= watermark:
            why = f"id <= watermark {watermark}, so it predates this run"
        elif str(tid) in done:
            why = "already driven by this run"
        elif row.get("Status") == "Completed":
            why = "already Completed"
        elif row.get("CreatorJobKey") != instance_id:
            why = f"raised by instance {row.get('CreatorJobKey')}, not this one"
        else:
            why = "PASSES every filter, so the lookup should have taken it"
        print(f"    {tid} {row.get('Status')} created {row.get('CreatedTime')}: {why}")


def complete_gate(task: dict, action: str, who: str, data: dict | None = None) -> None:
    task_id = str(task["Id"])
    folder_id = str(task.get("FolderId") or "")
    if not folder_id:
        fail(f"task {task_id} carries no FolderId; cannot complete it")
    # Checked, because an unchecked assign surfaces two steps later as `tasks complete`
    # reporting "This action is no longer assigned to you", which names the symptom and
    # hides whether the assign was refused or the task was reassigned after it.
    assigned = envelope(["uip", "tasks", "assign", task_id, "--user", who, "--output", "json"])
    if assigned.get("Result") != "Success":
        fail(f"assigning task {task_id} to {who} failed: "
             f"{assigned.get('Message') or assigned.get('Code') or assigned}")
    reply = envelope([
        "uip", "tasks", "complete", task_id,
        "--type", "AppTask",
        "--folder-id", folder_id,
        "--action", action,
        "--data", json.dumps(data or {"Comment": f"Driven by the SupplierOnboarding e2e check ({action})."}),
        "--output", "json",
    ])
    if reply.get("Result") != "Success":
        detail = [f"completing task {task_id} with action {action!r} failed: "
                  f"{reply.get('Message') or reply.get('Code') or reply}"]
        for key in ("Instructions", "Stderr"):
            if reply.get(key):
                detail.append(f"  {key}: {str(reply[key])[:600]}")
        fail("\n".join(detail))


def incidents(instance_id: str) -> list:
    data = run(["uip", "maestro", "case", "instance", "incidents", instance_id,
                "-f", CASE_FOLDER_KEY, "--output", "json"])
    return data if isinstance(data, list) else (data.get("value") or [])


def describe_incident(item: dict) -> str:
    detail = str(item.get("ErrorDetails") or item.get("ErrorMessage") or item.get("Message") or "")
    return f"{item.get('ElementId')!r} ({item.get('ErrorCode')}): {detail[:400]}"


def fail_with_diagnosis(instance_id: str, msg: str):
    """Fail, but first print what the case itself says about why.

    post_run deletes the solution when the task ends, and the instance record goes with it, so
    an incident that is readable now is unreadable by the time anyone opens the result. Whatever
    the case recorded has to be captured here or not at all.
    """
    raised = incidents(instance_id)
    for item in raised[:4]:
        print(f"  incident on {describe_incident(item)}")
    if not raised:
        stages = [r.get("ElementId") for r in executions(instance_id)
                  if r.get("ElementType") == "CaseStage"]
        print(f"  no incident; the case reached stages {stages}")
    fail(msg)


def executions(instance_id: str) -> list:
    return run_list([
        "uip", "maestro", "case", "instance", "element-executions", instance_id,
        "-f", CASE_FOLDER_KEY, "--output", "json",
    ])


def waiting_selection(instance_id: str, answered: set):
    """The stage whose selection element is waiting and has not been answered yet.

    `element-executions` reports one row per element and folds every visit into that row's `ElementRuns`; the row's own `Status` describes the element, not the visit, and it carries no run id. So a sendback's second visit to a stage is only visible as a second entry in `ElementRuns`, each with its own `ElementRunId`. Answering is keyed on that id: without it the second visit looks like the first and is skipped, and the case waits forever."""
    prefix = "CaseWaitForUser_StageSelection_"
    for row in executions(instance_id):
        eid = row.get("ElementId") or ""
        if not eid.startswith(prefix):
            continue
        for run in row.get("ElementRuns") or []:
            if run.get("Status") != "InProgress":
                continue
            key = run.get("ElementRunId") or ""
            if key in answered:
                continue
            answered.add(key)
            return eid[len(prefix):]
    return None


def send_stage_selection(instance_id: str, from_stage: str, to_stage: str) -> None:
    # `message send` takes no instance argument: the reference inside the payload names the instance.
    message = {
        "name": "UserSelectStage",
        "reference": f"case-{instance_id}-CaseEntered:Wait for User to Select Next Stage for {from_stage}",
        "itemData": {"stageName": to_stage},
    }
    reply = envelope([
        "uip", "maestro", "case", "instance", "message", "send",
        "-f", CASE_FOLDER_KEY, "--inputs", json.dumps(message), "--output", "json",
    ])
    if reply.get("Result") != "Success":
        fail(f"stage selection {from_stage!r} -> {to_stage!r} was rejected: {reply.get('Message') or reply}")


def run_status(instance_id: str) -> str:
    """The instance's run status. `instance get` reports it as LatestRunStatus, not Status."""
    data = run(["uip", "maestro", "case", "instance", "get", instance_id, "-f", CASE_FOLDER_KEY, "--output", "json"])
    return data.get("LatestRunStatus") or ""


def globals_of(instance_id: str) -> dict:
    """The case's own variables at the end of the run. Names come back PascalCase: CaseOutcome, not caseOutcome."""
    data = run(["uip", "maestro", "case", "instance", "variables", instance_id, "-f", CASE_FOLDER_KEY, "--output", "json"])
    return data.get("Globals") or {}


_PLAN = None


def plan_nodes() -> list:
    global _PLAN
    if _PLAN is None:
        plan_path = next(Path(".").glob("**/caseplan.json"), None)
        if plan_path is None:
            fail("no caseplan.json found under the sandbox")
        _PLAN = json.loads(plan_path.read_text(encoding="utf-8"))
    return _PLAN.get("nodes") or []


def task_title(sdd_name: str) -> str:
    """The Action Center title for this task, or "" when the plan cannot supply one."""
    for node in plan_nodes():
        if node.get("type") != "case-management:Stage":
            continue
        for lane in (node.get("data") or {}).get("tasks") or []:
            for task in lane:
                if task.get("displayName") == sdd_name:
                    return ((task.get("data") or {}).get("taskTitle")) or ""
    return ""


def task_title_for(sdd_name: str) -> str:
    """What Action Center shows for the task the SDD calls sdd_name. The caseplan's own taskTitle is the authority: the build chooses that wording, so it cannot be hardcoded here."""
    for node in plan_nodes():
        if node.get("type") != "case-management:Stage":
            continue
        for lane in (node.get("data") or {}).get("tasks") or []:
            for task in lane:
                if task.get("displayName") == sdd_name:
                    title = (task.get("data") or {}).get("taskTitle")
                    if not title:
                        fail(f"task {sdd_name!r} carries no taskTitle; Action Center would show nothing")
                    return title
    fail(f"the caseplan has no task named {sdd_name!r}")


def task_id_for(sdd_name: str) -> str:
    """The plan's own id for the task the SDD calls `sdd_name`."""
    for node in plan_nodes():
        if node.get("type") != "case-management:Stage":
            continue
        for lane in (node.get("data") or {}).get("tasks") or []:
            for task in lane:
                if task.get("displayName") == sdd_name:
                    return task["id"]
    fail(f"the caseplan has no task named {sdd_name!r}")


def stage_label(stage_id: str) -> str:
    for node in plan_nodes():
        if node.get("id") == stage_id and node.get("type") == "case-management:Stage":
            return ((node.get("data") or {}).get("label")) or stage_id
    return stage_id


def stage_entries(instance_id: str, display_name: str) -> int:
    """How many times the case entered this stage, counted from the stage element's own `ElementRuns`. One row is reported per element however many times it is visited, so the row count is always 1 and only the runs distinguish a sendback's second pass."""
    target = next((n["id"] for n in plan_nodes()
                   if n.get("type") == "case-management:Stage"
                   and ((n.get("data") or {}).get("label")) == display_name), None)
    if target is None:
        fail(f"the caseplan has no stage named {display_name!r}")
    return sum(len(r.get("ElementRuns") or [])
               for r in executions(instance_id)
               if r.get("ElementId") == target and r.get("ElementType") == "CaseStage")


def advance(instance_id: str, watermark: int, next_title, answered: set, done: set, override: dict) -> str:
    """Wait for whatever happens after a gate: a stage selection to answer, the next task to open, or the case to end. Returns which one."""
    deadline = time.time() + GATE_TIMEOUT
    while time.time() < deadline:
        stage_id = waiting_selection(instance_id, answered)
        if stage_id:
            from_stage = stage_label(stage_id)
            to_stage = override.get(from_stage) or NEXT_STAGE.get(from_stage)
            if to_stage is None:
                fail(f"the case is asking which stage follows {from_stage!r}, and this route has no answer for it")
            print(f"  select {from_stage!r} -> {to_stage!r}")
            send_stage_selection(instance_id, from_stage, to_stage)
            return "selected"
        if next_title and pending_task(watermark, next_title, done, instance_id):
            return "task"
        if run_status(instance_id) in FINISHED:
            return "finished"
        time.sleep(POLL_SLEEP)
    return "timeout"


def drive_sla(instance_id: str, watermark: int, who: str, done: set, answered: set, override: dict) -> None:
    """Let the intake phase breach, answer its escalation, then finish the phase's own task."""
    escalation = task_title_for("Escalate delayed application check")
    intake = task_title_for("Validate application details")

    print(f"  waiting for the intake phase to breach and open {escalation!r}")
    deadline = time.time() + BREACH_TIMEOUT
    task = None
    while task is None and time.time() < deadline:
        task = pending_task(watermark, escalation, done, instance_id)
        if task is None:
            if run_status(instance_id) in FINISHED:
                fail("the case finished before the intake phase breached; its SLA never fired")
            time.sleep(POLL_SLEEP)
    if task is None:
        fail_with_diagnosis(instance_id,
            f"{escalation!r} never opened within {BREACH_TIMEOUT}s; the phase SLA did not breach")

    print(f"  breach {task['Id']} {task.get('Title')!r} -> approve")
    revised = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=3)).strftime("%Y-%m-%d")
    complete_gate(task, "approve", who, data={"newExpectedDate": revised,
                                              "Comment": "New date agreed with the requester."})
    done.add(str(task["Id"]))

    # The phase's own task must still be completable. An escalation that replaced it, rather than
    # running beside it, would leave nothing here to finish.
    gate = None
    deadline = time.time() + GATE_TIMEOUT
    while gate is None and time.time() < deadline:
        gate = pending_task(watermark, intake, done, instance_id)
        if gate is None:
            time.sleep(POLL_SLEEP)
    if gate is None:
        fail(f"{intake!r} was gone after the escalation; the breach must not consume the phase's own work")
    print(f"  gate {gate['Id']} {gate.get('Title')!r} -> approve")
    complete_gate(gate, "approve", who)
    done.add(str(gate["Id"]))

    # The phase is finished, so the case now asks which stage follows. Answer it here rather than
    # leaving it to the main loop, which looks for the next gate's task first and would time out
    # waiting for a task that cannot open until the selection is made.
    while advance(instance_id, watermark, None, answered, done, override) == "selected":
        pass


def clear_solution_id(solution_dir: str) -> None:
    """Drop the SolutionId a previous debug session wrote into the `.uipx`.

    `case debug` imports the solution on its first run and writes the new id back. Every
    later run reads that id and calls Overwrite instead, and Overwrite answers this
    solution with 400 code 1001. The CLI falls back to a fresh import only on 404, so
    routes after the first one died at upload and reported `no case instance appeared`.
    Clearing the id puts every route on the import path the first one took.
    """
    manifest = next(iter(sorted(Path(solution_dir).glob("*.uipx"))), None)
    if manifest is None:
        return
    try:
        doc = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"could not read {manifest} to clear its SolutionId: {exc}")
        return
    stale = doc.pop("SolutionId", None)
    if not stale:
        return
    # 4-space indent matches what the CLI itself writes back, so the file does not churn.
    manifest.write_text(json.dumps(doc, indent=4), encoding="utf-8")
    print(f"cleared SolutionId {stale} from {manifest.name}; debug will import a fresh copy")


def main() -> int:
    global CASE_FOLDER_KEY
    parser = argparse.ArgumentParser()
    parser.add_argument("--route", choices=sorted(ROUTES), required=True)
    args = parser.parse_args()
    steps = ROUTES[args.route]
    override = SELECT_OVERRIDE.get(args.route, {})

    who = current_identity()
    print(f"route {args.route!r}, driving the case as {who}")

    # Everything this route needs is readable from the plan, so check it before uploading
    # anything. A build missing a task title or an escalation task cannot be driven, and
    # discovering that after starting the case costs a solution upload and a live instance per
    # route for a fact that was in the file all along.
    # Only the tasks this route COMPLETES need an Action Center title. The sla route also asserts
    # a delay note ran, but that is a connector task: it fires on its own and carries no title,
    # so requiring one would reject a plan that is perfectly drivable.
    needed = [name for name, _action in steps]
    if args.route == "sla":
        needed.append("Escalate delayed application check")
    missing = [name for name in needed if not task_title(name)]
    if missing:
        fail(f"the plan cannot be driven: {missing}. Each is a task this route has to complete, "
             f"and either the task is absent or it carries no taskTitle for Action Center to show")

    project_dir = find_project_dir()
    solution_dir = find_solution_dir()
    clear_solution_id(solution_dir)

    refresh = subprocess.run(
        ["uip", "solution", "resources", "refresh", "--solution-folder", solution_dir, "--output", "json"],
        capture_output=True, text=True, timeout=180,
    )
    if refresh.returncode != 0 and "Node already added to the graph" not in refresh.stdout + refresh.stderr:
        fail(f"solution resources refresh exit {refresh.returncode}\n{refresh.stdout}\n{refresh.stderr}")

    watermark = task_watermark()
    # Snapshot before starting debug: the instance this route drives is the one that was
    # not here a moment ago.
    before_debug = instance_ids()
    started = time.time()

    # stderr folded into stdout: two pipes with one reader leaves the other to fill, and
    # a 64 KB buffer is enough for `case debug` to block before it ever creates the
    # instance. Two routes waited out the full 600s timeout that way while the first,
    # quieter one succeeded.
    debug = subprocess.Popen(
        # `--log-level debug` because three guesses at why a second route gets no instance
        # were all wrong, and the command says nothing at default level: the failure message
        # quoted an empty stream every time.
        ["uip", "maestro", "case", "debug", project_dir,
         "--output", "json", "--log-level", "debug"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    _DEBUG_SESSION.append(debug)

    # Drained on a thread so a full pipe cannot block the debug process, and so its output
    # is available to quote when no instance appears.
    def drain_debug(sink: list) -> None:
        for line in iter(debug.stdout.readline, ""):
            sink.append(line)

    debug_lines: list = []
    threading.Thread(target=drain_debug, args=(debug_lines,), daemon=True).start()

    instance_id = ""
    while not instance_id and time.time() - started < INSTANCE_TIMEOUT:
        time.sleep(POLL_SLEEP)
        instance_id = appeared_since(before_debug)
        if instance_id:
            break
        # `case debug` exits 1 the moment its upload or import fails, and it says why on the
        # stream this thread is draining. Waiting the full timeout out anyway turned a
        # one-line error into `no case instance appeared`, three times per run.
        if debug.poll() is not None:
            fail(
                f"`case debug` exited {debug.returncode} before any instance appeared, after "
                f"{time.time() - started:.0f}s:\n{''.join(debug_lines)[-4000:]}"
            )
    if not instance_id:
        debug.kill()
        fail(f"no case instance appeared within {INSTANCE_TIMEOUT}s of starting debug\n"
             f"debug output so far ({len(debug_lines)} line(s)), exit="
             f"{debug.poll()}:\n{''.join(debug_lines)[-4000:]}")
    print(f"instance {instance_id}")
    _OWN_INSTANCE.append((instance_id, CASE_FOLDER_KEY))
    # The outcome probe grades the mailbox for this instance and runs as its own criterion in a
    # fresh process, so the id is handed over on disk. It goes in the sandbox working directory,
    # not beside this script: the harness mounts the task directory read-only.
    state_path = Path(".supplier-onboarding-run.json")
    runs = []
    if state_path.exists():
        try:
            runs = json.loads(state_path.read_text(encoding="utf-8")).get("runs") or []
        except (json.JSONDecodeError, OSError):
            runs = []
    runs = [r for r in runs if r.get("route") != args.route]
    runs.append({"route": args.route, "instance_id": instance_id,
                 "folder_key": CASE_FOLDER_KEY})
    # `runs` accumulates across routes so the outcome probe grades every one of them; the flat
    # pair stays for the child-case cleanup, which only needs the last instance to find its package.
    state_path.write_text(
        json.dumps({"instance_id": instance_id, "route": args.route, "runs": runs}),
        encoding="utf-8")

    answered: set = set()
    done: set = set()

    try:
        if args.route == "sla":
            drive_sla(instance_id, watermark, who, done, answered, override)
        for index, (sdd_name, action) in enumerate(steps):
            title = task_title_for(sdd_name)
            deadline = time.time() + GATE_TIMEOUT
            task = None
            while task is None and time.time() < deadline:
                task = pending_task(watermark, title, done, instance_id)
                if task is None:
                    if run_status(instance_id) in FINISHED:
                        break
                    # A case that raised an incident is stalled, not slow. Waiting out the gate
                    # budget on it costs seven minutes per route and then reports "the task never
                    # appeared", which names the symptom and hides the cause.
                    raised = incidents(instance_id)
                    if raised:
                        for item in raised[:4]:
                            print(f"  incident on {describe_incident(item)}")
                        fail(f"the case raised {len(raised)} incident(s) while waiting for "
                             f"{sdd_name!r}; it is stalled, so the gate will never open")
                    time.sleep(POLL_SLEEP)
            if task is None:
                if run_status(instance_id) in FINISHED:
                    print(f"  the case finished before {sdd_name!r} opened; its guard closed that route")
                    break
                explain_missing_gate(watermark, title, done, instance_id)
                fail_with_diagnosis(instance_id,
                    f"the gate task for {sdd_name!r} (Action Center title {title!r}) never appeared")
            print(f"  gate {task['Id']} {task.get('Title')!r} -> {action}")
            complete_gate(task, action, who)
            done.add(str(task["Id"]))

            remaining = steps[index + 1:]
            next_title = task_title_for(remaining[0][0]) if remaining else None
            while advance(instance_id, watermark, next_title, answered, done, override) == "selected":
                pass
    except RuntimeError as exc:
        # A lookup that could not run at all, surfaced by run_list_checked. Reported as a failure
        # in its own right rather than as an empty result the caller mistakes for "not yet".
        fail(str(exc))
    finally:
        try:
            debug.wait(timeout=max(30, DEBUG_TIMEOUT - int(time.time() - started)))
        except subprocess.TimeoutExpired:
            debug.kill()

    status = run_status(instance_id)
    g = globals_of(instance_id)
    outcome = g.get("CaseOutcome")
    bank = g.get("BankVerificationStatus")
    buyer, compliance = g.get(BUYER_DECISION), g.get(COMPLIANCE_DECISION)
    print(f"instance {instance_id} run={status!r} CaseOutcome={outcome!r} "
          f"BankVerificationStatus={bank!r} {BUYER_DECISION}={buyer!r} "
          f"{COMPLIANCE_DECISION}={compliance!r}")

    if status not in {"Completed", "Successful"}:
        fail(f"the case ended {status!r}; every route in this test must run to completion")

    if args.route == "sla":
        own = REVISED_DATE[CHECKING]
        if not g.get(own):
            fail(f"{own} is empty; the intake escalation must record the new date it was given")
        # The delay note is what the supplier actually receives, so it has to have run, not just
        # been wired. Its task id comes from the plan rather than a hardcoded name.
        note_id = task_id_for("Send delay note for the application check")
        ran = {r.get("ElementId") for r in executions(instance_id) if r.get("Status") == "Completed"}
        if note_id not in ran:
            fail(f"the intake phase breached but its delay note never ran; the supplier was told nothing")
        print(f"  {own}={g.get(own)!r}; delay note sent")
    elif args.route == "withdraw":
        if outcome != "Withdrawn":
            fail(f"the supplier withdrew but CaseOutcome={outcome!r}; {WITHDRAWN!r} must close the case as withdrawn")
        if not stage_entries(instance_id, WITHDRAWN):
            fail(f"the case never entered {WITHDRAWN!r}; a review stage must offer it as a choice")
    elif args.route == "reject":
        if buyer != "reject":
            fail(f"the buyer's decision never reached the case: {BUYER_DECISION}={buyer!r}, expected 'reject'")
        if outcome != "Rejected":
            fail(f"the buyer declined but CaseOutcome={outcome!r}; the decline guard did not route the case")
    elif args.route == "sendback":
        entries = stage_entries(instance_id, CHECKING)
        if entries < 2:
            fail(f"{CHECKING!r} was entered {entries} time(s); a sendback must send the case back into it")
        if buyer != "approve":
            fail(f"the second buyer decision never landed: {BUYER_DECISION}={buyer!r}, expected 'approve'")

    # Applies to every route, not one of them. A conformant build always emits an empty file
    # default, so ERP reports `failed` and the setup stage exits to rejection. A run that reports
    # verified and still rejects, or the reverse, is routing on something the SDD does not describe.
    if bank == "verified" and outcome == "Rejected":
        fail(f"bank verification passed but CaseOutcome={outcome!r}; setup should have completed to {ONBOARDED!r}")
    if bank == "failed" and outcome not in ("Rejected", "Withdrawn"):
        fail(f"bank verification returned {bank!r} but CaseOutcome={outcome!r}; that route must end in {REJECTED!r}")

    print(f"OK: route {args.route!r} ran to completion with CaseOutcome={outcome!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
