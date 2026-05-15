---
confidence: high
---

# Foreground Job Requires Unattended Robot (409, #1230)

## Context

What this looks like:
- HTTP 409 from Orchestrator surfaced by Maestro
- Error message: `Operation returned invalid status code '409'. Foreground job requires an unattended robot to be defined on your user`
- Orchestrator error code `#1230`

What can cause it:
- The user triggering a foreground (UI-interactive) unattended job has no unattended robot configured
- Underlying RPA project is a Studio (desktop) project running in **My Workspace**, which doesn't allow assigning bots/machines
- User has Unattended runtime license at tenant level but no machine credentials configured
- Debug-only manifestation — deployed flows running under a different identity work fine

What to look for:
- Whether the underlying RPA project is Studio (desktop, `.xaml`) or Studio Web (Agentless/Serverless)
- Whether the folder is "My Workspace" vs a standard folder
- Whether the user has unattended machine credentials configured

## Investigation

> Substitute `<type>` with `bpmn`, `flow`, or `case` per the [Maestro investigation guide](../investigation_guide.md) § Determine the Maestro process type.


1. Get the incident: `uip maestro <type> instance incidents <instance-id> -f <folder-key> --output json`
2. Confirm the user has Unattended Robot enabled: Orchestrator UI → **Tenant > Manage Access > Users** → select user → license tab
3. Check that machine credentials are set (domain\username + password)
4. Confirm the folder type — "My Workspace" cannot host unattended robots
5. Identify the underlying RPA project type from the service task's binding

## Resolution

- **If user lacks Unattended enabled:** enable "Unattended Robot" on the user and assign valid machine credentials
- **If running from My Workspace:** move the process to a standard folder where unattended bots can be assigned
- **If Studio (desktop) project:** rebuild in Studio Web so the workflow runs on Agentless/Serverless and no unattended bot is needed
- **If runtime license missing:** assign an Unattended runtime license to the user
- **If debug-only and deployed works:** debug runs under the user's identity, deployed under the robot's — provision an unattended robot on the user, or run via deployed mode

## References

- [Forum: Error #1230](https://forum.uipath.com/t/foreground-job-requires-an-unattended-robot-to-be-defined-on-your-user-1230/718082)
