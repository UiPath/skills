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

**Always check [summary.md](./summary.md) Top-20 table first** — it lists the highest-volume Maestro errors (by production telemetry) with direct playbook links and marks each one's API debuggability (Full / Partial / None). Route there before walking the range table below.

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

1. **Determine runtime type** — check the job's `RuntimeType` or `Source` field. If it's a ProcessOrchestration job (Maestro), gather Maestro-specific data below. Standard Orchestrator jobs don't need these steps.
2. **Determine the Maestro process type** — `bpmn`, `flow`, or `case`. Every Maestro CLI invocation requires this segment (`uip maestro bpmn ...`, `uip flow ...`, `uip maestro case ...`). Identify the type from the source artifact (`.bpmn`, `.flow`, Case JSON), the `processType` field on the instance/incident, or by asking the user. Examples below use `<type>` as a placeholder — substitute the actual type.
3. **Resolve the Maestro instance ID** — for ProcessOrchestration jobs, the **Orchestrator job key IS the Maestro instance ID**. They are the same GUID. Do NOT use `ParentJobKey` — that is the parent Orchestrator job, not the Maestro instance.
   - **User provided a job key and `RuntimeType` is `ProcessOrchestration`**: the job key is the instance ID. Go directly to `uip maestro <type> instance get <job-key> -f <folder-key>`.
   - **User provided a job key and `RuntimeType` is NOT `ProcessOrchestration`** (standard child job): the child job was spawned by a Maestro service task. Check `ParentJobKey` — that parent job's key may be the instance ID. Try `uip maestro <type> instance get <parent-job-key> -f <folder-key>`.
   - **Neither works**: search with `uip maestro <type> incident summary --output json` to find the `processKey`, then `uip maestro <type> processes incidents <process-key> --folder-key <folder-key>` to find incident records containing the `instanceId`. If the process type is unknown, try each (`bpmn`, `flow`, `case`) in turn.
   - **`instance list` may return empty** for completed or faulted instances. Always try `instance get` directly before concluding an instance doesn't exist. Do NOT rely on `instance list` alone.
4. **Full incident details** — `uip maestro <type> instance incidents <instance-id> -f <folder-key>`. This returns `errorDetails` with stack traces. Do NOT use `uip maestro <type> incident summary` — that returns summaries only without error details.
5. **Element executions** — `uip maestro <type> instance element-executions <instance-id> -f <folder-key>` to see what each element did and where execution stopped.
6. **Child jobs** — if the process has service tasks, list child jobs and check their state and error messages. The child's failure reason is often the actual root cause.

## Top-20 Error Quick Route

Match the error text/code in the incident to one of the highest-volume Maestro errors before doing a full investigation. Full table with playbook links: [summary.md](./summary.md).

| Symptom hint | Playbook |
|--------------|----------|
| `Personal Automation quota` | [personal-automation-quota.md](./playbooks/personal-automation-quota.md) |
| `job's associated process could not be found` / 170007 | [process-not-found-404.md](./playbooks/process-not-found-404.md) |
| `unattended robot permissions in the current folder` / #1671 | [unattended-robot-permissions.md](./playbooks/unattended-robot-permissions.md) |
| `Job Operation Timeout` | [job-operation-timeout.md](./playbooks/job-operation-timeout.md) |
| `Input does not conform to schema` / `InputArgumentsSchema` | [input-schema-mismatch.md](./playbooks/input-schema-mismatch.md) |
| `Missing value for required parameter` | [missing-required-parameter.md](./playbooks/missing-required-parameter.md) |
| `Error_400` (no specific name) | [generic-error-400.md](./playbooks/generic-error-400.md) |
| `Property 'X' not found against object of type ExpressionDictionary` | [expression-evaluation-errors.md](./playbooks/expression-evaluation-errors.md) |
| `No condition for an outgoing flow was met` / 400001 | [gateway-no-outgoing-flow.md](./playbooks/gateway-no-outgoing-flow.md) |
| `Possible loop detected` / 400009 | [loop-detected.md](./playbooks/loop-detected.md) |
| `"File" field is required` / DAP-RT-1003 | [file-field-required.md](./playbooks/file-field-required.md) |
| `Request to Integration Services failed with status code '404'` | [integration-service-404.md](./playbooks/integration-service-404.md) |
| `Insufficient funds` / Agent Units | [insufficient-funds.md](./playbooks/insufficient-funds.md) |
| `Input collection for the marker element must not be null` / 400007 | [marker-input-null.md](./playbooks/marker-input-null.md) |
| `Request to Integration Services failed with status code '400'` | [integration-service-400.md](./playbooks/integration-service-400.md) |
| `Folder does not exist or the user does not have access` / #1100 | [folder-not-accessible.md](./playbooks/folder-not-accessible.md) |
| `Could not find a machine with Unattended or NonProduction runtimes` / #2818 | [no-suitable-runtime-machine.md](./playbooks/no-suitable-runtime-machine.md) |
| `No Message events found` / `No File events found` | [no-message-events.md](./playbooks/no-message-events.md) |
| `Foreground job requires an unattended robot` / #1230 | [foreground-unattended-robot.md](./playbooks/foreground-unattended-robot.md) |
| `Index was outside the bounds of the array` | [index-out-of-bounds.md](./playbooks/index-out-of-bounds.md) |

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
