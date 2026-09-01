#!/usr/bin/env python3
"""Tenant lifecycle for the Flow→IXP handoff e2e: `seed` / `check` / `teardown`.

One script, three subcommands, matching the task YAML's three hook points:

  python3 handoff.py seed      # pre_run — precondition guards + tenant snapshot
  python3 handoff.py check     # success criterion — the primary gate (exit 0/1)
  python3 handoff.py teardown  # post_run — delete this run's artifacts; ALWAYS exit 0

**seed** fails loudly on any unmet precondition, naming the real cause before
the agent spends its budget: the `deployments create` verb must exist (rides
the CLI `dev` dist-tag) and no published extractor may cover the fixture
domain (a resolvable match makes reuse the correct agent action, so the
redirect becomes unmeasurable — rotate the fixture domain per
documents/README.md). It then creates the run-scoped Orchestrator folder the
prompt names (RUN_FOLDER_NAME — the per-task fixed-name convention of
tests/tasks/uipath-platform/cleanup.py's uuid8 tagging), first deleting any
same-named leftover found by an exact-name `folders get`: a leftover OLDER
than one task budget is the previous run's failed teardown, and deleting it
removes the leaked deployment and its registry node, so seed self-heals the
fixture domain without ever touching a folder it did not name. A same-named
folder YOUNGER than that is presumed a live concurrent instance (the fixed
name makes the task single-flight per tenant) and seed fails instead of
deleting it. Finally it snapshots the tenant's project names as digests.

**Why a snapshot-and-diff instead of asking the agent to record what it made:**
the prompt deliberately never mentions IXP, projects, or deployments —
recognising that a design-time project must be built first is the behaviour
under test, and a "record what you created" instruction would leak the answer.
Naming the run FOLDER in the prompt leaks nothing (an admin-assigned sandbox
folder is ordinary user language), so folder attribution is exact; project
attribution still needs the diff. The snapshot file is neutrally named and
stores SHA-256 digests so an agent `ls`-ing the sandbox learns nothing.

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
reported, never guessed at. The run folder itself is always deleted —
deleting a folder is what removes its deployments and their registry nodes
(deployments have no delete verb of their own) — which is what lets a passing
run restore its own preconditions instead of permanently burning the fixture
domain. No other folder is ever deleted: a deployment the agent parked
elsewhere is reported as LEAKED for a hand-delete. Always exits 0: post_run
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
from datetime import datetime, timezone
from typing import Any

TASK_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(TASK_DIR, "..", "..", "_shared"))

from flow_check import find_project_dir  # noqa: E402

# ── shared helpers ────────────────────────────────────────────────────────────

# Written to the sandbox root by `seed`, read back by `check` and `teardown`.
# Relative, so it resolves against the sandbox. Neutrally named — see the
# module docstring on opacity.
SNAPSHOT = ".grader_baseline.json"

# Well above any plausible tenant project count. list_project_names() raises
# rather than diffing against a truncated page, which would report
# page-fallen-off projects as newly created.
PROJECT_LIST_LIMIT = "500"

# Per-call cap. The YAML's pre_run / post_run / run_command timeouts (300s, the
# harness hard cap) must all exceed this — and the worst case must too: seed
# makes ~12 uip calls, so at 45s even four hung calls (180s) plus ~45s of
# retry/re-probe sleeps and a nominal remainder fit under 300s, where the
# previous 120s cap busted the budget at two hung calls. Every call seed/check/
# teardown make is a list/get/registry/folder op that completes in seconds when
# healthy — nothing here runs `projects create` (~50s; that's the agent's).
# Env-tunable (like HANDOFF_RETRY_SECONDS) so the unit tests can exercise the
# timeout path without waiting out the real cap.
UIP_TIMEOUT_SECONDS = float(os.environ.get("HANDOFF_UIP_TIMEOUT_SECONDS", "45"))

# Node-type prefix for an IxP extraction node in a .flow.
IXP_NODE_PREFIX = "uipath.ixp."

# The run-scoped Orchestrator folder: seed creates it, the prompt names it, and
# it is the ONLY folder this script ever deletes. Fixed per task (the uuid8
# suffix distinguishes this task from siblings, per the
# tests/tasks/uipath-platform/cleanup.py convention), which makes the task
# single-flight per tenant — see LIVE_FOLDER_AGE_SECONDS.
# KEEP IN SYNC with the folder name in the task YAML's initial_prompt. The
# name must not contain "ixp"/"project"/"publish" — the prompt carries it, and
# never saying those is the point of the task.
RUN_FOLDER_NAME = "flow-e2e-e9fbf2d0"

# A same-named folder younger than this is presumed to belong to a LIVE
# concurrent instance of this task (task_timeout is 3000s — anything younger
# may still be running), not a failed teardown. Seed fails instead of deleting
# it. Age comes from the stamp below; a missing or unparseable stamp degrades
# to "old" (deletable), so the guard never blocks on an optional field.
LIVE_FOLDER_AGE_SECONDS = 3600.0

# The folder API exposes no creation time (verified 2026-09-01 on the CI
# tenant: Name/Id/Key/Description/Path/ParentID/FolderType/IsPersonal/
# ProvisionType/PermissionModel/FeedType — nothing temporal), so seed writes
# its own: this marker plus a UTC ISO-8601 timestamp goes into the folder's
# Description at create time (`folders create -d`), and heal reads it back.
# The rest of the description explains the folder to anyone browsing the tenant.
STAMP_MARKER = "created="

# Folder deletes can fail transiently (provisioning race on a just-created
# folder, GH run 32967816894; an "Error resolving folder" on a half-hour-old
# folder, GH run 32968685992 — the CLI's RetryWillNotFix hint was wrong both
# times). Retried briefly wherever a folder is deleted. Env-tunable so the
# unit-test suite is not slowed by real sleeps.
FOLDER_DELETE_ATTEMPTS = 4
FOLDER_DELETE_RETRY_SECONDS = float(os.environ.get("HANDOFF_RETRY_SECONDS", "5"))


def delete_folder_with_retry(folder_key: str) -> subprocess.CompletedProcess[str]:
    """Delete a folder, retrying transient failures; returns the last attempt."""
    for attempt in range(FOLDER_DELETE_ATTEMPTS):
        completed = run_uip(["or", "folders", "delete", folder_key, "--yes", "--output", "json"])
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
            "raise PROJECT_LIST_LIMIT"
        )
    return {project["Name"] for project in projects}


def project_digest(project_name: str) -> str:
    return hashlib.sha256(project_name.encode("utf-8")).hexdigest()


def folder_get(identifier: str) -> dict[str, Any] | None:
    """One folder by name or key, or None when it does not resolve.

    `or folders get` accepts either form, so this is both teardown's
    already-gone check (by key) and seed's leftover lookup (by name) — a
    single O(1) call. Listing the tenant instead does not work: the CI
    tenant holds more folders than one page (GH run 33533126890).
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


