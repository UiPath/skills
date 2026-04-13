# Wait-for-Connector Task — Implementation

Requires CLI enrichment. Do not hand-write `serviceType`, `context`, `inputs`, or `outputs`.

## Step 1 — Preview Schema

```bash
uip case tasks describe \
  --type connector-trigger \
  --id <typeId> \
  --connection-id <connectionId> \
  --output json
```

## Step 2 — Add the Enriched Task

```bash
uip case tasks add-connector <file> <stage-id> \
  --type trigger \
  --type-id <typeId> \
  --connection-id <connectionId> \
  --display-name "Wait for Jira Event" \
  --lane 0 \
  --output json
```

With event parameters:
```bash
uip case tasks add-connector <file> <stage-id> \
  --type trigger \
  --type-id <typeId> \
  --connection-id <connectionId> \
  --input-values '{"body": {"project": "PROJ"}}' \
  --output json
```

With filter expression:
```bash
uip case tasks add-connector <file> <stage-id> \
  --type trigger \
  --type-id <typeId> \
  --connection-id <connectionId> \
  --filter "((fields.status<`Done`>))" \
  --output json
```

## What Gets Written

```json
{
  "id": "t<8chars>",
  "elementId": "<stageId>-t<8chars>",
  "displayName": "Wait for Jira Event",
  "type": "wait-for-connector",
  "data": {
    "serviceType": "Intsvc.WaitForEvent",
    "context": [
      { "name": "connectorKey", "value": "uipath-atlassian-jira", "type": "string" },
      { "name": "connection",   "value": "=bindings.<connectionBindingId>", "type": "string" },
      { "name": "resourceKey",  "value": "<connectionId>", "type": "string" },
      { "name": "folderKey",    "value": "=bindings.<folderKeyBindingId>", "type": "string" },
      { "name": "operation",    "value": "ISSUE_UPDATED", "type": "string" },
      { "name": "objectName",   "value": "Issue", "type": "string" },
      { "name": "method",       "value": "", "type": "string" },
      { "name": "path",         "value": "", "type": "string" },
      { "name": "metadata",     "type": "json", "body": { ... } }
    ],
    "inputs": [
      { "name": "body", "type": "json", "body": { "filters": { "expression": "" }, "parameters": {} } }
    ],
    "outputs": [
      { "name": "response", "type": "jsonSchema", "source": "=response", "_jsonSchema": { ... } },
      { "name": "Error",    "type": "json",       "source": "=error" }
    ],
    "bindings": []
  },
  "entryConditions": [
    { "id": "Condition_<6chars>", "displayName": "Stage entered", "rules": [[{ "rule": "current-stage-entered", "id": "Rule_<6chars>" }]] }
  ]
}
```

Key difference from execute-connector-activity: `serviceType` is `"Intsvc.WaitForEvent"` and `inputs` uses the trigger body format with `filters` and `parameters`.
