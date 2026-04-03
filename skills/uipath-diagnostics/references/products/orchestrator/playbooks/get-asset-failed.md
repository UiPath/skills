---
confidence: medium
---

# Get Asset Failed

## Context

Get Asset or Get Robot Asset fails during job execution, but the error is not the exact "asset not found" pattern.

What this looks like:
- Error messages such as "You are not authenticated", "Folder does not exist or the user does not have access", or timeout/connection failures
- Intermittent failures across runs for the same process and asset
- Process succeeds in debug or one runtime context, but fails in unattended Orchestrator jobs

What can cause it:
- Identity or token issues for the execution identity (robot account)
- Folder scoping and permissions mismatch between job context and asset location
- Asset value configuration mismatch (global vs per-account/per-account-machine)
- Network/platform instability or transient Orchestrator connectivity issues
- Package/runtime changes that altered folder binding or execution context

What to look for:
- Exact error signature and code from traces (authentication, access, timeout, transport)
- Execution identity and folder context for failed runs versus successful runs
- Asset value mode and whether the running account-machine pair has a valid value
- Time clustering of failures and correlation with upgrades, deployments, or environment changes

## Investigation

1. Collect at least 3 failed executions and 2 successful executions for the same process and compare error signatures, folder, and execution identity.
2. Categorize failures by type (authentication, access/folder, timeout/connection, or value/config mismatch). Do not treat mixed categories as one root cause.
3. Verify folder scoping: confirm the process run folder is the folder where the asset is defined and where the robot account has asset access.
4. Verify runtime identity context: compare debug user context versus unattended robot account context, including role/permission differences.
5. Verify asset value assignment mode (global, per-account, per-account-machine) and confirm a valid value exists for the failing execution context.
6. If failures are intermittent, correlate timestamps with platform events (deployment, package update, robot version update, network incidents) to identify environmental causes.

A complete root cause must explain all failed executions in scope. If one hypothesis explains only part of the failures, keep investigating remaining categories.

## Resolution

- **If authentication context issue:** re-establish robot authentication/session and validate the run uses the expected robot account.
- **If folder or permission mismatch:** run the process in the correct folder and grant the robot account required asset permissions in that folder.
- **If value assignment mismatch:** update asset value configuration so the executing account or account-machine pair has a valid value.
- **If intermittent connectivity/timeouts:** implement retry handling for asset retrieval and stabilize network/platform dependencies before rerun.
- **If deployment/runtime regression:** align package bindings and runtime versions with the last known good configuration.
