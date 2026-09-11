#!/usr/bin/env python3
"""Tenant lifecycle for the Flow→IXP handoff e2e tasks: `seed` / `check` / `teardown`.

One script, three subcommands, matching the task YAML's three hook points:

  python3 handoff.py seed      # pre_run — precondition guards + tenant snapshot
  python3 handoff.py check     # success criterion — the primary gate (exit 0/1)
  python3 handoff.py teardown  # post_run — delete this run's artifacts; ALWAYS exit 0

**One grader, two tasks, split at the handoff (RE-13543).**

  e2e_03_project_creation_handoff.yaml — the DECISION. Its prompt never says
  IXP, project or publish, and `stop_early` on its uipath-ixp criterion cuts
  the run the moment the sibling skill is invoked, before `projects create`.
  Uses `seed` and `teardown`; never `check`, because nothing is built.

  e2e_04_build_mechanics.yaml — the BUILD. Its prompt says the extractor is
  missing, so the agent creates, deploys and wires it. Uses all three.

Why split: the decision is only observable while no resolvable extractor covers
the fixture domain. That precondition is an ABSENCE in shared tenant state, so
it cannot be allocated per run — a task that only READS it can share it with
every concurrent sibling, whereas e2e_03 used to CONSUME it by publishing an
extractor of its own. Cutting e2e_03 at the invocation makes it a reader, and
naming e2e_04's extractor from BUILD_PROJECT_PREFIX rather than the domain
stops it consuming the absence it no longer needs. Both tasks therefore share
one fixture domain and can run at the same time.

**seed** checks the one precondition left — that the `deployments create` verb
exists, since it rides the CLI `dev` dist-tag — then sweeps stale
domain-covering projects, snapshots tenant project names as digests, and
creates this run's folder, naming it in seed.json for the prompt.

The snapshot is how both tasks tell this run's projects from pre-existing ones:
`check` diffs against it, and teardown reads it for the run folder and for
attribution. It exists rather than asking the agent to record what it made
because e2e_03's prompt cannot say "project" without leaking the answer. It is
neutrally named and stores digests, so an agent `ls`-ing the sandbox learns
nothing.

**check** passes on either of two shapes, because flow-registry indexing
latency is org-scoped weather. Canonical measurement (2026-08-24, cited by
every other comment that mentions it): ~25s when healthy, ~8 minutes observed
during runs, hours at the tail on the CI tenant — with the Message Bus publish
itself clean at ~400ms throughout. The two shapes:

1. wired — a .flow node references this run's deployment or project, matched
   against parsed node fields, never file text;
2. degraded — the project was folder-deployed AND the flow landed a
   `core.logic.mock` AND the DeploymentName appears in the built artifacts
   (the breadcrumb proves the agent knew what it deployed and makes the swap
   mechanical; file text is deliberately accepted HERE — its job is to be
   found, not to execute).

A deployed-but-unwired-and-unbreadcrumbed run fails and is labelled
PROPAGATION SIGNATURE so tenant weather is never misread as a skill
regression.

**teardown** deletes only what it can attribute to this run: a project must be
wired into this sandbox's flow OR carry a deployment whose FolderKey is the
seed-created run folder. Anything else that appeared during the run is
reported, never guessed at — under parallel dispatch the lone new project can
be a sibling task's, and guessing deletes it mid-run. What that leaves behind
is collected on the next run by seed's domain sweep, which can be certain
where teardown cannot: attribution is per-run, but the fixture domain is
owned outright. The run folder itself is always deleted — deleting a folder is
what removes its deployments and their registry nodes (deployments have no
delete verb of their own), so the tenant does not accumulate a published
extractor per run. No other folder is ever deleted: a deployment the agent
parked elsewhere is reported as LEAKED for a hand-delete. Always exits 0: post_run
runs after grading, so a cleanup problem must never turn a graded result into
a failure (every failure is still printed).

`uip ixp projects list` returns a PAGED envelope (`Data.Projects[]` + `Total`);
`uip ixp deployments list` does NOT (bare array, nothing to guard truncation
against). Response shapes are indexed, not `.get`-ed: a backend change should
crash the grader with a named KeyError, not silently produce a false verdict.
"""

from __future__ import annotations

import glob
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import traceback
import uuid
from datetime import datetime, timezone
from typing import Any

TASK_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(TASK_DIR, "..", ".."))

from _shared.flow_check import find_project_dir  # noqa: E402

# ── shared helpers ────────────────────────────────────────────────────────────

# Written to the sandbox root by `seed`, read back by `check` and `teardown`.
# Relative, so it resolves against the sandbox. Neutrally named — see the
# module docstring on opacity.
SNAPSHOT = ".grader_baseline.json"

