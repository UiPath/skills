"""Unit tests for the Flow→IXP handoff grader. Run with ``pytest`` from any directory.

The grader's verdict depends on live tenant state (`uip ixp projects list`,
`uip ixp deployments list`), so these tests stub `uip` with a fake executable on
PATH. That exercises the diff, attribution and node-matching logic without
creating IXP projects — which matters more than usual here: a real exercise of
the positive path creates a folder deployment, and the only way to remove one
(and its `uipath.ixp.*` registry node) is to delete its Orchestrator folder.
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest

TASK_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TASK_DIR)

from handoff import BUILD_PROJECT_PREFIX, RUN_FOLDER_PREFIX  # noqa: E402
from handoff import RUN_HANDOFF_FILE, SNAPSHOT, project_digest  # noqa: E402
from handoff import DOMAIN_MARKERS  # noqa: E402

# A domain-covering project left behind by a previous run's teardown, which
# could not attribute it (created, never deployed, never wired). Named after
# the real one observed on the CI tenant, and built from the sweep's own first
# marker so rotating the fixture domain re-points these tests automatically.
LEAKED_DOMAIN_PROJECT = f"{DOMAIN_MARKERS[0]}_licences-7607b890-ixp"


def iso_ago(seconds: float) -> str:
    """A UTC ISO-8601 instant `seconds` in the past."""
    return (datetime.now(timezone.utc) - timedelta(seconds=seconds)).isoformat()


PRE_EXISTING = ["dtf-contract-aaaa1111-ixp", "trained-bbbb2222-ixp"]
CREATED_PROJECT = "invoices-cccc3333-ixp"
DEPLOYMENT_NAME = "invoices-cccc3333-dddd4444-ixp"
OTHER_PROJECT = "concurrent-eeee5555-ixp"
OTHER_DEPLOYMENT = "concurrent-eeee5555-ffff6666-ixp"
FOLDER_KEY = "5f31a6b2-fa5a-46a5-aac2-7eef48457811"
# The seed-created run folder (recorded in the snapshot's "scope") — the only
# folder teardown deletes.
RUN_FOLDER_KEY = "8c1d2e3f-0a1b-4c2d-9e3f-aabbccddee00"
CONCURRENT_FOLDER_KEY = "9d2e3f4a-1b2c-4d3e-8f4a-bbccddeeff11"
MODEL_ID = "aae28538-450f-80f9-9f27-5e803b4ea473"

# Stands in for the real CLI, reading canned answers from payload.json beside it.
# Only the verbs the grader calls are handled; anything else exits 2 so an
# unexpected call fails the test rather than passing silently.
FAKE_UIP = '''#!/usr/bin/env python3
"""Stand-in for `uip`, answering only the verbs the grader calls.

