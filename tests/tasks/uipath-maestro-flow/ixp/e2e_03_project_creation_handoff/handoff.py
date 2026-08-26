#!/usr/bin/env python3
"""Tenant lifecycle for the Flow→IXP handoff e2e: `seed` / `check` / `teardown`.

One script, three subcommands, matching the task YAML's three hook points:

  python3 handoff.py seed      # pre_run — precondition guards + tenant snapshot
  python3 handoff.py check     # success criterion — the primary gate (exit 0/1)
  python3 handoff.py teardown  # post_run — delete this run's artifacts; ALWAYS exit 0

**seed** fails loudly on any unmet precondition, naming the real cause before
the agent spends its budget: the `deployments create` verb must exist (rides
the CLI `dev` dist-tag), no published extractor may cover the fixture domain
(a resolvable match makes reuse the correct agent action, so the redirect
becomes unmeasurable — rotate the fixture domain per documents/README.md), and the
runner must be able to create AND delete folders (teardown depends on it).
It then snapshots the tenant: project-name digests plus a folder-Id watermark
from a created-and-deleted sentinel (folder Ids are a monotonic sequence; a
tenant can hold thousands of folders, so inventory diffing is not an option).

**Why a snapshot-and-diff instead of asking the agent to record what it made:**
the prompt deliberately never mentions IXP, projects, or deployments —
recognising that a design-time project must be built first is the behaviour
under test, and a "record what you created" instruction would leak the answer.
The snapshot file is neutrally named and stores SHA-256 digests so an agent
`ls`-ing the sandbox learns nothing.

**check** passes on either of two shapes, because flow-registry indexing
latency is org-scoped weather (~25s when healthy; hours observed on the CI
tenant, with the Message Bus publish measured clean at ~400ms):

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
wired into this sandbox's flow or be the only new project on the tenant; a
folder must be created-after-seed (Id above the watermark) AND carry this
run's deployment. Deleting the folder is what removes the deployment and its
registry node — deployments have no delete verb of their own — which is what
lets a passing run restore its own preconditions instead of permanently
burning the fixture domain. Always exits 0: post_run runs after grading, so a
cleanup problem must never turn a graded result into a failure (every failure
is still printed).

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
import subprocess
import sys
import time
import traceback
import uuid
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
            "raise PROJECT_LIST_LIMIT"
        )
    return {project["Name"] for project in projects}


def project_digest(project_name: str) -> str:
    return hashlib.sha256(project_name.encode("utf-8")).hexdigest()


def folder_id(folder_key: str) -> int | None:
    """The folder's integer Id, or None if the folder no longer exists.

    Folder Ids are a monotonic sequence (deletion never reuses one), so
    comparing Ids orders folder creation — neither `folders create` nor
    `folders get` exposes a timestamp, and a tenant can hold thousands of
    folders, ruling out inventory snapshots.
    """
    completed = run_uip(["or", "folders", "get", folder_key, "--output", "json"])
    if completed.returncode != 0:
        return None
    return int(json.loads(completed.stdout)["Data"]["Id"])


def write_snapshot(project_names: set[str], folder_id_watermark: int) -> None:
    """Record the baseline as opaque digests — see the module docstring."""
    with open(SNAPSHOT, "w", encoding="utf-8") as handle:
        # Neutral key names — see the module docstring on opacity. "mark" is
        # the sentinel folder's Id: larger Id = created after seed.
        json.dump(
            {
                "names": sorted(project_digest(name) for name in project_names),
                "mark": folder_id_watermark,
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
    return {"projects": set(raw["names"]), "watermark": int(raw["mark"])}


def new_project_names() -> list[str]:
    """Project names that appeared since seed ran (tenant-wide — see module docstring)."""
    before = _read_snapshot()["projects"]
    return sorted(name for name in list_project_names() if project_digest(name) not in before)


def folder_created_after_seed(folder_key: str) -> bool | None:
    """True if the folder was created after seed ran, None if it is gone.

    Necessary but not sufficient for deletion — teardown additionally requires
    the folder to carry a deployment attributed to this run.
    """
    current_id = folder_id(folder_key)
    if current_id is None:
        return None
    return current_id > _read_snapshot()["watermark"]


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


def require_domain_uncovered() -> None:
    """Fail if a resolvable published extractor already covers the fixture domain.

    If one does, reusing it is the correct agent action and the handoff never
    fires — the run would go red for a reason unrelated to the behaviour under
    test. Each name match is probed with `registry get`: resolvable = a live
    extractor (block); unresolvable = dangling residue nobody can use (report,
    step over). Residue can stay resolvable long after its project is deleted,
    so a block here usually means a prior teardown failed to delete its folder
    — rotate the fixture domain per documents/README.md.
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

    if covered:
        raise RuntimeError(
            "the fixture domain is already covered by resolvable published "
            f"extractor(s) {covered} — the agent can correctly reuse one, so this "
            "task cannot measure the handoff. Change the fixture domain "
            "(documents/README.md) or point the run at a tenant without it."
        )
    print(
        f"OK: none of the {len(nodes)} published IxP node(s) cover the fixture domain "
        f"({len(matched)} name match(es), none resolvable)"
    )


