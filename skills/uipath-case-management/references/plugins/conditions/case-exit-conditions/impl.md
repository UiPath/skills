# case-exit-conditions — Implementation

## CLI Command

```bash
uip maestro case case-exit-conditions add <file> \
  --display-name "<name>" \
  --marks-case-complete <true|false> \
  --rule-type <rule-type> \
  --selected-stage-id "<stage-id>" \
  --condition-expression "<expr>" \
  --output json
```

> Note: there is no `<stage-id>` positional argument — case-exit-conditions attach at the root, not to a stage. `--selected-stage-id` is a flag used only by `selected-stage-*` rule-types to name the referenced stage.

## Rule-Type × Marks-Case-Complete Matrix

| `marks-case-complete` | Valid `--rule-type` | Extra flag |
|------------------------|---------------------|-----------|
| `true` | `required-stages-completed` | — |
| `true` | `wait-for-connector` | `--condition-expression` |
| `false` | `selected-stage-completed` | `--selected-stage-id` |
| `false` | `selected-stage-exited` | `--selected-stage-id` |
| `false` | `wait-for-connector` | `--condition-expression` |

## Translation from tasks.md

- `selected-stage` → `--selected-stage-id <id>` via the stage capture map.

## Example — Preferred completion pattern

```bash
uip maestro case case-exit-conditions add caseplan.json \
  --display-name "Case resolved" \
  --marks-case-complete true \
  --rule-type required-stages-completed \
  --output json
```

Completes the case when every stage flagged `isRequired: true` (in the planning metadata for `stages add`) has completed.

## Example — Non-completing exit when a specific stage completes

```bash
uip maestro case case-exit-conditions add caseplan.json \
  --display-name "Early exit via Escalation" \
  --marks-case-complete false \
  --rule-type selected-stage-completed \
  --selected-stage-id stg_escalation_id \
  --output json
```

## Example — Wait for connector event to close

```bash
uip maestro case case-exit-conditions add caseplan.json \
  --display-name "Closed by downstream system" \
  --marks-case-complete true \
  --rule-type wait-for-connector \
  --condition-expression "event.type = 'case_closed'" \
  --output json
```

## Resulting JSON Shape

The root's `caseExitConditions` array gains:

```json
{
  "id": "cond00000004",
  "displayName": "Case resolved",
  "marksCaseComplete": true,
  "rules": [
    [ { "rule": "required-stages-completed", "id": "..." } ]
  ]
}
```

Rules use DNF — outer array is OR, inner array is AND.

## Post-Add Validation

Capture `ConditionId` from `--output json`. Confirm in `caseplan.json`:

- Root's `caseExitConditions[].id` matches
- `marksCaseComplete` matches what you passed
- `rules` contains the expected rule-type
- `selectedStageId` (if set) matches

## Editing / Removing

```bash
uip maestro case case-exit-conditions edit <file> <condition-id> \
  --display-name "<new-name>" \
  --marks-case-complete <bool> \
  --rule-type <additional> \
  --condition-expression "<expr>" \
  --selected-stage-id "<id>"

uip maestro case case-exit-conditions remove <file> <condition-id>
```

`edit --rule-type` appends a new rule (OR group). Use `remove` + re-`add` to replace.
