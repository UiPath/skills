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

> **Secondary triggers are NOT the same shape as the initial trigger.**
>
> The initial trigger (created by `uip maestro case cases add` with fixed id `trigger_1`, position `{x: 0, y: 0}`, minimal `data`) has NO `style`, `measured`, or `parentElement`.
>
> **Secondary triggers** (added via `uip maestro case triggers add-manual` — this plugin) DO have `style`, `measured`, and `parentElement`. They also use a randomly generated `trigger_` + 6-char ID.

> **ID format.** `trigger_` + 6 random chars from `[A-Za-z0-9]` (e.g. `trigger_xY2mNp`).
>
> **Position (auto-computed):** `x: -100` (fixed); `y: 200` for the first secondary trigger, otherwise `max(existingTriggerY) + 140` (stacked vertically below existing triggers).

The Trigger node in `caseplan.json.nodes`:

```json
{
  "id": "trigger_xY2mNp",
  "type": "case-management:Trigger",
  "position": { "x": -100, "y": 200 },
  "style": { "width": 96, "height": 96 },
  "measured": { "width": 96, "height": 96 },
  "data": {
    "label": "Start Manually",
    "parentElement": { "id": "root", "type": "case-management:root" },
    "uipath": { "serviceType": "None" }
  }
}
```

`serviceType: "None"` marks this as a manual trigger (no event, no schedule).

## Post-Add Validation

Capture `TriggerId` from `--output json`. Use it as the `--source` when adding an edge from the trigger to the first stage (via `uip maestro case edges add`).

Confirm `data.uipath.serviceType == "None"` in `caseplan.json`.
