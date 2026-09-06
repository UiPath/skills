#!/usr/bin/env python3
"""Can this case be started with input arguments instead of through `case debug`?

Four questions, answered in one pass, each reported on its own line so a failure names the
step it stopped at rather than the whole chain:

 1. Does `solution pack` / `publish` / `deploy run` put a runnable process on the tenant?
 2. Does that process expose the SDD's `In` arguments as job input arguments?
 3. Does `jobs start --input-arguments` create a case instance the Maestro commands see?
 4. Does a value passed that way reach the case variable it names?

Every one of these exists because the debug entry point supplies no arguments, so
`bankDetailsDocument` is always empty, `bankVerificationStatus` never reaches `verified`,
and the SDD's primary scenario cannot run. The measurements behind that are in the
input-driven findings note.

This publishes a solution and starts a job, so it writes to the tenant. It reports what it
created and leaves it in place: the routes that follow need the process to stay.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from _shared.case_check import find_solution_dir  # noqa: E402

# What a debug run cannot supply. The spend is the high-value figure rather than the SDD's
# 120000 default, so a run that gets this far also exercises the director sign-off path.
PROBE_INPUTS = {"companyName": "Northwind Components Ltd", "expectedAnnualSpend": 750000}

START_TIMEOUT = 300
INSTANCE_TIMEOUT = 180
POLL = 5


def envelope(args: list[str], timeout: int = START_TIMEOUT) -> dict:
    label = " ".join(args[:3])
    try:
        proc = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"Result": "Error", "Message": f"`{label}` timed out after {timeout}s"}
    out = (proc.stdout or "") + (proc.stderr or "")
    try:
        return json.loads(out)
    except ValueError:
        return {
            "Result": "Error",
            "Message": f"`{label}` returned an unparseable reply (exit {proc.returncode})",
            "Instructions": out[:500],
        }


def detail(reply: dict) -> str:
    """Every field the CLI puts a reason in.

    `Message` is a generic one-liner; the reason a call was refused rides in
    `Instructions`. Reading only `Message` names the symptom and hides the cause.
    """
    parts = [str(reply[k]) for k in ("Message", "Code", "ErrorCode", "Instructions") if reply.get(k)]
    return " | ".join(parts) or str(reply)[:300]


def rows(reply: dict) -> list:
    data = reply.get("Data")
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("value", "Items", "Processes", "EntryPoints"):
            if isinstance(data.get(key), list):
                return data[key]
    return []


def case_processes() -> list:
    return rows(envelope(["uip", "maestro", "case", "processes", "list", "--output", "json"]))


def process_key(row: dict) -> str:
    return str(row.get("ProcessKey") or row.get("Key") or row.get("Id") or "")


def case_instances() -> dict:
    found = {}
    for row in rows(envelope(["uip", "maestro", "case", "instance", "list", "--output", "json"])):
        key = row.get("InstanceId") or row.get("Id")
        if key:
            found[str(key)] = row
    return found


def report(number: int, question: str, ok: bool, text: str) -> bool:
    print(f"[{number}] {question}")
    print("    " + ("YES" if ok else "NO ") + f"  {text}")
    return ok


def publish_and_deploy(solution_dir: str) -> tuple[bool, str]:
    """Returns (ok, detail). Each command's own reason is passed through on failure."""
    packed = envelope(["uip", "solution", "pack", solution_dir, "--output", "json"])
    if packed.get("Result") != "Success":
        return False, f"`solution pack` failed: {detail(packed)}"
    data = packed.get("Data") or {}
    zip_path = data.get("PackagePath") or data.get("Path") or data.get("OutputPath") or ""
    if not zip_path or not os.path.exists(zip_path):
        return False, f"`solution pack` reported success but named no readable package: {detail(packed)}"

    published = envelope(["uip", "solution", "publish", zip_path, "--output", "json"])
    if published.get("Result") != "Success":
        return False, f"`solution publish` failed: {detail(published)}"

    deployed = envelope(["uip", "solution", "deploy", "run", "--output", "json"])
    if deployed.get("Result") != "Success":
        return False, f"`solution deploy run` failed: {detail(deployed)}"
    return True, f"packed {os.path.basename(zip_path)}, published and deployed"


