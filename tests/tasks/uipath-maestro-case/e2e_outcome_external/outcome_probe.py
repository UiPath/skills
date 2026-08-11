#!/usr/bin/env python3
"""Shared plumbing for the outcome-based graders.

Three separate criteria need the case to have RUN, but coder_eval does not
guarantee the order criteria are evaluated in (and may run them concurrently).
``ensure_debug_ran`` therefore makes execution idempotent: the first grader to
arrive runs ``uip solution resources refresh`` + ``uip maestro case debug`` and
publishes the payload to ``debug_result.json``; the others reuse it. An
exclusive lock file keeps two concurrent graders from launching two debug runs.

The external reads go to the vendor's real API (Microsoft Graph, Atlassian) but
authenticate through the tenant's existing Integration Service connection, so no
third-party credentials are needed in CI.
"""

from __future__ import annotations

import glob
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone

OUTLOOK_CONN = "dd657127-91f5-4568-a3a3-c024bc03fb0f"
JIRA_CONN = "f5273a4d-d492-4bcd-a106-5a20bf89a3ef"
JIRA_PROJECT = "SJP"
MAILBOX_FOLDER = "Inbox"

DEBUG_RESULT = "debug_result.json"
DEBUG_LOCK = "debug_result.lock"

# Two independent sources of lag, so the budget is generous (~10 min):
#   1. Graph is not immediately consistent — a delivered message can take minutes
#      to become searchable.
#   2. `uip maestro case debug` gives up polling after a fixed 600 s, but the case
#      keeps running server-side. Measured 2026-08-07: the CLI timed out at 600 s
#      and the case's effects landed ~7 min later. A short probe budget reports a
#      false negative for a case that did its job.
POLL_ATTEMPTS = 20
POLL_SLEEP = 30

# Terminal instance states, used when falling back to instance polling.
TERMINAL_STATES = {"Completed", "Successful", "Faulted", "Cancelled", "Canceled", "Stopped"}
INSTANCE_WAIT_SECONDS = 600
INSTANCE_POLL_SLEEP = 20

# Waiting for a peer grader's debug run; must exceed a cold debug (pack + deploy
# + execute), which measured ~60s but can be far slower on a loaded tenant.
PEER_WAIT_SECONDS = 900

# A lock older than this had its owner killed (coder_eval kills a criterion at its
# timeout, so the `finally` that releases the lock never runs). Must exceed the
# worst honest debug duration: 600s CLI poll + INSTANCE_WAIT_SECONDS.
STALE_LOCK_SECONDS = 1500

# Clock-skew tolerance when comparing a third-party timestamp to our debug start.
SKEW_SECONDS = 30


def precondition_failed(msg: str) -> None:
    """Fail loudly and label the cause as environmental.

    NOTE: coder_eval has no skip semantics — a non-zero exit scores the criterion
    as failed regardless of the message. This only makes triage unambiguous for a
    human reading the log. The real guard is the connection health check in
    ``pre_run`` (``seed_outcome.py``), which fails before an agent run is spent.
    """
    sys.exit(f"test precondition failed: {msg} — this is an ENVIRONMENT gap "
             "(unhealthy connection / missing sandbox fixture), NOT a skill regression")


def _to_epoch(stamp: str | None) -> float | None:
    """Parse the timestamp shapes these two APIs return, into epoch seconds.

    Graph returns ``2026-08-07T23:55:17Z``; Jira returns
    ``2026-08-08T02:55:28.242+0300`` (offset without a colon). Both must be
    comparable to the harness's debug-start time.
    """
    if not stamp:
        return None
    text = str(stamp).strip().replace("Z", "+00:00")
    # Normalize ±HHMM to ±HH:MM, which datetime.fromisoformat requires on <3.11.
    match = re.search(r"([+-]\d{2})(\d{2})$", text)
    if match:
        text = text[: match.start()] + f"{match.group(1)}:{match.group(2)}"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.timestamp()


def fail(msg: str) -> None:
    sys.exit(f"FAIL: {msg}")


def run_token() -> str:
    if not os.path.exists("seed.json"):
        precondition_failed("seed.json is missing; pre_run seed_outcome.py did not run")
    with open("seed.json") as fh:
        token = (json.load(fh) or {}).get("run_token")
    if not token:
        precondition_failed("seed.json carries no run_token")
    return token


def _uip_json(args: list[str], timeout: int = 180) -> dict:
    r = subprocess.run(["uip", *args, "--output", "json"],
                       capture_output=True, text=True, timeout=timeout)
    try:
        return json.loads(r.stdout)
    except Exception:
        return {"Result": "ParseError", "raw": (r.stdout or "")[-1500:],
                "err": (r.stderr or "")[-800:]}


def _items(payload: dict) -> list:
    d = payload.get("Data") or {}
    if isinstance(d, list):
        return d
    return d.get("items") or d.get("Items") or []


