# task-entry-conditions — Implementation (CLI)

> Direct-JSON alternative: [`impl-json.md`](impl-json.md).

## CLI Command

```bash
uip maestro case task-entry-conditions add <file> <stage-id> <task-id> \
  --display-name "<name>" \
  --rule-type <rule-type> \
  --selected-tasks-ids "<id1>,<id2>" \
  --condition-expression "<expr>" \
  --output json
```

### Flag matrix

| `--rule-type` | Required extra flag |
|---------------|---------------------|
| `current-stage-entered` | — |
| `selected-tasks-completed` | `--selected-tasks-ids "<comma-separated task IDs>"` |
| `wait-for-connector` | `--condition-expression` |
| `adhoc` | `--condition-expression` |

## Translation from tasks.md

- `target-stage` / `target-task` → `<stage-id> <task-id>` via capture map.
- `selected-tasks` → `--selected-tasks-ids <ids>` via capture map (names → IDs).

## Example — Run only after a sibling task completes

```bash
uip maestro case task-entry-conditions add caseplan.json stg_review_id tsk_notify_id \
  --display-name "After Approval" \
  --rule-type selected-tasks-completed \
  --selected-tasks-ids "tsk_approval_id" \
  --output json
```

## Example — Ad-hoc expression gate

```bash
uip maestro case task-entry-conditions add caseplan.json stg_triage_id tsk_escalate_id \
  --display-name "High-risk only" \
  --rule-type adhoc \
  --condition-expression "in.riskScore > 700" \
  --output json
```

## Example — Wait for connector event before starting

```bash
uip maestro case task-entry-conditions add caseplan.json stg_triage_id tsk_process_id \
  --display-name "Wait for inbound" \
  --rule-type wait-for-connector \
  --condition-expression "event.type = 'order_received'" \
  --output json
```

## Resulting JSON Shape

The task's `entryConditions` array gains:

```json
{
  "id": "cond00000003",
  "displayName": "After Approval",
  "rules": [
    [ { "rule": "selected-tasks-completed", "id": "...", "selectedTasksIds": ["tsk_approval_id"] } ]
  ]
}
```

## Post-Add Validation

Capture `ConditionId`. Confirm:

- The target task's `entryConditions[].id` matches
- `rules` contains the expected rule-type
- `selectedTasksIds` (if set) matches the comma-split list

## Editing Existing Conditions

```bash
uip maestro case task-entry-conditions edit <file> <stage-id> <task-id> <condition-id> \
  --display-name "<new-name>" \
  --rule-type <additional> \
  --condition-expression "<expr>" \
  --selected-tasks-ids "<ids>"
```

`edit --rule-type` appends a new rule. Use `remove` + re-`add` to replace a rule.
