#!/usr/bin/env python3
"""Shared helpers for uipath-governance setup, verify and cleanup scripts.

The two policy kinds have different envelopes (verified against the live service):

  access-policy  list -> Data.Results[], id field "Id",         delete <Id>
  aops-policy    list -> Data.Result[],  id field "Identifier", delete <Identifier>

Deployments are read per subject:

  tenant  deployment tenant get <tid>  -> Data.TenantPolicies[]
  user    deployment user get <uid>    -> Data.UserPolicies[] (per-product, no license type)
  group   deployment group get <gid>   -> Data.GroupPolicies[]
"""

import json
import logging
import os
import subprocess
import sys
import tempfile
import time
import uuid

logger = logging.getLogger(__name__)

# kind -> (rows key under Data, id field on each row)
POLICY_KINDS = {
    "access-policy": ("Results", "Id"),
    "aops-policy": ("Result", "Identifier"),
}


def run_cli(args: list[str], timeout: int = 60) -> dict | None:
    """Run a uip CLI command and return parsed JSON, or None on failure."""
    try:
        result = subprocess.run(
            ["uip", *args, "--output", "json"],
            capture_output=True, text=True, timeout=timeout,
        )
        if result.returncode != 0:
            logger.warning(
                "CLI exit %d: %s", result.returncode,
                (result.stderr or result.stdout).strip()[:200],
            )
            return None
        return json.loads(result.stdout)
    except (json.JSONDecodeError, subprocess.TimeoutExpired, OSError) as e:
        logger.warning("CLI call failed: %s", e)
        return None


def poll(fn, max_attempts: int = 4, delay: int = 5):
    """Retry fn() until it returns something truthy. Handles eventual consistency."""
    for i in range(max_attempts):
        result = fn()
        if result:
            return result
        if i < max_attempts - 1:
            time.sleep(delay)
    return None


def fail(message: str):
    print(f"FAIL: {message}")
    sys.exit(1)


def ok(message: str):
    print(f"OK: {message}")


def login_info() -> dict:
    """Return the `uip login status` Data block (UserId, TenantId, Tenant, ...)."""
    data = run_cli(["login", "status"])
    if not data or data.get("Result") != "Success":
        return {}
    return data.get("Data") or {}


def policy_rows(kind: str, limit: int = 20, offset: int = 0) -> list[dict] | None:
    """One page of policies, or None when the list call itself failed."""
    rows_key, _ = POLICY_KINDS[kind]
    data = run_cli(["gov", kind, "list", "--limit", str(limit), "--offset", str(offset)])
    if not data or data.get("Result") != "Success":
        return None
    payload = data.get("Data") or {}
    return payload.get(rows_key, []) or []


def policy_by_name(kind: str, name: str) -> dict | None:
    """Find a policy by exact name, paging until it is found or the list runs out.

    `access-policy --offset` counts rows; `aops-policy --offset` counts pages —
    both are walked with their own step so the search covers either shape.
    """
    step = 20 if kind == "access-policy" else 1
    offset = 0
    while offset <= 200:
        rows = policy_rows(kind, offset=offset)
        if rows is None:
            return None
        for r in rows:
            if (r.get("Name") or "") == name:
                return r
        if not rows:
            return None
        offset += step
    return None


def policy_id(kind: str, policy: dict) -> str | None:
    _, id_field = POLICY_KINDS[kind]
    return policy.get(id_field)


def tenant_policies(tenant_id: str) -> list[dict] | None:
    data = run_cli(["gov", "aops-policy", "deployment", "tenant", "get", tenant_id])
    if not data or data.get("Result") != "Success":
        return None
    return (data.get("Data") or {}).get("TenantPolicies") or []