def declared_inputs(key: str) -> set[str]:
    entry = envelope(["uip", "or", "packages", "entry-points", key, "--output", "json"])
    names = set()
    for point in rows(entry):
        args = point.get("InputArguments") or point.get("inputArguments") or []
        for arg in args:
            name = arg.get("Name") or arg.get("name")
            if name:
                names.add(str(name))
    return names


def globals_of(instance_id: str) -> dict:
    reply = envelope(
        ["uip", "maestro", "case", "instance", "global-variables", instance_id, "--output", "json"]
    )
    held: dict = {}
    listed = rows(reply)
    if listed:
        for row in listed:
            if isinstance(row, dict):
                name = row.get("Name") or row.get("name")
                if name is not None:
                    held[str(name)] = row.get("Value", row.get("value"))
                else:
                    held.update(row)
    elif isinstance(reply.get("Data"), dict):
        held.update(reply["Data"])
    return held


def missing_values(held: dict) -> dict:
    """The probe inputs whose value did not arrive.

    `instance global-variables` returns the case's globals PascalCased, so `companyName`
    reads back as `CompanyName`; both spellings are checked before calling one missing.
    """
    gone = {}
    for name, sent in PROBE_INPUTS.items():
        pascal = name[:1].upper() + name[1:]
        got = held.get(name, held.get(pascal))
        if str(got) != str(sent):
            gone[name] = got
    return gone


def main() -> int:
    solution_dir = find_solution_dir()
    if not solution_dir:
        print("no solution directory found; nothing to publish", file=sys.stderr)
        return 1

    before_processes = {process_key(p) for p in case_processes()}
    before_instances = set(case_instances())

    ok, how = publish_and_deploy(solution_dir)
    if not ok:
        report(1, "does publishing put a runnable process on the tenant?", False, how)
        return 1
    fresh = [p for p in case_processes() if process_key(p) not in before_processes]
    if not report(1, "does publishing put a runnable process on the tenant?", bool(fresh),
                  f"{how}; {len(fresh)} new case process(es)"):
        return 1
    key = process_key(fresh[0])

    declared = declared_inputs(key)
    wanted = set(PROBE_INPUTS)
    if not report(2, "does the process expose the SDD's In arguments?", wanted <= declared,
                  f"declared {sorted(declared)[:8]}; this probe sends {sorted(wanted)}"):
        return 1

    started = envelope(["uip", "or", "jobs", "start", key,
                        "--input-arguments", json.dumps(PROBE_INPUTS), "--output", "json"])
    if started.get("Result") != "Success":
        report(3, "does a started job create a case instance the Maestro commands see?", False,
               f"`jobs start` failed: {detail(started)}")
        return 1

    deadline = time.time() + INSTANCE_TIMEOUT
    appeared: dict = {}
    while time.time() < deadline and not appeared:
        appeared = {k: v for k, v in case_instances().items() if k not in before_instances}
        if not appeared:
            time.sleep(POLL)
    if not report(3, "does a started job create a case instance the Maestro commands see?",
                  bool(appeared), f"{len(appeared)} new instance(s) within {INSTANCE_TIMEOUT}s"):
        return 1
    instance_id = sorted(appeared)[0]

    gone = missing_values(globals_of(instance_id))
    arrived = not gone
    report(4, "does a passed value reach the case variable it names?", arrived,
           f"instance {instance_id}: "
           + ("every value arrived" if arrived else f"these did not: {gone}"))

    print(f"\ncreated process {key} and instance {instance_id}; both left in place")
    return 0 if arrived else 1


if __name__ == "__main__":
    sys.exit(main())
