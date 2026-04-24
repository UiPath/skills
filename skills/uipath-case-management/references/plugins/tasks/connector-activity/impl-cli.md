# connector-activity task — Implementation

## CLI Command

```bash
uip maestro case tasks add-connector <file> <stage-id> \
  --type activity \
  --type-id "<uiPathActivityTypeId>" \
  --connection-id "<connection-id>" \
  --display-name "<display-name>" \
  --input-values '<json>' \
  --output json
```

### Required flags

| Flag | Required | Notes |
|------|----------|-------|
| `--type activity` | yes | Fixed for connector-activity tasks |
| `--type-id` | yes | `uiPathActivityTypeId` from TypeCache |
| `--connection-id` | yes | Connection UUID from `get-connection` |
| `--display-name` | no | Overrides the default |
| `--input-values` | no | JSON object with `body`, `queryParameters`, etc. |

## Example

```bash
uip maestro case tasks add-connector caseplan.json stg000abc123 \
  --type activity \
  --type-id "718fdc36-73a8-3607-8604-ddef95bb9967" \
  --connection-id "7622a703-5d85-4b55-849b-6c02315b9e6e" \
  --display-name "Create Jira Issue" \
  --input-values '{"body":{"fields.project.key":"PROJ","fields.issuetype.id":"10004","fields.summary":"=result.summary"}}' \
  --output json
```

> **Shell quoting tip** — for complex JSON, write to a temp file and read it back:
> `uip maestro case tasks add-connector caseplan.json <stage-id> --type activity ... --input-values "$(cat /tmp/inputs.json)" --output json`

## Resulting JSON Shape

> **ID and elementId format.** Task `id` is `t` + 8 random chars. `elementId` is the composite `${stageId}-${taskId}`.
>
> **Default entry condition auto-injected.** Unlike non-connector tasks, `tasks add-connector` automatically attaches a default entry condition (`rule: "current-stage-entered"`) to every connector task. Direct-JSON-write for connector tasks must emit this too — the frontend expects it.

```json
{
  "id": "tB4jRw7Km",
  "elementId": "Stage_aB3kL9-tB4jRw7Km",
  "type": "execute-connector-activity",
  "displayName": "Create Jira Issue",
  "data": {
    "name": "Create Jira Issue",
    "folderPath": null,
    "serviceType": "Intsvc.Activity",
    "bindings": [
      {
        "type": "connection",
        "connectionId": "7622a703-5d85-4b55-849b-6c02315b9e6e",
        "connectorKey": "uipath-atlassian-jira"
      }
    ],
    "inputs": [ /* from --input-values */ ],
    "outputs": [ /* from describe */ ],
    "context": {
      "uiPathActivityTypeId": "718fdc36-73a8-3607-8604-ddef95bb9967",
      "objectName": "issue"
    }
  },
  "entryConditions": [
    {
      "id": "c4fGhJ2Mn",
      "displayName": "Entry rule 1",
      "rules": [
        [{ "id": "rK9xQw3Lp", "rule": "current-stage-entered" }]
      ]
    }
  ],
  "isRequired": true
}
```

> Note: the task `type` in `caseplan.json` is `execute-connector-activity` (the internal schema name), not `connector-activity` (the CLI / plugin name).

## Binding Inputs via var bind

Fields inside `--input-values` can reference cross-task outputs or expressions, but **the CLI does not accept `--source-*` in the `--input-values` JSON**. For cross-task wires, pass the literal expression inline:

```json
{"body":{"summary":"=result.some_field","description":"=metadata.description"}}
```

For complex cross-task references, after `tasks add-connector`, run `uip maestro case var bind` on the individual input as with other task types. See [bindings-and-expressions.md](../../../bindings-and-expressions.md).

## Filter Expression (if needed)

Connector-activity does not use `--filter` — that flag is for triggers. If sdd.md describes filtering, apply it inside `input-values` or via an upstream task.

## Post-Add Validation

Capture `TaskId`. Confirm:

- `type: "execute-connector-activity"`
- `data.bindings[0].connectionId` matches the UUID you passed
- `data.context.uiPathActivityTypeId` matches what you passed

If `data.inputs` or `data.outputs` is empty, the `--connection-id` may have been missing or invalid — the schema enrichment depends on a live connection.
