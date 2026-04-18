# connector-trigger task — Planning

A connector-based trigger **inside a stage** — waits for an external event (e.g., "issue created in Jira", "message posted to Slack channel") before continuing.

This plugin is **schema-data-driven** — one plugin covers every connector trigger. Per-connector shapes are discovered via `tasks describe --connection-id`. See [connector-integration.md](../../../connector-integration.md) for the shared resolution pipeline.

## When to Use

Pick this plugin when the sdd.md describes a task that **suspends the stage until an external event fires**. Typical patterns:

- "Wait until a new row appears in Salesforce"
- "Continue when a Slack reaction is added"
- "Suspend until a Jira issue is transitioned"

Distinguish from:

- **Case-level event triggers** (start the case from outside) → [`plugins/triggers/event/`](../../triggers/event/planning.md)
- **Connector activity** (call out, don't wait) → [connector-activity](../connector-activity/planning.md)
- **Timer wait** (not connector-driven) → [wait-for-timer](../wait-for-timer/planning.md)

## Required Fields from sdd.md

| Field | Source | Notes |
|-------|--------|-------|
| `display-name` | sdd.md task name | |
| `type-id` | `uiPathActivityTypeId` from TypeCache triggers | |
| `connection-id` | Connection UUID | |
| `connector-key` | `Config.connectorKey` | Recorded for debugging |
| `object-name` | `Config.objectName` | Recorded for debugging |
| `input-values` | sdd.md task data mapping | Event params |
| `filter` | sdd.md filter description | Translated to the connector's filter DSL |
| `isRequired` | sdd.md (default `true`) | |

## Resolution Pipeline

Same as [connector-activity/planning.md](../connector-activity/planning.md), but using the **trigger** TypeCache (`typecache-triggers-index.json`). Follow the full procedure in [connector-integration.md](../../../connector-integration.md) — use `--type typecache-triggers` for each call.

## Filter Translation

Translate the sdd.md natural-language filter to the connector's filter DSL. See [connector-integration.md](../../../connector-integration.md#filter-expression-syntax).

Example:
- sdd.md: "wait for an issue where status is Open"
- filter: `` ((fields.status=`Open`)) ``

If the filter cannot be translated unambiguously, ask the user.

## tasks.md Entry Format

```markdown
## T<n>: Add connector-trigger task "<display-name>" to "<stage>"
- type-id: <uiPathActivityTypeId>
- connection-id: <connection-uuid>
- connector-key: <connectorKey>
- object-name: <objectName>
- input-values: {"body":{"project":"PROJ"}}
- filter: "((fields.status=`Open`))"
- isRequired: true
- order: after T<m>
- lane: <n>  # FE layout coordinate; increment per task within the stage
- verify: Confirm Result: Success, capture TaskId
```
