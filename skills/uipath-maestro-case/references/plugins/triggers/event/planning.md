# event trigger — Planning

A case-level trigger that fires on an external connector event. Starts the case when the event matches a filter.

The planning pipeline is shared with the [connector-trigger task](../../tasks/connector-trigger/planning.md) — see [connector-trigger-common.md](../../../connector-trigger-common.md) for the full 7-step resolution pipeline.

## When to Use

Pick this plugin when the sdd.md describes the case as starting in response to an external event:

- "When a new email arrives in Inbox"
- "On each new Jira issue with priority High"
- "When a file is uploaded to SharePoint"

Distinguish from:

- **User-initiated start** → [manual](../manual/planning.md)
- **Scheduled start** → [timer](../timer/planning.md)
- **In-stage event wait** → [connector-trigger task](../../tasks/connector-trigger/planning.md)

## Resolution Pipeline

Follow the 7-step pipeline in [connector-trigger-common.md](../../../connector-trigger-common.md#planning-pipeline). All steps are identical for both event triggers and in-stage connector-trigger tasks.

## tasks.md Entry Format

```markdown
## T02: Configure event trigger "<display-name>"
- type-id: <uiPathActivityTypeId>
- connection-id: <connection-uuid>
- connector-key: <connectorKey>
- object-name: <objectName>
- event-operation: <eventOperation>
- event-mode: <polling|webhooks>
- input-values: {"parentFolderId": "AAMkADNm..."}
- filter: "(contains(subject, 'urgent'))"
- order: after T01
- verify: Confirm trigger configured with correct event parameters
```

## Unresolved Fallback

If the connector or connection cannot be resolved:
- Mark `type-id` or `connection-id` with `<UNRESOLVED: reason>`
- Omit `input-values:` and `filter:`
- **Event triggers do not support the skeleton pattern** — implementation skips the trigger, and the default `trigger_1` node remains as the case entry point
- Document the missing trigger in the completion report
