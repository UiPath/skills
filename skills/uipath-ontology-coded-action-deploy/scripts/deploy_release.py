#!/usr/bin/env python3
"""Create a deployment for a published version, in a NEW Orchestrator folder. MUTATES a live tenant.

A new version means a new deployment in a new folder under Shared -- the POC found no upgrade
verb, and the folder must be under Shared or it has no unattended robot permissions and the job
cannot start. The folder id this produces is what Phase 5 patches into each action TTL.
"""

import argparse
import os

from _solution import (
    PARENT_FOLDER_PATH,
    folder_id,
    deployments,
    live_at_version,
    name_taken,
    solution_name,
    tombstone,
)
from _uip import UIP, described, die, emit, uip_json

DESCRIBE = {
    "name": 'deploy_release',
    "purpose": 'Deploy a published version into a new Orchestrator folder',
    "phase": '3 - release',
    "inputs": {'env': ['SOLUTION_SRC or SOLUTION_NAME', 'PARENT_FOLDER_PATH (optional)', 'DEPLOY_NAME (optional)'], 'args': ['version', 'deployment_name (optional)', '--execute']},
    "outputs": {'deployment': 'the deployment name', 'folderPath': 'the folder created'},
    "mutates": True,
    "exit_codes": {"0": "ok, result on stdout", "1": "refused or failed, reason on stderr"},
}


def deploy_release(name, version, deploy_name, execute):
    """`deploy run` does NOT upgrade an existing deployment: it CREATES one, plus a new
    Orchestrator folder (-n required, fresh DeploymentKey returned). So a new version means a NEW
    deployment in a NEW folder, and the action's ont:processFolderId is then repointed at it.

    PARENT_FOLDER_PATH matters and defaults to Shared for a reason. A solution folder created at
    the ROOT gets no user with unattended robot permissions, so the service cannot start the job
    there: Orchestrator answers StartJobs with HTTP 409, errorCode 1671, "Couldn't find any user
    with unattended robot permissions in the current folder", and the invoke reports a bare
    "Unexpected error" on the Running job step. A folder created UNDER Shared inherits Shared's
    assignments and runs the job. Verified both ways.
    """
    # Idempotence first. Deploying a version that is ALREADY running is a no-op, not a new folder;
    # otherwise a repeated deploy quietly multiplies folders, each carrying the same processes,
    # and only one of them is the folder the TTL names.
    already = live_at_version(name, version)
    if already:
        return {"ok": True, "noop": True, "reason": "already deployed",
                "deployment": already, "version": version,
                "folder": folder_id("%s/%s" % (PARENT_FOLDER_PATH, already), required=False)}

    if name_taken(deploy_name):
        die("a deployment named %r already exists at a different version; pass a different name, "
            "or uninstall the old one. Reusing the name would create a duplicate rather than "
            "upgrade it." % deploy_name)

    argv = ["solution", "deploy", "run", "-n", deploy_name, "--package-name", name,
            "--package-version", version, "--folder-name", deploy_name,
            "--parent-folder-path", PARENT_FOLDER_PATH]
    if not execute:
        return {"ok": True, "dryRun": True, "command": [UIP] + argv}
    uip_json(argv)
    # The folder id is what the TTL patch needs, and deploy run reports only the path.
    return {"ok": True, "deployment": deploy_name, "version": version,
            "folder": folder_id("%s/%s" % (PARENT_FOLDER_PATH, deploy_name))}


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

