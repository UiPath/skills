#!/usr/bin/env python3
"""OUTCOME: the case actually sent the buyer notification.

Measured in the mailbox itself, through the same Integration Service connection the case
sends on. Not in caseplan.json, not in the debug log, not in anything the agent said. A
connector task can report Completed while the message never leaves: the commonest cause is
`saveAsDraft` left at its default of true, which files the mail as a draft that no
recipient ever sees.

Sent Items is the folder that answers the question. A draft never reaches it, and a message
with no recipient is never accepted for sending, so a message here proves both. Delivery is
a separate matter and deliberately not graded: whether the supplier's address resolves
depends on the contactEmail default the build chose, and the sandbox address in the staged
SDD bounces, so every send lands a bounce notice in the Inbox. Grading the Inbox would fail
a correct build for a fixture's choice of address.

Attribution is by the case's own ExternalId. Of the six connector tasks only 'Notify
buyer of application' puts it in the subject; every other subject carries just the company
name, which is identical across runs and cannot identify one. That one message is enough:
it is the first sequential task in 'Buyer review', so every route that leaves the intake
stage sends it exactly once.

Reads every route drive_case.py ran, from the list it accumulates in RUN_STATE, and grades
each one against its own expected count. Grading only the last route lets `withdraw`, which
should send nothing, stand in for the routes that must send.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
RUN_STATE = Path(".supplier-onboarding-run.json")

# No pinned folder: the case lands in whatever folder the run's own solution creates, and
# drive_case.py records the one its instance reported. A pinned key aims every lookup at a
# folder that may not exist, and the CLI answers that with a 404 — which the old reader
# could not tell from an instance that genuinely carries no id.
OUTLOOK_CONNECTOR = "uipath-microsoft-outlook365"
OUTLOOK_CONNECTION = "dd657127-91f5-4568-a3a3-c024bc03fb0f"
# `parentFolderId` is required: without it the query returns nothing at all.
SENT_FOLDER = "SentItems"

# How many buyer notifications each route should have sent. `Notify buyer of application` is the
# first sequential task in 'Buyer review', so the count is the number of times the case entered
# that phase: once normally, twice when a sendback returns it there, never when the supplier
# withdraws before the phase is reached.
EXPECTED_SENDS = {"reject": 1, "sendback": 2, "sla": 1, "withdraw": 0}

# Delivery lags the connector's own Completed status, so the mailbox is polled.
POLL_ATTEMPTS = 10
POLL_SLEEP = 15


def fail(msg: str):
    print(f"FAIL: {msg}")
    sys.exit(1)


def uip(args: list[str], timeout: int = 120) -> dict:
    try:
        proc = subprocess.run(["uip", *args, "--output", "json"],
                              capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"Result": "Failure", "Message": f"timed out after {timeout}s"}
    start = proc.stdout.find("{")
    if start < 0:
        return {"Result": "Failure", "Message": (proc.stderr or proc.stdout)[:400]}
    try:
        return json.loads(proc.stdout[start:])
    except json.JSONDecodeError:
        return {"Result": "Failure", "Message": proc.stdout[:400]}


def external_id(instance_id: str, folder_key: str) -> tuple[str, str]:
    """The instance's ExternalId, and the reason it is absent when it is.

    Returns `(id, "")` on success and `("", reason)` otherwise. The two cases are reported
    separately because they call for opposite responses: a lookup that failed says nothing
    about the build, while an instance that genuinely carries no id means its messages cannot
    be attributed. The engine mints one for every debug instance
    (`ExternalIdGenerator.Make8DigitCode`), so in practice the empty case is a lookup fault.
    """
    if not folder_key:
        return "", "drive_case recorded no folder for it"
    reply = uip(["maestro", "case", "instance", "get", instance_id, "-f", folder_key])
    if reply.get("Result") != "Success":
        return "", f"the lookup failed: {str(reply.get('Message'))[:120]}"
    token = str((reply.get("Data") or {}).get("ExternalId") or "")
    return (token, "") if token else ("", "the instance reports no ExternalId")


def sent_messages() -> list:
    """Recent messages in the shared sandbox mailbox's Sent Items.

    Matching happens here rather than in a server-side `contains(subject,...)` filter: that
    filter is backed by an index that lags delivery and reports zero for mail already in
    the box.
    """
    payload = uip([
        "is", "resources", "run", "list", OUTLOOK_CONNECTOR, "ListEmails",
        "--connection-id", OUTLOOK_CONNECTION,
        "--query", f"parentFolderId={SENT_FOLDER}&limit=100",
    ])
    if payload.get("Result") != "Success":
        blob = json.dumps(payload)
        if any(s in blob for s in ("Unauthorized", "invalid_grant", "401", "403")):
            fail(f"cannot read the sandbox mailbox: {blob[:400]}")
        return []
    data = payload.get("Data") or {}
    if isinstance(data, list):
        return data
    for key in ("items", "value", "Items"):
        if isinstance(data.get(key), list):
            return data[key]
    return next((v for v in data.values() if isinstance(v, list)), [])


def main() -> int:
    if not RUN_STATE.exists():
        fail(f"{RUN_STATE.name} is missing; drive_case.py must run before this check")
    state = json.loads(RUN_STATE.read_text(encoding="utf-8"))
    # Every route that reached an instance is graded. Grading only the last one lets a route that
    # sends nothing by design stand in for the ones that must send, which is a free pass.
    runs = state.get("runs")
    if not runs and state.get("instance_id"):
        runs = [{"route": state.get("route"), "instance_id": state.get("instance_id")}]
    if not runs:
        fail(f"{RUN_STATE.name} records no route that reached a case instance")

    unknown = sorted({r.get("route") for r in runs if r.get("route") not in EXPECTED_SENDS})
    if unknown:
        fail(f"{RUN_STATE.name} names route(s) {unknown}, which have no expected send count")
    if not any(EXPECTED_SENDS[r["route"]] for r in runs):
        fail("no route that sends a buyer notification reached a case instance, so the mailbox "
             f"proves nothing; recorded routes: {sorted(r['route'] for r in runs)}")

    problems: list[str] = []
    tokens: dict[str, str] = {}
    for entry in sorted(runs, key=lambda r: r.get("route") or ""):
        route = entry["route"]
        instance_id = entry.get("instance_id") or ""
        token, reason = external_id(instance_id, entry.get("folder_key") or "")
        if token:
            tokens[route] = token
            print(f"route {route!r}: expecting {EXPECTED_SENDS[route]} buyer notification(s) "
                  f"carrying ExternalId {token}")
            continue
        message = (f"instance {instance_id} (route {route!r}) has no usable ExternalId — "
                   f"{reason}; nothing identifies its messages")
        if EXPECTED_SENDS[route]:
            problems.append(message)
        else:
            print(f"  skipped: {message}, and this route should send nothing anyway")

    # One mailbox read per round, graded for every route at once. Polling each route separately
    # multiplies the wait by the number of routes and outlives the criterion's own timeout.
    counts: dict[str, int] = {route: 0 for route in tokens}
    found: dict[str, list] = {route: [] for route in tokens}
    for attempt in range(POLL_ATTEMPTS):
        messages = sent_messages()
        for route, token in tokens.items():
            found[route] = [m for m in messages if token in (m.get("subject") or "")]
            counts[route] = len(found[route])
        if all(counts[r] >= EXPECTED_SENDS[r] for r in tokens):
            break
        if attempt + 1 < POLL_ATTEMPTS:
            time.sleep(POLL_SLEEP)

    for route in sorted(tokens):
        expected = EXPECTED_SENDS[route]
        for m in found[route]:
            print(f"  {route}: found {m.get('subject')!r} sent "
                  f"{m.get('sentDateTime') or m.get('receivedDateTime')}")
        if counts[route] == expected:
            print(f"  {route}: OK, {expected} buyer notification(s)")
        elif counts[route] < expected:
            problems.append(
                f"route {route!r}: {counts[route]} of {expected} buyer notification(s) carry "
                f"ExternalId {tokens[route]} after {POLL_ATTEMPTS * POLL_SLEEP}s. A connector task "
                "can report Completed and still send nothing: check that saveAsDraft is false and "
                "that message.toRecipients is bound.")
        else:
            problems.append(
                f"route {route!r}: {counts[route]} messages carry ExternalId {tokens[route]} but "
                f"the route enters 'Buyer review' {expected} time(s); an extra notification means "
                "the phase was entered again")

    if not problems:
        print(f"OK: {len(runs)} route(s) sent exactly the buyer notifications they should")
        return 0
    print(f"\nFAIL: {len(problems)} outcome finding(s):", file=sys.stderr)
    for item in problems:
        print(f"  - {item}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
