# Integration Service Investigation Guide

## Data Correlation

Before using any fetched data, verify it matches the user's reported problem:

- **Connection identity** — the connection name and connector type match what the error message or user referenced
- **Folder** — connections can be folder-scoped; verify you're looking at the connection in the correct folder
- **Connector vs Connection** — a connector is the template (e.g., "uipath-microsoft365-o365"), a connection is an authenticated instance. Errors reference connections, not connectors.
- **Caller context** — determine whether the connection was called from an Orchestrator workflow, a Maestro BPMN process, or a Studio debug session. The calling identity (user vs robot account) affects permissions.

If the data doesn't match: **discard it**. Do NOT use unrelated data as a proxy. Report the mismatch and ask for clarification.

## First Step: Identify the Connection AND its Ownership

Always identify the specific connection AND determine where it lives before doing anything else. From the project's connection resource file (see "Connection Resource File" in [overview.md](./overview.md) for path pattern and field reference), you must answer four questions:

- **Which connector?**
- **Who owns the connection?**
- **Where is the connection bound?**
- **What is the connection ID?**

Together these answers determine whether the connection is in the runner's workspace, in a different user's workspace, or in a folder the runner cannot reach. **Always extract and compare them — do not stop after just the connector name.**

For the field-by-field extraction checklist for a specific error pattern, see the matched playbook's Investigation section — the playbook is authoritative for which fields and which comparisons matter for that error.

If no source code is available, the error message usually names the connection. Use `uip is connections list` to find it by name, then `uip is connections ping <connection-id>` to check its status. Without the resource file, ownership cannot be confirmed without asking the user.

**Do NOT infer the connector from the activity package name** — activity packages and connectors have different naming conventions (e.g., `UiPath.MicrosoftOffice365.Activities` uses connector "Microsoft OneDrive & SharePoint"). Always resolve from connection resource files or the connections API.

If the connection identity is still unclear, ask the user which connection or connector is involved.

## Connector Activity Runtime Exceptions

When the failure is a robot exception thrown by a connector activity (`ConnectorActivity`, `ConnectorTriggerActivity`, `ConnectorHttpActivity`, `ConnectorPersistenceActivity`), the exception class and its error code route the diagnosis:

- **`GeneralException` / `RuntimeException`** carry a structured `DAP-` code (`DAP-GE-####`, `DAP-RT-####`). The code maps to an exact cause — read it from the job log / Info and match the corresponding playbook before gathering more data. `DAP-GE-*` = connection resolution; `DAP-RT-*` = binding / input / trigger / operation.
- **`UiPath.Ipc.RemoteException` / `UiPath.CoreIpc.RemoteException`** carry NO DAP code. They are a generic out-of-process wrapper — **unwrap to the innermost message** (follow `--->` chains) and classify on that (token/auth, transport, downstream HTTP). The `RemoteException` class itself is not IS-specific; only treat it as a connector failure when the faulted activity is a connector activity and the inner message fits.
- **`System.AggregateException`** is never the cause — unwrap `InnerExceptions[0]` (recurse) and re-classify on the inner exception.
- **`System.NullReferenceException`** has no detail — use the stack frame (often a `ForEach` over a `SWEntities.*_List` connector output) to find which reference was null.

## Domain-Specific Data Gathering

After the Orchestrator job data bundle (job details, logs, traces) is collected and the connection is identified:

1. **Connection status** — `uip is connections ping <connection-id>` to check if it's active
2. **Connection details** — `uip is connections list` to find connector type, status, and folder scope
3. **Connection resource file** — if source code is available, read the connection resource JSON from the project (see "Connection Resource File" in [overview.md](./overview.md) for path pattern)

## Testing Prerequisites

When testing hypotheses for Integration Service issues, gather and verify these before drawing conclusions:

1. **Connection status** — ping the connection to check if it's active and enabled (`uip is connections ping <id>`)
2. **Connection details** — list the connection to see its connector type, status, and folder scope
3. **Caller identity** — determine if the caller is a user (debug mode) or robot account (deployed mode). Robot accounts may lack permissions the user has.
4. **Folder permissions** — verify the caller has access to the folder where the connection resides. For Maestro triggers, the robot account needs "Triggers" permission, not just "Connections.View".
5. **OAuth token state** — if the connection uses OAuth, check whether the token may have expired or been revoked. A ping failure after a period of working correctly suggests token expiry.
6. **External service availability** — if the connection pings successfully but operations fail, the issue may be on the external service side (API changes, rate limits, outages)