def age_seconds(folder: dict[str, Any]) -> float | None:
    """Seconds since seed stamped the folder's Description, or None if unstamped.

    Best-effort by design: no stamp (a pre-stamp leftover, a hand-made folder,
    the API's default "No description") or an unparseable one returns None and
    the caller treats the folder as old — the guard must never block a run on
    a missing field.
    """
    match = re.search(re.escape(STAMP_MARKER) + r"(\S+)", str(folder.get("Description") or ""))
    if not match:
        return None
    try:
        created = datetime.fromisoformat(match.group(1))
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

# ── seed ──────────────────────────────────────────────────────────────────────

# Substrings that would mean a published extractor already covers the fixture
# domain (see documents/README.md). Matched case-insensitively against every
# registry node's display name and type. Rotated whenever a passing run burns
# the domain (documents/README.md explains why that happens).
DOMAIN_MARKERS = ("falcon", "raptor", "mews", "bird-of-prey", "bird_of_prey")

# Registry deletion propagation can lag behind a folder delete, so a self-heal
# re-probes a few times before giving up. Two attempts, not more: the pre_run
# hook timeout is hard-capped at 300s and the whole self-heal path must fit
# under it. Same env knob as the folder-delete retry so the unit-test suite
# runs sleep-free.
DOMAIN_RECHECK_ATTEMPTS = 2
DOMAIN_RECHECK_SECONDS = float(os.environ.get("HANDOFF_RETRY_SECONDS", "15"))


