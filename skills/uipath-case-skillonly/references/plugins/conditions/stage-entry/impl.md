# Stage Entry Conditions — Implementation

Entry conditions are placed in `stage.data.entryConditions`.

## case-entered — First Stage Only

```json
"entryConditions": [
  {
    "id": "Condition_<6chars>",
    "displayName": "Case entered",
    "rules": [[{ "rule": "case-entered", "id": "Rule_<6chars>" }]]
  }
]
```

## selected-stage-completed — Depends on Another Stage Finishing

```json
"entryConditions": [
  {
    "id": "Condition_<6chars>",
    "displayName": "Stage 1 completed",
    "rules": [[{
      "rule": "selected-stage-completed",
      "id": "Rule_<6chars>",
      "selectedStageId": "Stage_f95rff"
    }]]
  }
]
```

With filter expression (only activate if condition is true when stage completes):

```json
{
  "rule": "selected-stage-completed",
  "id": "Rule_<6chars>",
  "selectedStageId": "Stage_f95rff",
  "conditionExpression": "=js:vars.approvalStatus === 'approved'"
}
```

## selected-stage-exited — Depends on Another Stage Exiting

```json
"entryConditions": [
  {
    "id": "Condition_<6chars>",
    "displayName": "Review stage exited",
    "rules": [[{
      "rule": "selected-stage-exited",
      "id": "Rule_<6chars>",
      "selectedStageId": "Stage_f95rff"
    }]]
  }
]
```

## current-stage-entered — Activates on Every Entry

Used when the stage should trigger every time it is entered, including re-entries:

```json
"entryConditions": [
  {
    "id": "Condition_<6chars>",
    "displayName": "Stage entered",
    "rules": [[{ "rule": "current-stage-entered", "id": "Rule_<6chars>" }]]
  }
]
```

With filter expression:

```json
{
  "rule": "current-stage-entered",
  "id": "Rule_<6chars>",
  "conditionExpression": "=js:vars.priority === 'high'"
}
```

## adhoc — Manual Activation

Stage can be triggered manually at any point during the case:

```json
"entryConditions": [
  {
    "id": "Condition_<6chars>",
    "displayName": "Adhoc activation",
    "rules": [[{ "rule": "adhoc", "id": "Rule_<6chars>" }]]
  }
]
```

## isInterrupting

Add to any entry condition to allow mid-execution stage interruption:

```json
{
  "id": "Condition_<6chars>",
  "displayName": "High priority interrupt",
  "isInterrupting": true,
  "rules": [[{
    "rule": "selected-stage-completed",
    "id": "Rule_<6chars>",
    "selectedStageId": "Stage_f95rff",
    "conditionExpression": "=js:vars.escalated === true"
  }]]
}
```

## OR Logic — Multiple Rule Sets

Stage activates when either condition fires (Stage 1 completes OR Stage 2 completes):

```json
"entryConditions": [
  {
    "id": "Condition_<6chars>",
    "displayName": "Stage 1 or Stage 2 completed",
    "rules": [
      [{ "rule": "selected-stage-completed", "id": "Rule_<6chars>", "selectedStageId": "Stage_aaa111" }],
      [{ "rule": "selected-stage-completed", "id": "Rule_<6chars>", "selectedStageId": "Stage_bbb222" }]
    ]
  }
]
```

## Rule Type Reference (full FE-aligned set)

Authoritative source: FE Zod schemas in `types/case-mgmt-zod/rules/` and `CaseManagementNodeEntryRuleCondition` type. Each rule is an object with `rule` + supporting fields:

| `rule` value | Companion fields | When to use here (stage entry) |
|---|---|---|
| `case-entered` | `conditionExpression?` | First stage; activates when the case starts |
| `current-stage-entered` | `conditionExpression?` | Stage activates each time it's entered (re-entry-aware) |
| `selected-stage-completed` | `selectedStageId`, `conditionExpression?` | Wait for another stage to complete |
| `selected-stage-exited` | `selectedStageId`, `conditionExpression?` | Wait for another stage to exit (regardless of completion) |
| `selected-tasks-completed` | `selectedTasksIds[]`, `conditionExpression?` | Wait for specific tasks across the case |
| `wait-for-connector` | `uipath: { serviceType?, context?[], inputs?[], outputs?[], bindings?[] }`, `conditionExpression?` | Wait for an external connector event (Outlook email, webhook, etc.) — usually written by `uip case tasks add-connector` rather than by hand |
| `adhoc` | `conditionExpression?` | Stage can be triggered manually at any point |

> **`isInterrupting: true`** on the entry condition (NOT on the rule) lets the new entry preempt running work in the source stage — common for ExceptionStage entries from multiple sources.

### Deprecated rules (legacy schema)

| Rule | Replacement |
|---|---|
| `condition` | Use `current-stage-entered` (or other rule) with `conditionExpression` |
| `stage-complete` | Use `selected-tasks-completed` or `selected-stage-completed` |
| `timer` (in conditions) | Use a Timer trigger or `wait-for-timer` task |
