# Connector Trigger — Implementation

The CLI enriches the trigger node with all connector metadata. Do not hand-write `data.uipath` fields.

## Step 1 — Find the Connector and Connection

```bash
# Search for connector trigger types
uip case registry search "<service name> trigger" --output json

# Get available connections
uip case registry get-connection --key <connectorKey> --output json
```

Capture:
- `typeId` — the `uiPathActivityTypeId` from the registry search result
- `connectionId` — UUID of the enabled connection to use

If no connection exists, tell the user — they must create one in the IS portal before proceeding.

## Step 2 — Preview the Trigger Schema (Optional but Recommended)

Inspect the trigger's input/output schema before adding it:

```bash
uip case tasks describe \
  --type connector-trigger \
  --id <typeId> \
  --connection-id <connectionId> \
  --output json
```

The output shows `inputs` (event parameters with `requiredFields`) and `outputs` (event payload fields). Use this to prepare `--event-params` in Step 3.

## Step 3 — Add the Enriched Event Trigger

The `add-event` command adds a new enriched trigger node and writes connection bindings to root:

```bash
uip case triggers add-event <file> \
  --type-id <typeId> \
  --connection-id <connectionId> \
  --output json
```

With event parameters (pre-configure which events to listen for):
```bash
uip case triggers add-event <file> \
  --type-id <typeId> \
  --connection-id <connectionId> \
  --event-params '{"project": "PROJ", "issuetype": "Bug"}' \
  --output json
```

With filter expression (only trigger on matching events):
```bash
uip case triggers add-event <file> \
  --type-id <typeId> \
  --connection-id <connectionId> \
  --filter "((fields.status<`In Progress`>))" \
  --output json
```

> `add-event` **adds** a new trigger node. If a manual trigger (`trigger_1`) already exists and should be replaced, remove it from `nodes` and its edge from `edges` before running this command.

Capture the trigger node ID from the output.

## What the CLI Writes

After enrichment, the trigger node's `data.uipath` is populated:

```json
{
  "id": "trigger_<6chars>",
  "type": "case-management:Trigger",
  "position": { "x": 0, "y": 0 },
  "data": {
    "label": "Trigger 1",
    "uipath": {
      "serviceType": "Intsvc.EventTrigger",
      "context": [
        { "name": "connectorKey", "value": "uipath-atlassian-jira", "type": "string" },
        { "name": "connection", "value": "=bindings.<connectionBindingId>", "type": "string" },
        { "name": "resourceKey", "value": "<connectionId>", "type": "string" },
        { "name": "folderKey", "value": "=bindings.<folderKeyBindingId>", "type": "string" },
        { "name": "operation", "value": "ISSUE_CREATED", "type": "string" },
        { "name": "objectName", "value": "Issue", "type": "string" },
        { "name": "method", "value": "", "type": "string" },
        { "name": "path", "value": "", "type": "string" },
        {
          "name": "metadata",
          "type": "json",
          "body": {
            "activityPropertyConfiguration": {
              "objectName": "Issue",
              "eventType": "ISSUE_CREATED",
              "eventMode": "polling",
              "configuration": "=jsonString:{...}",
              "uiPathActivityTypeId": "<typeId>"
            }
          }
        }
      ],
      "inputs": [
        {
          "name": "body",
          "type": "json",
          "body": {
            "filters": { "expression": "" },
            "parameters": {}
          }
        }
      ],
      "outputs": [
        {
          "name": "response",
          "displayName": "Issue Created",
          "type": "jsonSchema",
          "source": "=response",
          "_jsonSchema": { ... }
        },
        { "name": "Error", "type": "json", "source": "=error" }
      ],
      "bindings": []
    }
  }
}
```

Root bindings are also appended:
```json
{ "id": "b<8chars>", "name": "connection", "resource": "connection", "resourceKey": "<connectionId>", ... },
{ "id": "b<8chars>", "name": "folderKey", "resource": "folderKey", "resourceKey": "<folderKey>", ... }
```

Trigger outputs are added to `root.data.uipath.variables.inputOutputs` for BPMN conversion.

## Step 4 — Wire the Trigger to the First Stage

`add-event` adds the trigger node but not its edge. Add the edge manually:

```json
{
  "id": "edge_<6chars>",
  "source": "<triggerId>",
  "target": "Stage_<6chars>",
  "sourceHandle": "<triggerId>____source____right",
  "targetHandle": "Stage_<6chars>____target____left",
  "data": {},
  "type": "case-management:TriggerEdge"
}
```

Add this to the `edges` array in `caseplan.json`.

## CLI Reference

```bash
# Discovery
uip case registry search "<service> trigger" --output json
uip case registry get-connection --key <connectorKey> --output json

# Preview schema
uip case tasks describe --type connector-trigger --id <typeId> --connection-id <id> --output json

# Add enriched trigger
uip case triggers add-event <file> \
  --type-id <typeId> \
  --connection-id <connectionId> \
  [--event-params <json>] \
  [--filter <expression>] \
  [--display-name <name>] \
  --output json
```

## Common Errors

| Error | Cause | Fix |
|---|---|---|
| Trigger type not found in registry | Not authenticated or registry stale | Run `uip login` then `uip case registry pull` |
| `connection not found` | Connection ID incorrect or expired | Re-run `registry get-connection` to get valid IDs |
| No connection exists | User hasn't created a connection | User must create connection in IS portal first |
| `filter` syntax error | Wrong filter format | Use JMESPath: `((fields.<fieldName><\`value\`>))` |
| Trigger fires on all events | Filter expression incorrect or missing | Check `describe` output for available filter fields |
| Edge missing after add-event | `add-event` does not create edges automatically | Add a `TriggerEdge` manually from trigger to first stage (Step 4) |