def heal_leftover_run_folder() -> bool:
    """Delete a leftover run folder from a failed teardown; True if one went.

    Looked up by its exact name, so nothing this script did not itself name is
    ever a delete candidate (Orchestrator folder names are unique per parent,
    so there is at most one). A leftover carries the previous run's
    deployment, whose registry node covers the fixture domain — deleting the
    folder is the self-heal that unblocks the domain gate. Two refusals guard
    it: a folder young enough to belong to a LIVE concurrent instance of this
    task raises rather than yank a running sibling's folder (the fixed name
    makes this task single-flight — see RUN_FOLDER_NAME), and a delete that
    keeps failing raises because the same name is about to be recreated and a
    runner that cannot delete folders cannot tear down either.
    """
    leftover = folder_get(RUN_FOLDER_NAME)
    if leftover is None:
        return False

    folder_key = str(leftover["Key"])
    age = age_seconds(leftover)
    if age is not None and age < LIVE_FOLDER_AGE_SECONDS:
        raise RuntimeError(
            f"folder '{RUN_FOLDER_NAME}' ({folder_key}) was stamped only {age:.0f}s ago — "
            "younger than one task budget, so it likely belongs to a LIVE "
            "concurrent instance of this task rather than a failed teardown. "
            "Refusing to delete it: wait for that run to finish and retry, or "
            "delete the folder by hand if you know it is a fresh leak."
        )

    completed = delete_folder_with_retry(folder_key)
    if completed.returncode != 0:
        detail = " ".join((completed.stderr or completed.stdout).split())
        raise RuntimeError(
            f"could not delete leftover run folder '{RUN_FOLDER_NAME}' "
            f"({folder_key}, exit {completed.returncode}): {detail}. Teardown "
            "depends on folder delete — fix the runner's folder-delete "
            "permission or delete the folder by hand."
        )
    print(f"self-heal: deleted leftover run folder {folder_key} ('{RUN_FOLDER_NAME}')")
    return True


def create_run_folder() -> str:
    """Create the run-scoped folder the prompt names, stamped; return its Key.

    Also the create-permission pre-flight: a runner that cannot create folders
    fails here, loudly, before the agent spends its budget. (Delete permission
    is proven by heal_leftover_run_folder the first time it matters — a
    delete-permission regression costs one leaked run, then fails loudly at
    the next seed.)
    """
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    description = (
        f"uipath-maestro-flow handoff e2e run folder | {STAMP_MARKER}{stamp} | "
        "only a failed teardown leaves it behind; disposable once older than one hour"
    )
    created = run_uip_json(
        ["or", "folders", "create", RUN_FOLDER_NAME, "-d", description, "--output", "json"]
    )
    folder_key = str(created["Data"]["Key"])
    print(f"OK: created run folder '{RUN_FOLDER_NAME}' ({folder_key}), stamped {stamp}")
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


def resolvable_covering_nodes() -> tuple[list[str], int, int]:
    """One registry pull + search + probe cycle over the fixture domain.

    Returns (resolvable domain-matched NodeTypes, total nodes, name matches).
    Each name match is probed with `registry get`: resolvable = a live extractor;
    unresolvable = dangling residue nobody can use (report, step over).
    """
    run_uip(["maestro", "flow", "registry", "pull", "--force"])
    payload = run_uip_json(
        ["maestro", "flow", "registry", "search", "uipath.ixp", "--output", "json"]
    )
    nodes = payload["Data"]
    matched = [
        node["NodeType"]
        for node in nodes
        if any(
            marker in f"{node.get('DisplayName', '')} {node['NodeType']}".lower()
            for marker in DOMAIN_MARKERS
        )
    ]

    covered = []
    for node_type in matched:
        completed = run_uip(["maestro", "flow", "registry", "get", node_type, "--output", "json"])
        if completed.returncode == 0:
            covered.append(node_type)
        else:
            print(
                f"IGNORING unresolvable match '{node_type}' "
                f"(`registry get` exited {completed.returncode}) — stale deployment "
                "residue, not a usable extractor."
            )
    return covered, len(nodes), len(matched)


def require_domain_uncovered(healed: bool) -> None:
    """Fail if a resolvable published extractor already covers the fixture domain.

    If one does, reusing it is the correct agent action and the handoff never
    fires — the run would go red for a reason unrelated to the behaviour under
    test. When heal_leftover_run_folder just deleted a leftover, its node is
    the likely cover and registry deletion propagation can lag, so the probe
    re-checks a few times. A node still resolvable after that fails THIS run
    (the agent could reuse it), but if the cover was the healed leftover the
    next run starts clean; a persistent block means a genuinely foreign
    extractor covers the domain — this script never deletes anything it did
    not name, so delete that extractor's folder by hand if it is disposable,
    or rotate the fixture domain per documents/README.md.
    """
    covered, total, matched = resolvable_covering_nodes()
    if covered and healed:
        for _ in range(DOMAIN_RECHECK_ATTEMPTS):
            time.sleep(DOMAIN_RECHECK_SECONDS)
            covered, total, matched = resolvable_covering_nodes()
            if not covered:
                print("OK: fixture domain clear after self-heal")
                break

    if covered:
        remedy = (
            "A leftover run folder was deleted just now, so the registry may "
            "still be serving its stale node — re-run the task."
            if healed
            else "No leftover run folder was found to heal, so this is a foreign "
            "extractor: delete its folder by hand if it is disposable, or "
            "rotate the fixture domain (documents/README.md)."
        )
        raise RuntimeError(
            "the fixture domain is already covered by resolvable published "
            f"extractor(s) {covered} — the agent can correctly reuse one, so this "
            f"task cannot measure the handoff. {remedy}"
        )
    print(
        f"OK: none of the {total} published IxP node(s) cover the fixture domain "
        f"({matched} name match(es), none resolvable)"
    )


