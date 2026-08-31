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

Attribution is by the case's own ExternalId. Of the eight connector tasks only 'Notify
buyer of application' puts it in the subject; every other subject carries just the company
name, which is identical across runs and cannot identify one. That one message is enough:
it is the first sequential task in 'Buyer review', so every route that leaves the intake
stage sends it exactly once.

Reads the instance drive_case.py just ran, whose id it left in RUN_STATE.
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

CASE_FOLDER_KEY = "30b98ad6-522a-4630-85d5-5eb625387f2b"
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


def external_id(instance_id: str) -> str:
    data = uip(["maestro", "case", "instance", "get", instance_id,
                "-f", CASE_FOLDER_KEY]).get("Data") or {}
    value = str(data.get("ExternalId") or "")
    if not value:
        fail(f"instance {instance_id} reports no ExternalId; nothing identifies its messages")
    return value


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
    instance_id = state.get("instance_id")
    route = state.get("route")
    if not instance_id:
        fail(f"{RUN_STATE.name} carries no instance_id")
    if route not in EXPECTED_SENDS:
        fail(f"{RUN_STATE.name} names route {route!r}, which has no expected send count")
    expected = EXPECTED_SENDS[route]

    token = external_id(instance_id)
    print(f"route {route!r}: expecting {expected} buyer notification(s) carrying ExternalId {token}")

    hits = []
    for attempt in range(POLL_ATTEMPTS):
        hits = [m for m in sent_messages() if token in (m.get("subject") or "")]
        if len(hits) >= expected:
            break
        if attempt + 1 < POLL_ATTEMPTS:
            time.sleep(POLL_SLEEP)

    for m in hits:
        print(f"  found: {m.get('subject')!r} sent {m.get('sentDateTime') or m.get('receivedDateTime')}")

    if len(hits) == expected:
        print(f"OK: the case sent {expected} buyer notification(s)")
        return 0
    if len(hits) < expected:
        fail(f"{len(hits)} of {expected} buyer notification(s) carry ExternalId {token} after "
             f"{POLL_ATTEMPTS * POLL_SLEEP}s. A connector task can report Completed and still send "
             f"nothing: check that saveAsDraft is false and that message.toRecipients is bound.")
    fail(f"{len(hits)} messages carry ExternalId {token} but route {route!r} enters 'Buyer review' "
         f"{expected} time(s); an extra notification means the phase was entered again")


if __name__ == "__main__":
    sys.exit(main())
