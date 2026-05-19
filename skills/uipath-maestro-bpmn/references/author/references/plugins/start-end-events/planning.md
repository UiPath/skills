# Start, End, and Event Planning

Use this reference when planning BPMN start events, end events, intermediate events, and boundary events.

## When to use

- Manual, timer, message, or trigger-driven starts.
- Normal, terminate, error, or message ends.
- Intermediate catch or throw events in the process body.
- Boundary events attached to activities for timeout, error, or message paths.

## Planning steps

1. Identify whether the event starts work, waits for work, throws a notification, handles an exception, or finishes the process.
2. Choose the BPMN event type and event definition before adding UiPath metadata.
3. Determine scope: root process, subprocess, event subprocess, or activity boundary.
4. Decide entry point status for root start events and list required entry variables.
5. Plan event outputs and mappings to process variables.
6. Record any runtime resource that needs CLI enrichment, especially connector-backed triggers or waits.
7. Plan outgoing sequence flows, boundary escape paths, and end-state outputs.

## Model may draft

- Standard BPMN event elements and event definitions.
- `uipath:entryPointId` for runnable root start events.
- Public-safe IDs, labels, mappings, and diagram geometry.
- Message or error definitions with synthetic names.
- Boundary attachment and interrupting versus non-interrupting intent.

## Stop conditions

Stop before Operate when an event depends on unresolved connector metadata, trigger properties, dynamic schema, real message correlation contract, or private identifiers.

Do not generate event definitions listed in
[supported-elements.md](../../supported-elements.md#current-generation-exclusions)
for new source. Preserve imported instances and report them as unsupported for
regeneration.
