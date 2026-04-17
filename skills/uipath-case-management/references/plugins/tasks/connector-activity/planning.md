# connector-activity task — Planning

A connector activity task inside a stage. Calls an external service (Jira, Slack, Salesforce, Gmail, etc.) via UiPath Integration Service.

This plugin is **schema-data-driven** — one plugin covers every connector. Connector-specific input shapes are discovered at runtime via `tasks describe --connection-id`, not baked into this plugin. See [connector-integration.md](../../../connector-integration.md) for the shared resolution pipeline.

## When to Use

Pick this plugin when the sdd.md describes a task as `CONNECTOR_ACTIVITY` or names a specific external service action (e.g., "send a Slack message", "create a Jira issue", "update Salesforce opportunity").

For **connector-based triggers** inside a stage (wait for an external event), use [connector-trigger](../connector-trigger/planning.md).

For **case-level event triggers** (outside any stage), use [`plugins/triggers/event/`](../../triggers/event/planning.md).

## Required Fields from sdd.md

| Field | Source | Notes |
|-------|--------|-------|
| `display-name` | sdd.md task name | |
| `type-id` | `uiPathActivityTypeId` from TypeCache | See pipeline below |
| `connection-id` | Connection UUID from `get-connection` | See pipeline below |
| `connector-key` | `Config.connectorKey` | Recorded for debugging |
| `object-name` | `Config.objectName` | Recorded for debugging |
| `input-values` | sdd.md task data mapping | JSON object matching schema from `describe` |
| `isRequired` | sdd.md (default `true`) | |

## Resolution Pipeline

Follow the full procedure in [connector-integration.md](../../../connector-integration.md). Summary of planning-time decisions:

1. **Find `uiPathActivityTypeId`** by reading `~/.uipcli/case-resources/typecache-activities-index.json` directly. Match on `displayName`. Skip entries without `uiPathActivityTypeId`.
2. **Resolve connector metadata** (`connectorKey`, `objectName`) via the `get-connector` call documented in [connector-integration.md § Step 2](../../../connector-integration.md).
3. **Resolve the connection** via the `get-connection` call documented in [connector-integration.md § Step 3](../../../connector-integration.md):
   - Single connection → use it.
   - Multiple connections → **AskUserQuestion** with names + "Something else".
   - Empty `Connections` → mark `<UNRESOLVED: no IS connection for <connectorKey>>` and omit `input-values:`. Execution creates a skeleton connector task — see [skeleton-tasks.md](../../../skeleton-tasks.md).
4. **(Optional) Describe the input schema** when sdd.md requires specific field wiring — see [connector-integration.md § Step 4](../../../connector-integration.md).

## Input-Values Shape

The `--input-values` JSON is connector-specific. Common top-level keys:

- `body` — request body fields
- `queryParameters` — query string parameters
- `pathParameters` — URL path parameters

Discover exact keys from the `describe` response. Use resolved IDs (not display names) where the connector schema requires references — see [connector-integration.md](../../../connector-integration.md#step-4--optional-describe-inputsoutputs).

## tasks.md Entry Format

```markdown
## T<n>: Add connector-activity task "<display-name>" to "<stage>"
- type-id: <uiPathActivityTypeId>
- connection-id: <connection-uuid>
- connector-key: <connectorKey>
- object-name: <objectName>
- input-values: {"body":{"field":"value"},"queryParameters":{"key":"val"}}
- isRequired: true
- order: after T<m>
- verify: Confirm Result: Success, capture TaskId
```
