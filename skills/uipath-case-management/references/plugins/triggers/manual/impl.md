# manual trigger — Implementation

## CLI Command

```bash
uip maestro case triggers add-manual <file> \
  --display-name "<display-name>" \
  --output json
```

### Optional flags

| Flag | Notes |
|------|-------|
| `--display-name` | Auto-generated as `Trigger N` if omitted |
| `--position "<x>,<y>"` | Auto-stacked to the left of stages if omitted |

## Example

```bash
uip maestro case triggers add-manual caseplan.json \
  --display-name "Start Manually" \
  --output json
```

## Resulting JSON Shape

The Trigger node in `caseplan.json.nodes`:

```json
{
  "id": "trig0000001",
  "type": "case-management:Trigger",
  "position": { "x": -100, "y": 340 },
  "data": {
    "label": "Start Manually",
    "uipath": { "serviceType": "None" }
  }
}
```

`serviceType: "None"` marks this as a manual trigger (no event, no schedule).

## Post-Add Validation

Capture `TriggerId` from `--output json`. Use it as the `--source` when adding an edge from the trigger to the first stage (via `uip maestro case edges add`).

Confirm `data.uipath.serviceType == "None"` in `caseplan.json`.
