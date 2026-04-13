# Connector Activity Tasks — Implementation

Covers `execute-connector-activity`, `wait-for-connector`, and `external-agent`.

The CLI enriches the task with all connector metadata in a single command. Do not hand-write `serviceType`, `context`, `inputs`, or `outputs`.

## Step 1 — Find the Connector and Connection

```bash
# Search for the connector
uip case registry search "<service name>" --output json

# Get available connections for the connector
uip case registry get-connection --key <connectorKey> --output json
```

Capture:
- `typeId` — the `uiPathActivityTypeId` from the registry search result
- `connectionId` — UUID of the enabled connection to use

If no connection exists, tell the user — they must create one in the IS portal before proceeding.

## Step 2 — Preview the Schema (Optional but Recommended)

Before adding the task, inspect the input/output schema to know what fields are available and which are required:

```bash
uip case tasks describe \
  --type connector-activity \
  --id <typeId> \
  --connection-id <connectionId> \
  --output json
```

For `wait-for-connector` type:
```bash
uip case tasks describe \
  --type connector-trigger \
  --id <typeId> \
  --connection-id <connectionId> \
  --output json
```

The output lists all `inputs` (with `requiredFields`) and `outputs`. Use this to determine what `--input-values` to provide in Step 3.

## Step 3 — Add the Enriched Task

The `add-connector` command creates the task, enriches it, and appends bindings to `root.data.uipath.bindings` — all in one step:

```bash
# Add an execute-connector-activity task
uip case tasks add-connector <file> <stage-id> \
  --type activity \
  --type-id <typeId> \
  --connection-id <connectionId> \
  --display-name "Create Jira Issue" \
  --lane 0 \
  --output json
```

With pre-populated input values:
```bash
uip case tasks add-connector <file> <stage-id> \
  --type activity \
  --type-id <typeId> \
  --connection-id <connectionId> \
  --display-name "Create Jira Issue" \
  --input-values '{"body": {"fields.project.key": "PROJ", "fields.issuetype.id": "10004"}}' \
  --output json
```

For `wait-for-connector` tasks, use `--type trigger`:
```bash
uip case tasks add-connector <file> <stage-id> \
  --type trigger \
  --type-id <typeId> \
  --connection-id <connectionId> \
  --display-name "Wait for Jira Event" \
  --output json
```

With filter expression:
```bash
uip case tasks add-connector <file> <stage-id> \
  --type trigger \
  --type-id <typeId> \
  --connection-id <connectionId> \
  --filter "((fields.status<`In Progress`>))" \
  --output json
```

Capture the `TaskId` from the output — needed for variable binding.

## What the CLI Writes

After enrichment, the task data contains:

```json
{
  "id": "t<8chars>",
  "elementId": "<stageId>-t<8chars>",
  "displayName": "Create Jira Issue",
  "type": "execute-connector-activity",
  "data": {
    "serviceType": "Intsvc.ExecuteConnectorActivity",
    "context": [
      { "name": "connectorKey", "value": "uipath-atlassian-jira", "type": "string" },
      { "name": "connection", "value": "=bindings.<connectionBindingId>", "type": "string" },
      { "name": "resourceKey", "value": "<connectionId>", "type": "string" },
      { "name": "folderKey", "value": "=bindings.<folderKeyBindingId>", "type": "string" },
      { "name": "operation", "value": "Create", "type": "string" },
      { "name": "objectName", "value": "Issue", "type": "string" },
      { "name": "method", "value": "POST", "type": "string" },
      { "name": "path", "value": "/issues", "type": "string" },
      { "name": "_label", "value": "Create Issue", "type": "string" },
      { "name": "metadata", "type": "json", "body": { ... } }
    ],
    "inputs": [
      {
        "name": "body",
        "type": "json",
        "body": { "fields.project.key": "PROJ", "fields.issuetype.id": "10004" }
      }
    ],
    "outputs": [
      { "name": "response", "type": "jsonSchema", "source": "=response", "_jsonSchema": { ... } },
      { "name": "Error", "type": "json", "source": "=error", ... }
    ],
    "bindings": []
  }
}
```

And at root, two bindings are appended:
```json
{ "id": "b<8chars>", "name": "connection", "resource": "connection", "resourceKey": "<connectionId>", ... },
{ "id": "b<8chars>", "name": "folderKey", "resource": "folderKey", "resourceKey": "<folderKey>", ... }
```

## Step 4 — Bind Task Inputs (if needed)

Wire specific input fields to global variables or literal values:

```bash
# Bind a task input to a global variable
uip case var bind <file> <stage-id> <task-id> --name body.fields.project.key \
  --value "=vars.projectKey" --output json

# Bind a literal value
uip case var bind <file> <stage-id> <task-id> --name body.fields.issuetype.id \
  --value "10004" --output json
```

## CLI Reference

```bash
# Task type discovery
uip case registry search "<service>" --output json
uip case registry get-connection --key <connectorKey> --output json

# Preview schema before adding
uip case tasks describe --type connector-activity --id <typeId> --connection-id <id> --output json
uip case tasks describe --type connector-trigger --id <typeId> --connection-id <id> --output json

# Add enriched task
uip case tasks add-connector <file> <stage-id> \
  --type activity|trigger \
  --type-id <typeId> \
  --connection-id <connectionId> \
  [--display-name <name>] \
  [--lane <index>] \
  [--input-values <json>] \
  [--filter <expression>] \
  --output json
```

## Common Errors

| Error | Cause | Fix |
|---|---|---|
| `typeId not found` | Wrong type ID or registry stale | Run `uip case registry pull` then search again |
| `connection not found` | Connection ID incorrect or connection deleted | Re-run `registry get-connection` to get valid IDs |
| No connection exists | User hasn't created a connection | User must create connection in IS portal first |
| Input field missing at runtime | Required input not bound | Check `tasks describe` output for `requiredFields` and bind them |
| `filter` syntax error | Wrong filter format | Use JMESPath: `((fields.<fieldName><\`value\`>))` |
