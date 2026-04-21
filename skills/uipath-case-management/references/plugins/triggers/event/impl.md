# event trigger — Implementation

## CLI Command

```bash
uip maestro case triggers add-event <file> \
  --type-id "<uiPathActivityTypeId>" \
  --connection-id "<connection-id>" \
  --event-params '<json>' \
  --filter '<filter-expression>' \
  --display-name "<display-name>" \
  --output json
```

### Required flags

| Flag | Required | Notes |
|------|----------|-------|
| `--type-id` | yes | `uiPathActivityTypeId` from `typecache-triggers-index.json` |
| `--connection-id` | yes | Connection UUID |
| `--event-params` | no | JSON object of event parameter key/values |
| `--filter` | no | Connector filter DSL string |

## Example

```bash
uip maestro case triggers add-event caseplan.json \
  --type-id "829ef147-84b9-4718-9715-eefa06cc0a78" \
  --connection-id "7622a703-5d85-4b55-849b-6c02315b9e6e" \
  --event-params '{"project":"PROJ"}' \
  --filter '((fields.status=`Open`))' \
  --display-name "New Jira Issue" \
  --output json
```

## Resulting JSON Shape

```json
{
  "id": "trig0000003",
  "type": "case-management:Trigger",
  "position": { "x": -100, "y": 620 },
  "data": {
    "label": "New Jira Issue",
    "uipath": {
      "serviceType": "Intsvc.EventTrigger",
      "bindings": [
        {
          "type": "connection",
          "connectionId": "7622a703-5d85-4b55-849b-6c02315b9e6e",
          "connectorKey": "uipath-atlassian-jira"
        },
        {
          "type": "eventTrigger",
          "uiPathActivityTypeId": "829ef147-84b9-4718-9715-eefa06cc0a78",
          "eventParams": { "project": "PROJ" },
          "filter": "((fields.status=`Open`))"
        }
      ]
    }
  }
}
```

`serviceType: "Intsvc.EventTrigger"` marks this as an event-driven trigger.

## Post-Add Validation

Capture `TriggerId`. Use it as the `--source` when wiring an edge to the first stage.

Confirm:
- `data.uipath.serviceType == "Intsvc.EventTrigger"`
- `data.uipath.bindings` has both `connection` and `eventTrigger` entries
- `eventTrigger.filter` matches what you passed
- `eventTrigger.uiPathActivityTypeId` matches

If `data.uipath.bindings` is missing the `eventTrigger` entry, re-run with `--connection-id` — schema enrichment requires a live connection.
