# Exception Stage — Implementation

## Node

```json
{
  "id": "Stage_excABC",
  "type": "case-management:ExceptionStage",
  "position": { "x": 300, "y": 600 },
  "style": { "width": 304, "opacity": 0.8 },
  "measured": { "width": 304, "height": 128 },
  "width": 304,
  "zIndex": 1001,
  "data": {
    "label": "Error Handler",
    "parentElement": { "id": "root", "type": "case-management:root" },
    "isInvalidDropTarget": false,
    "isPendingParent": false,
    "description": "Handles processing errors and returns to origin stage.",
    "isRequired": false,
    "tasks": [
      [
        {
          "id": "t<8chars>",
          "elementId": "Stage_excABC-t<8chars>",
          "displayName": "Notify on Error",
          "description": "Sends error notification to the operations team.",
          "type": "action",
          "isRequired": true,
          "shouldRunOnlyOnce": false,
          "data": {
            "name": "=bindings.<nameBindingId>",
            "folderPath": "=bindings.<folderBindingId>",
            "taskTitle": "Error Notification",
            "priority": "High",
            "assignmentCriteria": "user",
            "recipient": { "Type": 2, "Value": "ops-team@company.com" },
            "inputs": [],
            "outputs": []
          },
          "entryConditions": [
            {
              "id": "Condition_<6chars>",
              "displayName": "Stage entered",
              "rules": [[{ "rule": "current-stage-entered", "id": "Rule_<6chars>" }]]
            }
          ]
        }
      ]
    ],
    "entryConditions": [
      {
        "id": "Condition_<6chars>",
        "displayName": "Error triggered",
        "rules": [[{ "rule": "adhoc", "id": "Rule_<6chars>" }]]
      }
    ],
    "exitConditions": [
      {
        "id": "Condition_<6chars>",
        "displayName": "Return to origin",
        "type": "return-to-origin",
        "marksStageComplete": true,
        "rules": [[{ "rule": "required-tasks-completed", "id": "Rule_<6chars>" }]]
      }
    ],
    "slaRules": []
  }
}
```

## Edge from Main Stage to ExceptionStage

Use `bottom` → `top` handles for vertical branching:

```json
{
  "id": "edge_<6chars>",
  "source": "Stage_f95rff",
  "target": "Stage_excABC",
  "sourceHandle": "Stage_f95rff____source____bottom",
  "targetHandle": "Stage_excABC____target____top",
  "data": {},
  "type": "case-management:Edge"
}
```

## Re-entry Behaviour Note

`shouldRunOnlyOnce` is set to `false` on tasks in the example above. In an ExceptionStage, the runtime forces all tasks to run on every re-entry regardless of this value — but set it explicitly to `false` to make intent clear.

## isRequired on ExceptionStage

Set `isRequired: false` on the ExceptionStage node itself. Exception stages should not be required for normal case completion — they only activate on error paths.

## Multiple Entry Sources Pattern

ExceptionStages often receive entries from multiple main-flow stages. Each source stage needs its own entry condition with `isInterrupting: true`:

```json
"entryConditions": [
  {
    "id": "Condition_<6chars>",
    "displayName": "Entry from 'Intake'",
    "isInterrupting": true,
    "rules": [[{
      "rule": "selected-stage-exited",
      "id": "Rule_<6chars>",
      "selectedStageId": "stage-1",
      "conditionExpression": "=js:vars.decision == \"Claim needs info from customer\""
    }]]
  },
  {
    "id": "Condition_<6chars>",
    "displayName": "Entry from 'Review'",
    "isInterrupting": true,
    "rules": [[{
      "rule": "selected-stage-exited",
      "id": "Rule_<6chars>",
      "selectedStageId": "Stage_xCv7s5",
      "conditionExpression": "=js:vars.decision == \"Claim needs info from customer\""
    }]]
  },
  {
    "id": "Condition_<6chars>",
    "displayName": "Entry from 'Settlement'",
    "isInterrupting": true,
    "rules": [[{
      "rule": "selected-stage-exited",
      "id": "Rule_<6chars>",
      "selectedStageId": "Stage_7Plxpi",
      "conditionExpression": "=js:vars.decision == \"Claim needs info from customer\""
    }]]
  }
]
```

Key points:
- Each entry condition has a unique `displayName` indicating the source stage
- All use `isInterrupting: true` to preempt the source stage
- The `conditionExpression` filters which exit values trigger the exception path
- Use `selected-stage-exited` (not `selected-stage-completed`) when the source stage is still active

## Re-entry Counter Pattern

When stages can be re-entered (e.g., from an ExceptionStage returning to origin, or a rework loop), use counter variables to differentiate first-pass vs re-entry behavior.

### Declaring the Counter Variable

Add to `root.data.uipath.variables.inputOutputs`:

```json
{
  "id": "finishedRunCountIntake",
  "name": "finishedRunCountIntake",
  "type": "number",
  "internal": true
}
```

The FE sets `internal: true` for system-managed counters.

### Using in Conditions

**First-pass exit (counter is 0 or null):**

```json
{
  "id": "Condition_<6chars>",
  "displayName": "Tasks completed rule",
  "type": "exit-only",
  "marksStageComplete": true,
  "rules": [[{
    "rule": "required-tasks-completed",
    "id": "Rule_<6chars>",
    "conditionExpression": "=js:(vars.finishedRunCountIntake == null || vars.finishedRunCountIntake == 0)"
  }]]
}
```

**Re-entry exit (counter > 0):**

```json
{
  "id": "Condition_<6chars>",
  "displayName": "'Intake' re-entry exit",
  "type": "return-to-origin",
  "marksStageComplete": false,
  "rules": [[{
    "rule": "selected-tasks-completed",
    "id": "Rule_<6chars>",
    "selectedTasksIds": ["<lastTaskId>"],
    "conditionExpression": "=js:(vars.finishedRunCountIntake != null && vars.finishedRunCountIntake > 0)"
  }]]
}
```

**Task entry on re-entry (skip early tasks, run only follow-up):**

```json
{
  "id": "Condition_<6chars>",
  "displayName": "StageEntered",
  "rules": [[{
    "rule": "current-stage-entered",
    "id": "Rule_<6chars>",
    "conditionExpression": "=js:(vars.finishedRunCountIntake != null && vars.finishedRunCountIntake > 0)"
  }]]
}
```

### Counter Naming Convention

Use `finishedRunCount<StageName>` where `<StageName>` is the PascalCase stage label:
- `finishedRunCountIntake`
- `finishedRunCountReview`
- `finishedRunCountSettlement`

### Runtime Behavior

The runtime increments the counter each time the stage completes a full run. The agent does not write counter-increment logic — the runtime manages it automatically. The agent only:
1. Declares the counter variable in `inputOutputs`
2. Uses `=js:vars.finishedRunCount<Stage>` in `conditionExpression` to gate behavior

## Deprecated Fields

The following ExceptionStage fields are **deprecated** and should not be used:

| Deprecated Field | Replacement |
|---|---|
| `isTerminalStage` | Use `exitConditions` with `type: "exit-only"` and add a case exit condition on root |
| `exitRulesType` | Use `exitConditions` with explicit `type` on each exit condition |
| `exitRules` | Use `exitConditions` array |
| `entryRules` | Use `entryConditions` array |

Always use the structured `entryConditions` and `exitConditions` arrays instead of the legacy flat rule arrays.
