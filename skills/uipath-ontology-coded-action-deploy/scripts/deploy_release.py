#!/usr/bin/env python3
"""Deploy a published version, creating its Orchestrator folder. MUTATES a live tenant.

A NEW deployment name creates a new folder; the SAME name with a new --package-version upgrades
that deployment in place, one folder throughout. See deploy_release() for why reusing the name is
the correct path for a re-release and why uninstalling is never one.

The folder must be under Shared or it has no user with unattended robot permissions and the job
cannot start. The folder this creates is what Phase 5 reports; no artifact is edited.
"""

import argparse
import os

from _solution import PARENT_FOLDER_PATH, live_at_version, solution_name
from _uip import UIP, described, emit, uip_json

DESCRIBE = {
    "name": 'deploy_release',
    "purpose": 'Deploy a version, creating the folder or upgrading the deployment in place',
    "phase": '3 - release',
    "inputs": {'env': ['SOLUTION_SRC or SOLUTION_NAME', 'PARENT_FOLDER_PATH (optional)', 'DEPLOY_NAME (optional)'], 'args': ['version', 'deployment_name (optional)', '--execute']},
    "outputs": {'deployment': 'the deployment name', 'folderPath': 'the folder created'},
    "mutates": True,
    "exit_codes": {"0": "ok, result on stdout", "1": "refused or failed, reason on stderr"},
}


def deploy_release(name, version, deploy_name, execute):
    """Deploy a published version. The SAME deployment name upgrades in place.

    `deploy run` with an existing deployment name and a new --package-version upgrades that
    deployment: one folder throughout, same folder key, no duplicate processes. Reusing the name is
    the correct path for a re-release, not a hazard.

    NEVER uninstall to re-release. `uninstall` removes the solution folder and everything
    provisioned in it -- which includes the ontology's Data Fabric entities, because those are
    created inside this folder. Uninstalling to get a clean deploy destroys the author's data.

    The folder cannot be chosen, only named: every folder flag names a parent or a NEW folder. Given
    --folder-name X while a folder X already exists, it creates "X 1" and puts the processes there,
    leaving anything bound to the original folder pointing at zero processes. So the deployment
    creates the folder, and everything else follows it -- which is why this runs before the entities
    and before the ontology is created.

    PARENT_FOLDER_PATH defaults to Shared, and that matters. A solution folder created at the ROOT
    gets no user with unattended robot permissions, so the service cannot start the job there:
    Orchestrator answers StartJobs with HTTP 409, errorCode 1671, "Couldn't find any user with
    unattended robot permissions in the current folder", and the invoke reports a bare "Unexpected
    error" on the Running job step. Verified both ways.
    """
    # Deploying a version that is already running is a no-op rather than a second folder.
    already = live_at_version(name, version)
    if already:
        return {"ok": True, "noop": True, "reason": "already deployed at this version",
                "deployment": already, "version": version}

    argv = ["solution", "deploy", "run", "-n", deploy_name, "--package-name", name,
            "--package-version", version, "--folder-name", deploy_name,
            "--parent-folder-path", PARENT_FOLDER_PATH]
    if not execute:
        return {"ok": True, "dryRun": True, "command": [UIP] + argv,
                "note": "reusing an existing deployment name upgrades it in place; never uninstall "
                        "to re-release, because that deletes the folder and the entities in it"}
    uip_json(argv)
    return {"ok": True, "deployment": deploy_name, "version": version,
            "folderPath": "%s/%s" % (PARENT_FOLDER_PATH, deploy_name),
            "next": "read the folder's Key and Id with `uip or folders get`; the ontology is "
                    "created against that Key"}


def main():
    if described(DESCRIBE):
        return
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("version")
    ap.add_argument("deployment_name", nargs="?")
    ap.add_argument("--execute", action="store_true")
    args = ap.parse_args()
    name = solution_name()
    deploy_name = args.deployment_name or os.environ.get("DEPLOY_NAME") or name
    emit(deploy_release(name, args.version, deploy_name, args.execute))


if __name__ == "__main__":
    main()