## Trigger Trace Evidence

A trigger trace is one execution of an Integration Service event trigger — one poll
cycle, or one webhook delivery. Reading traces answers "did the trigger run, and what
did it see" with observed data, so it comes **before** configuration checks, not after.
Three playbooks share this procedure: [trigger-not-firing.md](./playbooks/trigger-not-firing.md),
[start-trigger-not-firing.md](../maestro/playbooks/start-trigger-not-firing.md) and
[wait-for-event-stuck.md](../maestro/playbooks/wait-for-event-stuck.md).

### Applicability gate — run this first

**These commands apply to Integration Service event triggers only.** Time, queue, HTTP
and API triggers, manual runs and parent-process starts record no traces, and an empty
result against one of them is meaningless, not evidence. Confirm the trigger type before
reading anything:

| Starting point | Confirms an event trigger when | Not an event trigger → |
|---|---|---|
| Orchestrator trigger | `ApiTriggerType` is `IntegrationTrigger` | time / queue / HTTP trigger — use `uip or triggers history <key>`; this guide does not apply |
| Maestro process or instance | instance `Source` is `IntegrationTrigger`, or the start element's `ElementExtensionType` is `Intsvc.EventTrigger` | `Manual`, an API call, a time trigger or a parent process — route to the Maestro deployment or job playbooks |
| A waiting Maestro element | the element's `ElementExtensionType` is `Intsvc.WaitForEvent` **and** its span carries `intSvcTriggerId` | a timer, Action Center task or child job — see [bpmn-job-stuck.md](../maestro/playbooks/bpmn-job-stuck.md) |

If the gate fails, say so and route. Do not fall back to reading traces anyway.

### Step 1 — did the trigger run in the window?

```bash
# Orchestrator event trigger, or a Maestro start trigger (add --source maestro)
uip is trigger-traces list --trigger-key <trigger-key> --folder-path "<folder>" --from 24h --output json

# A Maestro instance's mid-process Wait-For-Event
uip is trigger-traces list --instance-id <instance-id> --from 24h --output json
```

`--from` takes `30m`, `6h`, `7d` or ISO 8601, and matches the user's reported window.
Traces are retained 30 days; a longer `--from` comes back with a `Warning` naming the
window actually searched — quote it rather than reporting the narrowed result as complete.

**Zero rows is itself a finding:** the trigger never polled. Only then do the
configuration checks (connection ping, enabled state, folder permission,
`uip or triggers history`) earn their place.

### Step 2 — read the row before gathering anything else

Column names match the Traces tab in Orchestrator and Maestro, so they can be compared
with what the user sees.

| Reading | What it means | Next |
|---|---|---|
| **zero rows** | trigger never ran | configuration checks; `uip or triggers history <key>` |
| **`Outcome: Faulted`** | the poll or delivery itself failed | Step 3 — the error is in the spans |
| **`EventsFetched: 0`** | the connector saw no events; the cause is upstream of UiPath | Step 3 — check the query window actually sent |
| **`EventsFetched > 0`, `EventsMatched: 0`** | events arrived and **the trigger's filter rejected them** | Step 3 — compare filter against payload |
| **`EventsMatched > 0`, `Notified: false`** | matched but dispatch failed | `uip or jobs list` in the trigger's folder |
| **`EventsMatched > 0`, `Notified: true`** | the trigger did its job — the fault is downstream | Orchestrator job state, or the Maestro instance |

### Step 3 — spans carry the filter and the payload

```bash
uip traces spans get <trace-id> --output json
```

Every trace carries two spans, named `Data - <n>` / `UserFilters - <n>` for a polling
trigger and `Webhook Data` / `Webhook User Filters` for a webhook one. The second is
usually the answer:

- **`DataFilters.input.filter`** — the filter expression the trigger actually evaluated
- **`DataFilters.output.matched`** — the records that survived it

A Wait-For-Event filter correlates to one specific record, e.g.
`(Id == 'F9BAC415-…' && Name == 'TriggersReliability_Updated')`. An instance waits for
**that** record and no other, so an update to a different record of the same type
produces a trace that fetched data and matched nothing. Quote the expression and the id
back to the user — it is the fastest way to end a "but I did update it" disagreement.

Span `Attributes` arrive as a JSON string; parse before reading fields.
