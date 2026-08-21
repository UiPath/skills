"""Tenant IXP-project inventory helpers for the Flow→IXP handoff e2e.

Shared by ``seed.py`` (snapshot before the run), ``check_handoff.py`` (grade what
the run created) and ``teardown.py`` (clean it up). This module is the canonical
place for the two design rationales; the other files cross-reference it rather
than restating them.

**Why a snapshot-and-diff instead of asking the agent to record what it made.**
The task prompt deliberately never mentions IXP, projects, publishing or
deployments — recognising that a design-time project must be built first is the
behaviour under test. A ``report.json``-style instruction ("record the project
you create") would hand the agent the answer. Diffing the tenant is the only way
to identify this run's artifacts without hinting.

**Why the baseline is hashed and neutrally named.** The snapshot file sits in the
sandbox root, beside the documents the agent works on. A name like
`.ixp_pre_projects.json` holding `[..., "dtf-contract-...-ixp"]` would hand the
agent the answer on any routine `ls -la` — IXP projects are exactly the concept
the prompt withholds. So the file is called `.grader_baseline.json` and stores
SHA-256 digests: the set difference still works, but nothing in it names IXP or a
project.

**Why the diff alone is not proof of ownership.** It is tenant-wide, so a project
created by a concurrent run — or by a person — while this task is in flight also
lands in the diff. That is fine for grading (a foreign project just won't be
wired into this sandbox's flow, so the check fails honestly) but NOT for
deletion. ``teardown.py`` therefore never deletes on the diff alone; see its
docstring for the attribution rule.

**Failure policy.** Every helper here fails loudly. Response shapes are indexed,
not ``.get``-ed, so a backend change surfaces as a KeyError naming the missing
field rather than an empty diff that reads as "the agent did nothing" — a false
verdict on the behaviour under test is worse than a crashed grader.

`uip ixp projects list` returns a PAGED envelope — ``Data.Projects[]`` plus
``Total``/``Offset``/``Limit``. `uip ixp deployments list` does NOT: its ``Data``
is a bare array with no total, so there is nothing to guard truncation against.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from typing import Any

# Written to the sandbox root by seed.py, read back by check_handoff.py and
# teardown.py. Relative, so it resolves against the sandbox each script runs in.
# Deliberately says nothing about IXP or projects — see the module docstring.
SNAPSHOT = ".grader_baseline.json"

# Well above any plausible tenant project count. list_project_names() raises
# rather than diffing against a truncated page, which would report
# page-fallen-off projects as newly created.
PROJECT_LIST_LIMIT = "500"

# Generous enough for `projects list` / `deployments list` on a cold tenant. The
# YAML's pre_run / post_run / run_command timeouts must all exceed this.
UIP_TIMEOUT_SECONDS = 120

# Node-type prefix for an IxP extraction node in a .flow.
IXP_NODE_PREFIX = "uipath.ixp."


def run_uip(arguments: list[str]) -> subprocess.CompletedProcess[str]:
    """Run one `uip` subcommand, capturing both streams."""
    return subprocess.run(
        ["uip", *arguments],
        capture_output=True,
        text=True,
        timeout=UIP_TIMEOUT_SECONDS,
    )


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


def list_project_names() -> set[str]:
    """Every IXP project `Name` (the slug, not the Title) visible on the tenant."""
    payload = run_uip_json(
        ["ixp", "projects", "list", "--limit", PROJECT_LIST_LIMIT, "--output", "json"]
    )
    listing = payload["Data"]
    projects = listing["Projects"]
    total = listing["Total"]
    if total > len(projects):
        raise RuntimeError(
            f"project list truncated ({len(projects)} of {total}) — "
            "raise PROJECT_LIST_LIMIT in ixp_projects.py"
        )
    return {project["Name"] for project in projects}


def project_digest(project_name: str) -> str:
    return hashlib.sha256(project_name.encode("utf-8")).hexdigest()


def write_snapshot(project_names: set[str]) -> None:
    """Record the baseline as opaque digests — see the module docstring."""
    with open(SNAPSHOT, "w", encoding="utf-8") as handle:
        json.dump(sorted(project_digest(name) for name in project_names), handle, indent=2)


def new_project_names() -> list[str]:
    """Project names that appeared since seed.py ran, sorted.

    Tenant-wide: see the module docstring on why this is safe to grade on but not
    safe to delete on.
    """
    if not os.path.exists(SNAPSHOT):
        raise RuntimeError(
            f"{SNAPSHOT} missing from {os.getcwd()} — the pre_run seed step did not run, "
            "so this run's projects cannot be told apart from pre-existing ones"
        )
    with open(SNAPSHOT, encoding="utf-8") as handle:
        before: set[str] = set(json.load(handle))
    return sorted(name for name in list_project_names() if project_digest(name) not in before)


def list_deployments(project_name: str) -> list[dict[str, Any]]:
    """Folder deployments for one project.

    Empty list means the project exists but was never folder-deployed. A missing
    project raises — `deployments list` is project-scoped and 404s once the
    project is gone, so callers must read this before deleting anything.
    """
    payload = run_uip_json(["ixp", "deployments", "list", project_name, "--output", "json"])
    return payload["Data"]


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
