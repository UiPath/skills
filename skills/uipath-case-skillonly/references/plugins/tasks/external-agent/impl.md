# External Agent Task — Implementation

Requires CLI enrichment. Do not hand-write `serviceType`, `context`, `inputs`, or `outputs`.

## Step 1 — Preview Schema

```bash
uip case tasks describe \
  --type connector-activity \
  --id <typeId> \
  --connection-id <connectionId> \
  --output json
```

## Step 2 — Add the Enriched Task

```bash
uip case tasks add-connector <file> <stage-id> \
  --type activity \
  --type-id <typeId> \
  --connection-id <connectionId> \
  --display-name "External AI Agent" \
  --lane 0 \
  --output json
```

## What Gets Written

```json
{
  "id": "t<8chars>",
  "elementId": "<stageId>-t<8chars>",
  "displayName": "External AI Agent",
  "type": "external-agent",
  "data": {
    "serviceType": "<connectorServiceType>",
    "context": [
      { "name": "connectorKey", "value": "<connectorKey>", "type": "string" },
      { "name": "connection",   "value": "=bindings.<connectionBindingId>", "type": "string" },
      { "name": "resourceKey",  "value": "<connectionId>", "type": "string" },
      { "name": "folderKey",    "value": "=bindings.<folderKeyBindingId>", "type": "string" },
      { "name": "metadata",     "type": "json", "body": { ... } }
    ],
    "inputs": [ ... ],
    "outputs": [ ... ],
    "bindings": []
  },
  "entryConditions": [
    { "id": "Condition_<6chars>", "displayName": "Stage entered", "rules": [[{ "rule": "current-stage-entered", "id": "Rule_<6chars>" }]] }
  ]
}
```

The exact `serviceType`, context fields, inputs, and outputs depend on the specific external agent connector — always verify with `tasks describe` first.