Uses print(..., file=sys.stderr) rather than stderr.write with an escape, so this
script carries no backslash escapes that could be mangled when embedded.
"""
import json, os, sys, time

here = os.path.dirname(os.path.abspath(__file__))
payload = json.load(open(os.path.join(here, "payload.json")))
deleted_log = os.path.join(here, "deleted.txt")
deleted_folders_log = os.path.join(here, "deleted_folders.txt")
argv = sys.argv[1:]

# A command matching a `slow_commands` substring stalls, for the timeout test.
if any(slow in " ".join(argv) for slow in payload.get("slow_commands", [])):
    time.sleep(payload.get("slow_seconds", 3))


def deleted_projects():
    if not os.path.exists(deleted_log):
        return []
    with open(deleted_log) as handle:
        return handle.read().split()


def deleted_folders():
    if not os.path.exists(deleted_folders_log):
        return []
    with open(deleted_folders_log) as handle:
        return handle.read().split()


if argv[:3] == ["ixp", "projects", "list"]:
    if payload.get("list_exit"):
        print("boom: tenant unreachable", file=sys.stderr)
        sys.exit(payload["list_exit"])
    names = [name for name in payload["projects"] if name not in deleted_projects()]
    # The real record carries Name/Title/CreatedAt (verified on the CI tenant);
    # CreatedAt is what seed's residue sweep ages projects by. Default old, as
    # a pre-existing project is. project_created_at overrides per name; a None
    # there omits the field, which the sweep must treat as "too young to touch".
    created_at = payload.get("project_created_at", {})
    titles = payload.get("project_titles", {})
    records = []
    for name in names:
        record = {"Name": name, "Title": titles.get(name, name)}
        stamp = created_at.get(name, "2020-01-01T00:00:00+00:00")
        if stamp is not None:
            record["CreatedAt"] = stamp
        records.append(record)
    print(json.dumps({"Data": {
        "Projects": records,
        "Total": payload.get("total_override", len(names)),
    }}))
elif argv[:4] == ["ixp", "deployments", "create", "--help"]:
    # A real subcommand's --help exits 0; an unknown one exits 3.
    if payload.get("no_deployments_create"):
        print("error: unknown command", file=sys.stderr)
        sys.exit(3)
    print("Usage: uip ixp deployments create <project-name> --version --folder-key")
elif argv[:4] == ["maestro", "flow", "registry", "pull"]:
    print(json.dumps({"Data": {"NodesCount": 1}}))
elif argv[:4] == ["maestro", "flow", "registry", "get"]:
    # Reached only from check's served-node probe. Deleting a deployment's
    # folder removes its registry node (an IxP NodeType's trailing 36 chars are
    # the folder key).
    if argv[4][-36:] in deleted_folders():
        print("node type not found", file=sys.stderr)
        sys.exit(1)
    print(json.dumps({"Data": {"Node": {"type": argv[4]}}}))
elif argv[:4] == ["maestro", "flow", "registry", "search"]:
    print(json.dumps({"Data": payload.get("registry_nodes", [])}))
elif argv[:3] == ["ixp", "deployments", "list"]:
    # Mirrors the real 404 once the project is gone, so the read-before-delete
    # ordering in delete_this_runs_projects is actually exercised. vanished_projects models
    # the narrower race: still in `projects list`, deleted by a concurrent run
    # before this call.
    if argv[3] in payload.get("vanished_projects", []):
        print("Project with name %r was not found." % argv[3], file=sys.stderr)
        sys.exit(1)
    # An infra fault, not a 404 — the grader must NOT read this as "gone".
    if argv[3] in payload.get("deployments_list_broken", []):
        print("upstream unavailable (503)", file=sys.stderr)
        sys.exit(1)
    if argv[3] in deleted_projects():
        print("Project with name %r was not found." % argv[3], file=sys.stderr)
        sys.exit(1)
    print(json.dumps({"Data": payload["deployments"].get(argv[3], [])}))
elif argv[:3] == ["or", "folders", "create"]:
    # Seed's run folder: returns the Key teardown will read back as "scope".
    key = payload.get("created_folder_key", "created-" + argv[3])
    print(json.dumps({"Data": {"Key": key, "Name": argv[3]}}))
elif argv[:3] == ["or", "folders", "get"]:
    folder_ids = payload.get("folder_ids", {})
    if argv[3] not in folder_ids or argv[3] in deleted_folders():
        print("folder not found", file=sys.stderr)
        sys.exit(1)
    # folder_names is how a test marks a folder as a concurrent RUN's, which
    # teardown reads to disown a project wired from a sibling's registry node.
    data = {"Key": argv[3], "Id": folder_ids[argv[3]]}
    name = payload.get("folder_names", {}).get(argv[3])
    if name:
        data["Name"] = name
    print(json.dumps({"Data": data}))
elif argv[:3] == ["or", "folders", "delete"]:
    # Mirrors the real CLI: refuses without --yes, since the operation is
    # irreversible and the CLI never prompts.
    if "--yes" not in argv:
        print("Confirmation required: re-run with --yes.", file=sys.stderr)
        sys.exit(1)
    transient = payload.get("folder_delete_failures", {}).get(argv[3], 0)
    if transient > 0:
        attempts_log = os.path.join(here, "delete_attempts_" + argv[3] + ".txt")
        with open(attempts_log, "a") as handle:
            handle.write("x")
        with open(attempts_log) as handle:
            attempts_so_far = len(handle.read())
        if attempts_so_far <= transient:
            print("folder is still provisioning", file=sys.stderr)
            sys.exit(1)
    if argv[3] in payload.get("undeletable_folders", []):
        print("folder delete refused", file=sys.stderr)
        sys.exit(1)
    # Deleting something that does not resolve fails, as the real verb does —
    # teardown must never read a failed delete as a successful one.
    if argv[3] not in payload.get("folder_ids", {}) or argv[3] in deleted_folders():
        print("folder not found", file=sys.stderr)
        sys.exit(1)
    with open(deleted_folders_log, "a") as handle:
        handle.write(argv[3] + os.linesep)
    print(json.dumps({"Data": {"Status": "ok"}}))
elif argv[:3] == ["ixp", "projects", "delete"]:
    if argv[3] in payload.get("undeletable", []):
        print("delete refused", file=sys.stderr)
        sys.exit(1)
    with open(deleted_log, "a") as handle:
        handle.write(argv[3] + os.linesep)
    print(json.dumps({"Data": {"Status": "ok"}}))
else:
    print("fake uip: unhandled %r" % (argv,), file=sys.stderr)
    sys.exit(2)
'''


def install_fake_uip(sandbox: pathlib.Path, **payload: Any) -> dict[str, str]:
    """Install the fake `uip` on a copy of PATH and return the env to run with."""
    payload.setdefault("projects", PRE_EXISTING)
    payload.setdefault("deployments", {})
    # Seed's `folders create` returns RUN_FOLDER_KEY so the snapshot's "scope"
    # is deterministic; folder_ids is what `folders get` resolves against.
    payload.setdefault("created_folder_key", RUN_FOLDER_KEY)
    payload.setdefault(
        "folder_ids",
        {FOLDER_KEY: 50, RUN_FOLDER_KEY: 100010, CONCURRENT_FOLDER_KEY: 100020},
    )

    bin_dir = sandbox.parent / "bin"
    bin_dir.mkdir(exist_ok=True)
    (bin_dir / "payload.json").write_text(json.dumps(payload), encoding="utf-8")
    executable = bin_dir / "uip"
    executable.write_text(FAKE_UIP, encoding="utf-8")
    executable.chmod(0o755)

    env = dict(os.environ)
    env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
    # No real sleeps between simulated folder-delete retries.
    env["HANDOFF_RETRY_SECONDS"] = "0"
    return env


def deployment(
    name: str = DEPLOYMENT_NAME, folder_key: str = RUN_FOLDER_KEY
) -> dict[str, Any]:
    """Defaults to the seed-created run folder — the contract the prompt sets.

    check's gating only counts deployments in that folder, so tests modelling a
    deployment parked elsewhere pass folder_key explicitly.
    """
    return {"DeploymentName": name, "ModelVersion": 0, "FolderKey": folder_key}


def ixp_node_type(deployment_name: str, folder_key: str = FOLDER_KEY) -> str:
    """The real registry shape: uipath.ixp.{deploymentName}.{modelId}-{folderKey}."""
    return f"uipath.ixp.{deployment_name}.{MODEL_ID}-{folder_key}"


def write_flow(sandbox: pathlib.Path, nodes: list[dict[str, Any]]) -> None:
    """A .flow in the double-nested layout, with a Flow-typed project manifest.

    The manifest is required: check_handoff locates the flow via
    _shared/flow_check.find_project_dir, which filters on ProjectType="Flow".
    """
    project_dir = sandbox / "Sol" / "Proj"
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "project.uiproj").write_text(
        json.dumps({"Name": "Proj", "ProjectType": "Flow"}), encoding="utf-8"
    )
    (project_dir / "Proj.flow").write_text(json.dumps({"nodes": nodes}), encoding="utf-8")


def wired_flow(sandbox: pathlib.Path, deployment_name: str = DEPLOYMENT_NAME) -> None:
    write_flow(
        sandbox,
        [
            {
                "id": "extractInvoiceFields",
                "type": ixp_node_type(deployment_name),
                "inputs": {"modelName": deployment_name, "folderKey": FOLDER_KEY},
            }
        ],
    )


def write_snapshot(
    sandbox: pathlib.Path,
    project_names: list[str],
    scope: str = RUN_FOLDER_KEY,
) -> None:
    """Baseline in the same opaque form seed writes (digests + run folder key)."""
    (sandbox / SNAPSHOT).write_text(
        json.dumps(
            {
                "names": sorted(project_digest(name) for name in project_names),
                "scope": scope,
            }
        ),
        encoding="utf-8",
    )


def run_script(
    subcommand: str,
    sandbox: pathlib.Path,
    env: dict[str, str],
    *flags: str,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, os.path.join(TASK_DIR, "handoff.py"), subcommand, *flags],
        cwd=str(sandbox),
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )


@pytest.fixture
def sandbox(tmp_path: pathlib.Path) -> pathlib.Path:
    sandbox_dir = tmp_path / "sandbox"
    sandbox_dir.mkdir()
    return sandbox_dir


def tenant(sandbox: pathlib.Path, **overrides: Any) -> dict[str, str]:
    """Snapshot + fake CLI for a tenant where one new project was deployed.

    Overrides replace the defaults, so a test states only what differs.
    """
    write_snapshot(sandbox, PRE_EXISTING)
    payload: dict[str, Any] = {
        "projects": PRE_EXISTING + [CREATED_PROJECT],
        "deployments": {CREATED_PROJECT: [deployment()]},
    }
    payload.update(overrides)
    return install_fake_uip(sandbox, **payload)


@pytest.fixture
def one_new_deployed_project(sandbox: pathlib.Path) -> dict[str, str]:
    """The happy-path tenant: snapshot taken, one new project, one deployment."""
    return tenant(sandbox)


# ── check_handoff ───────────────────────────────────────────────────────────


def test_passes_when_this_runs_deployment_is_wired(
    sandbox: pathlib.Path, one_new_deployed_project: dict[str, str]
) -> None:
    wired_flow(sandbox)
    completed = run_script("check", sandbox, one_new_deployed_project)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert DEPLOYMENT_NAME in completed.stdout


def test_passes_when_only_inputs_model_name_carries_the_deployment(
    sandbox: pathlib.Path, one_new_deployed_project: dict[str, str]
) -> None:
    """A hand-built node may not embed the name in its type; inputs still count."""
    write_flow(
        sandbox,
        [
            {
                "id": "extract",
                "type": f"uipath.ixp.something-else.{MODEL_ID}-{FOLDER_KEY}",
                "inputs": {"modelName": DEPLOYMENT_NAME},
            }
        ],
    )
    completed = run_script("check", sandbox, one_new_deployed_project)
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_wired_match_survives_an_underscored_deployment_name(
    sandbox: pathlib.Path,
) -> None:
    """The registry sanitizes the deployment name inside the NodeType
    (lowercased, non-alnum runs → '-'). A node carrying no inputs.modelName
    must still match via its sanitized type — otherwise a healthy wired run
    prints PROPAGATION SIGNATURE, the mislabel this grader exists to prevent.
    """
    raw_name = "Falconry_Licences-cccc3333-ixp"
    write_flow(
        sandbox,
        [
            {
                "id": "extract",
                "type": (
                    f"uipath.ixp.falconry-licences-cccc3333-ixp.{MODEL_ID}-{FOLDER_KEY}"
                ),
                "inputs": {},
            }
        ],
    )
    env = tenant(sandbox, deployments={CREATED_PROJECT: [deployment(raw_name)]})

    completed = run_script("check", sandbox, env)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "wires an IxP node" in completed.stdout


def test_deployment_name_outside_an_ixp_node_is_a_degraded_pass_not_wiring(
    sandbox: pathlib.Path, one_new_deployed_project: dict[str, str]
) -> None:
    """Text mentioning the name is not wiring — but mock + deployed + the name
    recorded IS the documented degraded shape (registry never served the node),
    so it passes via that branch, explicitly not the wired one."""
    write_flow(
        sandbox,
        [
            {
                "id": "logIt",
                "type": "core.action.script",
                "inputs": {"code": f"console.log('{DEPLOYMENT_NAME}')"},
            },
            {"id": "placeholder", "type": "core.logic.mock"},
        ],
    )
    completed = run_script("check", sandbox, one_new_deployed_project)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "OK (degraded)" in completed.stdout
    assert "wires an IxP node" not in completed.stdout


def test_fails_when_name_appears_in_text_but_no_mock_was_landed(
    sandbox: pathlib.Path, one_new_deployed_project: dict[str, str]
) -> None:
    """Without the mock placeholder the flow has no extraction step at all —
    a name in a script literal alone is neither wiring nor the degraded shape."""
    write_flow(
        sandbox,
        [
            {
                "id": "logIt",
                "type": "core.action.script",
                "inputs": {"code": f"console.log('{DEPLOYMENT_NAME}')"},
            }
        ],
    )
    completed = run_script("check", sandbox, one_new_deployed_project)
    assert completed.returncode == 1
    assert "no IxP node" in completed.stderr


def test_fails_when_mock_landed_but_deployment_name_recorded_nowhere(
    sandbox: pathlib.Path, one_new_deployed_project: dict[str, str]
) -> None:
    """The breadcrumb requirement is what separates the documented degraded
    fallback from a lazy mock: the agent must provably know what it deployed."""
    write_flow(sandbox, [{"id": "placeholder", "type": "core.logic.mock"}])
    completed = run_script("check", sandbox, one_new_deployed_project)
    assert completed.returncode == 1
    assert "PROPAGATION SIGNATURE" in completed.stderr


def test_degraded_pass_via_a_breadcrumb_in_a_sibling_markdown_file(
    sandbox: pathlib.Path, one_new_deployed_project: dict[str, str]
) -> None:
    """impl.md tells the agent to record the DeploymentName in the plan's Open
    Questions — a markdown file beside the flow counts."""
    write_flow(sandbox, [{"id": "placeholder", "type": "core.logic.mock"}])
    project_dir = next((sandbox).glob("**/*.flow")).parent
    (project_dir / "PLAN.md").write_text(
        f"## Open Questions\n- swap the mock for {DEPLOYMENT_NAME} once the "
        "registry serves it\n",
        encoding="utf-8",
    )
    completed = run_script("check", sandbox, one_new_deployed_project)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "OK (degraded)" in completed.stdout
    assert "PLAN.md" in completed.stdout


def test_foreign_served_node_cannot_reject_the_degraded_fallback(
    sandbox: pathlib.Path,
) -> None:
    """A concurrent task's project can appear in the tenant-wide diff already
    folder-deployed elsewhere, with the registry serving ITS node. Gating
    identifiers are scoped to this run's folder, so the foreign node must not
    read as "the registry serves this run's node" and reject the fallback."""
    write_flow(sandbox, [{"id": "placeholder", "type": "core.logic.mock"}])
    project_dir = next(sandbox.glob("**/*.flow")).parent
    (project_dir / "PLAN.md").write_text(
        f"- swap the mock for {DEPLOYMENT_NAME}\n", encoding="utf-8"
    )
    foreign_node = ixp_node_type(OTHER_DEPLOYMENT, folder_key=CONCURRENT_FOLDER_KEY)
    env = tenant(
        sandbox,
        projects=PRE_EXISTING + [CREATED_PROJECT, OTHER_PROJECT],
        deployments={
            CREATED_PROJECT: [deployment()],
            OTHER_PROJECT: [
                deployment(OTHER_DEPLOYMENT, folder_key=CONCURRENT_FOLDER_KEY)
            ],
        },
        registry_nodes=[{"NodeType": foreign_node, "DisplayName": OTHER_DEPLOYMENT}],
    )

    completed = run_script("check", sandbox, env)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "OK (degraded)" in completed.stdout
    assert "ignored for gating" in completed.stdout


def test_fails_when_no_project_was_created(sandbox: pathlib.Path) -> None:
    """The baseline shape: the agent never handed off, so the tenant is unchanged."""
    write_flow(sandbox, [{"id": "placeholder", "type": "core.logic.mock"}])
    env = tenant(sandbox, projects=PRE_EXISTING, deployments={})

    completed = run_script("check", sandbox, env)
    assert completed.returncode == 1
    assert "no IXP project was created" in completed.stderr


def test_fails_when_project_created_but_never_folder_deployed(
    sandbox: pathlib.Path,
) -> None:
    """A trained version alone is not reachable from a flow — it needs a folder deploy."""
    write_flow(sandbox, [{"id": "placeholder", "type": "core.logic.mock"}])
    env = tenant(sandbox, deployments={CREATED_PROJECT: []})

    completed = run_script("check", sandbox, env)
    assert completed.returncode == 1
    assert "were folder-deployed" in completed.stderr


def test_fails_when_flow_wires_a_different_extractor(
    sandbox: pathlib.Path, one_new_deployed_project: dict[str, str]
) -> None:
    """Guards the leak scenario: reusing residue from an earlier run must not pass."""
    stale = "leftover-9999-8888-ixp"
    wired_flow(sandbox, stale)
    completed = run_script("check", sandbox, one_new_deployed_project)
    assert completed.returncode == 1
    assert "no IxP node" in completed.stderr
    # Diagnostics must name the stale node so the reader can spot the cause.
    assert stale in completed.stderr


def test_fails_when_snapshot_missing(sandbox: pathlib.Path) -> None:
    """Without the pre_run snapshot a pre-existing project could read as 'created'."""
    wired_flow(sandbox)
    env = install_fake_uip(
        sandbox,
        projects=PRE_EXISTING + [CREATED_PROJECT],
        deployments={CREATED_PROJECT: [deployment()]},
    )
    completed = run_script("check", sandbox, env)
    assert completed.returncode != 0
    assert SNAPSHOT in completed.stderr


def test_fails_when_no_flow_project(
    sandbox: pathlib.Path, one_new_deployed_project: dict[str, str]
) -> None:
    completed = run_script("check", sandbox, one_new_deployed_project)
    assert completed.returncode != 0
    assert "FAIL" in completed.stdout + completed.stderr


def test_truncated_project_page_is_an_error_not_a_silent_diff(
    sandbox: pathlib.Path,
) -> None:
    """A short page would make page-fallen-off projects look newly created."""
    env = tenant(sandbox, projects=["a-ixp"], total_override=99)

    completed = run_script("check", sandbox, env)
    assert completed.returncode != 0
    assert "truncated" in completed.stderr


def test_cli_failure_surfaces_the_exit_code_and_stderr(sandbox: pathlib.Path) -> None:
    """run_uip_json must not turn a failed call into an empty result."""
    env = tenant(sandbox, list_exit=3)

    completed = run_script("check", sandbox, env)
    assert completed.returncode != 0
    assert "exited 3" in completed.stderr
    assert "tenant unreachable" in completed.stderr


# ── teardown ────────────────────────────────────────────────────────────────


def test_teardown_deletes_the_wired_project_and_reports_the_leak(
    sandbox: pathlib.Path,
) -> None:
    """A wired project deployed OUTSIDE the run folder: project goes, leak named."""
    wired_flow(sandbox)
    env = tenant(
        sandbox, deployments={CREATED_PROJECT: [deployment(folder_key=FOLDER_KEY)]}
    )
    completed = run_script("teardown", sandbox, env)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert f"deleted IXP project '{CREATED_PROJECT}'" in completed.stdout
    assert "LEAKED" in completed.stdout
    assert DEPLOYMENT_NAME in completed.stdout


def test_teardown_reports_a_lone_undeployed_project_instead_of_guessing(
    sandbox: pathlib.Path,
) -> None:
    """A lone new project is NOT assumed ours: under parallel dispatch
    (`make e2e`, run-coder-eval -j 4) it can be a sibling task's — e.g.
    uipath-ixp full_lifecycle — and guessing would delete it mid-run.
    Undeployed leftovers are reported for a hand-delete, never deleted."""
    env = tenant(sandbox, deployments={CREATED_PROJECT: []})
    completed = run_script("teardown", sandbox, env)
    assert completed.returncode == 0
    assert "deleted IXP project" not in completed.stdout
    assert "NOT DELETED" in completed.stdout
    assert CREATED_PROJECT in completed.stdout


def test_teardown_deletes_an_unwired_project_deployed_into_the_run_folder(
    sandbox: pathlib.Path,
) -> None:
    """The common failure path: project built and deployed, run died before
    wiring it. The run-folder FolderKey attributes it exactly — no guessing."""
    env = tenant(
        sandbox,
        deployments={CREATED_PROJECT: [deployment(folder_key=RUN_FOLDER_KEY)]},
    )
    completed = run_script("teardown", sandbox, env)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert f"deleted IXP project '{CREATED_PROJECT}'" in completed.stdout
    assert f"deleted run-scoped folder {RUN_FOLDER_KEY}" in completed.stdout
    assert "LEAKED" not in completed.stdout


def test_teardown_refuses_to_delete_an_unattributable_concurrent_project(
    sandbox: pathlib.Path,
) -> None:
    """The destructive case: two projects appeared, only one is ours."""
    wired_flow(sandbox)
    env = tenant(
        sandbox,
        projects=PRE_EXISTING + [CREATED_PROJECT, OTHER_PROJECT],
        deployments={
            CREATED_PROJECT: [deployment()],
            # The concurrent project's deployment sits in its own folder — it
            # must stay unattributable.
            OTHER_PROJECT: [deployment(OTHER_DEPLOYMENT, folder_key=CONCURRENT_FOLDER_KEY)],
        },
    )
    completed = run_script("teardown", sandbox, env)
    assert completed.returncode == 0
    assert f"deleted IXP project '{CREATED_PROJECT}'" in completed.stdout
    assert "NOT DELETED" in completed.stdout
    assert OTHER_PROJECT in completed.stdout
    assert f"deleted IXP project '{OTHER_PROJECT}'" not in completed.stdout


def test_teardown_warns_on_a_failed_delete(
    sandbox: pathlib.Path,
) -> None:
    wired_flow(sandbox)
    env = tenant(sandbox, undeletable=[CREATED_PROJECT])
    completed = run_script("teardown", sandbox, env)
    assert completed.returncode == 0
    assert "WARN: could not delete" in completed.stdout
    assert "delete refused" in completed.stdout


def test_teardown_deletes_a_run_scoped_folder_and_its_deployment(
    sandbox: pathlib.Path,
) -> None:
    """The clean-teardown design: deployment in a folder the run created.

    Deleting that folder is what removes the deployment's registry node, so a
    passing run no longer burns its fixture domain (verified live 2026-08-24).
    """
    wired_flow(sandbox)
    env = tenant(
        sandbox,
        deployments={CREATED_PROJECT: [deployment(folder_key=RUN_FOLDER_KEY)]},
    )
    completed = run_script("teardown", sandbox, env)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert f"deleted run-scoped folder {RUN_FOLDER_KEY}" in completed.stdout
    assert "LEAKED" not in completed.stdout


def test_teardown_never_deletes_a_pre_existing_folder(
    sandbox: pathlib.Path,
) -> None:
    """A deployment the agent put in Shared leaks; Shared itself must survive."""
    wired_flow(sandbox)
    env = tenant(
        sandbox, deployments={CREATED_PROJECT: [deployment(folder_key=FOLDER_KEY)]}
    )
    completed = run_script("teardown", sandbox, env)
    assert completed.returncode == 0
    assert f"deleted run-scoped folder {FOLDER_KEY}" not in completed.stdout
    assert "LEAKED" in completed.stdout
    assert FOLDER_KEY in completed.stdout


def test_teardown_disowns_a_project_deployed_into_a_siblings_run_folder(
    sandbox: pathlib.Path,
) -> None:
    """Wired here, but deployed into another run's folder — not ours to delete.

    Both tasks build extractors over the same documents and search the same
    registry, so an agent whose own node has not propagated can wire a
    sibling's. Deleting on "wired" alone would take out a live run's project.
    """
    siblings_folder = "1f2e3d4c-5b6a-4079-8e1f-0a1b2c3d4e5f"
    wired_flow(sandbox, deployment_name=OTHER_DEPLOYMENT)
    env = tenant(
        sandbox,
        projects=PRE_EXISTING + [OTHER_PROJECT],
        deployments={OTHER_PROJECT: [deployment(OTHER_DEPLOYMENT, folder_key=siblings_folder)]},
        folder_ids={RUN_FOLDER_KEY: 100010, siblings_folder: 100030},
        folder_names={siblings_folder: f"{RUN_FOLDER_PREFIX}deadbeef"},
    )

    completed = run_script("teardown", sandbox, env)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "deleted IXP project" not in completed.stdout
    assert "NOT DELETED" in completed.stdout
    assert not (sandbox.parent / "bin" / "deleted.txt").exists()


def test_a_broken_deployments_list_is_not_read_as_a_deleted_project(
    sandbox: pathlib.Path,
) -> None:
    """Only the 404 race is absorbed; an infra fault must not read as "gone".

    Swallowing it would silently skip a real project in teardown's attribution
    and leave its deployment on the tenant. It still must not cost the folder
    delete, so cleanup reports it and carries on — teardown always exits 0.
    """
    write_snapshot(sandbox, PRE_EXISTING)
    env = install_fake_uip(
        sandbox,
        projects=PRE_EXISTING + [CREATED_PROJECT],
        deployments={CREATED_PROJECT: [deployment()]},
        deployments_list_broken=[CREATED_PROJECT],
        folder_ids={RUN_FOLDER_KEY: 100010},
    )

    completed = run_script("teardown", sandbox, env)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "vanished mid-run" not in completed.stdout
    assert "WARN: project cleanup failed" in completed.stdout
    assert f"deleted run-scoped folder {RUN_FOLDER_KEY}" in completed.stdout


def test_an_unresolvable_folder_does_not_authorise_a_delete(
    sandbox: pathlib.Path,
) -> None:
    """Fail safe when `folders get` fails: the project might be a sibling's.

    The same rule cleanup() applies to deletes — a failing lookup is not proof.
    Reading it as "not a sibling's folder" would delete a live run's project on
    nothing more than a transient error.
    """
    unreadable = "3c4d5e6f-7a8b-4c9d-8e0f-1a2b3c4d5e6f"
    wired_flow(sandbox, deployment_name=OTHER_DEPLOYMENT)
    env = tenant(
        sandbox,
        projects=PRE_EXISTING + [OTHER_PROJECT],
        deployments={OTHER_PROJECT: [deployment(OTHER_DEPLOYMENT, folder_key=unreadable)]},
        folder_ids={RUN_FOLDER_KEY: 100010},
    )

    completed = run_script("teardown", sandbox, env)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert f"folder {unreadable} did not resolve" in completed.stdout
    assert "deleted IXP project" not in completed.stdout
    assert f"deleted run-scoped folder {RUN_FOLDER_KEY}" in completed.stdout


def test_teardown_survives_a_project_deleted_by_a_concurrent_run(
    sandbox: pathlib.Path,
) -> None:
    """A sibling's teardown can delete its project mid-cleanup.

    `deployments list` 404s on it, and the project set is a tenant-wide diff so
    it contains siblings. If that raise escaped, cleanup would abort BEFORE
    deleting the run folder — stranding this run's deployment and its registry
    node, which is exactly what burns the fixture domain.
    """
    write_snapshot(sandbox, PRE_EXISTING)
    env = install_fake_uip(
        sandbox,
        projects=PRE_EXISTING + [CREATED_PROJECT, OTHER_PROJECT],
        deployments={CREATED_PROJECT: [deployment()]},
        vanished_projects=[OTHER_PROJECT],
        folder_ids={RUN_FOLDER_KEY: 100010},
    )

    completed = run_script("teardown", sandbox, env)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert f"'{OTHER_PROJECT}' vanished mid-run" in completed.stdout
    assert f"deleted run-scoped folder {RUN_FOLDER_KEY}" in completed.stdout


def test_teardown_leaves_a_new_folder_owned_by_a_concurrent_run(
    sandbox: pathlib.Path,
) -> None:
    """Only the seed-created run folder is deleted — a folder some concurrent
    run created is never a candidate, whatever it carries."""
    wired_flow(sandbox)
    env = tenant(
        sandbox,
        projects=PRE_EXISTING + [CREATED_PROJECT, OTHER_PROJECT],
        deployments={
            CREATED_PROJECT: [deployment(folder_key=RUN_FOLDER_KEY)],
            OTHER_PROJECT: [deployment(OTHER_DEPLOYMENT, folder_key=CONCURRENT_FOLDER_KEY)],
        },
    )
    completed = run_script("teardown", sandbox, env)
    assert completed.returncode == 0
    assert f"deleted run-scoped folder {RUN_FOLDER_KEY}" in completed.stdout
    assert f"deleted run-scoped folder {CONCURRENT_FOLDER_KEY}" not in completed.stdout


def test_teardown_never_reads_an_unresolvable_folder_as_deleted(
    sandbox: pathlib.Path,
) -> None:
    """A folder that will not delete AND will not resolve is reported, never
    assumed gone. GH runs 33162961197 / 33173123153 printed 'already gone' for
    a folder whose registry node still served days later — that silent
    inference burned the falconry fixture domain."""
    wired_flow(sandbox)
    env = tenant(
        sandbox,
        deployments={CREATED_PROJECT: [deployment(folder_key=RUN_FOLDER_KEY)]},
        folder_ids={FOLDER_KEY: 50},
    )
    completed = run_script("teardown", sandbox, env)
    assert completed.returncode == 0
    assert "does not resolve after the failed delete" in completed.stdout
    assert "LEAKED" in completed.stdout


def test_teardown_reports_leak_when_the_folder_delete_fails(
    sandbox: pathlib.Path,
) -> None:
    wired_flow(sandbox)
    env = tenant(
        sandbox,
        deployments={CREATED_PROJECT: [deployment(folder_key=RUN_FOLDER_KEY)]},
        undeletable_folders=[RUN_FOLDER_KEY],
    )
    completed = run_script("teardown", sandbox, env)
    assert completed.returncode == 0
    assert "WARN: could not delete folder" in completed.stdout
    assert "LEAKED" in completed.stdout


def test_teardown_exits_zero_when_the_tenant_call_fails(sandbox: pathlib.Path) -> None:
    """post_run must never turn a graded result into a failure."""
    env = tenant(sandbox, list_exit=3)

    completed = run_script("teardown", sandbox, env)
    assert completed.returncode == 0
    assert "cleanup failed" in completed.stdout


def test_teardown_skips_cleanly_without_a_snapshot(sandbox: pathlib.Path) -> None:
    env = install_fake_uip(sandbox)
    completed = run_script("teardown", sandbox, env)
    assert completed.returncode == 0
    assert "SKIP" in completed.stdout


# ── seed ────────────────────────────────────────────────────────────────────


def test_seed_snapshots_existing_projects_and_records_the_run_folder(
    sandbox: pathlib.Path,
) -> None:
    env = install_fake_uip(sandbox)
    completed = run_script("seed", sandbox, env)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert f"created run folder '{RUN_FOLDER_PREFIX}" in completed.stdout
    expected = {
        "names": sorted(project_digest(name) for name in PRE_EXISTING),
        "scope": RUN_FOLDER_KEY,
    }
    assert json.loads((sandbox / SNAPSHOT).read_text()) == expected


def test_seed_fails_loudly_when_the_tenant_is_unreachable(
    sandbox: pathlib.Path,
) -> None:
    """A silent empty snapshot would make every pre-existing project look new."""
    env = install_fake_uip(sandbox, list_exit=3)
    completed = run_script("seed", sandbox, env)
    assert completed.returncode != 0
    assert not (sandbox / SNAPSHOT).exists()


def test_null_deployment_name_does_not_match_a_stale_node(
    sandbox: pathlib.Path,
) -> None:
    """DeploymentName is nullable; an empty candidate would match any node."""
    stale = "leftover-9999-8888-ixp"
    wired_flow(sandbox, stale)
    env = tenant(
        sandbox,
        deployments={CREATED_PROJECT: [{**deployment(), "DeploymentName": None}]},
    )

    completed = run_script("check", sandbox, env)
    assert completed.returncode == 1
    assert stale in completed.stderr


def test_passes_when_the_node_carries_the_project_name_instead(
    sandbox: pathlib.Path,
) -> None:
    """Older demo deployments put the project name in modelName, not DeploymentName."""
    write_flow(
        sandbox,
        [
            {
                "id": "extract",
                "type": ixp_node_type(CREATED_PROJECT),
                "inputs": {"modelName": CREATED_PROJECT},
            }
        ],
    )
    env = tenant(sandbox)

    completed = run_script("check", sandbox, env)
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_seed_fails_when_the_cli_cannot_folder_deploy(sandbox: pathlib.Path) -> None:
    """Environment drift must not read as a skill regression."""
    env = install_fake_uip(sandbox, no_deployments_create=True)

    completed = run_script("seed", sandbox, env)
    assert completed.returncode != 0
    assert "no `ixp deployments create`" in completed.stderr
    assert not (sandbox / SNAPSHOT).exists()


def test_undeployed_sibling_project_cannot_satisfy_the_gate(
    sandbox: pathlib.Path,
) -> None:
    """Per-project scoping: an undeployed project's name is not a candidate.

    Concurrent tenant activity puts a second project in the diff. If its bare
    name were accepted, it could satisfy the "created + folder-deployed + wired"
    gate without ever having been deployed.
    """
    write_flow(
        sandbox,
        [
            {
                "id": "extract",
                "type": ixp_node_type(OTHER_PROJECT),
                "inputs": {"modelName": OTHER_PROJECT},
            }
        ],
    )
    env = tenant(
        sandbox,
        projects=PRE_EXISTING + [CREATED_PROJECT, OTHER_PROJECT],
        deployments={CREATED_PROJECT: [deployment()], OTHER_PROJECT: []},
    )

    completed = run_script("check", sandbox, env)
    assert completed.returncode == 1
    # The undeployed project prints no "-> DeploymentName=" line, so it never
    # became a candidate.
    assert f"{OTHER_PROJECT} -> DeploymentName=" not in completed.stdout


def test_teardown_reads_deployments_before_deleting(sandbox: pathlib.Path) -> None:
    """Ordering invariant: `deployments list` 404s once the project is deleted.

    The fake mimics that, so a future reordering (delete then list) would lose the
    LEAKED report — which is the only record of the un-removable residue.
    """
    wired_flow(sandbox)
    env = tenant(
        sandbox, deployments={CREATED_PROJECT: [deployment(folder_key=FOLDER_KEY)]}
    )

    completed = run_script("teardown", sandbox, env)
    assert completed.returncode == 0, completed.stdout
    assert "LEAKED" in completed.stdout
    assert DEPLOYMENT_NAME in completed.stdout
    assert "cleanup failed" not in completed.stdout


def test_baseline_file_names_nothing_under_test(sandbox: pathlib.Path) -> None:
    """The snapshot sits beside the agent's documents; it must not leak the answer."""
    env = install_fake_uip(sandbox)
    completed = run_script("seed", sandbox, env)
    assert completed.returncode == 0, completed.stdout + completed.stderr

    assert "ixp" not in SNAPSHOT.lower()
    assert "project" not in SNAPSHOT.lower()
    contents = (sandbox / SNAPSHOT).read_text().lower()
    for leak in ("ixp", "project", "folder", "dtf-contract", "trained-"):
        assert leak not in contents, f"baseline leaks {leak!r}"


