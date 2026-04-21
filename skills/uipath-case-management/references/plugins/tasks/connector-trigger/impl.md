# connector-trigger task — Implementation

## CLI Command

```bash
uip maestro case tasks add-connector <file> <stage-id> \
  --type trigger \
  --type-id "<uiPathActivityTypeId>" \
  --connection-id "<connection-id>" \
  --display-name "<display-name>" \
  --input-values '<json>' \
  --filter '<filter-expression>' \
  --output json
```

### Required flags

| Flag | Required | Notes |
|------|----------|-------|
| `--type trigger` | yes | Distinguishes from connector-activity |
| `--type-id` | yes | From `typecache-triggers-index.json` |
| `--connection-id` | yes | From `get-connection` |
| `--input-values` | no | Event parameters as JSON |
| `--filter` | no | Connector filter DSL string |

## Example

```bash
uip maestro case tasks add-connector caseplan.json stg000abc123 \
  --type trigger \
  --type-id "829ef147-84b9-4718-9715-eefa06cc0a78" \
  --connection-id "7622a703-5d85-4b55-849b-6c02315b9e6e" \
  --display-name "Wait for Jira Issue Update" \
  --input-values '{"body":{"project":"PROJ"}}' \
  --filter '((fields.status=`Resolved`))' \
  --output json
```

## Resulting JSON Shape

```json
{
  "id": "tsk00000008",
  "elementId": "el_0008",
  "type": "wait-for-connector",
  "displayName": "Wait for Jira Issue Update",
  "data": {
    "name": "Wait for Jira Issue Update",
    "serviceType": "Intsvc.EventTrigger",
    "bindings": [
      {
        "type": "connection",
        "connectionId": "7622a703-5d85-4b55-849b-6c02315b9e6e",
        "connectorKey": "uipath-atlassian-jira"
      },
      {
        "type": "eventTrigger",
        "filter": "((fields.status=`Resolved`))",
        "eventParams": { "project": "PROJ" }
      }
    ],
    "outputs": [ /* from describe */ ],
    "context": {
      "uiPathActivityTypeId": "829ef147-84b9-4718-9715-eefa06cc0a78",
      "objectName": "issue"
    }
  },
  "isRequired": true
}
```

> The task `type` in `caseplan.json` is `wait-for-connector` (the internal schema name), not `connector-trigger` (the CLI / plugin name).

## Binding Outputs

Outputs of a connector-trigger are the fields of the fired event (e.g., `issueId`, `summary`). Downstream tasks reference them via cross-task refs per [bindings-and-expressions.md](../../../bindings-and-expressions.md).

## Post-Add Validation

Capture `TaskId`. Confirm:

- `type: "wait-for-connector"`
- `data.bindings` has **both** a `connection` entry and an `eventTrigger` entry
- `data.bindings[].filter` matches what you passed
- `data.context.uiPathActivityTypeId` matches

If `data.outputs` is empty, the connection may be invalid — schema enrichment requires a live connection.