# Well above any plausible tenant project count. list_projects() raises
# rather than diffing against a truncated page, which would report
# page-fallen-off projects as newly created.
PROJECT_LIST_LIMIT = "500"

# Per-call cap. The YAML's pre_run / post_run / run_command timeouts (300s, the
# harness hard cap) must all exceed this — and the worst case must too: seed
# makes ~12 uip calls, so at 45s even four hung calls (180s) plus ~45s of
# retry sleeps and a nominal remainder fit under 300s, where the
# previous 120s cap busted the budget at two hung calls. Every call seed/check/
# teardown make is a list/get/registry/folder op that completes in seconds when
# healthy — nothing here runs `projects create` (~50s; that's the agent's).
# Env-tunable (like HANDOFF_RETRY_SECONDS) so the unit tests can exercise the
# timeout path without waiting out the real cap.
UIP_TIMEOUT_SECONDS = float(os.environ.get("HANDOFF_UIP_TIMEOUT_SECONDS", "45"))

# Node-type prefix for an IxP extraction node in a .flow.
IXP_NODE_PREFIX = "uipath.ixp."

# The run-scoped Orchestrator folder: seed creates it, seed.json names it for
# the prompt, and it is the ONLY folder this script ever deletes. Suffixed per
# RUN (uuid8, per tests/tasks/uipath-platform/seed.py), because a fixed literal
# is what two concurrent runs collided on in RE-13543. The prefix must not
# contain "ixp"/"project"/"publish" — the name reaches the agent, and e2e_03
# measures whether it works those words out for itself.
#
# Cost of a per-run name: nothing reclaims a leaked folder today. Finding one
# means enumerating `or folders list --all` and filtering the prefix, which the
# grader does not do — folders carry no timestamp, so there is no safe age
# guard of the kind sweep_domain_projects uses for projects. Affordable only
# because nothing gates on the folder now: an orphan is inert clutter, and
# leaked PROJECTS are still collected.
RUN_FOLDER_PREFIX = "flow-e2e-"

# Handed to the agent, and the reason the prompt can stay static while the
# folder name cannot. Convention and rationale: tests/README.md, "Lifecycle E2E
# tests (uipath-platform pattern)". Carries the folder name always, and for
# e2e_04 only, the extractor name — see create_run_folder for why e2e_03 must
# not be given that key.
RUN_HANDOFF_FILE = "seed.json"

# The extractor name e2e_04 hands its agent — THE reason both tasks can share
# one fixture domain concurrently. e2e_04 publishes an extractor trained on
# e2e_03's very documents; naming it from the domain would make it read as
# coverage, both to e2e_03's agent scanning the registry and to the sweep
# below. Off this prefix it is instead one more irrelevant node among the
# tenant's existing published ones, which that agent already filters by
# relevance (the registry is never empty there).
#
# Residual risk, unavoidable by any naming scheme: an agent that interrogates
# the node's taxonomy, finds falconry fields and reuses it — correct behaviour,
# and a false negative.
BUILD_PROJECT_PREFIX = "flow-build-"

# Folder deletes can fail transiently (provisioning race on a just-created
# folder, GH run 32967816894; an "Error resolving folder" on a half-hour-old
# folder, GH run 32968685992 — the CLI's RetryWillNotFix hint was wrong both
# times). Retried briefly wherever a folder is deleted. Env-tunable so the
# unit-test suite is not slowed by real sleeps.
FOLDER_DELETE_ATTEMPTS = 4
FOLDER_DELETE_RETRY_SECONDS = float(os.environ.get("HANDOFF_RETRY_SECONDS", "5"))


def _delete_folder_with_retry(folder_key: str) -> subprocess.CompletedProcess[str]:
    """Delete a folder, retrying transient failures; returns the last attempt."""
    for attempt in range(FOLDER_DELETE_ATTEMPTS):
        try:
            completed = run_uip(
                ["or", "folders", "delete", folder_key, "--yes", "--output", "json"]
            )
        except RuntimeError as exc:
            # run_uip turns a hung call into RuntimeError. Letting it escape
            # would skip delete_folder's WARN and cleanup's LEAKED line, losing
            # the only record that this run's folder — and its published node —
            # is still on the tenant.
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
    return completed


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
        # Neutral key names — see the module docstring on opacity. "scope" is
        # the seed-created run folder's Key (a bare GUID leaks nothing the
        # prompt's folder name doesn't already say).
        json.dump(
            {
                "names": sorted(project_digest(name) for name in project_names),
                "scope": run_folder_key,
            },
            handle,
            indent=2,
        )


