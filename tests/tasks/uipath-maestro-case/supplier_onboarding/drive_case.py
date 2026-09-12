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
import os
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
    # The application the `In` defaults describe, carried all the way to onboarding. It is
    # the only route that reaches `Supplier onboarded`, and the only one that proves the
    # bank details a debug run collects in-case are enough for ERP to verify them. The
    # 750000 default puts it over the director threshold, so the sign-off gate opens on
    # this route and is answered here rather than needing a route of its own.
    # Withdrawal is offered by a stage that waits for a user to pick what follows it, and
    # `Setting up the supplier` is not one: its exit rows are all exit-only. This route walks
    # into setup and then checks that nothing is asking, which is the only way to test that
    # an option is absent rather than that one is present.
    "no-withdraw-in-setup": [
        ("Validate application details", "approve"),
        ("Record buyer review decision", "approve"),
        ("Obtain procurement director sign-off", "approve"),
        ("Record compliance review decision", "approve"),
        ("Provide bank details for payment setup", "approve"),
        ("Confirm supplier portal access", "approve"),
    ],
    # The compliance reviewer rejects after the director has already signed off. The only
    # route that reaches `Application rejected` from the compliance stage rather than the
    # buyer's, and the only proof that a sign-off does not override the later decision.
    "compliance-reject": [
        ("Validate application details", "approve"),
        ("Record buyer review decision", "approve"),
        ("Obtain procurement director sign-off", "approve"),
        ("Record compliance review decision", "reject"),
    ],
    "onboard": [
        ("Validate application details", "approve"),
        ("Record buyer review decision", "approve"),
        ("Obtain procurement director sign-off", "approve"),
        ("Record compliance review decision", "approve"),
        ("Provide bank details for payment setup", "approve"),
        ("Confirm supplier portal access", "approve"),
    ],
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
        # This fixture's representative application is the high-value one, so the
        # director gate opens on every route that reaches the compliance stage, not
        # only on the one written to exercise it. A route that walks past it without
        # an answer waits until its budget runs out.
        ("Obtain procurement director sign-off", "approve"),
        ("Record compliance review decision", "approve"),
        # The setup stage's two required gates. This fixture put them on the path, so a
        # route that stops at compliance leaves the case parked and can never show that
        # a sent-back application still finishes.
        ("Provide bank details for payment setup", "approve"),
        ("Confirm supplier portal access", "approve"),
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
BANK_STATUS = "BankVerificationStatus"

FINISHED = {"Completed", "Successful", "Faulted", "Cancelled"}

# The intake phase's deadline is 16 minutes, so its escalation cannot open before then. Waiting is
# the whole point of that route, and the budget has to clear the deadline with room for the platform
# to notice it, so it is set well above the deadline rather than at it.
BREACH_TIMEOUT = 1500

# A solution's first upload registers the solution and its process before any instance exists, so
# the first route of a fresh build waits longer here than later ones. Measured: a re-uploaded
# solution surfaces its instance inside a minute, a brand new one took over five.
# `--as-admin` because the default view is the caller's own queue. Six runs reported the
# gate task "never appeared" while the engine logged `HITL task created ... TaskId=...`
# with the exact title: the task is raised against the action app's own recipient, which
# is a role the driving identity does not belong to, so it never enters that queue.
TASKS_LIST = ["uip", "tasks", "list", "--as-admin", "--output", "json"]

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


# A named login the CLI keeps beside the default one, so a second case can be driven on
# another organisation from the same machine without either login evicting the other.
# Unset in CI, where the runner has exactly one login and passing a name it has never
# authenticated would fail every call.
UIP_PROFILE = os.environ.get("UIP_PROFILE", "").strip()


def with_profile(args: list[str]) -> list[str]:
    """The same command, addressed to the named login when one is configured."""
    if not UIP_PROFILE or args[:1] != ["uip"]:
        return args
    return args + ["--profile", UIP_PROFILE]


def envelope(args: list[str], *, timeout: int = 120) -> dict:
    """The whole uip response envelope, so callers can read Result as well as Data."""
    try:
        proc = subprocess.run(with_profile(args), capture_output=True, text=True, timeout=timeout)
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


