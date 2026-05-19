---
confidence: high
---

# Job's Associated Process Not Found (404)

## Context

What this looks like:
- HTTP 404 from Orchestrator surfaced by Maestro
- Error message: `Operation returned invalid status code '404'. The job's associated process could not be found`
- Often reported as Maestro error code `170007` (`OrchestratorRpaJobFailedToStart`) when the failure occurs at job-start time

What can cause it:
- Stale or incorrect `ReleaseKey` in the service task binding
- Process was deleted, renamed, or moved to a different folder
- Solution imported across environments (staging → alpha) where folder keys / release keys were baked in
- API call missing the `X-UIPATH-OrganizationUnitId` header (folder context)
- Debug binding override pointing at a folder where the dependency was not deployed (the "Will be deployed in Debug folder" trap)

What to look for:
- Compare `bindings_v2.json` (deployed) or `debug_overwrites.json` (debug) with the actual processes in the target folder
- Check whether the solution was re-imported from another environment recently

## Investigation

> Substitute `<type>` with `bpmn`, `flow`, or `case` per the [Maestro investigation guide](../investigation_guide.md) § Determine the Maestro process type.


1. Get the incident: `uip maestro <type> instance incidents <instance-id> -f <folder-key> --output json`
2. Find the failing service task in element executions: `uip maestro <type> instance element-executions <instance-id> -f <folder-key> --output json`
3. Pull the binding for the failing task — request `bindings_v2.json` (deployed) or `debug_overwrites.json` (debug) from the user
4. Look up the `ReleaseKey` in Orchestrator: `uip or processes get <release-key> --output json` (process keys are tenant-unique; no folder context needed)
5. Verify the folder key in the binding matches the folder the instance is actually running in

## Resolution

- **If ReleaseKey is stale or missing:** re-publish the solution against the correct folder; update bindings; re-deploy
- **If solution was cross-imported:** re-create the folder mapping or re-bind dependencies in the destination environment
- **If debug mode:** change the debug config from "Will be deployed in Debug folder" to use the already-deployed dependency in the target folder
- **If API call:** include the `X-UIPATH-OrganizationUnitId` header pointing at the correct folder
- **If process was moved/renamed:** update the ReleaseKey, robot account, environment, and machine config in the binding

## References

- [Forum: Start job via API in Modern Folders](https://forum.uipath.com/t/start-job-process-via-api-in-modern-folders-the-jobs-associated-process-could-not-be-found/478483)
- [Forum: StartJobs API error](https://forum.uipath.com/t/startjobs-api-the-jobs-associated-process-could-not-be-found-error/29637)