def seed_main() -> int:
    require_deployments_create()
    healed = heal_leftover_run_folder()
    require_domain_uncovered(healed)
    # Snapshot the projects BEFORE creating the folder, so the only step
    # between the folder existing and the snapshot recording it is a local
    # file write. A network failure in between would leave a folder teardown
    # cannot see (it reads the scope from the snapshot) — recoverable, since
    # the next seed heals it by name, but not worth the round trip.
    project_names = list_project_names()
    run_folder_key = create_run_folder()
    write_snapshot(project_names, run_folder_key)
    print(f"Snapshotted {len(project_names)} pre-existing IXP project(s) to {SNAPSHOT}")
    return 0

# ── check (the primary gate) ──────────────────────────────────────────────────

MOCK_NODE_TYPE = "core.logic.mock"


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

    Returns an empty list when nothing was created or nothing was deployed into
    the run folder, after printing which of the two it was.
    """
    scope = _read_snapshot()["scope"]
    created_projects = new_project_names()
    if not created_projects:
        print(
            "FAIL: no IXP project was created during this run — the Flow skill never "
            "handed off to uipath-ixp.",
            file=sys.stderr,
        )
        return [], []
    print(f"Projects created this run: {created_projects}")

    names: list[str] = []
    deployment_names: list[str] = []
    for project_name in created_projects:
        in_scope = 0
        for deployment in list_deployments(project_name):
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
    for name in names:
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
    completed = delete_folder_with_retry(folder_key)
    if completed.returncode == 0:
        print(f"OK: deleted run-scoped folder {folder_key} (removes its registry nodes)")
        return True
    detail = (completed.stdout or completed.stderr).strip()
    print(f"WARN: could not delete folder {folder_key} (exit {completed.returncode}): {detail}")
    return False


def delete_project(project_name: str) -> None:
    completed = run_uip(["ixp", "projects", "delete", project_name, "-y", "--output", "json"])
    if completed.returncode == 0:
        print(f"OK: deleted IXP project '{project_name}'")
    else:
        detail = (completed.stdout or completed.stderr).strip()
        print(
            f"WARN: could not delete '{project_name}' "
            f"(exit {completed.returncode}): {detail}"
        )


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


def cleanup() -> None:
    if not os.path.exists(SNAPSHOT):
        print(f"SKIP: no {SNAPSHOT} — the pre_run seed step did not run.")
        return
    run_folder_key = _read_snapshot()["scope"]

    created_projects = new_project_names()
    deployment_records: list[tuple[str, str]] = []
    if not created_projects:
        print("No IXP project was created this run — only the run folder to remove.")
    else:
        # Read deployments BEFORE deleting: `deployments list` is project-scoped
        # and 404s once the project is gone, so this is the last chance to name
        # both what is attributable and what is being left behind.
        deployments_by_project = {
            project_name: list_deployments(project_name)
            for project_name in created_projects
        }
        flow_text = wired_ixp_references()

        # Exact attribution only: wired into this sandbox's flow, or deployed
        # into the folder seed created. Never "the only new project" — under
        # parallel task dispatch (`make e2e`, run-coder-eval -j 4) the lone new
        # project can be a sibling task's, and guessing deletes it mid-run.
        attributable = [
            project_name
            for project_name, deployments in deployments_by_project.items()
            if project_name in flow_text
            or any(
                deployment["DeploymentName"] and deployment["DeploymentName"] in flow_text
                for deployment in deployments
            )
            or any(
                deployment["FolderKey"] == run_folder_key for deployment in deployments
            )
        ]

        unattributable = [name for name in created_projects if name not in attributable]
        if unattributable:
            print(
                f"NOT DELETED: {unattributable} appeared during this run but are "
                "neither wired into this sandbox's flow nor deployed into this "
                "run's folder — they may belong to a concurrent run or another "
                "user. Reported, not guessed at; delete by hand if they are ours."
            )

        for project_name in attributable:
            delete_project(project_name)

        deployment_records = [
            (deployment["DeploymentName"], deployment["FolderKey"])
            for project_name in attributable
            for deployment in deployments_by_project[project_name]
        ]

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
            "leaked either way; the next seed heals it by name if it survived."
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

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in SUBCOMMANDS:
        print(f"usage: handoff.py {'|'.join(SUBCOMMANDS)}", file=sys.stderr)
        sys.exit(2)
    sys.exit(SUBCOMMANDS[sys.argv[1]]())
