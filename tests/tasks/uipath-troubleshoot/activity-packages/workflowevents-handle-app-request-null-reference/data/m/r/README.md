# workflowevents-handle-app-request-null-reference

Faithful-replay scenario: a workflow invoked by a UiPath App faults at the internal `HandleAppRequest` activity (`UiPath.WorkflowEvents.Activities`) with `System.NullReferenceException`, because a null was dereferenced **inside the App-invoked workflow** (an input argument the App did not bind).

## What this exercises

The agent must recognise that `HandleAppRequest` is internal Apps machinery that *runs* the invoked workflow and *surfaces* its exception — so the NRE originates in the workflow / its input contract, not in the WorkflowEvents package and not in the App↔robot SignalR channel. The disambiguation evidence is in the spans: the `Handle Apps Request` span carries `WorkflowFile = ProcessRequest.xaml`, and the faulting Assign span carries `Value = io_Records.Rows.Count`. Tests playbook `activity-packages/workflowevents-activities/playbooks/handle-app-request-null-reference.md`.

## Evidence in the fixtures

- `or folders list` → personal workspace + Shared.
- `or jobs list` (folder-scoped + generic fallback) → the faulted `RequestHandler` job is the most recent row.
- `or jobs get <key>` → `State: Faulted`, `Info` with the NRE and the `UiPath.WorkflowEvents.Activities.HandleAppRequest.EndExecute` faulting frame.
- `or jobs logs <key> --level Error` → the same exception as a single Error row.
- `or jobs history <key>` → Pending → Running → Faulted.
- `or jobs traces <key>` and `traces spans get` (both forms) → RobotJob span (NRE stack) + Handle Apps Request span (`FullTypeName`, `WorkflowFile`, `ConnectionMode`) + faulting Assign span.
- `docsai ask` → passthrough.

## Provenance

Hand-built faithful-replay. A live repro was not stageable: the WorkflowEvents activities only execute inside the UiPath Apps / Studio Web runtime (not a plain published process), there is no CLI path to drive a UiPath App, and the package is not in a tenant feed. Per the validation-pipeline guidance, this scenario is built from signatures and stack frames mined verbatim from the `UiPath.WorkflowEvents.Activities` source (`HandleAppRequest.EndExecute`; the workflow-executor boundary; the standard `System.NullReferenceException` framework message). Job/folder/process/org/tenant keys are synthetic; host → `MOCK-HOST`, identities → `original_user` / `original_email@test.com` / `UIPATH\REPLACEMENT_USER`.

## Success criteria

`skill_triggered` + `llm_judge` against `RESOLUTION.md` (canonical lean judge, threshold 0.7).
