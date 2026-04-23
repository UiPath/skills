# stage-exit-conditions — Implementation (CLI)

> Direct-JSON alternative: [`impl-json.md`](impl-json.md).

## CLI Command

```bash
uip maestro case stage-exit-conditions add <file> <stage-id> \
  --display-name "<name>" \
  --type <exit-only|wait-for-user|return-to-origin> \
  --exit-to-stage-id "<target-stage-id>" \
  --marks-stage-complete <true|false> \
  --rule-type <rule-type> \
  --selected-tasks-ids "<id1>,<id2>" \
  --condition-expression "<expr>" \
  --output json
```

## Rule-Type × Marks-Stage-Complete Matrix

| `marks-stage-complete` | Valid `--rule-type` | Extra flag |
|------------------------|---------------------|-----------|
| `true` | `required-tasks-completed` | — |
| `true` | `wait-for-connector` | `--condition-expression` |
| `false` | `selected-tasks-completed` | `--selected-tasks-ids "<id1>,<id2>"` |
| `false` | `wait-for-connector` | `--condition-expression` |

## Translation from tasks.md

- `target-stage` → `<stage-id>` (positional arg) via capture map.
- `exit-to-stage` → `--exit-to-stage-id <id>` via capture map.
- `selected-tasks` → `--selected-tasks-ids <comma-separated task IDs>` via capture map.

## Example — Complete when all required tasks finish

```bash
uip maestro case stage-exit-conditions add caseplan.json stg_triage_id \
  --display-name "All tasks done" \
  --type exit-only \
  --marks-stage-complete true \
  --rule-type required-tasks-completed \
  --output json
```

## Example — Route to Escalation when specific tasks complete

```bash
uip maestro case stage-exit-conditions add caseplan.json stg_review_id \
  --display-name "Route to Escalation" \
  --type exit-only \
  --exit-to-stage-id stg_escalation_id \
  --marks-stage-complete false \
  --rule-type selected-tasks-completed \
  --selected-tasks-ids "tsk_flag_1,tsk_flag_2" \
  --output json
```

## Example — Wait for user decision

```bash
uip maestro case stage-exit-conditions add caseplan.json stg_manager_review_id \
  --display-name "User picks next step" \
  --type wait-for-user \
  --marks-stage-complete true \
  --rule-type required-tasks-completed \
  --output json
```

## Example — Return to origin on rework

```bash
uip maestro case stage-exit-conditions add caseplan.json stg_exception_id \
  --display-name "Rework — return to origin" \
  --type return-to-origin \
  --marks-stage-complete false \
  --rule-type required-tasks-completed \
  --output json
```

## Resulting JSON Shape

The stage node's `data.exitConditions` array gains:

```json
{
  "id": "cond00000002",
  "displayName": "All tasks done",
  "type": "exit-only",
  "exitToStageId": null,
  "marksStageComplete": true,
  "rules": [
    [ { "rule": "required-tasks-completed", "id": "..." } ]
  ]
}
```

## Post-Add Validation

Capture `ConditionId`. Confirm:

- `exitConditions[].type` matches
- `exitConditions[].marksStageComplete` matches
- `exitConditions[].exitToStageId` matches (if set)
- `rules` contains the expected rule-type

## Editing Existing Conditions

```bash
uip maestro case stage-exit-conditions edit <file> <stage-id> <condition-id> \
  --display-name "<new-name>" \
  --type <new-type> \
  --exit-to-stage-id <id> \
  --marks-stage-complete <bool> \
  --rule-type <additional> \
  --condition-expression "<expr>"
```

`edit --rule-type` **appends** a new rule. Removing rules requires `remove` then re-`add`.
