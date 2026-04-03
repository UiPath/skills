---
confidence: high
---

# Get Asset Failed

## Context

A Get Asset or Get Credential activity failed when trying to read an asset from Orchestrator at runtime.

What this looks like:
- Job fails with exception message: "Could not find the asset" or "does not have the required permissions to access the asset" or "Get Orchestrator Asset does not work with assets of type Credential" or
"Folder does not exist or the user does not have access to the folder"
- Activity name: `Get Orchestrator Asset` or `Get Orchestrator Credential`
- Process works in one folder but fails in another

What can cause it:
- Asset does not exist in the target folder
- Asset exists but has type Credential and `Get Asset` activity is used instead of `Get Credential`
- Asset exists but with a different name (case-sensitive mismatch)
- Asset exists in a parent folder but folder inheritance is not enabled
- Robot/user does not have permission to read assets in the folder

What to look for:
- Get the exact error message from the job traces
- Identify which asset name and type the process is trying to read
- Check if the asset was successfully fetched in any previous runs
- Identify which folder the job is running in

### Scenario: wrong-activity-for-credential-asset

When the error message is "Get Orchestrator Asset does not work with assets of type Credential".

**Investigation:**
1. Identify the asset name from the faulted activity
2. Verify the asset type in Orchestrator is `Credential`
3. Check if the workflow uses `Get Orchestrator Asset` instead of `Get Orchestrator Credential`

**Resolution:**
- Replace the `Get Orchestrator Asset` activity with `Get Orchestrator Credential` activity
- The `Get Credential` activity returns a SecureString for password and a String for username
- Update downstream activities to use the credential object properties correctly

### Scenario: asset-does-not-exist

When the error message is "Could not find the asset".

**Investigation:**
1. Get the asset name from the activity (check XAML or job traces)
2. List assets in the job's folder: `uip or assets list {folderId} --format json`
3. Compare asset name in source code vs Orchestrator (exact match, case-sensitive)
4. Check if the asset exists in a parent folder but inheritance is disabled

**Resolution:**
- If asset doesn't exist: create the asset in the correct folder with the correct type
- If name mismatch: fix the asset name in the workflow to match Orchestrator exactly (case-sensitive)
- If asset is in parent folder: enable folder inheritance or create the asset directly in the target folder

### Scenario: permission-denied

When the error message is "does not have the required permissions to access the asset".

**Investigation:**
1. Identify the robot account running the job
2. Check the robot account's role assignments in the target folder
3. Verify the role includes the "View Assets" permission

**Resolution:**
- Grant the robot account a role that includes "View Assets" permission in the folder
- Common roles with this permission: Automation User, Automation Developer, Administrator
- If using folder inheritance, check permissions in parent folders as well