def envelope_detail(reply: dict) -> str:
    """Every field the CLI puts a reason in, joined.

    `Message` is a generic one-liner (`Error listing tasks`, `Error assigning task`); the
    reason the call was refused rides in `Instructions`. Reading only `Message` names the
    symptom and hides the cause.
    """
    return " | ".join(
        str(reply[key]) for key in ("Message", "Code", "ErrorCode", "Instructions")
        if reply.get(key)
    ) or str(reply)


# A refusal is permanent and must surface at once; the service being briefly away is
# not. One 503 inside a breach poll cost a whole route and the two checks after it.
TRANSIENT_RETRIES = 3
TRANSIENT_PAUSE = 10
_TRANSIENT_MARKERS = (
    "service unavailable",
    "bad gateway",
    "gateway timeout",
    "temporarily",
    "too many requests",
    # A 403 naming `authentication_required` is the tenant's session, never the plan:
    # a build defect cannot produce it. It cost four route verdicts across two runs,
    # on `instance get` and `instance variables` after the route had already driven
    # its gates.
    "authentication_required",
)

# The listing service answering with no reason at all. A refusal names one in
# `Instructions`, so the pair of a generic code and a content-free message is the
# signature of a service that could not answer rather than one that would not. It
# ended a route on 34632357797 at the point where the buyer stage had been selected.
_TRANSIENT_PAIR = ("unknown_error", "an error occurred")


def _is_transient(detail: str) -> bool:
    lowered = detail.lower()
    if all(part in lowered for part in _TRANSIENT_PAIR):
        return True
    return any(marker in lowered for marker in _TRANSIENT_MARKERS)



def envelope_retrying(args: list[str], *, timeout: int = 120) -> dict:
    """`envelope`, but a service that is briefly away gets another chance.

    Writes are the calls that cost a whole route when they fail: a gate answered twice
    is harmless, an unanswered gate ends the run. A refusal still comes back on the
    first attempt, because only the markers that mean "could not answer yet" retry.
    """
    for attempt in range(TRANSIENT_RETRIES + 1):
        reply = envelope(args, timeout=timeout)
        if reply.get("Result") == "Success":
            return reply
        detail = envelope_detail(reply)
        if attempt == TRANSIENT_RETRIES or not _is_transient(detail):
            return reply
        print(f"  `{' '.join(args[:5])}` came back {detail}; retrying in {TRANSIENT_PAUSE}s")
        time.sleep(TRANSIENT_PAUSE)
    return reply

def run_checked(args: list[str], *, timeout: int = 120) -> dict:
    """`run`, but a failed CLI call raises instead of reading as an empty payload.

    A caller that reads a field off `{}` gets `None`, which is indistinguishable from the
    case genuinely holding no value. One route reported all four case variables as `None`
    when the lookup itself had failed, and that reads as a case defect rather than a
    lookup that never answered.
    """
    for attempt in range(TRANSIENT_RETRIES + 1):
        reply = envelope(args, timeout=timeout)
        if reply.get("Result") == "Success":
            return reply.get("Data") or {}
        detail = envelope_detail(reply)
        if attempt == TRANSIENT_RETRIES or not _is_transient(detail):
            fail(f"`{' '.join(args[:6])}` failed: {detail}")
        print(f"  `{' '.join(args[:6])}` came back {detail}; retrying in {TRANSIENT_PAUSE}s")
        time.sleep(TRANSIENT_PAUSE)


