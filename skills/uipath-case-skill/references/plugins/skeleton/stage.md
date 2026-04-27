# Stage — Implementation

## Stage Node Skeleton

```json
{
  "id": "Stage_<6chars>",
  "type": "case-management:Stage",
  "position": { "x": 100, "y": 200 },
  "style": { "width": 304, "opacity": 0.8 },
  "measured": { "width": 304, "height": 128 },
  "width": 304,
  "zIndex": 1001,
  "data": {
    "label": "<Stage Name>",
    "parentElement": { "id": "root", "type": "case-management:root" },
    "isInvalidDropTarget": false,
    "isPendingParent": false,
    "description": "<stage description>",
    "isRequired": true,
    "tasks": [],
    "entryConditions": [],
    "exitConditions": [],
    "slaRules": []
  }
}
```

## Fixed Fields

Always use these values — do not change them:

`style`: `{ "width": 304, "opacity": 0.8 }` | `measured`: `{ "width": 304, "height": 128 }` | `width`: `304` | `zIndex`: `1001` | `parentElement`: `{ "id": "root", "type": "case-management:root" }` | `isInvalidDropTarget`: `false` | `isPendingParent`: `false`

## Position Layout

Stages go left-to-right: `x = 100 + (N-1) × 500`, `y = 200`.

Exception stages branch vertically below the triggering stage: same `x`, `y = 600` (or lower to avoid overlap).

## Reading from Planning (tasks.md)

```
## T02: Create stage "Stage 1"
- isRequired: true
- description: Performs initial processing...
```

Maps to: `data.label` ← `"Stage 1"`, `data.isRequired` ← `true`, `data.description` ← the description string. `tasks`, `entryConditions`, `exitConditions` start as `[]`.

---

## ExceptionStage

An `ExceptionStage` is a stage used as an error or exception handler that branches off the main flow.

### When to Use ExceptionStage vs Regular Stage

| Situation | ExceptionStage? |
|---|---|
| Stage handles errors or exceptions from another stage | Yes |
| All tasks should always re-run if the stage is re-entered | Yes |
| Stage is part of the normal sequential workflow | No — use regular Stage |

**Key difference:** In an ExceptionStage, **all tasks always run on re-entry** regardless of `shouldRunOnlyOnce`. Use this when every step of the error-handling flow should re-execute.

**Typical pattern:** Main Stage → (error path) → ExceptionStage → (return-to-origin) → back to Main Stage.

**Exit type:** Always `return-to-origin` unless the exception is terminal. Set `isRequired: false` on the node.

**Layout:** Place below the main flow; connect with `bottom` → `top` handles.

### ExceptionStage Node Skeleton

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

### Edge from Main Stage to ExceptionStage

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

### Re-entry Behaviour

`shouldRunOnlyOnce` is set to `false` on tasks in the example above. In an ExceptionStage, the runtime forces all tasks to run on every re-entry regardless of this value — but set it explicitly to `false` to make intent clear.

### isRequired on ExceptionStage

Set `isRequired: false` on the ExceptionStage node itself. Exception stages should not be required for normal case completion — they only activate on error paths.
