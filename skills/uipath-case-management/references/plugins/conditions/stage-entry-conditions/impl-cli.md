# stage-entry-conditions — Implementation

## CLI Command

```bash
uip maestro case stage-entry-conditions add <file> <stage-id> \
  --display-name "<name>" \
  --is-interrupting <true|false> \
  --rule-type <rule-type> \
  --selected-stage-id "<upstream-stage-id>" \
  --condition-expression "<expr>" \
  --output json
```

### Flag matrix

| `--rule-type` | Required extra flags |
|---------------|-----------------------|
| `case-entered` | — |
| `selected-stage-completed` | `--selected-stage-id` |
| `selected-stage-exited` | `--selected-stage-id` |
| `user-selected-stage` | — |
| `wait-for-connector` | `--condition-expression` |

`--is-interrupting` is optional (defaults to `false`).

## Translation from tasks.md

The planning phase records stage names; the implementation phase looks up the captured IDs from Step 7 (stages add) and passes them as `--selected-stage-id`.

## Example — Enter "Resolution" after "Triage" exits

```bash
uip maestro case stage-entry-conditions add caseplan.json stg_resolution_id \
  --display-name "After Triage" \
  --rule-type selected-stage-exited \
  --selected-stage-id stg_triage_id \
  --output json
```

## Example — Interrupt when a connector event arrives

```bash
uip maestro case stage-entry-conditions add caseplan.json stg_exception_id \
  --display-name "Fraud detected" \
  --is-interrupting true \
  --rule-type wait-for-connector \
  --condition-expression "event.fraudScore > 0.8" \
  --output json
```

## Resulting JSON Shape

The stage node's `data.entryConditions` array gains:

```json
{
  "id": "Condition_xxxxxx",
  "displayName": "After Triage",
  "rules": [
    [
      { "rule": "selected-stage-exited", "id": "Rule_xxxxxx", "selectedStageId": "Stage_xxxxxx" }
    ]
  ]
}
```

IDs follow the CLI's `prefixedId` scheme: `Condition_` + 6 random chars, `Rule_` + 6 random chars. See [`../../../case-editing-operations-json.md § ID Generation`](../../../case-editing-operations-json.md#id-generation).

`isInterrupting` is emitted **only** when `--is-interrupting` is passed — the key is absent otherwise. When present it trails after `rules`.

Rules use DNF — outer array is OR, inner array is AND. Adding rules via `edit --rule-type` appends a new outer-group (new OR-clause), not a new inner AND-term. See `case-commands.md`.

For the full per-rule-type JSON shape (all five rule-types) and the direct-JSON-write recipe, see [`impl-json.md`](impl-json.md).

## Post-Add Validation

Capture `ConditionId`. Confirm in `caseplan.json`:

- Target stage's `data.entryConditions[].id` matches
- `rules` non-empty and contains the expected rule-type
- `isInterrupting` matches what you passed

## Editing Existing Conditions

```bash
uip maestro case stage-entry-conditions edit <file> <stage-id> <condition-id> \
  --display-name "<new-name>" \
  --rule-type <additional-rule-type> \
  --condition-expression "<expr>"
```

`edit --rule-type` **appends** a new rule (new AND-clause added as an OR group). Removing rules requires `remove` then re-`add`.