def _read_snapshot() -> dict[str, Any]:
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
    before = _read_snapshot()["projects"]
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
    caller mid-cleanup — see cleanup(), where that used to strand the run
    folder and with it the published node that burns the fixture domain.

    ONLY the not-found case is absorbed. Every other failure — auth, network,
    a changed response shape — is re-raised, per the module docstring: a
    grader that swallows an infra fault reports a false verdict, and here it
    would also leave a real deployment behind in teardown.
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

# ── seed ──────────────────────────────────────────────────────────────────────

# Substrings that mark a project as belonging to the fixture domain, matched
# case-insensitively against its Name and Title by matches_fixture_domain.
#
# Keep them narrow: a match means an unattended `projects delete` on a shared
# tenant, so include only words an agent would build a project name from (the
# document type), never form field labels, and prefer the longer form
# ("falconry", not "falcon").
#
# Rotating the domain: pick one absent from and semantically distant to the
# tenant's published nodes, re-render the fixtures (../_fixtures/falconry/
# README.md has the spec), rename that directory and the two template_dir
# paths pointing at it, update these markers, and update both prompts — each
# names the document type.
#
# Deliberately narrow, because a match here means an unattended `projects
# delete` on a SHARED tenant. Only words an agent would plausibly build a
# project name from — the document type — earn a place. Field labels from the
# form ("raptor", "mews") do not: no agent names an extractor after them, and
# as bare substrings they collide with real products (Mews, Raptor). For the
# same reason this is "falconry", not "falcon" (CrowdStrike Falcon).
DOMAIN_MARKERS = ("falconry", "bird-of-prey", "bird_of_prey")

# A domain-covering project younger than this may belong to a LIVE concurrent
# instance of this task, so the sweep leaves it alone. The floor is the longest
# task budget using this grader (e2e_04's task_timeout, 3000s); two hours keeps
# a real margin over it even with clock skew between the tenant's CreatedAt and
# the runner's own clock. Anything older is a failed
# teardown's residue: no legitimate tenant asset carries a DOMAIN_MARKER,
# because the fixture owns its domain outright.
LEAKED_PROJECT_AGE_SECONDS = 7200.0


def matches_fixture_domain(*fields: str | None) -> bool:
    """True when any field carries a fixture-domain marker (case-insensitive)."""
    haystack = " ".join(str(field or "") for field in fields).lower()
    return any(marker in haystack for marker in DOMAIN_MARKERS)


def sweep_domain_projects(projects: list[dict[str, Any]]) -> list[str]:
    """Delete this fixture's stale projects; return what went.

    Collects two kinds: anything carrying a fixture-domain marker, and anything
    under BUILD_PROJECT_PREFIX (e2e_04's extractors, deliberately unmarked).

    Hygiene, not a gate. Teardown deletes only what it can attribute to its own
    run, so a project the agent created but never deployed nor wired is
    unattributable and gets left behind — that residue is what defeated the
    next run in RE-13543. Sweeping by domain marker is safe where per-run
    attribution is not, because the fixture owns its domain outright. Age is
    the concurrency guard: younger than one task budget, or undateable, and the
    project is left for its own run to clean up.
    """
    deleted: list[str] = []
    for project in projects:
        name = str(project["Name"])
        if not (
            matches_fixture_domain(name, project.get("Title"))
            or name.startswith(BUILD_PROJECT_PREFIX)
        ):
            continue
        age = iso_age_seconds(project.get("CreatedAt"))
        if age is None or age < LEAKED_PROJECT_AGE_SECONDS:
            age_note = "undateable" if age is None else f"{age:.0f}s old"
            print(
                f"KEEPING fixture project '{name}' ({age_note}) — it may belong "
                "to a live concurrent run."
            )
        elif delete_project(name):
            print(f"swept leaked fixture project '{name}' ({age:.0f}s old)")
            deleted.append(name)
    return deleted


def create_run_folder(name_extractor: bool) -> str:
    """Create this run's folder, write seed.json, return the folder's Key.

    Also the create-permission pre-flight: a runner that cannot create folders
    fails here, loudly, before the agent spends its budget.

    `name_extractor` adds the extractor name for e2e_04. e2e_03 must not get
    it: its prompt may never say "project" or "extractor", and a key by that
    name in a file the agent reads would leak exactly what it is graded on
    working out for itself.
    """
    run_folder_name = f"{RUN_FOLDER_PREFIX}{uuid.uuid4().hex[:8]}"
    created = run_uip_json(
        [
            "or", "folders", "create", run_folder_name,
            "-d",
            "uipath-maestro-flow handoff e2e run folder | one run's sandbox | "
            "only a failed teardown leaves it behind, and nothing reclaims it — "
            "disposable",
            "--output", "json",
        ]
    )
    folder_key = str(created["Data"]["Key"])
    handoff: dict[str, str] = {"folder": run_folder_name}
    if name_extractor:
        handoff["extractor"] = f"{BUILD_PROJECT_PREFIX}{uuid.uuid4().hex[:8]}"
    with open(RUN_HANDOFF_FILE, "w", encoding="utf-8") as handle:
        json.dump(handoff, handle, indent=2)
    print(f"OK: created run folder '{run_folder_name}' ({folder_key})")
    if name_extractor:
        print(f"OK: named this run's extractor '{handoff['extractor']}'")
    return folder_key


