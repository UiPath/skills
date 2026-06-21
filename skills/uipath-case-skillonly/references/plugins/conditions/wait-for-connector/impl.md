# Wait-for-Connector Condition — Implementation

`wait-for-connector` conditions wait for an Integration Service event (email, Teams message, webhook, etc.) before activating a stage or task.

> **Do not hand-write the full `uipath` object.** The connector metadata, inputs schema, and outputs schema are complex and version-sensitive. Use CLI enrichment to generate the structure, then edit only the parameter values.

## CLI Enrichment (Recommended)

For stage entry conditions, the recommended flow is:

1. Write a placeholder condition with `rule: "wait-for-connector"` and empty `uipath: {}`
2. Run CLI to enrich the condition with connector metadata
3. Edit the generated `inputs` to set parameter values

```bash
# Get connector info and connection
uip case registry get-connector --type typecache-triggers \
  --activity-type-id "<uiPathActivityTypeId>" --output json

uip case registry get-connection --type typecache-triggers \
  --activity-type-id "<uiPathActivityTypeId>" --output json
```

## Full JSON Schema

When CLI enrichment isn't available or you need to hand-write, here's the complete structure:

```json
{
  "id": "Condition_<6chars>",
  "displayName": "Wait for Teams message",
  "isInterrupting": true,
  "rules": [[
    {
      "id": "Rule_<6chars>",
      "rule": "wait-for-connector",
      "uipath": {
        "serviceType": "Intsvc.WaitForEvent",
        "context": [
          {
            "name": "connectorKey",
            "value": "uipath-microsoft-teams",
            "type": "string"
          },
          {
            "name": "connection",
            "value": "=bindings.<connectionBindingId>",
            "type": "string"
          },
          {
            "name": "folderKey",
            "value": "=bindings.<folderKeyBindingId>",
            "type": "string"
          },
          {
            "name": "resourceKey",
            "value": "<connectionId>",
            "type": "string"
          },
          {
            "name": "operation",
            "value": "NEW_MESSAGE_IN_CHANNEL",
            "type": "string"
          },
          {
            "name": "objectName",
            "value": "teams::channels::messages",
            "type": "string"
          },
          {
            "name": "metadata",
            "body": {
              "designTimeMetadata": { ... },
              "metadataState": { "jsonSchema": { ... } },
              "telemetryData": { ... },
              "inputMetadata": {},
              "errorState": { "hasError": false },
              "bindings": []
            },
            "type": "json"
          },
          {
            "name": "activityConfigurationVersion",
            "value": "v1",
            "type": "string"
          }
        ],
        "inputs": [
          {
            "name": "body",
            "type": "json",
            "target": "body",
            "body": {
              "parameters": {
                "teamId": "<team-uuid>",
                "channelId": "<channel-id>"
              }
            },
            "id": "<inputId>",
            "var": "<inputId>",
            "elementId": "<stageId>-<ruleId>"
          }
        ],
        "outputs": [
          {
            "name": "id",
            "var": "id",
            "type": "string",
            "source": "=response.id",
            "id": "id",
            "value": "id",
            "elementId": "<stageId>-<ruleId>"
          },
          {
            "name": "response",
            "var": "response",
            "type": "jsonSchema",
            "source": "=response",
            "id": "response",
            "value": "response",
            "elementId": "<stageId>-<ruleId>",
            "body": { /* JSON schema of response */ }
          }
        ],
        "bindings": []
      }
    }
  ]]
}
```

## Connection Bindings (Required)

Before using `wait-for-connector`, declare Connection bindings at `root.data.uipath.bindings`:

```json
{
  "id": "b<8chars>",
  "name": "<connector-name> connection",
  "type": "string",
  "resource": "Connection",
  "resourceKey": "<connectionId>",
  "default": "<connectionId>",
  "propertyAttribute": "ConnectionId"
},
{
  "id": "b<8chars>",
  "name": "FolderKey",
  "type": "string",
  "resource": "Connection",
  "resourceKey": "<connectionId>",
  "default": "<folderKey>",
  "propertyAttribute": "folderKey"
}
```

Reference these bindings in the condition's `context`:
- `connection`: `"=bindings.<connectionBindingId>"`
- `folderKey`: `"=bindings.<folderKeyBindingId>"`

## Context Fields Reference

| Field | Required | Value |
|-------|----------|-------|
| `connectorKey` | ✓ | Connector identifier (e.g., `uipath-microsoft-teams`, `uipath-microsoft-outlook365`) |
| `connection` | ✓ | Binding reference to ConnectionId |
| `folderKey` | ✓ | Binding reference to folder key |
| `resourceKey` | ✓ | The connection UUID |
| `operation` | ✓ | Event operation (e.g., `NEW_MESSAGE_IN_CHANNEL`, `MAIL_RECEIVED`) |
| `objectName` | ✓ | Object path (e.g., `teams::channels::messages`, `outlook::mail::messages`) |
| `metadata` | ✓ | Complex object with design-time metadata and JSON schema — use CLI enrichment |
| `activityConfigurationVersion` | ✓ | Currently `"v1"` |

## Common Connector Operations

| Connector | Operation | Object Name |
|-----------|-----------|-------------|
| `uipath-microsoft-teams` | `NEW_MESSAGE_IN_CHANNEL` | `teams::channels::messages` |
| `uipath-microsoft-outlook365` | `MAIL_RECEIVED` | `outlook::mail::messages` |
| `uipath-uipath-dataservice` | `ENTITY_CREATED` | `dataservice::entities::<entityName>` |

## isInterrupting

Set `isInterrupting: true` on the condition (not the rule) when the connector event should interrupt the current stage mid-execution. This is common for ExceptionStage entries where an external event redirects the case flow.

```json
{
  "id": "Condition_<6chars>",
  "displayName": "Customer responded",
  "isInterrupting": true,
  "rules": [[{ "rule": "wait-for-connector", ... }]]
}
```

## Condition Scopes

### Stage Entry

Most common use — ExceptionStage activated by external event:

```json
"entryConditions": [
  {
    "id": "Condition_<6chars>",
    "displayName": "Customer email received",
    "isInterrupting": true,
    "rules": [[{
      "rule": "wait-for-connector",
      "id": "Rule_<6chars>",
      "uipath": { /* ... */ }
    }]]
  }
]
```

### Task Entry

Task waits for connector event before starting:

```json
"entryConditions": [
  {
    "id": "Condition_<6chars>",
    "displayName": "Wait for approval email",
    "rules": [[{
      "rule": "wait-for-connector",
      "id": "Rule_<6chars>",
      "uipath": { /* ... */ }
    }]]
  }
]
```

### Stage Exit

Stage exits when connector event fires:

```json
"exitConditions": [
  {
    "id": "Condition_<6chars>",
    "displayName": "Exit on customer response",
    "type": "exit-only",
    "marksStageComplete": true,
    "rules": [[{
      "rule": "wait-for-connector",
      "id": "Rule_<6chars>",
      "uipath": { /* ... */ }
    }]]
  }
]
```

## Anti-patterns

- **Do not hand-write the `metadata.body` object** — it contains versioned JSON schemas that must match the connector's current definition. Use CLI enrichment.
- **Do not omit Connection bindings** — the `=bindings.<id>` references require corresponding entries at `root.data.uipath.bindings`.
- **Do not forget `elementId`** on inputs/outputs — format is `<stageId>-<ruleId>` (not `<stageId>-<taskId>`).
