# workflowevents-initialize-hub-connection-aggregate-failure

Faithful-replay scenario: a Studio Web app-workflow run faults at the internal `InitializeHubConnection` activity (`UiPath.WorkflowEvents.Activities`) with `System.AggregateException` wrapping `System.Activities.WorkflowApplicationException: SignalR: Invalid SessionId:  OR Orchestrator Url: ` — the synchronous hub-connection bootstrap rejected a blank session id / resource URL.

## What this exercises

The agent must unwrap the `AggregateException` to the inner `WorkflowApplicationException` and recognise this as a **session/URL bootstrap** failure (blank session id / unresolved resource URL from the Studio Web app-preview context), not a SignalR socket/transport failure (the background `StartConnectionAsync` swallows those), not an in-workflow error, not a `HandleAppRequest` null reference, and not an `AppRequestTrigger` timeout. Disambiguation evidence: the `Initialize Apps Hub Connection` span shows `SessionId = ""`, and the fault is fast (~3s, not a 60s connect wait). Tests playbook `activity-packages/workflowevents-activities/playbooks/initialize-hub-connection-aggregate-failure.md`.

## Evidence in the fixtures

- `or folders list` → personal workspace + Shared.
- `or jobs list` (folder-scoped + generic fallback) → the faulted `AppRuntimeHost` job is the most recent row.
- `or jobs get <key>` → `State: Faulted`, `Info` = `System.AggregateException ... ---> System.Activities.WorkflowApplicationException: SignalR: Invalid SessionId:  OR Orchestrator Url: `, frame `InitializeHubConnection.ExecuteAsync`.
- `or jobs logs <key> --level Error` → the same exception.
- `or jobs history <key>` → Pending → Running → Faulted (~3s).
- `or jobs traces <key>` and `traces spans get` (both forms) → RobotJob span + Initialize Apps Hub Connection span (`SessionId = ""`).
- `docsai ask` → passthrough.

## Provenance

Hand-built faithful-replay. A live repro was not stageable: the WorkflowEvents activities only execute inside the UiPath Apps / Studio Web runtime, there is no CLI path to drive a Studio Web app preview into a blank-session state, and the package is not in a tenant feed. Built from signatures mined verbatim from the `UiPath.WorkflowEvents.Activities` source — the `SignalR: Invalid SessionId: {sessionId} OR Orchestrator Url: {url}` `WorkflowApplicationException` thrown synchronously in `InitializeHubConnection.ExecuteAsync`, and the source fact that the background `StartConnectionAsync` swallows transport errors (so the job-faulting `AggregateException` is the synchronous bootstrap). Keys are synthetic; host → `MOCK-HOST`, identities → `original_user` / `original_email@test.com` / `UIPATH\REPLACEMENT_USER`.

## Success criteria

`skill_triggered` + `llm_judge` against `RESOLUTION.md` (canonical lean judge, threshold 0.7).