def subject_policies(scope: str, subject_id: str) -> list[dict] | None:
    """Deployment entries for a user or group subject, or None when the read failed.

    `deployment user|group get` returns Data as a bare list of per-product entries
    (unlike `tenant get`, which nests them under Data.TenantPolicies). A user's
    list also includes entries inherited from a group, marked with GroupName /
    DeploymentLevel — callers that mean "pinned directly on this subject" filter
    on PolicyIdentifier themselves.
    """
    data = run_cli(["gov", "aops-policy", "deployment", scope, "get", subject_id])
    if not data or data.get("Result") != "Success":
        return None
    payload = data.get("Data")
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("UserPolicies", "GroupPolicies", "Policies", "TenantPolicies"):
            if isinstance(payload.get(key), list):
                return payload[key]
    return []


def group_id_by_name(name: str) -> str | None:
    """Resolve a directory group's UUID by exact name (tests use marker groups)."""
    data = run_cli(["admin", "groups", "list"])
    if not data or data.get("Result") != "Success":
        return None
    for row in (data.get("Data") or []):
        if (row.get("Name") or row.get("name") or "") == name:
            return row.get("Id") or row.get("id")
    return None


def state_file(name: str) -> str:
    return os.path.join(tempfile.gettempdir(), name)


def write_state(name: str, payload: dict) -> None:
    with open(state_file(name), "w", encoding="utf-8") as fh:
        json.dump(payload, fh)


def read_state(name: str) -> dict | None:
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


# --- Per-run isolation -------------------------------------------------------
#
# These tests run against ONE shared organization while several agents (claude,
# codex, gemini) execute the same task concurrently. Every seeded object
# therefore carries a name unique to its run, and every check and cleanup step
# looks only at its own run's objects.
#
# The mechanism mirrors tests/tasks/uipath-platform/seed.py: pre_run writes
# `seed.json` into the run's working directory — shared by pre_run, the agent and
# the success criteria, isolated between runs — carrying a `uuid8` prefix plus
# whatever the run seeded.

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
    """Name an object for this run only: `ce-gov-policy` -> `ce-gov-policy-1a2b3c4d`."""
    return f"{base}-{run_id()}"


def seed_entry(key: str) -> dict | None:
    """A record this run seeded, e.g. the policy a delete scenario must remove."""
    entry = load_seed().get(key)
    return entry if isinstance(entry, dict) else None


def owned_by_this_run(name: str) -> bool:
    """True when an object name carries this run's prefix."""
    token = load_seed().get("uuid8")
    return bool(token) and str(name).endswith(token)


# --- access-policy -----------------------------------------------------------
#
# Envelopes verified against the live service:
#   create -> Code PolicyCreated, Data.UpsertedPolicy{Id, ...}
#   get    -> Code PolicyGet,     Data{Id, Name, Status, Selectors, ...} (PascalCase)
#   update -> Code PolicyUpdated
#   delete -> Code PolicyDeleted, Data.PolicyIds[]  — a SOFT delete: `get` keeps
#             succeeding with Status "Deleted" + DeletedOn, and the row leaves `list`.
#
# Two traps the tests are built around:
#   * `update` needs the COMPLETE definition in recursive camelCase, including
#     `id`. `get` returns PascalCase, so a verbatim get -> update round-trip is
#     rejected with HTTP 400.
#   * `list --filter` silently ignores unsupported fields (`name eq '...'`
#     returns every policy), so name resolution has to happen client-side.


def ap_definition(name: str, description: str, org_id: str, tenant_id: str,
                  actor_user_id: str, resource_type: str = "Agent",
                  actor_process_type: str = "Flow",
                  status: str = "Simulated") -> dict:
    """A minimal valid PolicyDefinition in the camelCase the service requires.

    `status` defaults to Simulated: the policy is evaluated and logged but never
    enforced, so seeding one cannot gate real traffic on the shared test org.
    `executableRule` is mandatory — omitting it fails validation with HTTP 400.
    """
    return {
        "policyType": "ToolUsePolicy",
        "organizationId": org_id,
        "tenantId": tenant_id,
        "name": name,
        "description": description,
        "selectors": [{"resourceType": resource_type, "values": ["*"], "operator": "Or"}],
        "executableRule": {"values": [{"type": actor_process_type, "values": ["*"], "operator": "Or"}]},
        "actorRule": {"values": [{"type": "User", "values": [actor_user_id], "operator": "Or"}]},
        "enforcement": "Allow",
        "status": status,
    }


