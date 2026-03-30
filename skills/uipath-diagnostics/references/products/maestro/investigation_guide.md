# Maestro Investigation Guide

## Data Correlation

Before using any fetched data, verify it matches the user's reported problem:

- **Process/Solution** — the BPMN process name and solution match what the user reported
- **Instance** — the process instance ID matches the specific execution the user is investigating
- **Folder** — data comes from the correct Orchestrator folder (permissions, triggers, and jobs are folder-scoped)
- **Time window** — timestamps fall within the relevant period the user described
- **Child Jobs** — if investigating a service task, verify the child job belongs to the correct parent instance

If the data doesn't match: **discard it**. Do NOT use unrelated data as a proxy. Report the mismatch and ask for clarification.

## First Step: Get the Error Code

Always retrieve the error code from the incident before doing anything else. If the user provides a process instance ID or incident ID, query the incident details to get the error code — this is the most reliable way to route to the correct playbook.

Error codes appear in the Maestro incident detail view. Ask the user for the incident ID or process instance ID if not provided. If neither is available, work from the error message text.

Full error code reference: [error-codes.md](./error-codes.md) — all error codes by subsystem with numeric values and messages.

Quick routing by range:

| Range | Subsystem | Common action |
|-------|-----------|---------------|
| 102000–102018 | Integration Service | Check connection config, endpoint URLs, input parameters |
| 150001–150009 | Auth & Permissions | Check folder permissions for robot/user account |
| 170000–170041 | Orchestrator Runtime | Check child job errors, robot availability, task inputs |
| 300200–300208 | Data Fabric | Check file references, connectivity, record operations |
| 300500–300503 | Script Tasks | Check for browser-only JS APIs; use Jint-compatible code |
| 400000–400023 | BPMN Elements | Check BPMN model, gateway conditions, marker inputs |
| 400300–400302 | Expression Evaluation | Check variable names, types, expression syntax |
| 400500–400505 | Licensing | Check Maestro license entitlement on the tenant |

## Testing Prerequisites

When testing hypotheses for Maestro issues, gather and verify these before drawing conclusions:

1. **Error code from incident** — always retrieve the error code from the Maestro incident before drawing conclusions. The error code is the primary classifier for Maestro issues
2. **Maestro service status** — confirm the Maestro service is enabled on the tenant (license revocations silently disable it)
3. **License entitlement** — confirm the user's license includes Maestro access
4. **Folder context** — confirm the folder the process runs in; permissions, connections, and triggers are folder-scoped
5. **Robot account permissions** — verify the robot account has required permissions in the folder (including "Triggers" permission for wait-for scenarios, not just "Connections.View")
6. **Debug vs deployed mode** — determine if the issue occurs in debug, deployed, or both. Debug runs under the user's identity with `debug_overwrites.json` folder bindings; deployed runs under the robot account with `bindings_v2.json`
7. **Source artifacts** — request the `.bpmn` file and `bindings_v2.json` when investigating process logic or variable resolution issues
8. **Instance and incidents** — get the process instance ID from Maestro Instance Management; check for incidents that may not appear in Orchestrator
9. **Dependencies** — check `## Dependencies` in `overview.md` for cross-product issues (e.g., Integration Service, AI Trust Layer, Semantic Proxy)
