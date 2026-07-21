---
confidence: medium
---

# Get Queue Item / Set Transaction Status Failed — Orchestrator Queue Activities

## Context

A modern Orchestrator queue activity (`Get Queue Item` / `Get Transaction Item`, `Set Transaction Status`, or `Add Queue Item`) from `UiPath.System.Activities` faulted — either on client-side input validation or on the Orchestrator API call. Storage-bucket activities (`Get / Upload / Delete Storage File`) share the same "not connected" and API-error modes below.

> For the classic `Add Queue Item` activity (`UiPath.Core.Activities` — "Queue name may not be null or empty", reserved-character keys, duplicate keys), use [classic-activities/add-queue-item-failed.md](../../classic-activities/playbooks/add-queue-item-failed.md). For `Get Asset` / `Get Credential`, use the get-asset playbooks in this package.

What this looks like:
- `Queue Name is required.` (`ArgumentValueNotSetException`) — the `QueueName` input was empty/unresolved.
- `Reason is required when Status is Failed` (`ArgumentException`) — `Set Transaction Status` set to Failed without a Reason.
- `Service URL is empty.` (`InvalidOperationException`) — the activity ran with no Orchestrator connection (no service URL): executed outside a robot context, or the robot is not connected to Orchestrator.
- `OrchestratorHttpException: Status code: 404 (Not Found). Orchestrator response: <name> does not exist. Error code: 1002` — the queue does not exist in the job's folder. In a faulted job this surfaces under the header `HTTP Error` with `ErrorCode: System.Utilities.Sys.HttpError`.
- A `TimeoutException`, or another wrapped Orchestrator error (HTTP status / message) — connectivity, permission, or the queue/bucket not existing in the job's folder.

What can cause it:
- A required input (`QueueName`, or the `Reason` on a Failed transaction) resolved to empty/null from an unset variable/argument.
- The workflow ran without a connected robot / Orchestrator context, so no service URL was available (common when run from Studio without a robot connection, or in a unit test).
- The queue or storage bucket does not exist in the Orchestrator folder where the job runs, or the robot account lacks permission on it.
- Network / session issues between the robot and Orchestrator, producing an HTTP error or timeout.

What to look for:
- The message plus the resolved `QueueName` (or bucket name) and the folder the job ran in.
- Whether the job ran on a connected robot (a `Service URL is empty.` fault means it did not have an Orchestrator connection at all).
- The HTTP status / error text if Orchestrator returned one; whether the queue/bucket exists in that folder and the robot has rights to it.

## Investigation

1. Capture the message and classify it: required-input-empty, `Reason`-missing, `Service URL is empty` (no connection), or an Orchestrator API error/timeout.
2. For a validation error, inspect the named input (`QueueName`, `Reason`) and trace an empty value to the upstream step that should set it.
3. For `Service URL is empty.`, confirm the workflow runs on a robot connected to Orchestrator — not a bare Studio/unit-test run without a connection.
4. For an API error/timeout, read the HTTP status/message; confirm the queue or bucket exists in the job's folder and the robot account has permission on it.

## Resolution

### `Queue Name is required.` / `Reason is required when Status is Failed`
Set the missing input — populate `QueueName`, or supply a `Reason` when setting a transaction to Failed — and ensure the upstream variable/argument that feeds it is set.

### `Service URL is empty.`
Run the workflow on a robot connected to Orchestrator so a service URL is available. If it is executing outside a robot context (Studio run without a connection, or a test harness), connect the robot / provide the Orchestrator connection before the queue activity runs.

### Orchestrator API error / timeout / not-found / permission
Confirm the queue or storage bucket exists in the folder where the job runs (create it there or run the job in the correct folder); grant the robot account permission on the queue/bucket in that folder; and address robot↔Orchestrator connectivity for HTTP/timeout errors, then retry.