def ap_create(definition: dict) -> dict | None:
    """Create an access policy from a definition dict. Returns the stored policy."""
    path = os.path.join(tempfile.gettempdir(), f"ap-{uuid.uuid4().hex[:8]}.json")
    try:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(definition, fh)
        data = run_cli(["gov", "access-policy", "create", "--file", path])
    finally:
        try:
            os.remove(path)
        except OSError:
            pass
    if not data or data.get("Result") != "Success":
        return None
    return (data.get("Data") or {}).get("UpsertedPolicy") or None


def ap_get(policy_id: str) -> dict | None:
    """Fetch one access policy. Returns the record even after a soft delete."""
    data = run_cli(["gov", "access-policy", "get", policy_id])
    if not data or data.get("Result") != "Success":
        return None
    return data.get("Data") or None


def ap_delete(policy_id: str) -> bool:
    data = run_cli(["gov", "access-policy", "delete", policy_id])
    return bool(data and data.get("Result") == "Success")


def ap_live_rows(max_pages: int = 6) -> list[dict]:
    """Every access policy `list` returns (deleted rows excluded by the service).

    `--limit` is capped at 20 by the service; --offset counts rows.
    """
    rows: list[dict] = []
    for page in range(max_pages):
        data = run_cli(["gov", "access-policy", "list", "--limit", "20",
                        "--offset", str(page * 20)])
        if not data or data.get("Result") != "Success":
            break
        chunk = (data.get("Data") or {}).get("Results") or []
        rows.extend(chunk)
        if len(chunk) < 20:
            break
    return rows


def ap_by_name(name: str) -> dict | None:
    """Resolve a live access policy by exact name (client-side: see the trap above)."""
    return next((r for r in ap_live_rows() if (r.get("Name") or "") == name), None)


# --- aops-policy -------------------------------------------------------------
#
# Envelopes verified against the live service:
#   create -> Code AopsPolicyCreate, Data{Name, Identifier, Priority, Availability, Product, Data}
#   get    -> Code AopsPolicyGet    (HTTP 404 once deleted — a HARD delete, unlike access-policy)
#   update -> Code AopsPolicyUpdate (full replace: omitted flags are cleared)
#   list   -> Code AopsPolicyList,  Data{TotalCount, Result[]}; --search works server-side
#
# `--priority` is validated against the product's current policy count (range
# 1..count+1), and inserting at 1 renumbers the rest, so tests always create at
# priority 1 and never assert another policy's priority.


def aops_form_data(product: str, path: str) -> bool:
    """Write the product's fillable form-data blueprint to `path`."""
    data = run_cli(["gov", "aops-policy", "template", "get", product,
                    "--output-form-data", path])
    return bool(data and data.get("Result") == "Success" and os.path.exists(path))


def aops_create(name: str, product: str, description: str, form_data_path: str,
                availability: int = 365) -> dict | None:
    data = run_cli(["gov", "aops-policy", "create", "--name", name,
                    "--product-name", product, "--description", description,
                    "--priority", "1", "--availability", str(availability),
                    "--input", form_data_path])
    if not data or data.get("Result") != "Success":
        return None
    return data.get("Data") or None


def aops_get(identifier: str) -> dict | None:
    """Fetch one aops policy, or None when it does not exist (hard-deleted)."""
    data = run_cli(["gov", "aops-policy", "get", identifier])
    if not data or data.get("Result") != "Success":
        return None
    return data.get("Data") or None


def aops_search(term: str, product: str | None = None) -> list[dict]:
    """Server-side substring search over policy names."""
    args = ["gov", "aops-policy", "list", "--search", term, "--limit", "20"]
    if product:
        args += ["--product-name", product]
    data = run_cli(args)
    if not data or data.get("Result") != "Success":
        return []
    return (data.get("Data") or {}).get("Result") or []


def aops_delete(identifier: str) -> bool:
    data = run_cli(["gov", "aops-policy", "delete", identifier])
    return bool(data and data.get("Result") == "Success")