def require_deployments_create() -> None:
    """Exit 0 from the subcommand's own --help means the verb exists.

    Checked this way rather than grepping the parent help text, where unrelated
    prose containing "create" would slip past: a real subcommand's --help exits 0,
    an unknown one exits 3.
    """
    completed = run_uip(["ixp", "deployments", "create", "--help"])
    if completed.returncode != 0:
        raise RuntimeError(
            "this `uip` has no `ixp deployments create` — the task cannot pass. "
            "The verb landed in UiPath/cli#3575 and rides the `dev` tool dist-tag; "
            "check the image's CLI_VERSION rather than the skill. "
            f"`uip ixp deployments create --help` exited {completed.returncode}."
        )
    print("OK: `uip ixp deployments create` is available")


def seed_main(name_extractor: bool = False) -> int:
    require_deployments_create()
    # One listing serves both the sweep and the baseline. Sweep first, so a
    # swept name is not recorded as pre-existing — an agent that recreates that
    # slug then correctly reads as having created it.
    projects = list_projects()
    swept = sweep_domain_projects(projects)
    # Snapshot the projects BEFORE creating the folder, so the only step
    # between the folder existing and the snapshot recording it is a local
    # file write. A network failure in between leaks a folder teardown cannot
    # see (it reads the scope from the snapshot) — inert, per RUN_FOLDER_PREFIX.
    project_names = {str(project["Name"]) for project in projects} - set(swept)
    run_folder_key = create_run_folder(name_extractor)
    write_snapshot(project_names, run_folder_key)
    print(f"Snapshotted {len(project_names)} pre-existing IXP project(s) to {SNAPSHOT}")
    return 0


# ── check (the primary gate) ──────────────────────────────────────────────────

MOCK_NODE_TYPE = "core.logic.mock"


# The grader's own sandbox files. Excluded from the breadcrumb scan below:
# seed.json carries e2e_04's extractor name verbatim, so a Flow project that
# scaffolds at the sandbox root would otherwise satisfy the degraded gate for
# free, turning the fallback into a no-op.
GRADER_FILES = frozenset({RUN_HANDOFF_FILE, SNAPSHOT})


def project_files(*patterns: str) -> list[str]:
    """Matching files in the Flow project graded by validate_flow.py.

    find_project_dir exits with a FAIL: message when there is no Flow project or
    when several are ambiguous — the right diagnostic either way.
    """
    project_dir = find_project_dir()
    paths: list[str] = []
    for pattern in patterns:
        paths.extend(glob.glob(os.path.join(project_dir, pattern), recursive=True))
    return sorted(set(paths))


def flow_files() -> list[str]:
    return project_files("**/*.flow")


def load_flow(flow_path: str) -> dict[str, Any]:
    """Parse a .flow. An unparseable file raises, naming which one."""
    with open(flow_path, encoding="utf-8") as handle:
        try:
            return json.load(handle)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"{flow_path} is not valid JSON: {exc}") from exc


def describe(flow_path: str, document: dict[str, Any]) -> str:
    types = [str(node.get("type", "")) for node in document.get("nodes", [])]
    ixp_types = [node_type for node_type in types if node_type.startswith(IXP_NODE_PREFIX)]
    # The mock count is the tell that the agent took the no-model fallback, which
    # is the expected pre-fix behaviour — the most informative line in a failure.
    return (
        f"{flow_path}: uipath.ixp.* nodes={ixp_types} "
        f"{MOCK_NODE_TYPE}={types.count(MOCK_NODE_TYPE)}"
    )