def _find_dir(pattern: str) -> str:
    hits = glob.glob(pattern, recursive=True)
    if not hits:
        fail(f"nothing matching {pattern} — the agent did not produce a case solution")
    return os.path.dirname(sorted(hits, key=len)[0])


def _our_stage_ids() -> set:
    """Stage node ids from the caseplan the agent built.

    These are randomly minted per build (e.g. ``Stage_aR4mK9``), which makes them
    a reliable fingerprint for OUR instance. Trigger ids are not: the skill often
    emits the literal ``trigger_1``, which any other case can also carry.
    """
    hits = glob.glob("**/caseplan.json", recursive=True)
    if not hits:
        return set()
    try:
        with open(sorted(hits, key=len)[0]) as fh:
            plan = json.load(fh)
    except Exception:
        return set()
    return {n.get("id") for n in (plan.get("nodes") or [])
            if "Stage" in str(n.get("type")) and n.get("id")}


def _instance_is_ours(instance_id: str, folder_key: str, stage_ids: set) -> bool:
    """True when the instance executed elements belonging to OUR caseplan.

    The runtime names per-stage elements after the stage id (e.g.
    ``stageSlaEventSubprocess_Stage_aR4mK9``), so a substring match identifies the
    instance without needing an id the CLI never gave us.
    """
    payload = _uip_json(["maestro", "case", "instance", "variables",
                         str(instance_id), "--folder-key", str(folder_key)])
    elements = (payload.get("Data") or {}).get("Elements") or []
    seen = " ".join(str(e.get("ElementId") or "") for e in elements)
    return any(stage_id in seen for stage_id in stage_ids)


def _newest_debug_instance(since_iso: str) -> dict | None:
    """Find OUR Studio Web Debug instance started after ``since_iso``.

    The tenant is shared: other people's debug instances land in the same window
    (measured 2026-08-07 — a foreign instance reached Completed while ours was
    still stalled, and following "the newest" would have reported their success as
    ours). So candidates are fingerprinted against this build's stage ids.

    Deliberately does not filter by folder: debug lands the instance in the
    invoking user's personal workspace, whose key differs per user and per CI
    identity.
    """
    payload = _uip_json(["maestro", "case", "instance", "list"])
    data = payload.get("Data") or {}
    instances = data if isinstance(data, list) else (
        data.get("Items") or data.get("items") or [])
    candidates = [
        i for i in instances
        if str(i.get("Source") or "") == "Studio Web Debug"
        and str(i.get("CreatedTimeUtc") or "") >= since_iso
    ]
    if not candidates:
        return None

    stage_ids = _our_stage_ids()
    if not stage_ids:
        print("  cannot fingerprint our instance (no caseplan stage ids); "
              "refusing to follow one")
        return None

    ours = [i for i in candidates
            if _instance_is_ours(i.get("InstanceId"), i.get("FolderKey"), stage_ids)]
    if not ours:
        # An instance that stalls BEFORE entering a stage runs only generic
        # elements (trigger_1, CaseInitialVariablesSetupNode, caseStartedSendMessage
        # …), and its server-minted PackageId appears nowhere on disk — so there is
        # no way to tell it apart from a stranger's. Refuse rather than guess: this
        # criterion is the vehicle, and the outcome probes are token-scoped, so they
        # still report the truth about whether the case did its job.
        ids = ", ".join(str(i.get("InstanceId")) for i in candidates)
        print(f"  none of the {len(candidates)} debug instance(s) in this window "
              f"carry our stage ids {sorted(stage_ids)} — cannot identify ours "
              f"(an instance stalled before its first stage is indistinguishable): {ids}")
        return None
    return max(ours, key=lambda i: str(i.get("CreatedTimeUtc") or ""))


def _await_instance(since_iso: str) -> dict:
    """Poll the instance to a terminal state after the CLI stopped waiting.

    ``uip maestro case debug`` abandons its own polling at a fixed 600 s, but the
    case keeps executing. Treating that as a failure mis-reports a case that
    completes a minute later, so the instance itself is the source of truth.
    """
    instance = _newest_debug_instance(since_iso)
    if not instance:
        return {}
    instance_id = instance.get("InstanceId")
    folder_key = instance.get("FolderKey")
    print(f"  debug CLI stopped polling; following instance {instance_id}")

    waited = 0
    status = instance.get("LatestRunStatus")
    while waited < INSTANCE_WAIT_SECONDS:
        if status in TERMINAL_STATES:
            break
        time.sleep(INSTANCE_POLL_SLEEP)
        waited += INSTANCE_POLL_SLEEP
        got = _uip_json(["maestro", "case", "instance", "get", str(instance_id),
                         "--folder-key", str(folder_key)])
        status = ((got.get("Data") or {}).get("LatestRunStatus")) or status

    print(f"  instance {instance_id} reached status={status} after {waited}s")
    return {"finalStatus": status, "instanceId": instance_id,
            "followedInstance": True}


