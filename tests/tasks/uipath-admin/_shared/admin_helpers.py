#!/usr/bin/env python3
"""Shared helpers for uipath-admin check and cleanup scripts."""

import json
import logging
import os
import subprocess
import sys
import tempfile
import time
import uuid

logger = logging.getLogger(__name__)


def run_cli(args: list[str], timeout: int = 30, quiet: bool = False) -> dict | None:
    """Run a uip CLI command and return parsed JSON, or None on failure.

    Set quiet=True for commands whose output contains secret material — notably
    `external-apps generate-secret`, which returns the client secret exactly
    once. The error paths below echo stderr/stdout into pre_run logs, and those
    are forwarded verbatim into downloadable CI artifacts, so a non-JSON banner
    or an output-then-nonzero-exit would put the secret in an artifact.
    """
    try:
        result = subprocess.run(
            ["uip", *args, "--output", "json"],
            capture_output=True, text=True, timeout=timeout,
        )
        if result.returncode != 0:
            if quiet:
                logger.warning("CLI returned exit code %d (output suppressed: may contain a secret)",
                               result.returncode)
            else:
                logger.warning(
                    "CLI returned exit code %d: %s",
                    result.returncode, result.stderr.strip() or result.stdout.strip(),
                )
            return None
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        if quiet:
            logger.warning("CLI returned non-JSON (output suppressed: may contain a secret)")
        else:
            logger.warning("CLI returned non-JSON: %s", result.stdout[:200])
        return None
    except subprocess.TimeoutExpired:
        logger.warning("CLI timed out after %ds", timeout)
        return None
    except Exception as e:
        logger.warning("CLI call failed: %s", e)
        return None


def find_all(data: dict, needle: str, fields: list[str]) -> list[dict]:
    """Find all items in data['Data'] where needle matches exactly in any field."""
    matches = []
    for item in data.get("Data", []):
        for field in fields:
            val = item.get(field) or ""
            if val == needle:
                matches.append(item)
                break
    return matches


def find_one(data: dict, needle: str, fields: list[str]) -> dict | None:
    """Find first item in data['Data'] where needle matches exactly in any field."""
    matches = find_all(data, needle, fields)
    return matches[0] if matches else None


def poll(fn, max_attempts: int = 4, delay: int = 5):
    """Retry fn() up to max_attempts times with delay between attempts.

    Returns the first truthy result. Returns None after all attempts fail.
    Handles eventual consistency in tenant APIs.
    """
    for i in range(max_attempts):
        result = fn()
        if result:
            return result
        if i < max_attempts - 1:
            logger.info("Attempt %d/%d returned falsy — retrying in %ds", i + 1, max_attempts, delay)
            time.sleep(delay)
    return None


def fail(message: str):
    """Print FAIL message and exit 1."""
    print(f"FAIL: {message}")
    sys.exit(1)


def ok(message: str):
    """Print OK message."""
    print(f"OK: {message}")


def first_list(o):
    """Return the first list found anywhere in a nested dict/list structure.

    Tolerates how an API/agent wraps a collection (bare list, under a key, or in
    a paginated envelope). Returns None if no list exists.
    """
    if isinstance(o, list):
        return o
    if isinstance(o, dict):
        for v in o.values():
            r = first_list(v)
            if r is not None:
                return r
    return None


# --- Authorization (authz) helpers -------------------------------------------
#
# The authz endpoints have two shapes worth knowing:
#   * `roles list` nests rows under Data.Results (paginated envelope).
#   * `roles assignments list` groups rows by identity:
#     Data.Results[].RoleAssignmentDtos[].
# Both are normalized below so verify/setup scripts read tenant truth the same way.


def login_info() -> dict:
    """Return the `uip login status` Data block (UserId, TenantId, ...) or {}."""
    data = run_cli(["login", "status"])
    if not data or data.get("Result") != "Success":
        return {}
    return data.get("Data") or {}


def resolve_scope_path(raw: str | None, tenant_id: str | None = None) -> str:
    """Expand a scope-path template: `<TID>` -> the login tenant id.

    Defaults to the login tenant path (`/tenant/<TID>`) — the same default the
    CLI applies when no scope flags are given.
    """
    path = (raw or "/tenant/<TID>").strip()
    if "<TID>" in path:
        tid = tenant_id or login_info().get("TenantId") or ""
        path = path.replace("<TID>", tid)
    return path