def test_passes_only_via_the_wired_one_of_two_deployed_projects(
    sandbox: pathlib.Path,
) -> None:
    """Two new deployed projects, one wired: the gate passes on the wired one."""
    wired_flow(sandbox)
    env = tenant(
        sandbox,
        projects=PRE_EXISTING + [CREATED_PROJECT, OTHER_PROJECT],
        deployments={
            CREATED_PROJECT: [deployment()],
            OTHER_PROJECT: [deployment(OTHER_DEPLOYMENT)],
        },
    )

    completed = run_script("check", sandbox, env)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert DEPLOYMENT_NAME in completed.stdout


def test_explicit_null_model_name_is_not_the_string_none(
    sandbox: pathlib.Path,
) -> None:
    """`"modelName": null` must not stringify to "None" and match something."""
    write_flow(
        sandbox,
        [{"id": "extract", "type": ixp_node_type("None"), "inputs": {"modelName": None}}],
    )
    env = tenant(sandbox)

    completed = run_script("check", sandbox, env)
    assert completed.returncode == 1


def test_a_hung_uip_call_is_named_not_a_traceback(sandbox: pathlib.Path) -> None:
    """A `uip` call outliving the cap must fail naming the command and the cap,
    not as a bare TimeoutExpired."""
    env = install_fake_uip(sandbox, slow_commands=["projects list"], slow_seconds=3)
    env["HANDOFF_UIP_TIMEOUT_SECONDS"] = "1"
    completed = run_script("seed", sandbox, env)
    assert completed.returncode != 0
    assert "exceeded 1s" in completed.stderr
    assert "registry pull" in completed.stderr
    assert "TimeoutExpired" not in completed.stderr.strip().splitlines()[-1]


