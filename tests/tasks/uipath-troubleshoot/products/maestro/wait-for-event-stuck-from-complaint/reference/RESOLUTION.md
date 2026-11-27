# Resolution — the instances are waiting on a different case

## Root cause

The three instances are parked on a mid-process Wait-For-Event element,
`Wait for Case Updated`, and each waits for **one specific Salesforce case**.

The correlation filter on the trace is `(Id == '5008e00000AAAAA')`. The event
that arrived carries `id: 5008e00000ZZZZZ` — case `CASE-0042`. A different
record. So the trigger fetched an event, the filter rejected it, and the
instance stayed where it was.

Updating *a* case of the right type does not resume an instance waiting on
*another*. That is the whole mechanism.

## How to get there without an instance id

The reporter supplies only a process name and "running for hours". Nothing is
clickable.

1. `uip maestro bpmn instances list --status Running --to-date <now minus N hours>`
   — works tenant-wide, no folder or process key needed. `--to-date` filters on
   start time, so "started before T and still Running" is "stuck since T".
   Narrow with `--package-id` only because the reporter named the process.
   The rows also carry `Source: IntegrationTrigger`, which confirms the gate.
2. `uip traces spans get <instance-id>` — a Maestro instance id is its trace id.
   The waiting element is the span carrying `intSvcTriggerId`, with
   `elementType: ReceiveTask` and `elementExtensionType: Intsvc.WaitForEvent`.
3. `uip is trigger-traces list --instance-id <instance-id>` — resolves that
   trigger itself and queries with `source=maestro`; no folder needed.
4. `uip traces spans get <trace-id>` — the filter span holds the correlation
   expression and the payload that did arrive.

## What NOT to conclude

- Not a connection problem. The connection is `Enabled` and `IsConnected`.
- Not a dispatch problem. `correlated-jobs` cannot be used here at all: the
  endpoint authorizes against a folder with no `source=maestro` bypass, so a
  per-instance Wait-For-Event trigger has nothing to correlate. A Wait-For-Event
  resumes a running instance rather than starting a job.
- Not one shared trigger. Each stuck instance has its own `intSvcTriggerId`;
  never generalise one instance's cause to the rest without checking.

## Fix

Give the reporter the case id from the filter — `5008e00000AAAAA` — and have
them update that record. If the instances are waiting on the wrong key, the fix
is in the Wait-For-Event element's correlation, which is a process-design
change, not a runtime one.
