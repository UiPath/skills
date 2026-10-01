"""Shared helpers for the Automation Hub e2e tasks' setup and grading scripts.

Everything goes through the `uip ah` CLI the task itself uses — the scripts never
build a token or call the Open API directly, so they run under whatever login the
harness provides (Delegate env-auth, the nightly ROPC `.auth`, or a developer's
`uip login`). Kept dependency-free: it is staged into the sandbox as a file.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys

SEED_FILE = "seed.json"
BUSINESS_PROCESS_FLOW = "business process"
ARCHIVED_STATUS = "ARCHIVED"
PLACEHOLDERS = ("sample input", "first.last@example.com", "example.com")

# uip prints update-check chatter before the envelope on some builds; take the
# last JSON object on stdout.
_ENVELOPE = re.compile(r"\{.*\}\s*$", re.S)


def precondition_failed(message: str) -> None:
    """Exit labelling the cause as environmental, so triage never blames the skill.

    coder_eval has no skip semantics: in `pre_run` a non-zero exit lands the run as
    ERROR (what we want); in a criterion it is still scored as FAILURE, so the real
    guard is running these checks in `pre_run` before an agent run is spent.
    """
    sys.exit(f"test precondition failed: {message} — this is an ENVIRONMENT gap "
             "(tenant / identity / fixture), NOT a skill regression")


def uip_json(args: list[str], timeout: int = 180) -> dict:
    """Run `uip <args> --output json` and return the response envelope."""
    env = {**os.environ, "UIPATH_CLI_DISABLE_VERSION_SYNC": "1"}
    proc = subprocess.run(["uip", *args, "--output", "json"],
                          capture_output=True, text=True, timeout=timeout, env=env)
    match = _ENVELOPE.search(proc.stdout or "")
    if not match:
        return {"Result": "ParseError", "exit_code": proc.returncode,
                "raw": (proc.stdout or "")[-1500:], "err": (proc.stderr or "")[-800:]}
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        return {"Result": "ParseError", "exit_code": proc.returncode, "error": str(exc)}


def items(payload: dict) -> list:
    data = payload.get("Data")
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("Items") or data.get("items") or []
    return []


def succeeded(payload: dict) -> bool:
    return payload.get("Result") == "Success"


def describe_failure(payload: dict) -> str:
    return " | ".join(str(payload.get(k)) for k in ("Result", "Message", "Instructions") if payload.get(k))


def business_process_flow(flows: list[dict]) -> dict | None:
    matches = [f for f in flows if BUSINESS_PROCESS_FLOW in str(f.get("Name", "")).lower()]
    return matches[0] if matches else None


def archive_target(flow: dict) -> tuple[str, str] | None:
    """(phase variable, status variable) of the flow's first Archived status."""
    for statuses in (flow.get("Phases") or {}).values():
        for status in (statuses or {}).values():
            if str(status.get("StatusVariable", "")).upper() == ARCHIVED_STATUS:
                return status["PhaseVariable"], status["StatusVariable"]
    return None


def active_categories(categories: list[dict]) -> list[dict]:
    """Flatten the tree to the active, non-"Other" nodes."""
    found: list[dict] = []
    for category in categories or []:
        if category.get("CategoryIsActive") == 1 and not category.get("CategoryIsOther"):
            found.append(category)
        found.extend(active_categories(category.get("Subcategories") or []))
    return found


def load_seed() -> dict:
    if not os.path.exists(SEED_FILE):
        precondition_failed(f"{SEED_FILE} is missing; pre_run seed_publish.py did not run")
    with open(SEED_FILE, encoding="utf-8") as handle:
        seed = json.load(handle) or {}
    if not seed.get("run_token"):
        precondition_failed(f"{SEED_FILE} carries no run_token")
    return seed


def has_placeholder(text: str) -> bool:
    lowered = (text or "").lower()
    return any(p in lowered for p in PLACEHOLDERS)
