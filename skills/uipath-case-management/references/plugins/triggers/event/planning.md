# event trigger — Planning

A case-level trigger that fires on an external connector event (e.g., "new Salesforce opportunity created", "Jira issue transitioned"). Starts the case when the event matches a filter.

This plugin is **schema-data-driven** — one plugin covers every connector. The resolution pipeline is shared with the `connector-trigger` task plugin. See [connector-integration.md](../../../connector-integration.md).

## When to Use

Pick this plugin when the sdd.md describes the case as starting in response to an external event:

- "When a new row is added in Salesforce"
- "On each new Jira issue with priority High"
- "When a file is uploaded to SharePoint"

Distinguish from:

- **User-initiated start** → [manual](../manual/planning.md)
- **Scheduled start** → [timer](../timer/planning.md)
- **In-stage event wait** → [connector-trigger task](../../tasks/connector-trigger/planning.md)

## Required Fields from sdd.md

| Field | Source | Notes |
|-------|--------|-------|
| `display-name` | sdd.md (optional) | Defaults to `Trigger N` |
| `type-id` | `uiPathActivityTypeId` from TypeCache triggers | |
| `connection-id` | Connection UUID from `get-connection` | |
| `connector-key` | `Config.connectorKey` | Recorded for debugging |
| `object-name` | `Config.objectName` | Recorded for debugging |
| `event-params` | sdd.md event parameters | JSON object |
| `filter` | sdd.md filter description | Translated to connector's filter DSL |

## Resolution Pipeline

Follow the full procedure in [connector-integration.md](../../../connector-integration.md) using the **trigger** TypeCache (`typecache-triggers-index.json`):

1. **Find `uiPathActivityTypeId`** by reading the cache file directly.
2. **Resolve connector metadata** (`connectorKey`, `objectName`).
3. **Resolve the connection** — if `Connections` is empty, mark `<UNRESOLVED: no IS connection for <connectorKey>>` in `tasks.md`. **Event triggers do not support the skeleton pattern** — without a connector there is no trigger configuration, and a bare trigger node has no entry semantics. The implementation phase skips `triggers add-event` and falls back to the auto-created Trigger node (from `cases add` in T01) as the case entry point. Document the missing event trigger in the completion report so the user adds it after registering the connector + connection.
4. **(Optional) Describe trigger schema** when the event needs specific field wiring.

## Filter Translation

Convert sdd.md natural language to the connector's filter DSL. See [connector-integration.md](../../../connector-integration.md#filter-expression-syntax) for syntax.

## tasks.md Entry Format

```markdown
## T02: Configure event trigger "<display-name>"
- type-id: <uiPathActivityTypeId>
- connection-id: <connection-uuid>
- connector-key: <connectorKey>
- object-name: <objectName>
- event-params: {"project":"PROJ"}
- filter: "((fields.status=`Open`))"
- order: after T01
- verify: Confirm Result: Success, capture TriggerId
```
