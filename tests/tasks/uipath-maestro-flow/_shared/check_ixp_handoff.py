#!/usr/bin/env python3
"""Primary grading gate for the Flow→IXP handoff e2e pair (RE-13543).

Only e2e_04_build_mechanics.yaml invokes this (e2e_03_project_creation_handoff
never builds anything, so it has no `check`). Never staged into the agent's
sandbox — reached only via `$REFERENCE_DIR/_shared/check_ixp_handoff.py` — so
this file is where the answer-key logic (what counts as "wired", the degraded
mock-fallback acceptance shape, MOCK_NODE_TYPE, the breadcrumb scan) belongs.
Do not move any of it into `../ixp/e2e_03_project_creation_handoff/_setup/`,
which IS staged into the agent's sandbox for both tasks in the pair.

Imports the tenant plumbing (`uip` wrapping, snapshot bookkeeping, .flow node
parsing) from the REFERENCE MIRROR of
`ixp/e2e_03_project_creation_handoff/_setup/handoff_tenant.py` — never the
live sandbox copy staged for the agent, so a tampered sandbox file cannot
reach grading.

`uip ixp deployments list` returns a bare array (nothing to guard truncation
against). Response shapes are indexed, not `.get`-ed: a backend change should
crash the grader with a named KeyError, not silently produce a false verdict.
"""

from __future__ import annotations

import glob
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from flow_check import find_project_dir  # noqa: E402

# The reference mirror of handoff_tenant.py — a sibling of this file's own
# family root (`_shared/` and `ixp/` both hang off `uipath-maestro-flow/`).
# Resolved relative to THIS file, so it is the reference-tree copy both under
# a real repo checkout and under $REFERENCE_DIR's copytree mirror, never the
# agent-writable sandbox copy staged at `_setup/handoff_tenant.py`.
_TENANT_MODULE_DIR = (
    Path(__file__).resolve().parent.parent
    / "ixp" / "e2e_03_project_creation_handoff" / "_setup"
)
sys.path.insert(0, str(_TENANT_MODULE_DIR))
from handoff_tenant import (  # noqa: E402  (path set above)
    ixp_node_identifiers,
    list_deployments,
    list_deployments_if_present,
    matches_fixture_domain,
    new_project_names,
    read_snapshot,
    run_uip,
    run_uip_json,
)

# Node-type prefix for an IxP extraction node in a .flow — matches
# handoff_tenant.IXP_NODE_PREFIX; kept as a literal here too since it also
# gates the mock-fallback description below.
IXP_NODE_PREFIX = "uipath.ixp."

MOCK_NODE_TYPE = "core.logic.mock"

# The grader's own sandbox files. Excluded from the breadcrumb scan below:
# seed.json carries e2e_04's extractor name verbatim, so a Flow project that
# scaffolds at the sandbox root would otherwise satisfy the degraded gate for
# free, turning the fallback into a no-op.
RUN_HANDOFF_FILE = "seed.json"
SNAPSHOT = ".grader_baseline.json"
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
    in the node. Falsy names are dropped: `DeploymentName` is nullable in the
    API, and an empty string is a substring of everything, so keeping one would
    match any stale node and defeat the residue guard.

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
    scope = read_snapshot()["scope"]
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
                "node can take hours to surface (~25s when healthy), so the agent could never "
                "have discovered it. This is tenant weather, not a skill regression — see the "
                "task description before filing anything.",
                file=sys.stderr,
            )
    return 1


if __name__ == "__main__":
    sys.exit(check_main())