def run_list_checked(args: list[str], *, timeout: int = 120) -> list:
    """`run_list`, but a failed CLI call raises instead of reading as an empty result.

    A polling loop cannot tell "no task yet" from "the call failed" when both answer with an
    empty list, so a broken lookup burns the whole gate budget and then reports the wrong cause.
    """
    for attempt in range(TRANSIENT_RETRIES + 1):
        reply = envelope(args, timeout=timeout)
        if reply.get("Result") == "Success":
            return _rows_of(reply.get("Data") or {})
        detail = envelope_detail(reply)
        if attempt == TRANSIENT_RETRIES or not _is_transient(detail):
            # `Message` is the generic one-liner (`Error listing tasks`); the reason the call was
            # refused rides in `Instructions`. Reporting only `Message` cost a route its whole
            # budget and named nothing actionable.
            raise RuntimeError(f"`{' '.join(args[:3])}` failed: {detail}")
        print(f"  `{' '.join(args[:3])}` came back {detail}; retrying in {TRANSIENT_PAUSE}s")
        time.sleep(TRANSIENT_PAUSE)


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
    ids = [int(r["Id"]) for r in run_list(TASKS_LIST) if r.get("Id")]
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
    for row in run_list_checked(TASKS_LIST):
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
    rows = [r for r in run_list(TASKS_LIST)
            if (r.get("Title") or "") == title]
    print(f"  watermark {watermark}, instance {instance_id}, {len(rows)} task(s) carry this title")
    for row in sorted(rows, key=lambda r: int(r.get("Id") or 0))[-6:]:
        tid = int(row.get("Id") or 0)
        # Every filter it fails, not the first one. Reporting only the first read a task
        # as `already Completed` and stopped, so whether it even belonged to this instance
        # stayed unknown. That is the difference between a gate something else answered
        # and another run's task that was never ours.
        why = []
        if tid <= watermark:
            why.append(f"id <= watermark {watermark}, predates this run")
        if str(tid) in done:
            why.append("already driven by this run")
        if row.get("Status") == "Completed":
            why.append("already Completed")
        mine = row.get("CreatorJobKey") == instance_id
        why.append("this instance" if mine else f"raised by instance {row.get('CreatorJobKey')}")
        if not why[:-1] and mine:
            why = ["PASSES every filter, so the lookup should have taken it"]
        print(f"    {tid} {row.get('Status')} created {row.get('CreatedTime')}: {'; '.join(why)}")


# Orchestrator's answer when the action already landed. `envelope_retrying` retries a
# write on a transient marker, so a completion that reached the server and then answered
# with one gets sent again, and the second attempt is refused. Run 34672482504's
# compliance-reject lost its first gate exactly there, on a task the same identity had
# already completed. The state the caller wanted is the state the task is in.
_ALREADY_COMPLETED = "already completed by the same user"


