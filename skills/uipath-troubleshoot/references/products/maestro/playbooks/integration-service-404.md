---
confidence: medium
---

# Integration Service Failure (404)

## Context

What this looks like:
- HTTP 404 from an Integration Service call
- Error message: `Request to Integration Services failed with status code '404'`
- Sometimes seen with a related text like `Invalid Element Instance Id provided.` or `Missing instance` (Data Fabric writes)

What can cause it:
- Connector or action was deleted/renamed since publish
- Integration Service connection expired or was removed
- Tenant doesn't have Integration Service enabled (**Admin > Tenant > Services**)
- Webhook config references a non-existent object on the external side
- Solution cross-imported between environments (staging → alpha) where the folder key embedded in the solution doesn't exist in the destination — surfaces as 404/403
- For Data Fabric writes: missing instance, folder, or tenant permission on the target

What to look for:
- The connector name and action attempted — Variables API + element executions
- Whether the failure started right after a solution import or connector rename
- Connection state in the IS UI

## Investigation

> Substitute `<type>` with `bpmn`, `flow`, or `case` per the [Maestro investigation guide](../investigation_guide.md) § Determine the Maestro process type.


1. Get the incident: `uip maestro <type> instance incidents <instance-id> -f <folder-key> --output json`
2. Identify the failing connector activity: `uip maestro <type> instance element-executions <instance-id> -f <folder-key> --output json`
3. Check the IS connection: Orchestrator UI → **Integration Service > Connections** — verify exists, not expired
4. Confirm IS is enabled on the tenant
5. For Data Fabric writes, verify the target entity/instance exists in the destination folder and the robot has permission

## Resolution

- **If connection expired:** re-authenticate; re-publish the process if needed
- **If connector deleted/renamed:** re-create the activity against the current connector and re-publish
- **If IS not enabled on the tenant:** enable via **Admin > Tenant > Services**
- **If webhook config stale:** regenerate the webhook URL and update the external system
- **If solution cross-imported with stale keys:** update bindings to the destination folder keys and re-deploy
- **If Data Fabric target missing:** create the entity/instance in the destination folder, or fix the binding

## Notes

- This error is **Not Troubleshootable** from PIMS API alone — incident lacks the connector name, connection ID, and action attempted. Expect to ask the user for the failing element name; planned enrichment in incident data would move this to "Full"

## References

- [Forum: IS resource not found in Community Cloud](https://forum.uipath.com/t/persistent-integration-services-resource-not-found-error-in-community-cloud/5712850)
- [Docs: Connections Troubleshooting](https://docs.uipath.com/integration-service/automation-cloud/latest/user-guide/connections-troubleshooting)