def _do_debug(since: str) -> dict:
    solution_dir = _find_dir("**/*.uipx")
    project_dir = _find_dir("**/project.uiproj")

    # Resource refresh is mandatory: without it the connector resources are not
    # resolvable at runtime and debug reports "Resource is not configured".
    r = _uip_json(["solution", "resources", "refresh",
                   "--solution-folder", solution_dir])
    if r.get("Result") != "Success":
        blob = json.dumps(r)
        # Refresh is not idempotent — re-running it over its own output fails.
        # When the agent already refreshed, the resource docs are on disk and
        # debug can proceed; only that exact failure is tolerated.
        if "Node already added to the graph" not in blob:
            fail(f"solution resources refresh failed: {blob[:600]}")

    payload = _uip_json(["maestro", "case", "debug", project_dir], timeout=1500)
    data = payload.get("Data") if isinstance(payload, dict) else None
    data = data if isinstance(data, dict) else {}

    if not any(data.get(k) for k in ("finalStatus", "FinalStatus", "status", "Status")):
        data = {**data, **_await_instance(since)}

    return {"envelope": {k: v for k, v in payload.items() if k != "Data"},
            "data": data,
            # Attribution floor for the outcome probes: only effects at or after
            # this instant can have come from the case the harness just ran.
            "debug_started_at": since + "+00:00"}