def complete_gate(task: dict, action: str, who: str, data: dict | None = None) -> None:
    task_id = str(task["Id"])
    folder_id = str(task.get("FolderId") or "")
    if not folder_id:
        fail(f"task {task_id} carries no FolderId; cannot complete it")
    # `tasks assign` reports Success whenever the SDK call does not throw, and Orchestrator
    # answers a refused assignment with HTTP 200 carrying an error body, so the envelope
    # alone proves nothing. Read the task back and see whose name is on it: the symptom
    # otherwise arrives one step later as `tasks complete` saying the action is no longer
    # assigned to you, which does not say who holds it.
    # `tasks users <folder-id>` is the folder's assignable set, and its own help says to
    # pass the resulting user ID to `tasks assign`. An email that is not in that set is
    # what an assign refuses while still answering Success.
    allowed = run_list(["uip", "tasks", "users", folder_id, "--output", "json"])
    mine = next((u for u in allowed
                 if who in (u.get("UserName"), u.get("EmailAddress"), u.get("Name"))), None)
    if mine is None:
        fail(f"{who!r} is not in the assignable set for folder {folder_id}. That folder allows "
             f"{[u.get('UserName') or u.get('EmailAddress') for u in allowed][:8]}, so an assign "
             f"to {who!r} cannot take effect and `tasks complete` then reports the action is no "
             f"longer assigned to you")
    by_id = ["--user-id", str(mine["Id"])] if mine.get("Id") else ["--user", who]
    assigned = envelope_retrying(["uip", "tasks", "assign", task_id, *by_id, "--output", "json"])
    if assigned.get("Result") != "Success":
        fail(f"assigning task {task_id} to {who} failed: "
             f"{envelope_detail(assigned)}")
    # The assign lands on `AssignedToUserId`, but completion is gated on the task's
    # assignment criteria, which is a separate field. `AppTasksFacade.cs:782` maps a group
    # recipient to `AllUsers`, and Orchestrator then answers `tasks complete` with "this
    # action is no longer assigned to you" for any caller outside that group, whatever
    # `AssignedToUserId` says.
    back = envelope(["uip", "tasks", "get", task_id, "--output", "json"])
    holder = back.get("Data") or {}
    if holder.get("TaskAssignmentCriteria") == "AllUsers" and not holder.get(
        "IsCurrentUserInAllUserAssignedGroup"
    ):
        fail(f"task {task_id} carries TaskAssignmentCriteria 'AllUsers' and "
             f"IsCurrentUserInAllUserAssignedGroup is false, so {who!r} cannot complete it "
             f"however the assign reads. The SDD routes this task to a role, the engine maps a "
             f"group recipient to the AllUsers criteria, and the driving identity is not in that "
             f"group. AssignedToUserId={holder.get('AssignedToUserId')}, "
             f"LastAssignedTime={holder.get('LastAssignedTime')}")
    if not holder.get("AssignedToUserId"):
        fail(f"`tasks assign` reported Success for task {task_id}, and reading it back shows no "
             f"AssignedToUserId. Orchestrator answers a refused assignment with HTTP 200 and an "
             f"error body, so the envelope is not evidence. assign returned: "
             f"{str(assigned.get('Data'))[:300]}")
    reply = envelope_retrying([
        "uip", "tasks", "complete", task_id,
        "--type", "AppTask",
        "--folder-id", folder_id,
        "--action", action,
        "--data", json.dumps(data or {"Comment": f"Driven by the SupplierOnboarding e2e check ({action})."}),
        "--output", "json",
    ])
    if reply.get("Result") != "Success" and _ALREADY_COMPLETED in envelope_detail(reply).lower():
        print(f"  task {task_id} was already completed with this identity; the retry "
              "answered for a write that had landed")
        reply = {"Result": "Success"}
    if reply.get("Result") != "Success":
        detail = [f"completing task {task_id} with action {action!r} failed: "
                  f"{reply.get('Message') or reply.get('Code') or reply}"]
        for key in ("Instructions", "Stderr"):
            if reply.get(key):
                detail.append(f"  {key}: {str(reply[key])[:600]}")
        fail("\n".join(detail))

    # Read it back, for the same reason the assign above is read back: the envelope says
    # the SDK call did not throw, not that the task moved. Two routes ended with the gate
    # answered in this log, the decision variable still `None` and the case never
    # advancing: 34664083574's sendback and 34661773724's compliance-reject. A completion
    # that reported Success without landing produces exactly that.
    after = (envelope(["uip", "tasks", "get", task_id, "--output", "json"]).get("Data")
             or {})
    status = str(after.get("Status") or "")
    if status != "Completed":
        fail(f"`tasks complete` reported Success for task {task_id} with action "
             f"{action!r}, and reading it back shows Status {status!r}. The case is "
             "still waiting on this gate, so the route stalls with the decision "
             "variable unwritten.")


def incidents(instance_id: str) -> list:
    data = run(["uip", "maestro", "case", "instance", "incidents", instance_id,
                "-f", CASE_FOLDER_KEY, "--output", "json"])
    return data if isinstance(data, list) else (data.get("value") or [])


def describe_incident(item: dict) -> str:
    """One incident, keeping both ends of its message.

    A rules-evaluation failure reads `Failed to evaluate expression <the whole rule as
    JSON>: <the reason>`, so the reason sits at the end. Printing only the head shows
    several hundred characters of the rule and cuts off the one sentence that says what
    went wrong.
    """
    detail = " ".join(
        str(item.get("ErrorDetails") or item.get("ErrorMessage") or item.get("Message") or "").split()
    )
    if len(detail) > 700:
        detail = f"{detail[:300]} ...[{len(detail) - 700} chars]... {detail[-400:]}"
    return f"{item.get('ElementId')!r} ({item.get('ErrorCode')}): {detail}"


# Incidents the case records that the plan cannot cause. Both are content-free service
# errors raised while invoking an agent, with every input on the task correctly bound.
# Measured across 17 runs: 27 incidents in all, and only these two carry no plan input.
# `Input validation failed`, the expression errors and the Integration Services 400s each
# name something the build wrote.
_PLATFORM_INCIDENTS = (
    "llm model not available",
    "http request failed",
)