# ── seed: fixture-domain residue sweep ──────────────────────────────────────


def test_seed_sweeps_a_stale_leaked_domain_project(sandbox: pathlib.Path) -> None:
    """The leak that teardown cannot collect is healed by the next run's seed.

    A project created but never deployed nor wired is unattributable, so
    teardown reports it as NOT DELETED and leaves it. The agent then finds it
    with `ixp projects list` and reuses its trained model instead of creating
    one — the RE-13543 failure this sweep exists to prevent.
    """
    env = install_fake_uip(
        sandbox,
        projects=PRE_EXISTING + [LEAKED_DOMAIN_PROJECT],
        project_created_at={LEAKED_DOMAIN_PROJECT: iso_ago(7200)},
    )

    completed = run_script("seed", sandbox, env)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert f"swept leaked fixture project '{LEAKED_DOMAIN_PROJECT}'" in completed.stdout
    assert LEAKED_DOMAIN_PROJECT in (sandbox.parent / "bin" / "deleted.txt").read_text()


def test_swept_project_is_not_recorded_as_pre_existing(sandbox: pathlib.Path) -> None:
    """A swept name must leave the baseline, or recreating it reads as no-op.

    The agent may legitimately create a project with the same slug; if the
    swept name stayed in the snapshot, new_project_names would not see it and
    check would report "no project was created" — the very failure the sweep
    exists to prevent.
    """
    env = install_fake_uip(
        sandbox,
        projects=PRE_EXISTING + [LEAKED_DOMAIN_PROJECT],
        project_created_at={LEAKED_DOMAIN_PROJECT: iso_ago(7200)},
    )

    completed = run_script("seed", sandbox, env)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    recorded = set(json.loads((sandbox / SNAPSHOT).read_text())["names"])
    assert project_digest(LEAKED_DOMAIN_PROJECT) not in recorded
    assert {project_digest(name) for name in PRE_EXISTING} <= recorded
    assert "Snapshotted %d " % len(PRE_EXISTING) in completed.stdout


