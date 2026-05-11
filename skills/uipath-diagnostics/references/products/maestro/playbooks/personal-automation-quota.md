---
confidence: high
---

# Personal Automation Quota Exceeded (502)

## Context

What this looks like:
- HTTP 502 surfaced by Maestro when starting a job
- Error message: `Automation cannot be started. Your user's monthly Personal Automation quota has been exceeded.`
- Often reported as Orchestrator error code `170002` propagated through a Maestro service task

What can cause it:
- User is on a Personal Automation license plan and has consumed the monthly Robot Unit allocation
- Agentic Unit allocation expired (free trial ended) on the user/tenant
- Concurrent Personal Automation usage across multiple workspaces

What to look for:
- Incident `errorMessage` is self-explanatory — quota text appears verbatim
- Affects only the user/owner of the workspace, not the tenant

## Investigation

1. Get the incident: `uip maestro instance incidents <instance-id> -f <folder-key> --output json`
2. Confirm error text matches the quota wording above. If error code is `170002`, drill into the child Orchestrator job to see the underlying quota response
3. Check tenant consumption: Orchestrator UI → **Admin > Tenant > Licenses > Consumption**
4. If the user is running agents, also confirm Agentic Units are available (separate quota)

## Resolution

- **If Personal Automation quota exhausted:** request a license upgrade via [self-service license increase](https://uipath.atlassian.net/wiki/spaces/LIC/pages/2834596253), or wait for the monthly quota reset
- **If Agentic Units expired:** allocate AU from **Admin > Organization > Subscriptions** or contact the UiPath account manager
- **If recurring:** redesign the workflow to use a tenant-level Unattended robot instead of Personal Automation so quotas come from the shared pool

## Notes

- This is not a Maestro platform bug. Quota enforcement happens in Orchestrator's job execution layer; Maestro surfaces it as 502
- The incident `errorMessage` already contains everything needed — no PIMS deep-dive required