def folder_id_watermark() -> int:
    """Create and delete a sentinel folder; return its Id as the watermark.

    Any folder with a larger Id was created after this moment (see folder_id).
    Doubles as a permissions pre-flight: a runner that cannot create and delete
    folders would leak a deployment at teardown — fail now, naming the cause,
    before the agent spends its budget.
    """
    sentinel_name = f"baseline-marker-{uuid.uuid4().hex[:8]}"
    created = run_uip_json(["or", "folders", "create", sentinel_name, "--output", "json"])
    sentinel_key = created["Data"]["Key"]
    sentinel_id = int(created["Data"]["Id"])
    # Deleting a folder milliseconds after creating it can race provisioning
    # (GH run 32967816894: delete exit 1 straight after a successful create,
    # on a pair that had succeeded six runs straight) — retry briefly before
    # concluding the runner genuinely lacks the permission.
    for attempt in range(4):
        deleted = run_uip(["or", "folders", "delete", sentinel_key, "--yes", "--output", "json"])
        if deleted.returncode == 0:
            break
        if attempt < 3:
            print(
                f"sentinel delete attempt {attempt + 1} failed "
                f"(exit {deleted.returncode}); retrying in 5s"
            )
            time.sleep(5)
    if deleted.returncode != 0:
        detail = " ".join((deleted.stdout or deleted.stderr).split())
        raise RuntimeError(
            f"could not delete sentinel folder {sentinel_key} (exit {deleted.returncode}) — "
            "the runner lacks folder-delete permission, so teardown cannot remove the "
            "run-scoped folder and every run would leak a deployment. Fix the runner role "
            f"before running this task. Detail: {detail}"
        )
    print(f"OK: folder create/delete pre-flight passed (watermark Id {sentinel_id})")
    return sentinel_id


