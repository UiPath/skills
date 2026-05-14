---
confidence: high
---

# Folder Does Not Exist or No Access (400, #1100)

## Context

What this looks like:
- HTTP 400 (sometimes 403) from Orchestrator surfaced by Maestro
- Error message: `Operation returned invalid status code '400'. Folder does not exist or the user does not have access to the folder.`
- Orchestrator error code `#1100`

What can cause it:
- Robot/user account is not assigned to the target folder
- Folder name contains characters Maestro's folder-path resolver historically chokes on — e.g., commas (`"Autopilot, Agentic, and Gen AI"` triggered `PLT-82739`)
- Folder was renamed or deleted; bindings still reference the old path or key
- Solution imported across environments (staging → alpha) where folder keys differ — keys were baked into the solution
- API call missing or pointing the `X-UIPATH-OrganizationUnitId` header at the wrong folder
- Modern folder permissions missing at tenant level (need both tenant-level access and folder-level role)

What to look for:
- `folderKey` in the incident — does it actually exist in Orchestrator?
- Whether the folder name contains commas or other unusual characters
- Whether the solution was recently imported from another environment

## Investigation

1. Get the incident: `uip maestro instance incidents <instance-id> -f <folder-key> --output json`
2. Verify the folder exists: `uip or folders list --output json` — search by `Key`
3. List users on that folder: `uip or folders users list <folder-key> --output json` — is the robot account assigned?
4. Check the underlying bindings — request `bindings_v2.json` (deployed) or `debug_overwrites.json` (debug)
5. If the folder contains commas in its name, suspect the historical path-resolver bug

## Resolution

- **If user/robot not assigned:** assign with the appropriate role at Orchestrator → **Folder > Manage Access > Assign**
- **If folder name contains comma:** rename the folder to remove the comma; re-publish so bindings refresh
- **If solution cross-imported:** update bindings to the destination folder keys; re-deploy
- **If API call:** include the correct `X-UIPATH-OrganizationUnitId` header
- **If modern folder permissions:** ensure tenant-level access AND folder-level role for the account

## References

- [Forum: Error code #1100](https://forum.uipath.com/t/folder-does-not-exist-or-the-user-does-not-have-access-to-the-folder-error-code-1100/541536)
