#!/usr/bin/env python3
"""Grade the Flow→IXP design-time handoff from tenant state + the built artifact.

Passes only when all three links hold for THIS run:

  1. an IXP design-time project was created,
  2. one of its trained model versions was deployed to an Orchestrator folder
     (what publishes it into the Maestro flow registry), and
  3. the `.flow` wires an `uipath.ixp.*` node for that project's deployment.

Each link prints its own failure line, so stderr names which one broke.

Link 3 matches against the identifiers of parsed IxP nodes, never the file text
(see `ixp_projects.ixp_node_identifiers`). It accepts either the `DeploymentName`
or the project name: freshly created deployments carry the backend-slugged
`DeploymentName` in `inputs.modelName` (verified on a live tenant — project
`…-95d905dc-ixp` → node `…-295a144d-ixp`), while older demo deployments pinned in
`e2e_02_project_selection.yaml` carry the project name there. Both identifiers
are already scoped to this run, since the project came from the tenant diff.

Flow discovery uses `_shared/flow_check.find_project_dir`, the same helper
`validate_flow.py` uses, so both criteria grade the same artifact.

See ixp_projects.py for the tenant-diff rationale, and teardown.py for why the
un-deletable deployment residue means a later run may legitimately reuse an
extractor and fail here — check the reported node types before calling that a
skill regression.
"""

from __future__ import annotations

import glob
import json
import os
import sys
from typing import Any

TASK_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TASK_DIR)
sys.path.insert(0, os.path.join(TASK_DIR, "..", "..", "_shared"))

from flow_check import find_project_dir  # noqa: E402
from ixp_projects import (  # noqa: E402
    IXP_NODE_PREFIX,
    ixp_node_identifiers,
    list_deployments,
    new_project_names,
)

MOCK_NODE_TYPE = "core.logic.mock"


def flow_files() -> list[str]:
    """Every .flow in the Flow project graded by validate_flow.py.

    find_project_dir exits with a FAIL: message when there is no Flow project or
    when several are ambiguous — the right diagnostic either way.
    """
    project_dir = find_project_dir()
    return sorted(glob.glob(os.path.join(project_dir, "**/*.flow"), recursive=True))


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


def candidate_names() -> list[str]:
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
        return []
    print(f"Projects created this run: {created_projects}")

    names: list[str] = []
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
        return []
    return names


def main() -> int:
    names = candidate_names()
    if not names:
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
    return 1


if __name__ == "__main__":
    sys.exit(main())