def incidents_are_all_platform(raised: list) -> bool:
    """True when every incident is a service fault, so the route judges nothing."""
    if not raised:
        return False
    for item in raised:
        if not any(m in describe_incident(item).lower() for m in _PLATFORM_INCIDENTS):
            return False
    return True


def fail_with_diagnosis(instance_id: str, msg: str):
    """Fail, but first print what the case itself says about why.

    post_run deletes the solution when the task ends, and the instance record goes with it, so
    an incident that is readable now is unreadable by the time anyone opens the result. Whatever
    the case recorded has to be captured here or not at all.
    """
    # The status separates a case that ended on its own from one the platform closed
    # underneath the driver, and without it both read as "the case finished".
    print(f"  run status {run_status(instance_id)!r}")
    raised = incidents(instance_id)
    for item in raised[:4]:
        print(f"  incident on {describe_incident(item)}")
    if incidents_are_all_platform(raised):
        msg = (f"{msg}. Every incident on this instance is a service fault, so the route "
               "carries no verdict about the plan")
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
    reply = envelope_retrying([
        "uip", "maestro", "case", "instance", "message", "send",
        "-f", CASE_FOLDER_KEY, "--inputs", json.dumps(message), "--output", "json",
    ])
    if reply.get("Result") != "Success":
        fail(f"stage selection {from_stage!r} -> {to_stage!r} was rejected: {envelope_detail(reply)}")


def run_status(instance_id: str) -> str:
    """The instance's run status. `instance get` reports it as LatestRunStatus, not Status."""
    data = run_checked(["uip", "maestro", "case", "instance", "get", instance_id, "-f", CASE_FOLDER_KEY, "--output", "json"])
    return data.get("LatestRunStatus") or ""


def globals_of(instance_id: str) -> dict:
    """The case's own variables at the end of the run. Names come back PascalCase: CaseOutcome, not caseOutcome."""
    data = run_checked(["uip", "maestro", "case", "instance", "variables", instance_id, "-f", CASE_FOLDER_KEY, "--output", "json"])
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


