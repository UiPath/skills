# connector-trigger task — Planning

A connector-based trigger **inside a stage**. This file owns only task selection, placement fields, the T-entry envelope, and the task placeholder. Read the shared metadata owner directly: [connector-trigger-planning.md](../../../connector-trigger-planning.md).

## When to Use

Pick this plugin when the sdd.md describes a task that **suspends the stage until an external event fires**:

- "Wait until a new row appears in Salesforce"
- "Continue when a Slack reaction is added"
- "Suspend until an email arrives in Inbox"

Do not select it for a case-start event, an outbound connector call, or a timer wait; the connector selector routes those targets.

## Resolution Pipeline

Follow [connector-trigger-planning.md § Planning Pipeline](../../../connector-trigger-planning.md#planning-pipeline), then emit only this task's T-entry below.

## tasks.md Entry Format

Populate `outputs:` using the shared [I/O-binding output-list contract](../../variables/io-binding/planning.md#canonical-tasksmd-output-list).

```markdown
## T<n>: Add connector-trigger task "<display-name>" to "<stage>"
- type-id: <uiPathActivityTypeId>
- connection-id: <connection-uuid>
- connector-key: <connectorKey>
- object-name: <objectName>
- event-operation: <eventOperation>
- event-mode: <polling|webhooks>
- input-values: {"eventParameters": {"parentFolderId": "AAMkADNm..."}}
- filter: {"groupOperator":"And","index":0,"uuId":null,"filters":[{"id":"subject","operator":"Contains","value":{"isLiteral":true,"rawString":"\"urgent\"","value":"urgent"},"uiId":null}]}
- outputs:                            # optional; omit only when the SDD declares none
  - <SDD output row, copied verbatim>
- isRequired: true
- runOnlyOnce: false
- activation-mode: <copy the supplied/approved SDD activation mode>  # sequential | parallel | parallel-after-predecessor | event-triggered | adhoc | fan-in | conditional-gate
- entry-rule: <copy the matching supplied/approved SDD task-entry rule>  # legality: ../../conditions/task-entry-conditions/planning.md#phase-1-plan-presentation-contract
- rationale: "<copy the supplied/approved SDD rationale>"   # required
- order: after T<m>
- lane: <n>
- verify: Confirm task created with correct event parameters
```

Task type never supplies activation semantics. Copy the SDD pair losslessly: a stage-entry listener uses `parallel` + `current-stage-entered`; a listener after an immediate predecessor uses `parallel-after-predecessor` + `runs-sequentially`; an event-gated task uses `event-triggered` + `wait-for-connector`; any other explicitly authored legal task-entry rule remains authoritative.

## Unresolved Fallback

Enter fallback only when the common owner assigns a TypeCache zero to placeholder or connection creation is declined/fails. Empty `Connections` is not a Rule 17 zero and must receive the common owner's creation offer first.

Then:
- Mark `type-id` or `connection-id` with `<UNRESOLVED: reason>`
- Omit `input-values:` and `filter:`
- Execution creates a placeholder task (display-name + type only) per [placeholder-tasks.md](../../../placeholder-tasks.md)

<!-- END: planning.md -->