def test_seed_sweeps_on_the_title_when_the_slug_is_clean(sandbox: pathlib.Path) -> None:
    """Residue is matched on Title too — the agent names either from the domain."""
    disguised = "extraction-9c1f22ab-ixp"
    env = install_fake_uip(
        sandbox,
        projects=PRE_EXISTING + [disguised],
        project_titles={disguised: f"{DOMAIN_MARKERS[0]} licences"},
        project_created_at={disguised: iso_ago(7200)},
    )

    completed = run_script("seed", sandbox, env)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert f"swept leaked fixture project '{disguised}'" in completed.stdout


def test_seed_never_sweeps_a_project_outside_the_fixture_domain(
    sandbox: pathlib.Path,
) -> None:
    """Parallel safety: the sweep is certain only because the domain is owned.

    A sibling task's project — old, but carrying no domain marker — is not
    this fixture's to delete, however tempting the age.
    """
    sibling = "vendor-invoices-5a097334-ixp"
    env = install_fake_uip(
        sandbox,
        projects=PRE_EXISTING + [sibling],
        project_created_at={sibling: iso_ago(86400)},
    )

    completed = run_script("seed", sandbox, env)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "swept" not in completed.stdout
    assert not (sandbox.parent / "bin" / "deleted.txt").exists()


