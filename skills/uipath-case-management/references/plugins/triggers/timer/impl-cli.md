# timer trigger — CLI Implementation

> **Authoritative strategy:** JSON. See [`impl-json.md`](impl-json.md). This file is the fallback path, kept for plugins still in migration transit or for debugging CLI parity.

## CLI Command

```bash
uip maestro case triggers add-timer <file> \
  --time-cycle "<iso-8601-repeating-interval>" \
  --display-name "<display-name>" \
  --output json
```

Always use `--time-cycle` with the canonical `timeCycle` string from the `tasks.md` T-entry. The `--every` / `--at` / `--repeat` flags exist for human ergonomics at the shell; the skill's tasks.md format stores the already-composed ISO 8601 expression (see [`planning.md`](planning.md)), so we pass it through directly.

## Example

```bash
uip maestro case triggers add-timer caseplan.json \
  --time-cycle "R12/2026-04-21T22:00:00.000-07:00/PT10M" \
  --display-name "10-min Poll" \
  --output json
```

## Resulting JSON Shape

CLI `triggers add-timer` always emits a **secondary** trigger — it does not modify or replace `trigger_1`. The `buildBaseTriggerNode` helper ([`cli/packages/case-tool/src/commands/triggers.ts`](https://github.com/UiPath/uipath-cli) `buildBaseTriggerNode`) generates the ID via `prefixedId("trigger_")` (prefix + 6 random chars from `[A-Za-z0-9]`) and computes the position from existing trigger count.

Appended to `schema.nodes`:

```json
{
  "id": "trigger_aB3kLp",
  "type": "case-management:Trigger",
  "position": { "x": -100, "y": 140 },
  "style": { "width": 96, "height": 96 },
  "measured": { "width": 96, "height": 96 },
  "data": {
    "parentElement": { "id": "root", "type": "case-management:root" },
    "label": "10-min Poll",
    "uipath": {
      "serviceType": "Intsvc.TimerTrigger",
      "timerType": "timeCycle",
      "timeCycle": "R12/2026-04-21T22:00:00.000-07:00/PT10M"
    }
  }
}
```

**ID format.** `trigger_` + 6 random chars from `[A-Za-z0-9]` (e.g. `trigger_aB3kLp`).

**Position (auto-computed).**
- `x`: fixed `-100`.
- `y`: `200` when no existing triggers (`findTriggerNodes` returns length 0), else `max(existingTriggerY) + 140`. With the initial `trigger_1` already at `{x: 0, y: 0}` from `cases add`, the first secondary trigger lands at `y = 140`.

**Dual-file write.** `triggers add-timer` updates both `caseplan.json` (pushes node to `schema.nodes`) and `entry-points.json` (appends an entry with a random `uniqueId` UUID, `filePath: /content/<basename>.bpmn#<triggerId>`, `type: "CaseManagement"`, empty `input`/`output` schemas, `displayName`). Both writes must succeed; `saveTrigger` exits with failure on `entry-points.json` error.

## Post-Add Validation

Capture `TriggerId` from `--output json`. Use it as the `--source` when wiring an edge to the first stage.

Confirm in `caseplan.json`:
- New Trigger node appended to `schema.nodes` with `data.uipath.serviceType == "Intsvc.TimerTrigger"`
- `data.uipath.timerType == "timeCycle"`
- `data.uipath.timeCycle` matches the input `--time-cycle` string exactly

Confirm in `entry-points.json`:
- A new `entryPoints[]` entry whose `filePath` embeds the new `TriggerId`
- `displayName` matches the trigger's display name

Cross-check the CLI response's `TimeCycle` field against the sdd.md schedule to catch translation errors in the planning phase.
