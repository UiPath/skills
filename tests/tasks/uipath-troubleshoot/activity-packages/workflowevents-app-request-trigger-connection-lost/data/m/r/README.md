# workflowevents-app-request-trigger-connection-lost

Faithful-replay scenario: a UiPath-App-invoked job faults at the internal `AppRequestTrigger` activity (`UiPath.WorkflowEvents.Activities`) with `System.TimeoutException` — the SignalR connection between the App and the robot never established within 60 seconds.

## What this exercises

The agent must recognise this as an App↔robot **channel establishment** failure (the App never connected / the hub was unreachable), not an in-workflow error, not a `HandleAppRequest` null reference, and not an `InitializeHubConnection` bootstrap failure. Disambiguation evidence: the `Apps Request Trigger` span shows `ConnectionMode = SignalR` and there is no invoke-workflow child span (no request was ever received). Tests playbook `activity-packages/workflowevents-activities/playbooks/app-request-trigger-connection-lost.md`.

## Evidence in the fixtures

- `or folders list` → personal workspace + Shared.
- `or jobs list` (folder-scoped + generic fallback) → the faulted `RequestListener` job is the most recent row.
- `or jobs get <key>` → `State: Faulted`, `Info` = `System.TimeoutException: SignalR connection did not establish within 60 seconds. Current state: Connecting`, frames `HubConnectionService.EnsureChannelConnectedAsync` → `AppRequestTrigger.GetWorkflowRequest` → bookmark `Throw`.
- `or jobs logs <key> --level Error` → the same exception.
- `or jobs history <key>` → Pending → Running → Faulted (~66s, reflecting the 60s establish wait).
- `or jobs traces <key>` and `traces spans get` (both forms) → RobotJob span + Apps Request Trigger span (`ConnectionMode = SignalR`).
- `docsai ask` → passthrough.

## Provenance

Hand-built faithful-replay. A live repro was not stageable: the WorkflowEvents activities only execute inside the UiPath Apps / Studio Web runtime, there is no CLI path to drive a UiPath App, and the package is not in a tenant feed. Built from signatures mined verbatim from the `UiPath.WorkflowEvents.Activities` source — the 60s timeout message and `Current state:` interpolation in `HubConnectionService.EnsureChannelConnectedAsync`, and the `AppRequestTrigger.GetWorkflowRequest` → bookmark `Throw` fault path. Keys are synthetic; host → `MOCK-HOST`, identities → `original_user` / `original_email@test.com` / `UIPATH\REPLACEMENT_USER`.

## Success criteria

`skill_triggered` + `llm_judge` against `RESOLUTION.md` (canonical lean judge, threshold 0.7).
