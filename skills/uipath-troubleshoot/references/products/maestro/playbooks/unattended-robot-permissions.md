---
confidence: high
---

# No Unattended Robot Permissions in Folder (409, #1671)

## Context

What this looks like:
- HTTP 409 from Orchestrator surfaced by Maestro at job-start time
- Error message: `Operation returned invalid status code '409'. Couldn't find any user with unattended robot permissions in the current folder.`
- Orchestrator error code `#1671`

What can cause it:
- No user with an Unattended Robot license is assigned to the Orchestrator folder where the Maestro service task runs
- The "Unattended Automations" permission is missing on the folder role even though the license is granted at tenant level
- Process was built in classic Studio (desktop) where unattended robots are required, but the deployment folder has none — switching to Studio Web (Agentless/Serverless runtime) is a workaround
- API call missing or pointing the `OrganizationUnitId` header at the wrong folder

What to look for:
- Incident `folderKey` — tells you exactly which folder to inspect
- Is the underlying RPA project a Studio (desktop, `.xaml`) or Studio Web project? Studio Web runs on serverless and does not need an unattended robot

## Investigation

> Substitute `<type>` with `bpmn`, `flow`, or `case` per the [Maestro investigation guide](../investigation_guide.md) § Determine the Maestro process type.


1. Get the incident: `uip maestro <type> instance incidents <instance-id> -f <folder-key> --output json`
2. Extract `folderKey` from `errorDetails`
3. List users assigned to that folder: `uip or folders users list <folder-key> --output json`
4. Inspect license assignments: Orchestrator UI → **Tenant > Manage Access > Users** for the relevant user
5. Confirm the underlying RPA project type — Studio (desktop) vs Studio Web

## Resolution

- **If user has no Unattended license:** Orchestrator UI → **Tenant > Manage Access > Users** → enable "Unattended Robot" for the user
- **If permission missing on the folder:** assign the user to the folder with a role that includes "Unattended Automations"
- **If using a Studio (desktop) project unnecessarily:** rebuild the workflow in Studio Web so it runs on Agentless/Serverless
- **If API call:** make sure `X-UIPATH-OrganizationUnitId` points at the folder where the unattended user is assigned

## References

- [Forum: Error #1671](https://forum.uipath.com/t/couldnt-find-any-user-with-unattended-robot-permissions-in-the-current-folder-1671/417804)
