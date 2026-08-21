#!/usr/bin/env python3
"""post_run: delete the IXP design-time projects this run created.

**Attribution rule — why the tenant diff alone is not enough.** The diff
(``new_project_names()``) is tenant-wide, so a project created by a concurrent
run or by a person while this task was in flight also appears in it. Deleting on
the diff alone would destroy someone else's work. A project is deleted only when
one of these holds:

  * one of its identifiers (project name or a ``DeploymentName``) appears in an
    ``uipath.ixp.*`` node in this sandbox's flow — proof this run built it; or
  * it is the ONLY project in the diff, so there is nothing to confuse it with.

Anything else is reported and left alone. Design-time projects can be deleted by
hand, so erring toward a reported leak is strictly better than a wrong delete.

**Exit code.** Always 0. post_run runs after grading, so a cleanup problem must
never turn a graded result into a failure — hence the one broad handler around
main(). That is a policy at the process boundary, not error-swallowing: every
failure is printed.

**Folder deployments are never removed, because they cannot be.**
``deployments create`` is create-only on every reachable surface (the design-time
DeploymentsController exposes POST/PUT/GET and no ``[HttpDelete]``; a live DELETE
returns 405; the folder-scoped runtime API is GET-only), and deleting the project
does not cascade. Each run therefore leaves one permanent ``uipath.ixp.*`` node
in the tenant's flow registry. They are listed below so the residue accumulates
visibly — a growing list is the signal that the tenant needs replacing, or that a
delete path has appeared upstream.
"""

from __future__ import annotations

import glob
import json
import os
import sys
import traceback

TASK_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TASK_DIR)

from ixp_projects import (  # noqa: E402
    SNAPSHOT,
    ixp_node_identifiers,
    list_deployments,
    new_project_names,
    run_uip,
)


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

    Deliberately tolerant and glob-based rather than reusing
    check_handoff.flow_files(): that helper calls find_project_dir, which
    sys.exits on an ambiguous or missing project. A hard failure is right when
    grading and wrong here — cleanup falls back to the only-one-new-project rule
    when there is no readable flow. (glob skips hidden segments already.)
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

    stranded = [
        (deployment["DeploymentName"], deployment["FolderKey"])
        for project_name in attributable
        for deployment in deployments_by_project[project_name]
    ]
    if stranded:
        print(
            f"LEAKED: {len(stranded)} folder deployment(s) cannot be removed "
            "(create-only API — see this module's docstring):"
        )
        for deployment_name, folder_key in stranded:
            print(f"  - {deployment_name} in folder {folder_key}")


def main() -> int:
    # BaseException, not Exception: a helper that calls sys.exit raises SystemExit,
    # which Exception would let through and break the always-0 contract.
    try:
        cleanup()
    except BaseException:  # noqa: BLE001 — see module docstring: post_run must exit 0
        print("WARN: cleanup failed; projects created by this run may remain:")
        traceback.print_exc(file=sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
