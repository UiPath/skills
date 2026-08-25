"""Unit tests for the Flow→IXP handoff grader. Run with ``pytest`` from any directory.

The grader's verdict depends on live tenant state (`uip ixp projects list`,
`uip ixp deployments list`), so these tests stub `uip` with a fake executable on
PATH. That exercises the diff, attribution and node-matching logic without
creating IXP projects — which matters more than usual here: folder deployments
cannot be deleted, so every real exercise of the positive path leaves a permanent
`uipath.ixp.*` node in the tenant's registry.
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
from typing import Any

import pytest

TASK_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TASK_DIR)

from handoff import SNAPSHOT, project_digest  # noqa: E402
from handoff import DOMAIN_MARKERS  # noqa: E402

# Built from the guard's own first marker, so rotating the fixture domain
# (documents/generate.py) re-points these tests automatically.
COVERED_NAME = f"{DOMAIN_MARKERS[0]}-inspection-abc123-ixp"
STALE_RESIDUE_NAME = f"{DOMAIN_MARKERS[0]}-inspection-e0b615cf-ixp"

PRE_EXISTING = ["dtf-contract-aaaa1111-ixp", "trained-bbbb2222-ixp"]
CREATED_PROJECT = "invoices-cccc3333-ixp"
DEPLOYMENT_NAME = "invoices-cccc3333-dddd4444-ixp"
OTHER_PROJECT = "concurrent-eeee5555-ixp"
OTHER_DEPLOYMENT = "concurrent-eeee5555-ffff6666-ixp"
FOLDER_KEY = "5f31a6b2-fa5a-46a5-aac2-7eef48457811"
# A folder created DURING the run (absent from the seed snapshot) — the only
# kind teardown is allowed to delete.
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
import json, os, sys

here = os.path.dirname(os.path.abspath(__file__))
payload = json.load(open(os.path.join(here, "payload.json")))
deleted_log = os.path.join(here, "deleted.txt")
deleted_folders_log = os.path.join(here, "deleted_folders.txt")
argv = sys.argv[1:]


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
    print(json.dumps({"Data": {
        "Projects": [{"Name": name} for name in names],
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
    # seed.py probes each domain-matching node: a node listed in
    # unresolvable_nodes stands for this task's own deployment residue, whose
    # project has been deleted. Exit 1 is what the real CLI does for a node it
    # cannot resolve.
    if argv[4] in payload.get("unresolvable_nodes", []):
        print("node type not found", file=sys.stderr)
        sys.exit(1)
    print(json.dumps({"Data": {"Node": {"type": argv[4]}}}))
elif argv[:4] == ["maestro", "flow", "registry", "search"]:
    print(json.dumps({"Data": payload.get("registry_nodes", [])}))
elif argv[:3] == ["ixp", "deployments", "list"]:
    # Mirrors the real 404 once the project is gone, so the read-before-delete
    # ordering in teardown.py is actually exercised.
    if argv[3] in deleted_projects():
        print("Project with name %r was not found." % argv[3], file=sys.stderr)
        sys.exit(1)
    print(json.dumps({"Data": payload["deployments"].get(argv[3], [])}))
elif argv[:3] == ["or", "folders", "create"]:
    # Seed's sentinel: returns a fresh Key and the next Id in the tenant's
    # monotonic sequence, which becomes the snapshot watermark.
    print(json.dumps({"Data": {
        "Key": "sentinel-" + argv[3],
        "Id": payload.get("sentinel_id", 100000),
        "Name": argv[3],
    }}))
elif argv[:3] == ["or", "folders", "get"]:
    folder_ids = payload.get("folder_ids", {})
    if argv[3] not in folder_ids or argv[3] in deleted_folders():
        print("folder not found", file=sys.stderr)
        sys.exit(1)
    print(json.dumps({"Data": {"Key": argv[3], "Id": folder_ids[argv[3]]}}))
elif argv[:3] == ["or", "folders", "delete"]:
    # Mirrors the real CLI: refuses without --yes, since the operation is
    # irreversible and the CLI never prompts.
    if "--yes" not in argv:
        print("Confirmation required: re-run with --yes.", file=sys.stderr)
        sys.exit(1)
    if argv[3] in payload.get("undeletable_folders", []):
        print("folder delete refused", file=sys.stderr)
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
    # Ids ordered around the sentinel watermark (100000): FOLDER_KEY predates
    # seed (protected), RUN_FOLDER_KEY and CONCURRENT_FOLDER_KEY come after.
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
    return env


def deployment(
    name: str = DEPLOYMENT_NAME, folder_key: str = FOLDER_KEY
) -> dict[str, Any]:
    return {"DeploymentName": name, "ModelVersion": 0, "FolderKey": folder_key}


def ixp_node_type(deployment_name: str) -> str:
    """The real registry shape: uipath.ixp.{deploymentName}.{modelId}-{folderKey}."""
    return f"uipath.ixp.{deployment_name}.{MODEL_ID}-{FOLDER_KEY}"


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
    watermark: int = 100000,
) -> None:
    """Baseline in the same opaque form seed.py writes (digests + watermark)."""
    (sandbox / SNAPSHOT).write_text(
        json.dumps(
            {
                "names": sorted(project_digest(name) for name in project_names),
                "mark": watermark,
            }
        ),
        encoding="utf-8",
    )


def run_script(
    subcommand: str, sandbox: pathlib.Path, env: dict[str, str]
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, os.path.join(TASK_DIR, "handoff.py"), subcommand],
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
    sandbox: pathlib.Path, one_new_deployed_project: dict[str, str]
) -> None:
    wired_flow(sandbox)
    completed = run_script("teardown", sandbox, one_new_deployed_project)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert f"deleted IXP project '{CREATED_PROJECT}'" in completed.stdout
    assert "LEAKED" in completed.stdout
    assert DEPLOYMENT_NAME in completed.stdout


def test_teardown_deletes_a_lone_new_project_even_when_nothing_was_wired(
    sandbox: pathlib.Path,
) -> None:
    """The common failure path: project built, run died before wiring it."""
    env = tenant(sandbox, deployments={CREATED_PROJECT: []})
    completed = run_script("teardown", sandbox, env)
    assert completed.returncode == 0
    assert f"deleted IXP project '{CREATED_PROJECT}'" in completed.stdout


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
            OTHER_PROJECT: [deployment(OTHER_DEPLOYMENT)],
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
    sandbox: pathlib.Path, one_new_deployed_project: dict[str, str]
) -> None:
    """A deployment the agent put in Shared leaks; Shared itself must survive."""
    wired_flow(sandbox)
    completed = run_script("teardown", sandbox, one_new_deployed_project)
    assert completed.returncode == 0
    assert "deleted run-scoped folder" not in completed.stdout
    assert "LEAKED" in completed.stdout
    assert FOLDER_KEY in completed.stdout


def test_teardown_leaves_a_new_folder_owned_by_a_concurrent_run(
    sandbox: pathlib.Path,
) -> None:
    """New-since-seed is necessary but not sufficient: the folder must also
    carry a deployment attributed to THIS run."""
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
    assert CONCURRENT_FOLDER_KEY not in completed.stdout.replace(
        f"deleted run-scoped folder {RUN_FOLDER_KEY}", ""
    ) or f"deleted run-scoped folder {CONCURRENT_FOLDER_KEY}" not in completed.stdout


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


def test_seed_snapshots_existing_projects_and_folders(sandbox: pathlib.Path) -> None:
    env = install_fake_uip(sandbox)
    completed = run_script("seed", sandbox, env)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    expected = {
        "names": sorted(project_digest(name) for name in PRE_EXISTING),
        "mark": 100000,
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
    env = tenant(sandbox)

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


def test_seed_fails_when_the_fixture_domain_is_already_covered(
    sandbox: pathlib.Path,
) -> None:
    """A resolvable matching extractor makes reuse correct, so the test can't measure.

    Resolvable is the operative word — see the unresolvable-residue case below.
    """
    env = install_fake_uip(
        sandbox,
        registry_nodes=[
            {
                "NodeType": f"uipath.ixp.{COVERED_NAME}.g-f",
                "DisplayName": COVERED_NAME,
            }
        ],
    )

    completed = run_script("seed", sandbox, env)
    assert completed.returncode != 0
    assert "already covered" in completed.stderr
    assert not (sandbox / SNAPSHOT).exists()


def test_seed_ignores_a_domain_match_that_no_longer_resolves(
    sandbox: pathlib.Path,
) -> None:
    """This task's own residue matches the markers but is not a usable extractor.

    teardown.py deletes the project and cannot delete the folder deployment, so
    the node keeps appearing in `registry search` forever. Blocking on it would
    make the task single-shot per tenant — GH runs 32704589689 / 32704597551 /
    32704606313 all died this way. An unresolvable match must be reported and
    stepped over, and the snapshot must still be written.
    """
    stale = f"uipath.ixp.{STALE_RESIDUE_NAME}.g-f"
    env = install_fake_uip(
        sandbox,
        registry_nodes=[{"NodeType": stale, "DisplayName": STALE_RESIDUE_NAME}],
        unresolvable_nodes=[stale],
    )

    completed = run_script("seed", sandbox, env)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "IGNORING unresolvable match" in completed.stdout
    assert (sandbox / SNAPSHOT).exists()


def test_seed_blocks_when_one_of_several_matches_still_resolves(
    sandbox: pathlib.Path,
) -> None:
    """Residue must not mask a live extractor that genuinely covers the domain."""
    stale = f"uipath.ixp.{STALE_RESIDUE_NAME}.g-f"
    live = f"uipath.ixp.{DOMAIN_MARKERS[1]}-abc123-ixp.g-f"
    env = install_fake_uip(
        sandbox,
        registry_nodes=[
            {"NodeType": stale, "DisplayName": STALE_RESIDUE_NAME},
            {"NodeType": live, "DisplayName": f"{DOMAIN_MARKERS[1]}-abc123-ixp"},
        ],
        unresolvable_nodes=[stale],
    )

    completed = run_script("seed", sandbox, env)
    assert completed.returncode != 0
    assert live in completed.stderr
    assert stale not in completed.stderr


def test_seed_accepts_an_uncovered_fixture_domain(sandbox: pathlib.Path) -> None:
    env = install_fake_uip(
        sandbox,
        registry_nodes=[
            {
                "NodeType": "uipath.ixp.idp-benchmark-invoices-c735405a-ixp.g-f",
                "DisplayName": "idp-benchmark---invoices-c735405a-ixp",
            }
        ],
    )

    completed = run_script("seed", sandbox, env)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "do not cover" in completed.stdout or "cover the fixture domain" in completed.stdout
