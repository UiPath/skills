# Failure Modes

## Missing diagram

Studio Web import rejects BPMN without a valid diagram and plane.
Add `bpmndi:BPMNDiagram`, `bpmndi:BPMNPlane`, shapes for nodes, and edges for sequence flows.

## Orphaned diagram plane

A diagram plane references a process, collaboration, or subprocess that no longer exists.
Point the plane to a valid element or remove the orphaned diagram.

## Missing shape or waypoint

Rendered elements without BPMN DI may parse but fail to render correctly. Add bounds for nodes and waypoints for edges.

## Entry point mismatch

Entry point inputs reference a start event through `elementId`, but the start event lacks the matching
`uipath:entryPointId` or the ID is duplicated.
Fix root start event extensions and variable scoping.

## Binding reference missing

A node context value refers to `=bindings.<id>` but no matching root binding or generated binding resource exists.
Fix the BPMN binding source or rerun CLI enrichment/generation.

## Integration Service draft executed

An Integration Service activity or trigger was left as model-authored draft intent and reached upload/debug/run without
CLI enrichment.
Enrich connector metadata, connection binding, dynamic schemas, and generated resources before operating.

Signs:

- Incident points at a connector activity/event.
- Runtime variables show missing or malformed connector output.
- Deployed BPMN still contains draft intent rather than registry-backed `uipath:activity` or `uipath:event` metadata.
- `bindings_v2.json` lacks the corresponding generated binding resource.

Fix ownership: CLI enrichment/generation owns connector metadata, connection binding, dynamic schemas,
and generated package resources.
The model may adjust BPMN structure around the connector but must not invent connection IDs or private connector payloads.

## Stale generated package files

Generated JSON no longer reflects the BPMN source.
Regenerate package metadata and verify package descriptor file mappings before upload or deploy.

Signs:

- `entry-points.json` references an old start event ID or BPMN file.
- `package-descriptor.json` omits the current BPMN or generated JSON file mapping.
- `operate.json` contains stale runtime metadata.
- `bindings_v2.json` does not match executable binding references in the BPMN.

Fix ownership: change `.bpmn` only when the source is wrong; otherwise rerun the supported CLI package/enrichment path.

## Invalid gateway defaults

Exclusive or inclusive gateways have ambiguous conditions, missing defaults, or a default flow that points to the wrong
sequence flow.
Fix outgoing conditions and default references.

Runtime symptom: the instance stalls or takes an unexpected branch.
Diagnose with variables at the gateway, element executions, and cursors before changing conditions.

## Boundary error mismatch

A boundary error event references a missing or duplicate error definition, or is attached to an invalid activity.
Reconcile the error definition within the correct scope.

## Multi-instance variable mismatch

A multi-instance activity references an input collection or item variable that is not declared in the expected scope.
The process may parse, then fail or stall when the loop starts because the runtime cannot bind per-item state.

Signs:

- `uipath:loopCharacteristics` uses an `inputCollection` expression that does not match a declared variable.
- `inputElement` points at an undeclared item variable or a variable that is reused for unrelated state.
- A completion condition mutates state instead of evaluating state.
- Per-item output mappings target variables that are not declared in the subprocess or root scope.

Fix ownership: declare collection and item variables in `.bpmn`, keep item and aggregate outputs distinct,
and model retry/error behavior as visible BPMN paths rather than hidden loop metadata.

## Message reference mismatch

A catch, throw, or receive event references a message ID that is missing, renamed, or no longer matches the runtime
message contract.

Runtime symptom: the instance waits indefinitely at a message event or faults during event subscription.
Diagnose with cursors and element executions, then reconcile the `bpmn:message`, `messageRef`, and any
`uipath:event` message context in BPMN source.

## Expression treated as literal

An expression field is authored as a plain literal string.
Use expression form where Maestro expects evaluation, and avoid assignment operators in fields where
validation forbids assignment.

## Deployed asset differs from local BPMN

The local `.bpmn` does not match the deployed asset fetched from the faulted instance.
This happens after republish, branch switching, package reuse, or local edits made after deployment.

Diagnose what actually ran:

```bash
uip maestro bpmn instance asset <INSTANCE_ID> -f <FOLDER_KEY> --output json
```

Fix ownership: correlate the incident to deployed BPMN first.
Then decide whether to re-author local BPMN, republish, or operate the existing instance.

## Runtime state stuck at event or gateway

The instance has no active fault but is not progressing.
Inspect cursors and element executions before using lifecycle actions:

```bash
uip maestro bpmn instance cursors <INSTANCE_ID> -f <FOLDER_KEY> --output json
uip maestro bpmn instance element-executions <INSTANCE_ID> -f <FOLDER_KEY> --output json
```

Common causes include a message/event wait without the expected signal, a timer configuration mismatch,
gateway conditions that never evaluate true, or a subprocess dependency waiting externally.
Cursor movement is an Operate action and requires explicit user consent.