def candidate_names() -> tuple[list[str], list[str]]:
    """Identifiers that would mark an IxP node as built by THIS run.

    Both the project name and each of its DeploymentNames, since either can land
    in the node (see module docstring). Falsy names are dropped: `DeploymentName`
    is nullable in the API, and an empty string is a substring of everything, so
    keeping one would match any stale node and defeat the residue guard.

    Gating identifiers come ONLY from deployments in the seed-created run folder.
    The snapshot diff is tenant-wide, so a project a concurrent task created and
    deployed elsewhere can appear in it — counting that deployment would let a
    foreign node satisfy the served-node probe and wrongly reject this run's
    degraded fallback. The prompt directs everything into the run folder, so an
    in-folder deployment is this run's by construction; off-folder ones are
    printed and ignored.

    Returns an empty list when nothing was created, when what was created is
    named after the fixture domain, or when nothing was deployed into the run
    folder — printing which it was.
    """
    scope = _read_snapshot()["scope"]
    created_projects = new_project_names()
    if not created_projects:
        print(
            "FAIL: no IXP project was created during this run.",
            file=sys.stderr,
        )
        return [], []

    # The concurrency contract, enforced rather than hoped for. e2e_04's prompt
    # tells the agent to name the extractor from seed.json, off
    # BUILD_PROJECT_PREFIX; a domain-named one instead reads as fixture
    # coverage to any e2e_03 running alongside, and silently invalidates it.
    # Prose in a prompt cannot guarantee that, so fail here when it is ignored.
    domain_named = [
        name for name in created_projects if matches_fixture_domain(name)
    ]
    if domain_named:
        print(
            f"FAIL: {domain_named} named after the fixture domain. The prompt "
            "gives the extractor's name in seed.json precisely so what this run "
            "publishes cannot read as domain coverage to a concurrent sibling.",
            file=sys.stderr,
        )
        return [], []
    print(f"Projects created this run: {created_projects}")

    names: list[str] = []
    deployment_names: list[str] = []
    for project_name in created_projects:
        in_scope = 0
        for deployment in list_deployments_if_present(project_name):
            deployment_name = deployment["DeploymentName"]
            print(
                f"  {project_name} -> DeploymentName={deployment_name} "
                f"version={deployment['ModelVersion']} folder={deployment['FolderKey']}"
            )
            if deployment["FolderKey"] != scope:
                print(f"    ignored for gating: not in this run's folder ({scope})")
                continue
            in_scope += 1
            if deployment_name:
                names.append(deployment_name)
                deployment_names.append(deployment_name)
        # Per-project, not run-wide: a sibling project with no in-folder
        # deployment (concurrent tenant activity) must not contribute a
        # candidate name, or it could satisfy the gate for a node this run
        # never deployed.
        if in_scope and project_name:
            names.append(project_name)

    if not names:
        print(
            f"FAIL: none of the project(s) {created_projects} created this run were "
            "folder-deployed into this run's folder. "
            "`uip ixp deployments create --folder-key <the folder the prompt names>` "
            "is what makes a trained model appear in the Maestro flow registry; "
            "without it no uipath.ixp.* node can exist for this project.",
            file=sys.stderr,
        )
        return [], []
    return names, deployment_names


def sanitize_registry_segment(name: str) -> str:
    """The registry's tail-segment sanitization: lowercase, non-alnum runs → '-'.

    NodeTypes embed the deployment name in this form (`falconry_licences-x` →
    `falconry-licences-x`), so a raw name never substring-matches its own
    NodeType when it carries an underscore.
    """
    return re.sub(r"[^a-z0-9]+", "-", name.lower())


def name_matches(name: str, haystack: str) -> bool:
    """One containment rule everywhere a run identifier is looked for: the raw
    name (casefolded) or its registry-sanitized form, against the haystack as
    served. Only the NAME is sanitized — the registry already sanitizes the
    segment it embeds in a NodeType, so that form is exactly what matches it,
    and leaving the haystack alone keeps the dots between segments as
    boundaries. Keeps the .flow wired-match and the registry probe in
    agreement: a DeploymentName carrying `_` or uppercase still matches its own
    lowercased-and-hyphenated NodeType.
    """
    return (
        name.lower() in haystack.lower()
        or sanitize_registry_segment(name) in haystack.lower()
    )


def run_node_in_registry(names: list[str]) -> str | None:
    """The NodeType the registry currently serves for this run, or None.

    Pulls fresh, finds a uipath.ixp.* node that embeds one of this run's
    identifiers — via name_matches, the same rule check_main applies to the
    .flow — and confirms it resolves via `registry get`. Deliberately
    tolerant: any error reads as "not served" — this probe decides whether the
    degraded fallback is available, and a broken registry is exactly the case
    the fallback exists for.
    """
    try:
        run_uip(["maestro", "flow", "registry", "pull", "--force"])
        payload = run_uip_json(
            ["maestro", "flow", "registry", "search", "uipath.ixp", "--output", "json"]
        )
        for node in payload["Data"]:
            node_type = str(node["NodeType"])
            haystack = f"{node.get('DisplayName', '')} {node_type}"
            if any(name_matches(name, haystack) for name in names):
                completed = run_uip(
                    ["maestro", "flow", "registry", "get", node_type, "--output", "json"]
                )
                if completed.returncode == 0:
                    return node_type
    except Exception as exc:
        print(f"registry probe failed ({exc}); treating this run's node as not served")
    return None