def roles_matching(needle: str, role_type: str = "Custom", exact: bool = True) -> list[dict]:
    """Return roles whose Name matches `needle` (exact by default, else substring).

    `--filter` is a server-side substring match; the client-side comparison below
    pins it to the intended role(s).
    """
    data = run_cli([
        "admin", "authorization", "roles", "list",
        "--role-type", role_type, "--filter", needle, "--limit", "100",
    ])
    if not data or data.get("Result") != "Success":
        return []
    payload = data.get("Data") or {}
    results = payload.get("Results", []) if isinstance(payload, dict) else (payload or [])
    out = []
    for r in results:
        name = r.get("Name") or r.get("name") or ""
        if (name == needle) if exact else (needle in name):
            out.append(r)
    return out


def role_get(role_id: str) -> dict | None:
    """Fetch one role by id. Returns the role dict, or None when it does not exist."""
    data = run_cli(["admin", "authorization", "roles", "get", role_id])
    if not data or data.get("Result") != "Success":
        return None
    return data.get("Data") or None


def assignments_at(identity_id: str, scope_path: str) -> list[dict]:
    """Return the assignment records for one identity at an exact scope path.

    Uses `--scope-path` deliberately: the composed `--scope Organization|Tenant`
    form also sets a serviceName filter, which hides grants of roles owned by
    another service (built-in roles among them). The verbatim path is the
    reliable read-back.
    """
    data = run_cli([
        "admin", "authorization", "roles", "assignments", "list",
        "--scope-path", scope_path, "--identity-id", identity_id, "--limit", "10",
    ])
    if not data or data.get("Result") != "Success":
        return []
    payload = data.get("Data") or {}
    groups = payload.get("Results", []) if isinstance(payload, dict) else (payload or [])
    return [a for g in groups for a in (g.get("RoleAssignmentDtos") or [])]


def state_file(name: str) -> str:
    """Absolute path of a cross-step state file (setup writes, verify reads)."""
    return os.path.join(tempfile.gettempdir(), name)


def write_state(name: str, payload: dict) -> None:
    with open(state_file(name), "w", encoding="utf-8") as fh:
        json.dump(payload, fh)


def read_state(name: str) -> dict | None:
    """Return the recorded seed state, or None when the seed never ran."""
    path = state_file(name)
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError):
        return None


def clear_state(name: str) -> None:
    try:
        os.remove(state_file(name))
    except OSError:
        pass

# --- Per-run isolation ------------------------------------------------------
#
# The admin tests run against ONE shared organization while several agents
# (claude, codex, gemini) execute the same task concurrently. Every seeded
# object therefore needs a name unique to its run, and every check needs to look
# at its own run's objects only.
#
# The mechanism mirrors tests/tasks/uipath-platform/seed.py: pre_run writes
# `seed.json` into the run's working directory — shared by pre_run, the agent and
# the success criteria, isolated between runs — carrying a `uuid8` prefix plus
# whatever the run seeded. Names are suffixed with that prefix, so a concurrent
# run's objects are invisible to this run's checks and untouched by its cleanup.

SEED_FILE = "seed.json"


def load_seed() -> dict:
    """The run's seed.json from the working directory ({} when absent)."""
    if not os.path.exists(SEED_FILE):
        return {}
    try:
        with open(SEED_FILE, encoding="utf-8") as fh:
            return json.load(fh) or {}
    except (json.JSONDecodeError, OSError):
        return {}


def update_seed(**values) -> dict:
    """Merge values into seed.json, creating it (with a fresh uuid8) if needed."""
    seed = load_seed()
    if not seed.get("uuid8"):
        seed["uuid8"] = uuid.uuid4().hex[:8]
    seed.update(values)
    with open(SEED_FILE, "w", encoding="utf-8") as fh:
        json.dump(seed, fh)
    return seed


def run_id() -> str:
    """This run's short unique prefix, minted on first use."""
    return update_seed()["uuid8"]


def scoped(base: str) -> str:
    """Name an object for this run only: `ce-authz-role` -> `ce-authz-role-1a2b3c4d`."""
    return f"{base}-{run_id()}"


def seed_entry(key: str) -> dict | None:
    """A record this run seeded, e.g. the role a delete-scenario must remove."""
    entry = load_seed().get(key)
    return entry if isinstance(entry, dict) else None


def owned_by_this_run(name: str) -> bool:
    """True when an object name carries this run's prefix."""
    seed = load_seed()
    token = seed.get("uuid8")
    return bool(token) and str(name).endswith(token)
