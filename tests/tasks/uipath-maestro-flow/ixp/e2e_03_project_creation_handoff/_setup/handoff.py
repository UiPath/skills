#!/usr/bin/env python3
"""Tenant lifecycle for the Flow→IXP handoff e2e tasks: `seed` / `teardown`.

Two subcommands, matching two of the task YAML's three hook points:

  python3 handoff.py seed      # pre_run — precondition guards + tenant snapshot
  python3 handoff.py teardown  # post_run — delete this run's artifacts; ALWAYS exit 0

The primary gate (`check`) lives in `_shared/check_ixp_handoff.py`, reached
only via $REFERENCE_DIR — never staged into the agent's sandbox. This file IS
staged (sandbox.template_sources, mount_point: _setup) for both
e2e_03_project_creation_handoff.yaml and e2e_04_build_mechanics.yaml, so it
must carry no scoring/answer-key logic: only what pre_run/post_run need to
set up and tear down tenant state. Shared tenant plumbing (uip wrapping,
snapshot bookkeeping, node-identifier parsing) lives in `handoff_tenant.py`,
staged alongside this file for the same reason.

**One grader, two tasks, split at the handoff (RE-13543).**

  e2e_03_project_creation_handoff.yaml — the DECISION. Its prompt never says
  IXP, project or publish, and `stop_early` on its uipath-ixp criterion cuts
  the run the moment the sibling skill is invoked, before `projects create`.
  Uses `seed` and `teardown`; never `check`, because nothing is built.

  e2e_04_build_mechanics.yaml — the BUILD. Its prompt says the extractor is
  missing, so the agent creates, deploys and wires it. Uses `seed
  --name-extractor`, `teardown`, and reaches `check` via
  `$REFERENCE_DIR/_shared/check_ixp_handoff.py`.

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
"""

from __future__ import annotations

import glob
import json
import os
import sys
import traceback
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from handoff_tenant import (  # noqa: E402  (path set above)
    SNAPSHOT,
    delete_folder_with_retry,
    folder_get,
    iso_age_seconds,
    ixp_node_identifiers,
    list_deployments_if_present,
    matches_fixture_domain,
    new_project_names,
    read_snapshot,
    run_uip,
    run_uip_json,
    write_snapshot,
)

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

# Substrings that mark a project as belonging to the fixture domain — see
# handoff_tenant.matches_fixture_domain. Re-exported here (rather than only
# imported) because rotating the fixture domain means editing this constant
# and the one in handoff_tenant.py together — see the rotation recipe below.
#
# Keep them narrow: a match means an unattended `projects delete` on a shared
# tenant, so include only words an agent would build a project name from (the
# document type), never form field labels, and prefer the longer form
# ("falconry", not "falcon").
#
# Rotating the domain: pick one absent from and semantically distant to the
# tenant's published nodes, re-render the fixtures (../_fixtures/falconry/
# README.md has the spec), rename that directory and the two template_dir
# paths pointing at it, update these markers (here AND in handoff_tenant.py),
# and update both prompts — each names the document type.
DOMAIN_MARKERS = ("falconry", "bird-of-prey", "bird_of_prey")

# A domain-covering project younger than this may belong to a LIVE concurrent
# instance of this task, so the sweep leaves it alone. The floor is the longest
# task budget using this grader (e2e_04's task_timeout, 3000s); two hours keeps
# a real margin over it even with clock skew between the tenant's CreatedAt and
# the runner's own clock. Anything older is a failed
# teardown's residue: no legitimate tenant asset carries a DOMAIN_MARKER,
# because the fixture owns its domain outright.
LEAKED_PROJECT_AGE_SECONDS = 7200.0


def sweep_domain_projects(projects: list[dict]) -> list[str]:
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
    from handoff_tenant import list_projects  # local: only seed needs it

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


# ── teardown ──────────────────────────────────────────────────────────────────

def delete_folder(folder_key: str) -> bool:
    completed = delete_folder_with_retry(folder_key)
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

    Deliberately tolerant and glob-based: with no readable flow, attribution
    proceeds on the run-folder FolderKey alone.
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


def belongs_to_another_run(deployments: list[dict], run_folder_key: str) -> bool:
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
    deployments: list[dict],
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
    run_folder_key = read_snapshot()["scope"]

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
    # them (and their registry nodes). The run folder seed created is the ONLY
    # folder this script deletes; anything the agent parked elsewhere is
    # reported below.
    # Judge deletion by the delete's OWN result, never by a lookup — a failing
    # `folders get` is not proof the folder is gone, and treating it as proof
    # is what burned the fixture domain before. A spurious LEAKED line is
    # cheap; a silent skip costs the domain.
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
    except BaseException:  # noqa: BLE001 — post_run must exit 0 (see module docstring)
        print("WARN: cleanup failed; projects created by this run may remain:")
        traceback.print_exc(file=sys.stdout)
    return 0


# ── dispatch ──────────────────────────────────────────────────────────────────

SUBCOMMANDS = {"seed": seed_main, "teardown": teardown_main}
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
            f"(seed also takes {NAME_EXTRACTOR_FLAG}; `check` moved to "
            "_shared/check_ixp_handoff.py, reached via $REFERENCE_DIR)",
            file=sys.stderr,
        )
        sys.exit(2)
    if arguments[0] == "seed":
        sys.exit(seed_main(name_extractor=bool(extra)))
    sys.exit(SUBCOMMANDS[arguments[0]]())
