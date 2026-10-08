"""Shared helpers for the live Automation Hub tasks' setup and grading scripts.

Everything goes through the `uip ah` CLI the task itself uses — the scripts never
build a token or call the Open API directly, so they run under whatever login the
harness provides (the CI ROPC `.auth`, or a developer's `uip login`). Kept
dependency-free: it is staged into the sandbox as a file.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys

SEED_FILE = "seed.json"
# Written by use_tenant.py: HOME for `uip` when the task targets a second tenant.
TENANT_HOME_MARKER = ".ah-tenant-home"
BUSINESS_PROCESS_FLOW = "business process"
ARCHIVED_STATUS = "ARCHIVED"
PLACEHOLDERS = ("sample input", "first.last@example.com", "example.com")

_DECODER = json.JSONDecoder()


def parse_envelope(stdout: str) -> dict | None:
    """The CLI's JSON envelope, ignoring update-check chatter printed before or after it.

    Tries every `{` from the first one forwards and returns the first that decodes to an
    object: a brace inside leading chatter fails to decode and is skipped, and text after
    the envelope is ignored by `raw_decode`. (Scanning backwards would return the
    innermost nested object instead of the envelope.)
    """
    text = stdout or ""
    start = text.find("{")
    while start != -1:
        try:
            value, _ = _DECODER.raw_decode(text, start)
        except json.JSONDecodeError:
            value = None
        if isinstance(value, dict):
            return value
        start = text.find("{", start + 1)
    return None


def precondition_failed(message: str) -> None:
    """Exit labelling the cause as environmental, so triage never blames the skill.

    coder_eval has no skip semantics: in `pre_run` a non-zero exit lands the run as
    ERROR (what we want); in a criterion it is still scored as FAILURE, so the real
    guard is running these checks in `pre_run` before an agent run is spent.
    """
    sys.exit(f"test precondition failed: {message} — this is an ENVIRONMENT gap "
             "(tenant / identity / fixture), NOT a skill regression")


def uip_env() -> dict:
    """Environment for the harness's own `uip` calls.

    Never recorded (the call log is the agent's alone), and on the tenant that
    use_tenant.py selected when this task runs on a second tenant.
    """
    env = {**os.environ, "UIPATH_CLI_DISABLE_VERSION_SYNC": "1", "AH_EVAL_NO_RECORD": "1"}
    if os.path.isfile(TENANT_HOME_MARKER):
        with open(TENANT_HOME_MARKER, encoding="utf-8") as handle:
            home = handle.read().strip()
        if home:
            env["HOME"] = env["USERPROFILE"] = home
    return env


def uip_json(args: list[str], timeout: int = 180) -> dict:
    """Run `uip <args> --output json` and return the response envelope."""
    env = uip_env()
    proc = subprocess.run(["uip", *args, "--output", "json"],
                          capture_output=True, text=True, timeout=timeout, env=env)
    envelope = parse_envelope(proc.stdout)
    if envelope is None:
        return {"Result": "ParseError", "exit_code": proc.returncode,
                "raw": (proc.stdout or "")[-1500:], "err": (proc.stderr or "")[-800:]}
    return envelope


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
    """(phase variable, status variable) of the flow's first Archived status.

    Tenants name the variable differently (`ARCHIVED`, `QUALIFICATION_ARCHIVED`, ...),
    so match the suffix or the display value; an exact miss would make cleanup a silent no-op.
    """
    for statuses in (flow.get("Phases") or {}).values():
        for status in (statuses or {}).values():
            variable = str(status.get("StatusVariable", "")).upper()
            value = str(status.get("StatusValue", "")).strip().lower()
            if variable.endswith(ARCHIVED_STATUS) or value == "archived":
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
