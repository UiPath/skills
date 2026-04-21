# timer trigger — Implementation

## CLI Command

```bash
uip maestro case triggers add-timer <file> \
  --every "<duration>" \
  --at "<iso-datetime>" \
  --repeat <count> \
  --display-name "<display-name>" \
  --output json
```

Or use a raw ISO 8601 repeating interval:

```bash
uip maestro case triggers add-timer <file> \
  --time-cycle "<R/PT...>" \
  --display-name "<display-name>" \
  --output json
```

### Flag rules

| Flag | Notes |
|------|-------|
| `--every <duration>` | Required unless `--time-cycle` is set |
| `--at <iso>` | Optional start datetime |
| `--repeat <n>` | Optional; omit for infinite |
| `--time-cycle <expr>` | Overrides `--every`/`--at`/`--repeat` |

## Example — Every hour, forever

```bash
uip maestro case triggers add-timer caseplan.json \
  --every 1h \
  --display-name "Hourly Poll" \
  --output json
```

## Example — Every day at 9 AM UTC, for 30 days

```bash
uip maestro case triggers add-timer caseplan.json \
  --every 1d \
  --at 2026-04-26T09:00:00.000Z \
  --repeat 30 \
  --display-name "Daily 9 AM Check" \
  --output json
```

## Example — Raw ISO 8601

```bash
uip maestro case triggers add-timer caseplan.json \
  --time-cycle "R/PT1H" \
  --display-name "Raw Hourly" \
  --output json
```

## Resulting JSON Shape

```json
{
  "id": "trig0000002",
  "type": "case-management:Trigger",
  "position": { "x": -100, "y": 480 },
  "data": {
    "label": "Hourly Poll",
    "uipath": {
      "serviceType": "Intsvc.TimerTrigger",
      "timeCycle": "R/PT1H"
    }
  }
}
```

`serviceType: "Intsvc.TimerTrigger"` marks this as a timer trigger. Duration fields (`--every`, `--at`, `--repeat`) are composed into a `timeCycle` ISO 8601 string.

## Post-Add Validation

Capture `TriggerId`. Use it as the `--source` when wiring an edge to the first stage.

Confirm:
- `data.uipath.serviceType == "Intsvc.TimerTrigger"`
- `data.uipath.timeCycle` non-empty and matches the intended schedule

The response includes a `TimeCycle` field — cross-check it against the sdd.md phrasing to catch translation errors.