# ── seed: concurrency properties (RE-13543) ─────────────────────────────────


def test_seed_names_a_per_run_folder_in_the_handoff_file(sandbox: pathlib.Path) -> None:
    """The prompt reads the folder name from seed.json, so seed must write it.

    A fixed literal in the prompt is the other thing two concurrent runs
    cannot share; the file is what lets the prompt stay static while the name
    varies per run.
    """
    env = install_fake_uip(sandbox)

    completed = run_script("seed", sandbox, env)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    handoff = json.loads((sandbox / RUN_HANDOFF_FILE).read_text())
    assert handoff["folder"].startswith(RUN_FOLDER_PREFIX)
    assert f"created run folder '{handoff['folder']}'" in completed.stdout
    # Nothing about projects or extractors — that would leak the answer.
    assert set(handoff) == {"folder"}


def test_only_the_build_task_is_told_the_extractor_name(
    sandbox: pathlib.Path,
) -> None:
    """`--name-extractor` is what separates the two tasks' seed.json.

    e2e_04 needs the name so its extractor is not domain-named. e2e_03 must
    NOT get it: its agent reads this file, and a key called "extractor" hands
    it the prerequisite it is graded on working out for itself.
    """
    plain = run_script("seed", sandbox, install_fake_uip(sandbox))
    assert plain.returncode == 0, plain.stdout + plain.stderr
    assert set(json.loads((sandbox / RUN_HANDOFF_FILE).read_text())) == {"folder"}

    other = sandbox.parent / "sandbox-build"
    other.mkdir()
    named = run_script("seed", other, install_fake_uip(other), "--name-extractor")
    assert named.returncode == 0, named.stdout + named.stderr
    handoff = json.loads((other / RUN_HANDOFF_FILE).read_text())
    assert set(handoff) == {"folder", "extractor"}
    assert handoff["extractor"].startswith(BUILD_PROJECT_PREFIX)


