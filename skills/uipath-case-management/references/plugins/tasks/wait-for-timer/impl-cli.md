# wait-for-timer task — Implementation

## CLI Command

```bash
uip maestro case tasks add <file> <stage-id> \
  --type wait-for-timer \
  --display-name "<display-name>" \
  --is-required \
  --output json
```

> **Note:** The `uip maestro case tasks add` command itself does not accept `--every`, `--at`, `--repeat`, or `--time-cycle` — those flags exist on `triggers add-timer`, not on `tasks add`. For in-stage timer tasks, `tasks add --type wait-for-timer` creates the task with default timer data; configure the duration afterwards with direct JSON editing OR (preferred) by using `triggers add-timer` and wiring via an edge.

## Two Patterns

### Pattern A — Simple in-stage wait (fixed delay)

```bash
uip maestro case tasks add caseplan.json stg000abc123 \
  --type wait-for-timer \
  --display-name "24-hour cooldown" \
  --is-required \
  --output json
```

After creation, the task's `data` is empty. If the sdd.md specifies a duration, edit `caseplan.json` directly or use a case-level timer trigger instead (Pattern B).

### Pattern B — Case-level scheduled trigger (preferred for scheduled events)

Use [`plugins/triggers/timer/`](../../triggers/timer/impl-cli.md) — most "timer" behavior in sdd.md is better modeled as a case-level timer trigger than an in-stage wait.

## Example

```bash
uip maestro case tasks add caseplan.json stg000abc123 \
  --type wait-for-timer \
  --display-name "Wait 24 hours" \
  --is-required \
  --output json
```

## Resulting JSON Shape

> **ID and elementId format.** Task `id` is `t` + 8 random chars. `elementId` is the composite `${stageId}-${taskId}`.

```json
{
  "id": "tWm4Vx9Tp",
  "elementId": "Stage_aB3kL9-tWm4Vx9Tp",
  "type": "wait-for-timer",
  "displayName": "Wait 24 hours",
  "data": {
    "timer": null,
    "timeDuration": null,
    "timeDate": null,
    "timeCycle": null
  },
  "isRequired": true
}
```

The `data` fields are populated by subsequent edits — the CLI does not yet support setting them on `tasks add`.

## Post-Add Validation

Capture `TaskId`. Confirm `type: "wait-for-timer"` in `caseplan.json`.

If sdd.md specified a duration but the data fields remain null, flag to the user: "The CLI does not set timer duration on `tasks add`. Model this as a case-level timer trigger instead, or edit `caseplan.json.data` directly."