def check_main() -> int:
    names, deployment_names = candidate_names()
    if not names:
        # Print what was built anyway: "no project was created" alone cannot
        # distinguish a mock fallback (routing gap) from the agent wiring a
        # pre-existing extractor (correct on a tenant that already covers the
        # domain — the scenario's precondition does not hold).
        for flow_path in flow_files():
            print(f"  built: {describe(flow_path, load_flow(flow_path))}", file=sys.stderr)
        return 1

    flows = flow_files()
    if not flows:
        print("FAIL: the Flow project contains no .flow file.", file=sys.stderr)
        return 1

    parsed = {flow_path: load_flow(flow_path) for flow_path in flows}
    for flow_path, document in parsed.items():
        identifiers = ixp_node_identifiers(document)
        wired = next(
            (
                name
                for name in names
                if any(name_matches(name, found) for found in identifiers)
            ),
            None,
        )
        if wired:
            print(f"OK: {flow_path} wires an IxP node for this run's project ({wired})")
            print(f"    {describe(flow_path, document)}")
            return 0

    # Degraded acceptance: deployment exists, the flow landed the documented
    # mock fallback, and the DeploymentName is recorded in the built artifacts.
    has_mock = any(
        str(node.get("type", "")) == MOCK_NODE_TYPE
        for document in parsed.values()
        for node in document.get("nodes", [])
    )
    if has_mock and deployment_names:
        # The fallback is only legitimate while the registry genuinely does not
        # serve this run's node — otherwise the agent could (and should) have
        # wired the real one. Probe now rather than trusting the precondition.
        served = run_node_in_registry(names)
        if served:
            print(
                f"FAIL: the registry serves this run's node ('{served}'), so the "
                f"{MOCK_NODE_TYPE} fallback is not acceptable — the agent should have "
                "wired the real uipath.ixp.* node.",
                file=sys.stderr,
            )
            for flow_path, document in parsed.items():
                print(f"  {describe(flow_path, document)}", file=sys.stderr)
            return 1
        breadcrumbs = []
        for artifact_path in project_files("**/*.flow", "**/*.md", "**/*.json", "**/*.txt"):
            if os.path.basename(artifact_path) in GRADER_FILES:
                continue
            with open(artifact_path, encoding="utf-8", errors="replace") as handle:
                content = handle.read()
            breadcrumbs.extend(
                (name, artifact_path) for name in deployment_names if name in content
            )
        if breadcrumbs:
            recorded_name, recorded_in = breadcrumbs[0]
            print(
                "OK (degraded): the registry never served this run's node — the "
                "PROPAGATION SIGNATURE case — and the agent did exactly what the "
                f"docs prescribe: folder-deployed ({recorded_name}), landed a "
                f"{MOCK_NODE_TYPE} placeholder, and recorded the DeploymentName in "
                f"{recorded_in} so the swap is mechanical once the registry catches up."
            )
            for flow_path, document in parsed.items():
                print(f"    {describe(flow_path, document)}")
            return 0

    print(
        f"FAIL: no IxP node in {flows} references anything created this run ({names}).",
        file=sys.stderr,
    )
    for flow_path, document in parsed.items():
        print(f"  {describe(flow_path, document)}", file=sys.stderr)
    print(
        "  A uipath.ixp.* node that is NOT this run's means the agent wired a pre-existing "
        "extractor (possibly residue from an earlier run) instead of building one.",
        file=sys.stderr,
    )
    # Project names only: `deployments list` is project-scoped, so probing a
    # DeploymentName is a guaranteed 404 that only burns the criterion budget.
    for name in [candidate for candidate in names if candidate not in deployment_names]:
        # Tolerant read: this only LABELS an already-failed run, so the
        # grader fail-fast rule does not apply.
        try:
            has_deployments = bool(list_deployments(name))
        except Exception:
            has_deployments = False
        if has_deployments:
            print(
                f"  PROPAGATION SIGNATURE: '{name}' was created AND folder-deployed this run, "
                "yet no flow wires it. On an environment with lagging registry indexing the "
                "node can take hours to surface (~25s when healthy — module docstring), so "
                "the agent could never have discovered it. This is tenant weather, not a "
                "skill regression — see the task description before filing anything.",
                file=sys.stderr,
            )
    return 1

# ── teardown ──────────────────────────────────────────────────────────────────

