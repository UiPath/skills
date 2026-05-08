# Maestro Investigation Guide

## Data Correlation

Before using any fetched data, verify it matches the user's reported problem:

- **Process/Solution** — the BPMN process name and solution match what the user reported
- **Instance** — the process instance ID matches the specific execution the user is investigating
- **Folder** — data comes from the correct Orchestrator folder (permissions, triggers, and jobs are folder-scoped)
- **Time window** — timestamps fall within the relevant period the user described
- **Child Jobs** — if investigating a service task, verify the child job belongs to the correct parent instance. Always check the child job's **error message and final state** — the child's failure reason is often the actual root cause, not the parent's error code. Search for child jobs in all states (Faulted, Stopped, Successful, Running), not just the expected state.

If the data doesn't match: **discard it**. Do NOT use unrelated data as a proxy. Report the mismatch and ask for clarification.

## First Step: Get the Error Code

Always retrieve the error code from the incident before doing anything else. If the user provides a process instance ID or incident ID, query the incident details to get the error code — this is the most reliable way to route to the correct playbook.

Error codes appear in the Maestro incident detail view. Ask the user for the incident ID or process instance ID if not provided. If neither is available, work from the error message text.

Full error code reference: [error_codes.md](./error_codes.md) — all error codes by subsystem with numeric values and messages.

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

## Domain-Specific Data Gathering

After the Orchestrator job data bundle (job details, logs, history) is collected:

1. **Determine runtime type** — check the job's `RuntimeType` or `Source` field. If it's a ProcessOrchestration job (Maestro BPMN), gather Maestro-specific data below. Standard Orchestrator jobs don't need these steps.
2. **Resolve the Maestro instance ID** — for ProcessOrchestration jobs, the **Orchestrator job key IS the Maestro instance ID**. They are the same GUID. Do NOT use `ParentJobKey` — that is the parent Orchestrator job, not the Maestro instance.
   - **User provided a job key and `RuntimeType` is `ProcessOrchestration`**: the job key is the instance ID. Go directly to `uip maestro instance get <job-key> -f <folder-key>`.
   - **User provided a job key and `RuntimeType` is NOT `ProcessOrchestration`** (standard child job): the child job was spawned by a Maestro service task. Check `ParentJobKey` — that parent job's key may be the instance ID. Try `uip maestro instance get <parent-job-key> -f <folder-key>`.
   - **Neither works**: search with `uip maestro incident summary --output json` to find the `processKey`, then `uip maestro processes incidents <process-key> --folder-key <folder-key>` to find incident records containing the `instanceId`.
   - **`instances list` may return empty** for completed or faulted instances. Always try `instances get` directly before concluding an instance doesn't exist. Do NOT rely on `instances list` alone.
3. **Full incident details** — `uip maestro instance incidents <instance-id> -f <folder-key>`. This returns `errorDetails` with stack traces. Do NOT use `uip maestro incident summary` — that returns summaries only without error details.
4. **Element executions** — `uip maestro instance element-executions <instance-id> -f <folder-key>` to see what each BPMN element did and where execution stopped
5. **Child jobs** — if the BPMN process has service tasks, list child jobs and check their state and error messages. The child's failure reason is often the actual root cause.

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
