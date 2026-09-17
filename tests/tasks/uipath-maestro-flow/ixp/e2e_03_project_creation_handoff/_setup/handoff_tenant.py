"""Tenant plumbing shared by handoff.py (pre_run/post_run) and
_shared/check_ixp_handoff.py (grading). No scoring logic lives here — only
`uip` process wrapping, tenant listing/snapshot bookkeeping, and the .flow
node-identifier extraction both halves need. Staged into the agent's sandbox
via sandbox.template_sources (mount_point: _setup) alongside handoff.py, so
this file IS agent-visible — keep it that way (see check_ixp_handoff.py's
docstring for what must NOT live here).

Carries no scoring logic and is safe to be agent-visible for the same reason
as the retired flow_project_finder.py: pure tenant/plumbing helpers, not
answer-key content.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from datetime import datetime, timezone
from typing import Any

# Written to the sandbox root by `seed`, read back by `check` and `teardown`.
# Relative, so it resolves against the sandbox. Neutrally named — an agent
# `ls`-ing the sandbox should learn nothing from it.
SNAPSHOT = ".grader_baseline.json"

# Well above any plausible tenant project count. list_projects() raises
# rather than diffing against a truncated page, which would report
# page-fallen-off projects as newly created.
PROJECT_LIST_LIMIT = "500"

# Per-call cap. Env-tunable (like HANDOFF_RETRY_SECONDS) so the unit tests can
# exercise the timeout path without waiting out the real cap.
UIP_TIMEOUT_SECONDS = float(os.environ.get("HANDOFF_UIP_TIMEOUT_SECONDS", "45"))

# Node-type prefix for an IxP extraction node in a .flow.
IXP_NODE_PREFIX = "uipath.ixp."

# Substrings that mark a project as belonging to the fixture domain, matched
# case-insensitively against its Name and Title. See handoff.py's
# DOMAIN_MARKERS docstring (kept there, alongside the rotation recipe) for the
# full rationale — this is pure plumbing both halves need to recognize the
# domain, not a judgment about whether it's a defect.
DOMAIN_MARKERS = ("falconry", "bird-of-prey", "bird_of_prey")

# Folder deletes can fail transiently (provisioning race on a just-created
# folder). Retried briefly wherever a folder is deleted. Env-tunable so the
# unit-test suite is not slowed by real sleeps.
FOLDER_DELETE_ATTEMPTS = 4
FOLDER_DELETE_RETRY_SECONDS = float(os.environ.get("HANDOFF_RETRY_SECONDS", "5"))


def run_uip(arguments: list[str]) -> subprocess.CompletedProcess[str]:
    """Run one `uip` subcommand, capturing both streams.

    A call that outlives UIP_TIMEOUT_SECONDS raises a RuntimeError naming the
    command and the cap: `registry pull --force` is environment weather
    (seconds on CI, minutes observed elsewhere), and a bare TimeoutExpired
    traceback would read as a grader defect.
    """
    try:
        return subprocess.run(
            ["uip", *arguments],
            capture_output=True,
            text=True,
            timeout=UIP_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            f"`uip {' '.join(arguments)}` exceeded {UIP_TIMEOUT_SECONDS:g}s — "
            "environment weather (registry pull is the usual culprit), not a "
            "skill defect; re-run."
        ) from exc


def run_uip_json(arguments: list[str]) -> dict[str, Any]:
    """Run one `uip` subcommand and parse its JSON envelope.

    Raises RuntimeError on a non-zero exit; lets json.JSONDecodeError through on
    unparseable output.
    """
    completed = run_uip(arguments)
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        raise RuntimeError(
            f"`uip {' '.join(arguments)}` exited {completed.returncode}: {detail}"
        )
    return json.loads(completed.stdout)


def list_projects() -> list[dict[str, Any]]:
    """Every IXP project record visible on the tenant.

    Returns the records, not just names, so one listing serves both the
    baseline snapshot and seed's residue sweep — which is what makes the sweep
    free in `uip` calls. `CreatedAt` is present on every record and is the
    sweep's age source; the folder API exposes nothing temporal, which is why a
    leaked folder cannot be aged the same way.
    """
    payload = run_uip_json(
        ["ixp", "projects", "list", "--limit", PROJECT_LIST_LIMIT, "--output", "json"]
    )
    listing = payload["Data"]
    projects = listing["Projects"]
    total = listing["Total"]
    if total > len(projects):
        raise RuntimeError(
            f"project list truncated ({len(projects)} of {total}) — "
            "raise PROJECT_LIST_LIMIT"
        )
    return projects


def project_digest(project_name: str) -> str:
    import hashlib

    return hashlib.sha256(project_name.encode("utf-8")).hexdigest()


def folder_get(identifier: str) -> dict[str, Any] | None:
    """One folder by name or key, or None when it does not resolve.

    Two callers, both passing a key: teardown's already-gone check, which needs
    only resolvability, and belongs_to_another_run, which reads back the Name.
    """
    completed = run_uip(["or", "folders", "get", identifier, "--output", "json"])
    if completed.returncode != 0:
        return None
    payload = json.loads(completed.stdout)
    data = payload.get("Data")
    # The CLI's failure envelope has no Data key (verified: exit 1 plus
    # {Result: Failure, Message, Instructions, ...}). Should a CLI line ever
    # exit 0 with that envelope, it must still read as absent, not crash.
    if payload.get("Result") == "Failure" or not isinstance(data, dict) or not data.get("Key"):
        return None
    return data


def iso_age_seconds(timestamp: str | None) -> float | None:
    """Seconds since an ISO-8601 instant, or None when absent/unparseable.

    Naive timestamps are read as UTC. None means "too young to touch" to the
    only caller — the sweep never deletes a project it cannot date.
    """
    if not timestamp:
        return None
    try:
        created = datetime.fromisoformat(str(timestamp))
    except ValueError:
        return None
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - created).total_seconds()


def write_snapshot(project_names: set[str], run_folder_key: str) -> None:
    """Record the baseline as opaque digests — see the module docstring."""
    with open(SNAPSHOT, "w", encoding="utf-8") as handle:
        # Neutral key names. "scope" is the seed-created run folder's Key (a
        # bare GUID leaks nothing the prompt's folder name doesn't already say).
        json.dump(
            {
                "names": sorted(project_digest(name) for name in project_names),
                "scope": run_folder_key,
            },
            handle,
            indent=2,
        )


def read_snapshot() -> dict[str, Any]:
    if not os.path.exists(SNAPSHOT):
        raise RuntimeError(
            f"{SNAPSHOT} missing from {os.getcwd()} — the pre_run seed step did not run, "
            "so this run's artifacts cannot be told apart from pre-existing ones"
        )
    with open(SNAPSHOT, encoding="utf-8") as handle:
        raw = json.load(handle)
    return {"projects": set(raw["names"]), "scope": str(raw["scope"])}


def new_project_names() -> list[str]:
    """Project names that appeared since seed ran (tenant-wide — see module docstring)."""
    before = read_snapshot()["projects"]
    names = {project["Name"] for project in list_projects()}
    return sorted(name for name in names if project_digest(name) not in before)


def list_deployments(project_name: str) -> list[dict[str, Any]]:
    """Folder deployments for one project.

    Empty list means the project exists but was never folder-deployed. A missing
    project raises — `deployments list` is project-scoped and 404s once the
    project is gone, so callers must read this before deleting anything.
    """
    payload = run_uip_json(["ixp", "deployments", "list", project_name, "--output", "json"])
    return payload["Data"]


def list_deployments_if_present(project_name: str) -> list[dict[str, Any]]:
    """Deployments for one project, or [] if it vanished mid-run.

    `deployments list` is project-scoped and 404s once the project is gone.
    Callers get their project names from a TENANT-WIDE snapshot diff, so the
    set includes concurrent runs' projects, any of which their own teardown
    may delete between the listing and this call. Raising there would abort a
    caller mid-cleanup.

    ONLY the not-found case is absorbed. Every other failure — auth, network,
    a changed response shape — is re-raised: a caller that swallows an infra
    fault would report a false verdict or silently leave a real deployment
    behind.
    """
    try:
        return list_deployments(project_name)
    except RuntimeError as exc:
        if "not found" not in str(exc).lower():
            raise
        print(f"NOTE: '{project_name}' vanished mid-run; treating as gone.")
        return []


def ixp_node_identifiers(document: dict[str, Any]) -> list[str]:
    """Every identifying string carried by the IxP nodes of a parsed .flow.

    Each IxP node contributes its `type` (which embeds the deployed model's name)
    and its `inputs.modelName`. Callers match candidate names against these
    rather than against the file text, so a name appearing in a script literal,
    a label or an unused `definitions[]` entry does not count as wiring.
    """
    identifiers: list[str] = []
    for node in document.get("nodes", []):
        node_type = str(node.get("type", ""))
        if node_type.startswith(IXP_NODE_PREFIX):
            identifiers.append(node_type)
            identifiers.append(str((node.get("inputs") or {}).get("modelName") or ""))
    return identifiers


def matches_fixture_domain(*fields: str | None) -> bool:
    """True when any field carries a fixture-domain marker (case-insensitive)."""
    haystack = " ".join(str(field or "") for field in fields).lower()
    return any(marker in haystack for marker in DOMAIN_MARKERS)


def delete_folder_with_retry(folder_key: str) -> subprocess.CompletedProcess[str]:
    """Delete a folder, retrying transient failures; returns the last attempt."""
    completed: subprocess.CompletedProcess[str] | None = None
    for attempt in range(FOLDER_DELETE_ATTEMPTS):
        try:
            completed = run_uip(
                ["or", "folders", "delete", folder_key, "--yes", "--output", "json"]
            )
        except RuntimeError as exc:
            # run_uip turns a hung call into RuntimeError. Letting it escape
            # would skip the caller's WARN/LEAKED bookkeeping, losing the only
            # record that this run's folder — and its published node — is
            # still on the tenant.
            completed = subprocess.CompletedProcess(
                args=[], returncode=124, stdout="", stderr=str(exc)
            )
        if completed.returncode == 0:
            return completed
        if attempt < FOLDER_DELETE_ATTEMPTS - 1:
            print(
                f"folder delete attempt {attempt + 1} for {folder_key} failed "
                f"(exit {completed.returncode}); retrying in {FOLDER_DELETE_RETRY_SECONDS:g}s"
            )
            time.sleep(FOLDER_DELETE_RETRY_SECONDS)
    assert completed is not None
    return completed