def delete_folder(folder_key: str) -> bool:
    completed = _delete_folder_with_retry(folder_key)
    if completed.returncode == 0:
        print(f"OK: deleted run-scoped folder {folder_key} (removes its registry nodes)")
        return True
    detail = (completed.stdout or completed.stderr).strip()
    print(f"WARN: could not delete folder {folder_key} (exit {completed.returncode}): {detail}")
    return False


def delete_project(project_name: str) -> bool:
    """Delete one IXP project; True when it actually went.

    Tolerant on failure (prints, never raises) because teardown must always
    exit 0. The return value matters to seed's residue sweep, which must not
    report a project as collected when the delete was refused.
    """
    completed = run_uip(["ixp", "projects", "delete", project_name, "-y", "--output", "json"])
    if completed.returncode == 0:
        print(f"OK: deleted IXP project '{project_name}'")
        return True
    detail = (completed.stdout or completed.stderr).strip()
    print(
        f"WARN: could not delete '{project_name}' "
        f"(exit {completed.returncode}): {detail}"
    )
    return False


def wired_ixp_references() -> str:
    """IxP node identifiers from every .flow under the sandbox, joined.

    Deliberately tolerant and glob-based rather than reusing flow_files():
    that helper sys.exits on an ambiguous or missing project, which is right
    when grading and wrong here — with no readable flow, attribution proceeds
    on the run-folder FolderKey alone.
    """
    references: list[str] = []
    for flow_path in glob.glob("**/*.flow", recursive=True):
        try:
            with open(flow_path, encoding="utf-8") as handle:
                references.extend(ixp_node_identifiers(json.load(handle)))
        except Exception as exc:
            # One malformed .flow (a plausible failed-run artifact) must not
            # abort cleanup — attribution just proceeds without this file.
            print(f"skipping unreadable flow {flow_path} during cleanup: {exc}")
    return " ".join(references)


def belongs_to_another_run(deployments: list[dict[str, Any]], run_folder_key: str) -> bool:
    """True when any deployment sits in a DIFFERENT run's folder.

    One O(1) `folders get` per deployment, on the teardown path only, and only
    for projects that are not already proven ours. RUN_FOLDER_PREFIX is created
    by nothing but this grader, so a folder carrying it that is not ours is a
    concurrent instance's.
    """
    for deployment in deployments:
        folder_key = str(deployment["FolderKey"])
        if folder_key == run_folder_key:
            continue
        folder = folder_get(folder_key)
        if folder is None:
            # Fail safe. A failing `folders get` is not proof the folder is not
            # a sibling's — the same rule cleanup() states about deletes, for
            # the same reason. Disowning one of our own projects costs a leaked
            # project the next sweep collects; deleting a live sibling's costs
            # that run.
            print(
                f"NOTE: folder {folder_key} did not resolve; treating its "
                "project as possibly another run's and leaving it alone."
            )
            return True
        name = str(folder.get("Name") or folder.get("DisplayName") or "")
        if name.startswith(RUN_FOLDER_PREFIX):
            return True
    return False


def this_runs_project(
    project_name: str,
    deployments: list[dict[str, Any]],
    run_folder_key: str,
    flow_text: str,
) -> bool:
    """Whether this run may delete `project_name` — see delete_this_runs_projects."""
    if any(deployment["FolderKey"] == run_folder_key for deployment in deployments):
        return True
    wired = project_name in flow_text or any(
        deployment["DeploymentName"] and deployment["DeploymentName"] in flow_text
        for deployment in deployments
    )
    return wired and not belongs_to_another_run(deployments, run_folder_key)


def delete_this_runs_projects(run_folder_key: str) -> list[tuple[str, str]]:
    """Delete the projects attributable to this run; return their deployments.

    Attribution is deliberately narrow, because the candidate set is a
    tenant-wide diff and a wrong guess deletes a live sibling's project
    mid-run.

    A deployment in the folder seed created is proof — only this run has that
    folder. Failing that, being named in THIS sandbox's .flow is good evidence
    (the sandbox is private to the run) and catches the case worth catching: an
    agent that built the project but deployed it somewhere else, whose
    deployment would otherwise sit on the tenant forever.

    The exception is what makes that safe under concurrency. Both tasks build
    extractors over the same documents and search the same registry, so an
    agent whose own node has not propagated can legitimately wire a SIBLING's.
    Such a node's deployment lives in that sibling's run folder, so a wired
    project deployed into any other RUN_FOLDER_PREFIX folder is disowned.
    """
    created_projects = new_project_names()
    if not created_projects:
        print("No IXP project was created this run — only the run folder to remove.")
        return []

    # Read deployments BEFORE deleting: `deployments list` 404s once the
    # project is gone, so this is the last chance to name both what is
    # attributable and what is being left behind.
    deployments_by_project = {
        project_name: list_deployments_if_present(project_name)
        for project_name in created_projects
    }
    flow_text = wired_ixp_references()

    attributable = [
        project_name
        for project_name, deployments in deployments_by_project.items()
        if this_runs_project(project_name, deployments, run_folder_key, flow_text)
    ]

    unattributable = [name for name in created_projects if name not in attributable]
    if unattributable:
        print(
            f"NOT DELETED: {unattributable} appeared during this run but are "
            "neither deployed into this run's folder nor wired into this "
            "sandbox's flow — they may belong to a concurrent run or another "
            "user. Reported, not guessed at; the next seed's sweep collects "
            "this fixture's own residue."
        )

    for project_name in attributable:
        delete_project(project_name)

    return [
        (deployment["DeploymentName"], deployment["FolderKey"])
        for project_name in attributable
        for deployment in deployments_by_project[project_name]
    ]


