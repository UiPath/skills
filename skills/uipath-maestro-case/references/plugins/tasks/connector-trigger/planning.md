# connector-trigger task — Planning

A connector-based trigger **inside a stage** — waits for an external event before continuing.

The planning pipeline is shared with the [event trigger](../../triggers/event/planning.md) — see [connector-trigger-common.md](../../../connector-trigger-common.md) for the full 7-step resolution pipeline.

## When to Use

Pick this plugin when the sdd.md describes a task that **suspends the stage until an external event fires**:

- "Wait until a new row appears in Salesforce"
- "Continue when a Slack reaction is added"
- "Suspend until an email arrives in Inbox"

Distinguish from:

- **Case-level event triggers** (start the case from outside) → [`plugins/triggers/event/`](../../triggers/event/planning.md)
- **Connector activity** (call out, don't wait) → [connector-activity](../connector-activity/planning.md)
- **Timer wait** (not connector-driven) → [wait-for-timer](../wait-for-timer/planning.md)

## Resolution Pipeline

Follow the 7-step pipeline in [connector-trigger-common.md](../../../connector-trigger-common.md#planning-pipeline). All steps are identical for both in-stage triggers and case-level event triggers.

## tasks.md Entry Format

```markdown
## T<n>: Add connector-trigger task "<display-name>" to "<stage>"
- type-id: <uiPathActivityTypeId>
- connection-id: <connection-uuid>
- connector-key: <connectorKey>
- object-name: <objectName>
- event-operation: <eventOperation>
- event-mode: <polling|webhooks>
- input-values: {"parentFolderId": "AAMkADNm..."}
- filter: "(contains(subject, 'urgent'))"
- isRequired: true
- runOnlyOnce: false
- order: after T<m>
- lane: <n>
- verify: Confirm task created with correct event parameters
```

## Unresolved Fallback

If the connector or connection cannot be resolved:
- Mark `type-id` or `connection-id` with `<UNRESOLVED: reason>`
- Omit `input-values:` and `filter:`
- Execution creates a skeleton task (display-name + type only) per [skeleton-tasks.md](../../../skeleton-tasks.md)