def test_the_extractor_name_carries_no_domain_marker(sandbox: pathlib.Path) -> None:
    """The whole point: e2e_04's extractor must not read as domain coverage.

    A domain-named extractor is what a concurrent e2e_03 would find and
    correctly reuse, and it is also what seed's own sweep hunts for.
    """
    completed = run_script(
        "seed", sandbox, install_fake_uip(sandbox), "--name-extractor"
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    name = json.loads((sandbox / RUN_HANDOFF_FILE).read_text())["extractor"].lower()
    assert not any(marker in name for marker in DOMAIN_MARKERS)


def test_seed_sweeps_a_leaked_build_project(sandbox: pathlib.Path) -> None:
    """Unmarked by design, so the sweep has to collect it by prefix instead.

    Without this it is the one leak nothing reclaims: teardown could not
    attribute it, and the domain markers deliberately do not match it.
    """
    leaked = f"{BUILD_PROJECT_PREFIX}9c1f22ab-0a1b2c3d-ixp"
    env = install_fake_uip(
        sandbox,
        projects=PRE_EXISTING + [leaked],
        project_created_at={leaked: iso_ago(7200)},
    )

    completed = run_script("seed", sandbox, env)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert f"swept leaked fixture project '{leaked}'" in completed.stdout
    assert leaked in (sandbox.parent / "bin" / "deleted.txt").read_text()


def test_a_live_runs_build_project_is_not_swept(sandbox: pathlib.Path) -> None:
    """The age guard covers prefix matches too — a sibling mid-build keeps its
    project."""
    live = f"{BUILD_PROJECT_PREFIX}9c1f22ab-0a1b2c3d-ixp"
    env = install_fake_uip(
        sandbox,
        projects=PRE_EXISTING + [live],
        project_created_at={live: iso_ago(240)},
    )

    completed = run_script("seed", sandbox, env)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "KEEPING fixture project" in completed.stdout
    assert not (sandbox.parent / "bin" / "deleted.txt").exists()


def test_two_seeds_claim_different_run_folders(sandbox: pathlib.Path) -> None:
    """Two concurrent runs must not name the same folder."""
    first = run_script("seed", sandbox, install_fake_uip(sandbox))
    assert first.returncode == 0, first.stdout + first.stderr
    one = json.loads((sandbox / RUN_HANDOFF_FILE).read_text())["folder"]

    other = sandbox.parent / "sandbox-b"
    other.mkdir()
    second = run_script("seed", other, install_fake_uip(other))
    assert second.returncode == 0, second.stdout + second.stderr
    two = json.loads((other / RUN_HANDOFF_FILE).read_text())["folder"]

    assert one != two


def test_seed_proceeds_while_a_published_extractor_covers_the_domain(
    sandbox: pathlib.Path,
) -> None:
    """The RE-13543 fix, stated as a test.

    A resolvable published extractor for the fixture domain used to abort seed.
    Seed no longer probes the registry at all, so a covering node cannot stop
    it (`check` still probes, for its served-node fallback). Whether that is
    right for the task consuming this grader is the task's business, not the
    grader's.
    """
    siblings_node = ixp_node_type(LEAKED_DOMAIN_PROJECT, folder_key=CONCURRENT_FOLDER_KEY)
    env = install_fake_uip(
        sandbox,
        registry_nodes=[{"NodeType": siblings_node, "DisplayName": LEAKED_DOMAIN_PROJECT}],
    )

    completed = run_script("seed", sandbox, env)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert (sandbox / SNAPSHOT).exists()


def test_seed_leaves_a_live_siblings_domain_project_alone(
    sandbox: pathlib.Path,
) -> None:
    """A young domain project belongs to a live sibling: not swept, not fatal.

    Both halves matter. Deleting it would break the sibling mid-run; failing on
    it would recreate the single-flight behaviour this task just shed.
    """
    env = install_fake_uip(
        sandbox,
        projects=PRE_EXISTING + [LEAKED_DOMAIN_PROJECT],
        project_created_at={LEAKED_DOMAIN_PROJECT: iso_ago(240)},
    )

    completed = run_script("seed", sandbox, env)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "KEEPING fixture project" in completed.stdout
    assert not (sandbox.parent / "bin" / "deleted.txt").exists()
    # Still recorded as pre-existing, so the sibling's project can never be
    # mistaken for this run's creation.
    recorded = set(json.loads((sandbox / SNAPSHOT).read_text())["names"])
    assert project_digest(LEAKED_DOMAIN_PROJECT) in recorded


def test_an_undateable_domain_project_is_never_swept(sandbox: pathlib.Path) -> None:
    """No CreatedAt must never authorise a delete.

    The sweep's safe default: a project it cannot age might belong to a live
    concurrent run, so it is reported and left. Untested, this guard is one
    typo away from deleting a sibling's project mid-run.
    """
    env = install_fake_uip(
        sandbox,
        projects=PRE_EXISTING + [LEAKED_DOMAIN_PROJECT],
        project_created_at={LEAKED_DOMAIN_PROJECT: None},
    )

    completed = run_script("seed", sandbox, env)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "undateable" in completed.stdout
    assert not (sandbox.parent / "bin" / "deleted.txt").exists()


def test_an_undeletable_stale_project_does_not_fail_the_run(
    sandbox: pathlib.Path,
) -> None:
    """A refused sweep is reported, never fatal — it blocks nothing now."""
    env = install_fake_uip(
        sandbox,
        projects=PRE_EXISTING + [LEAKED_DOMAIN_PROJECT],
        project_created_at={LEAKED_DOMAIN_PROJECT: iso_ago(7200)},
        undeletable=[LEAKED_DOMAIN_PROJECT],
    )

    completed = run_script("seed", sandbox, env)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert f"WARN: could not delete '{LEAKED_DOMAIN_PROJECT}'" in completed.stdout
    assert "swept leaked fixture project" not in completed.stdout


def test_teardown_retries_a_transiently_failing_folder_delete(
    sandbox: pathlib.Path,
) -> None:
    """Folder deletes fail transiently; teardown must not leak on the first miss.

    Provisioning race on a just-created folder (GH run 32967816894) and an
    "Error resolving folder" on a half-hour-old one (GH run 32968685992) — the
    CLI's RetryWillNotFix hint was wrong both times. Deleting the run folder is
    what removes this run's deployment and its registry node, so giving up on
    attempt one is what leaves a published extractor behind.
    """
    write_snapshot(sandbox, PRE_EXISTING)
    env = install_fake_uip(
        sandbox,
        projects=PRE_EXISTING + [CREATED_PROJECT],
        deployments={CREATED_PROJECT: [deployment()]},
        folder_ids={RUN_FOLDER_KEY: 100010},
        folder_delete_failures={RUN_FOLDER_KEY: 2},
    )

    completed = run_script("teardown", sandbox, env)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "folder delete attempt 1" in completed.stdout
    assert f"deleted run-scoped folder {RUN_FOLDER_KEY}" in completed.stdout
    assert "LEAKED" not in completed.stdout