def _claim_lock() -> str | None:
    """Take ownership of the debug run, returning the attribution floor to use.

    The lock file carries the ISO instant its owner started. That matters when a
    stale lock is taken over: reusing the ORIGINAL start keeps the attribution
    floor from sliding forward, which would otherwise discard effects the first
    (killed) debug run legitimately produced.

    Returns None when another grader holds a live lock.
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    try:
        fd = os.open(DEBUG_LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, now.encode())
        os.close(fd)
        return now
    except FileExistsError:
        pass

    age = time.time() - os.path.getmtime(DEBUG_LOCK)
    if age <= STALE_LOCK_SECONDS:
        return None

    # The owner died without publishing — coder_eval kills a criterion at its
    # timeout, so `finally` never runs. Take over rather than waiting out
    # PEER_WAIT_SECONDS and reporting a timeout instead of the real problem.
    try:
        with open(DEBUG_LOCK) as fh:
            original = (fh.read() or "").strip()
    except OSError:
        original = ""
    print(f"  taking over a stale debug lock (age {int(age)}s); "
          f"keeping the original attribution floor {original or '<unknown>'}")
    return original or now


def ensure_debug_ran() -> dict:
    """Run the case once per task, no matter how many graders ask for it."""
    if os.path.exists(DEBUG_RESULT):
        with open(DEBUG_RESULT) as fh:
            return json.load(fh)

    floor = _claim_lock()
    while floor is None:
        # A peer grader owns the debug run — wait for it to publish.
        waited = 0
        while waited < PEER_WAIT_SECONDS:
            if os.path.exists(DEBUG_RESULT):
                with open(DEBUG_RESULT) as fh:
                    return json.load(fh)
            time.sleep(5)
            waited += 5
            floor = _claim_lock()   # the peer may have died mid-wait
            if floor is not None:
                break
        else:
            fail("timed out waiting for a peer grader's case debug run")

    # Always publish SOMETHING and always drop the lock. A bare `_do_debug()` here
    # stranded the lock on failure (its internal `fail()` raises SystemExit), which
    # made every peer grader wait out PEER_WAIT_SECONDS and then report a timeout
    # instead of the real error.
    try:
        result = _do_debug(floor)
    except BaseException as exc:
        result = {"envelope": {"Result": "Failure",
                               "Message": f"case debug raised: {exc!r}"},
                  "data": {}}
        with open(DEBUG_RESULT, "w") as fh:
            json.dump(result, fh, indent=1, default=str)
        raise
    else:
        with open(DEBUG_RESULT, "w") as fh:
            json.dump(result, fh, indent=1, default=str)
        return result
    finally:
        try:
            os.remove(DEBUG_LOCK)
        except OSError:
            pass


def final_status(result: dict) -> str | None:
    data = result.get("data") or {}
    for key in ("finalStatus", "FinalStatus", "status", "Status"):
        if data.get(key):
            return data[key]
    return None


def debug_started_at() -> float | None:
    """Epoch seconds when the HARNESS started the case, from ``debug_result.json``."""
    if not os.path.exists(DEBUG_RESULT):
        return None
    try:
        with open(DEBUG_RESULT) as fh:
            return _to_epoch((json.load(fh) or {}).get("debug_started_at"))
    except Exception:
        return None


def require_attributable(result: dict) -> None:
    """Refuse to measure outcomes unless the HARNESS actually ran the case.

    If no debug run happened, any email/issue bearing this run's token is
    unattributable — it could be a leftover, or the agent's own execution — so
    searching for one is not just pointless but actively misleading. Fail fast
    with the reason instead of polling for ten minutes and reporting "not found",
    which reads like the case did nothing when in truth nothing was measured.

    Deliberately requires only that a debug run was ATTEMPTED and a floor stamped,
    NOT that it reached a terminal status: a case whose effects land after the CLI
    stops polling (measured ~7 min late) has genuinely met the objective, and that
    recovery must stay possible. Whether it completed is graded separately by
    check_case_ran.py.
    """
    if debug_started_at() is None:
        envelope = (result or {}).get("envelope")
        fail("cannot attribute outcomes: the harness never established a debug start "
             f"for this run, so nothing measured here belongs to the case. envelope={envelope}")


def _only_after(hits: list, stamp_key: str, label: str) -> list:
    """Drop records that predate the harness-owned case run.

    Attribution guard. The token alone proves a record mentions this run; it does
    NOT prove the CASE produced it. An agent can reach the same connectors by any
    route the `command_not_executed` patterns miss — e.g. wrapping the CLI in a
    helper script and invoking `python3 helper.py`. Anything the agent creates
    necessarily predates the harness's debug run, which starts only after the
    agent has finished, so a timestamp floor removes that whole class of bypass.

    Fails CLOSED when the floor is unknown. Without a floor there is nothing to
    attribute against — the run token names the run, not which execution produced
    the record — so any hit could be a leftover or the agent's own doing. Callers
    must therefore establish the floor (see ``require_attributable``) before
    probing; reaching here without one is a bug, not a soft condition.
    """
    floor = debug_started_at()
    if floor is None:
        fail("no attribution floor: the harness never stamped a debug start, so no "
             "record can be attributed to the case (see require_attributable)")
    kept, dropped = [], []
    for hit in hits:
        when = _to_epoch(hit.get(stamp_key))
        # Small negative skew only: measured Graph/Atlassian stamps agreed with
        # ours to the second, and a wide window would let an execution that ran
        # just BEFORE the floor (e.g. an agent that ran debug itself) slip in.
        if when is None or when >= floor - SKEW_SECONDS:
            kept.append(hit)
        else:
            dropped.append(hit)
    for hit in dropped:
        print(f"  [{label}] IGNORED record predating the case run "
              f"({hit.get(stamp_key)}): {hit}")
    return kept


def probe_email(token: str) -> list:
    """Messages in the shared sandbox mailbox whose subject carries the token.

    Pages recent messages and matches CLIENT-SIDE. A server-side
    ``contains(subject,…)`` filter is available but is backed by an index that
    lags delivery, so it can report zero for a message that already arrived.
    """
    payload = _uip_json([
        "is", "resources", "run", "list",
        "uipath-microsoft-outlook365", "ListEmails",
        "--connection-id", OUTLOOK_CONN,
        "--query", f"parentFolderId={MAILBOX_FOLDER}&limit=100",
    ])
    if payload.get("Result") != "Success":
        blob = json.dumps(payload)
        if any(s in blob for s in ("Unauthorized", "invalid_grant", "401", "403")):
            precondition_failed(f"cannot read the sandbox mailbox: {blob[:400]}")
        return []
    hits = [
        {"subject": m.get("subject"), "received": m.get("receivedDateTime")}
        for m in _items(payload)
        if token in (m.get("subject") or "")
    ]
    return _only_after(hits, "received", "email")


def probe_issue(token: str) -> list:
    """Issues in the shared sandbox project whose summary carries the token."""
    payload = _uip_json([
        "is", "resources", "run", "list",
        "uipath-atlassian-jira", "issue_search_get",
        "--connection-id", JIRA_CONN,
        "--query", (f'jql=project={JIRA_PROJECT} AND summary~"{token}"'
                    "&fields=key,summary,created"),
    ])
    if payload.get("Result") != "Success":
        blob = json.dumps(payload)
        if any(s in blob for s in ("Unauthorized", "invalid_grant", "401", "403")):
            precondition_failed(f"cannot read the sandbox Jira project: {blob[:400]}")
        return []
    out = []
    for issue in _items(payload):
        fields = issue.get("fields") or {}
        if token in (fields.get("summary") or ""):
            out.append({"key": issue.get("key"),
                        "summary": fields.get("summary"),
                        "created": fields.get("created")})
    return _only_after(out, "created", "jira")


def poll(label: str, probe, token: str) -> list:
    for attempt in range(1, POLL_ATTEMPTS + 1):
        hits = probe(token)
        if hits:
            print(f"  [{label}] found on attempt {attempt}")
            return hits
        if attempt < POLL_ATTEMPTS:
            time.sleep(POLL_SLEEP)
    return []