def seed_main() -> int:
    require_deployments_create()
    require_domain_uncovered()
    watermark = folder_id_watermark()
    project_names = list_project_names()
    write_snapshot(project_names, watermark)
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

    Returns an empty list when nothing was created or nothing was deployed, after
    printing which of the two it was.
    """
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
        deployments = list_deployments(project_name)
        for deployment in deployments:
            deployment_name = deployment["DeploymentName"]
            print(
                f"  {project_name} -> DeploymentName={deployment_name} "
                f"version={deployment['ModelVersion']} folder={deployment['FolderKey']}"
            )
            if deployment_name:
                names.append(deployment_name)
                deployment_names.append(deployment_name)
        # Per-project, not run-wide: an undeployed sibling project (concurrent
        # tenant activity) must not contribute a candidate name, or it could
        # satisfy the gate without ever having been folder-deployed.
        if deployments and project_name:
            names.append(project_name)

    if not names:
        print(
            f"FAIL: none of the project(s) {created_projects} created this run were "
            "folder-deployed. "
            "`uip ixp deployments create --folder-key <guid>` is what makes a trained "
            "model appear in the Maestro flow registry; without it no uipath.ixp.* node "
            "can exist for this project.",
            file=sys.stderr,
        )
        return [], []
    return names, deployment_names


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
            (name for name in names if any(name in found for found in identifiers)), None
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
                "node can take hours to surface (measured 2026-08-24; ~22s when healthy), so "
                "the agent could never have discovered it. This is tenant weather, not a "
                "skill regression — see the task description before filing anything.",
                file=sys.stderr,
            )
    return 1

# ── teardown ──────────────────────────────────────────────────────────────────

def delete_folder(folder_key: str) -> bool:
    completed = run_uip(["or", "folders", "delete", folder_key, "--yes", "--output", "json"])
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
    when grading and wrong here — cleanup falls back to the
    only-one-new-project rule when there is no readable flow.
    """
    references: list[str] = []
    for flow_path in glob.glob("**/*.flow", recursive=True):
        with open(flow_path, encoding="utf-8") as handle:
            references.extend(ixp_node_identifiers(json.load(handle)))
    return " ".join(references)


def cleanup() -> None:
    if not os.path.exists(SNAPSHOT):
        print(f"SKIP: no {SNAPSHOT} — the pre_run seed step did not run.")
        return

    created_projects = new_project_names()
    if not created_projects:
        print("SKIP: no IXP project was created this run — nothing to clean up.")
        return

    # Read deployments BEFORE deleting: `deployments list` is project-scoped and
    # 404s once the project is gone, so this is the last chance to name both what
    # is attributable and what is being left behind.
    deployments_by_project = {
        project_name: list_deployments(project_name) for project_name in created_projects
    }
    flow_text = wired_ixp_references()

    attributable = [
        project_name
        for project_name, deployments in deployments_by_project.items()
        if project_name in flow_text
        or any(
            deployment["DeploymentName"] and deployment["DeploymentName"] in flow_text
            for deployment in deployments
        )
    ]
    if not attributable and len(created_projects) == 1:
        attributable = list(created_projects)
        print(
            f"Attributing '{created_projects[0]}' to this run: it is the only project "
            "that appeared, so there is nothing to confuse it with."
        )

    unattributable = [name for name in created_projects if name not in attributable]
    if unattributable:
        print(
            f"NOT DELETED: {unattributable} appeared during this run but are not wired "
            "into this sandbox's flow, and more than one project appeared — they may "
            "belong to a concurrent run or another user. Delete by hand if they are ours."
        )

    for project_name in attributable:
        delete_project(project_name)

    # Deployments cannot be deleted directly, but deleting their folder removes
    # them (and their registry nodes) — see the module docstring. Only folders
    # that are BOTH created-after-seed AND carrying this run's deployments
    # qualify; folder_created_after_seed compares the folder's Id against the
    # sentinel watermark seed recorded.
    deployment_records = [
        (deployment["DeploymentName"], deployment["FolderKey"])
        for project_name in attributable
        for deployment in deployments_by_project[project_name]
    ]
    deleted_folders: set[str] = set()
    for folder_key in sorted({folder_key for _, folder_key in deployment_records}):
        created_after_seed = folder_created_after_seed(folder_key)
        if created_after_seed is None:
            print(f"NOTE: folder {folder_key} is already gone — nothing to delete.")
            deleted_folders.add(folder_key)
        elif created_after_seed and delete_folder(folder_key):
            deleted_folders.add(folder_key)

    stranded = [
        (deployment_name, folder_key)
        for deployment_name, folder_key in deployment_records
        if folder_key not in deleted_folders
    ]
    if stranded:
        print(
            f"LEAKED: {len(stranded)} deployment(s) remain — each sits in a "
            "pre-existing folder (never deleted by this script) or in a folder "
            "whose deletion failed above:"
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