def cleanup() -> None:
    if not os.path.exists(SNAPSHOT):
        print(f"SKIP: no {SNAPSHOT} — the pre_run seed step did not run.")
        return
    run_folder_key = _read_snapshot()["scope"]

    # Project cleanup is best-effort and MUST NOT be able to skip the folder
    # delete below: the folder is what removes this run's deployment and its
    # registry node, and a stranded one burns the fixture domain for every
    # later run. Anything raising in here is reported and stepped over.
    deployment_records: list[tuple[str, str]] = []
    try:
        deployment_records = delete_this_runs_projects(run_folder_key)
    except BaseException:  # noqa: BLE001 — the folder delete is what matters
        print("WARN: project cleanup failed; still deleting the run folder:")
        traceback.print_exc(file=sys.stdout)

    # Deployments cannot be deleted directly, but deleting their folder removes
    # them (and their registry nodes) — see the module docstring. The run folder
    # seed created is the ONLY folder this script deletes; anything the agent
    # parked elsewhere is reported below.
    # Judge deletion by the delete's OWN result, never by a lookup. GH runs
    # 33162961197 and 33173123153 both printed "already gone" for a folder
    # whose registry node is still served days later: a failing `folders get`
    # is not proof the folder is gone, and treating it as proof is what burned
    # the falconry fixture domain. A spurious LEAKED line is cheap; a silent
    # skip costs the domain.
    run_folder_deleted = delete_folder(run_folder_key)
    if not run_folder_deleted and folder_get(run_folder_key) is None:
        print(
            f"NOTE: run folder {run_folder_key} does not resolve after the failed "
            "delete — it may already be gone, or merely unreadable. Reported as "
            "leaked either way. Nothing reclaims it — delete it by hand, or "
            "find it with `or folders list --all` (see RUN_FOLDER_PREFIX)."
        )

    stranded = [
        (deployment_name, folder_key)
        for deployment_name, folder_key in deployment_records
        if folder_key != run_folder_key or not run_folder_deleted
    ]
    if stranded:
        print(
            f"LEAKED: {len(stranded)} deployment(s) remain — each sits outside "
            "this run's folder (never deleted by this script) or in the run "
            "folder whose deletion failed above:"
        )
        for deployment_name, folder_key in stranded:
            print(f"  - {deployment_name} in folder {folder_key}")


def teardown_main() -> int:
    # BaseException, not Exception: a helper that calls sys.exit raises SystemExit,
    # which Exception would let through and break the always-0 contract.
    try:
        cleanup()
    except BaseException:  # noqa: BLE001 — see module docstring: post_run must exit 0
        print("WARN: cleanup failed; projects created by this run may remain:")
        traceback.print_exc(file=sys.stdout)
    return 0

# ── dispatch ──────────────────────────────────────────────────────────────────

SUBCOMMANDS = {"seed": seed_main, "check": check_main, "teardown": teardown_main}
NAME_EXTRACTOR_FLAG = "--name-extractor"

if __name__ == "__main__":
    arguments = sys.argv[1:]
    extra = arguments[1:]
    if (
        not arguments
        or arguments[0] not in SUBCOMMANDS
        or extra not in ([], [NAME_EXTRACTOR_FLAG] if arguments[0] == "seed" else [])
    ):
        print(
            f"usage: handoff.py {'|'.join(SUBCOMMANDS)}  "
            f"(seed also takes {NAME_EXTRACTOR_FLAG})",
            file=sys.stderr,
        )
        sys.exit(2)
    if arguments[0] == "seed":
        sys.exit(seed_main(name_extractor=bool(extra)))
    sys.exit(SUBCOMMANDS[arguments[0]]())
