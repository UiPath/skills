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

> **ID and elementId format.** Task `id` is `t` + 8 random chars. `elementId` is the composite `${stageId}-${taskId}`.
>
> **Default entry condition auto-injected.** `tasks add-connector` automatically attaches a default entry condition (`rule: "current-stage-entered"`) to every connector task. Direct-JSON-write must emit this too.

```json
{
  "id": "tF8hPq2Wr",
  "elementId": "Stage_aB3kL9-tF8hPq2Wr",
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
  "entryConditions": [
    {
      "id": "c7mLpV4Kj",
      "displayName": "Entry rule 1",
      "rules": [
        [{ "id": "rN3tGx8Qb", "rule": "current-stage-entered" }]
      ]
    }
  ],
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