def stage_runs(instance_id: str, display_name: str) -> int:
    """How many `ElementRun` records this stage carries.

    NOT the number of visits. One visit writes two records, `InProgress` then
    `Completed`, measured on every stage of three finished instances. So 0 means the
    case never reached the stage, 2 means one visit, and 4 means it came back.
    Reading this as a visit count is how the sendback assertion came to pass on a
    case that was never sent back.
    """
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
            status = run_status(instance_id)
            if status == "Cancelled":
                # This route's only idle stretch is the 16-minute wait for the intake
                # deadline, which is longer than the window `uip maestro case debug`
                # allows with no progress. An instance the platform closed there says
                # nothing about the SLA, and calling it a plan defect sent the reader
                # to look at a rule that had not been reached yet.
                fail_with_diagnosis(
                    instance_id,
                    "the instance was cancelled while waiting for the intake deadline; "
                    "the debug run gave up before the SLA could breach, so this route "
                    "carries no verdict about the plan",
                )
            if status in FINISHED:
                # Which stages it did reach says whether the SLA was never armed or
                # the case left the intake phase by another route.
                fail_with_diagnosis(
                    instance_id,
                    "the case finished before the intake phase breached; its SLA never "
                    "fired",
                )
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
        with_profile(["uip", "maestro", "case", "debug", project_dir,
                      "--output", "json", "--log-level", "debug"]),
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
        # A Faulted case records why it faulted, and post_run deletes the instance with
        # the solution, so the reason has to be read here or it is gone.
        fail_with_diagnosis(
            instance_id,
            f"the case ended {status!r}; every route in this test must run to completion",
        )

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
        if not stage_runs(instance_id, WITHDRAWN):
            fail(f"the case never entered {WITHDRAWN!r}; a review stage must offer it as a choice")
    elif args.route == "reject":
        if buyer != "reject":
            fail(f"the buyer's decision never reached the case: {BUYER_DECISION}={buyer!r}, expected 'reject'")
        if outcome != "Rejected":
            fail(f"the buyer declined but CaseOutcome={outcome!r}; the decline guard did not route the case")
    elif args.route == "sendback":
        # Two records per visit, so a second visit is four. `< 2` only caught a case
        # that never reached the stage at all, which let every un-sent-back run pass.
        runs = stage_runs(instance_id, CHECKING)
        if runs < 4:
            fail(f"{CHECKING!r} was visited {runs // 2} time(s) ({runs} run records); "
                 "a sendback must send the case back into it")
        if buyer != "approve":
            fail(f"the second buyer decision never landed: {BUYER_DECISION}={buyer!r}, expected 'approve'")

    elif args.route == "onboard":
        if outcome != "Onboarded":
            fail(f"every gate was approved but CaseOutcome={outcome!r}; this route must reach {ONBOARDED!r}")
        if bank != "verified":
            fail(f"the setup stage completed with {BANK_STATUS}={bank!r}; the portal gate only opens on 'verified'")
        if not g.get("SupplierId"):
            fail("the case onboarded a supplier and recorded no SupplierId; the ERP task wrote nothing back")
        if compliance != "approve":
            fail(f"{COMPLIANCE_DECISION}={compliance!r} on a route that approved every gate")
    elif args.route == "no-withdraw-in-setup":
        # Every stage the case passed through, and which of them offered a choice. The
        # three review stages must; setup must not, or a supplier could pull out after
        # the ERP record exists.
        offered = {
            stage_label(row.get("ElementId", "").split("CaseWaitForUser_StageSelection_")[-1])
            for row in executions(instance_id)
            if (row.get("ElementId") or "").startswith("CaseWaitForUser_StageSelection_")
        }
        if SETUP in offered:
            fail(f"{SETUP!r} offered a stage picker; the source allows withdrawal only before setup begins")
        if not offered & {CHECKING, BUYER, COMPLIANCE}:
            fail(f"no review stage offered a picker at all, so this route proves nothing; saw {sorted(offered)}")
        print(f"  stage pickers offered by: {sorted(offered)}; {SETUP!r} offered none")
    elif args.route == "compliance-reject":
        # A closed case must not be movable. The picker message is the only way anything
        # moves a case between stages, so sending one after the case has closed is the
        # test: nothing may match it. Checked here rather than on its own route, because
        # this is the shortest way to a terminal outcome.
        terminals = (ONBOARDED, REJECTED, WITHDRAWN)
        before = {label: stage_runs(instance_id, label) for label in terminals}
        send_stage_selection(instance_id, REJECTED, ONBOARDED)
        time.sleep(POLL_SLEEP * 2)
        after = {label: stage_runs(instance_id, label) for label in terminals}
        moved = {k: (before[k], after[k]) for k in before if before[k] != after[k]}
        if moved:
            fail(f"a closed case moved when sent a stage selection: {moved}")
        again = run_status(instance_id)
        if again != status:
            fail(f"a closed case changed run status from {status!r} to {again!r} on a stage selection")
        print(f"  closed case ignored a stage selection; still {again!r}")
        if compliance != "reject":
            fail(f"the compliance decision never reached the case: {COMPLIANCE_DECISION}={compliance!r}")
        if buyer != "approve":
            fail(f"{BUYER_DECISION}={buyer!r}; this route proves a later reject stands over an earlier approve")
        if outcome != "Rejected":
            fail(f"compliance rejected but CaseOutcome={outcome!r}; the reject row did not route the case")

    # Applies to every route, not one of them. The two readings the case can end on are tied
    # to where the route stopped: `verified` belongs to a route that completed setup, and a
    # rejection alongside it means the setup stage routed on something the SDD does not
    # describe. `pending` is the variable's own default and means the ERP task never ran.
    if bank == "verified" and outcome == "Rejected":
        fail(f"bank verification passed but CaseOutcome={outcome!r}; setup should have completed to {ONBOARDED!r}")
    if bank == "failed" and outcome not in ("Rejected", "Withdrawn"):
        fail(f"bank verification returned {bank!r} but CaseOutcome={outcome!r}; that route must end in {REJECTED!r}")

    print(f"OK: route {args.route!r} ran to completion with CaseOutcome={outcome!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
