# Edit Recipes — Brownfield Lookup Table

For structural edits to an existing `caseplan.case` (add, change, or remove tasks/stages), follow the matching recipe and read no other reference unless it names one (Rule 25 exception). For uncovered edits—SLA responses, conditions, triggers, variables—use [brownfield.md § Common edits](brownfield.md#common-edits). All recipes assume [brownfield.md § Read this first](brownfield.md#read-this-first): mutate with Read and Edit only, preserve every existing `id`, never Write the whole file, and use no edges.

## Lookup

| Edit | Recipe |
|---|---|
| Add a wait-for-timer task to a stage | [R1](#r1--add-a-wait-for-timer-task) |
| Add a resource task (process, agent, rpa, action, api-workflow, function, business-rule, case-management) | [R1](#r1--add-a-wait-for-timer-task) steps 1–2 and 4–6; use that type's shape from `plugins/tasks/<type>/impl-json.md` (read it to END) |
| Change a task's `isRequired`, `shouldRunOnlyOnce`, `description`, or `displayName` | [R2](#r2--change-a-task-envelope-field) |
| Remove a task (any type, including one bound to a resource) | [R3](#r3--remove-a-task) |
| Insert a regular stage between two stages | [R4](#r4--insert-a-stage-between-two-stages) |
| Remove a stage and reconnect its neighbours | [R5](#r5--remove-a-stage) |
| Finish any edit | [Close](#close--every-edit) |

**ID formats:** stage `Stage_` + 6 chars; stage- and case-level condition `Condition_` + 6, rule `Rule_` + 6; task `t` + 8; task-level condition `c` + 8, rule `r` + 8. Use unique random alphanumeric IDs case-wide. A task's `elementId` is `<stageId>-<taskId>`.

## R1 — Add a wait-for-timer task

1. Locate the stage by `id`; ensure `data.tasks` exists.
2. Give the task its own inner array: `data.tasks.push([task])`. Share one only when explicitly requested as a parallel sibling of existing tasks; otherwise use its own.
3. Use this shape; `data` contains only `timerType` and the duration; every other field is a top-level sibling:

   ```json
   {
     "id": "t<8 chars>",
     "type": "wait-for-timer",
     "displayName": "<exact name from the request>",
     "elementId": "<stageId>-<taskId>",
     "isRequired": false,
     "shouldRunOnlyOnce": false,
     "data": { "timerType": "timeDuration", "timeDuration": "PT1H" },
     "entryConditions": [
       { "id": "c<8 chars>", "displayName": "Entry rule 1",
         "rules": [[ { "id": "r<8 chars>", "rule": "current-stage-entered" } ]] }
     ]
   }
   ```

   Durations are ISO 8601: `PT3M`, `PT1H30M`, `P2D`; represent weeks as `P7D`. Set `isRequired` and `shouldRunOnlyOnce` as requested; unspecified defaults are `false`.
4. **Every added task carries its own entry condition**—otherwise it validates clean but never starts. Use `current-stage-entered`, unless the request orders it after a same-stage sibling; then use `selected-tasks-completed` with `selectedTasksIds: ["<siblingTaskId>"]`.
5. Make `displayName` unique across all stages and free of `:`.
6. [Close](#close--every-edit).

## R2 — Change a task envelope field

1. Locate the task by `displayName` in its stage's `data.tasks[lane][]`.
2. Edit only the named field in place; preserve `id`, `elementId`, `data`, and `entryConditions`.
3. For `displayName`, preserve case-wide uniqueness and omit `:`. `selectedTasksIds` reference `id`, so renaming needs no condition changes.
4. [Close](#close--every-edit).

## R3 — Remove a task

1. Locate the task in `stageNode.data.tasks[lane]`; note its `id` and `elementId`.
2. Remove it, drop an empty inner array, and preserve remaining order.
3. Remove its `id` from every `selected-tasks-completed` rule's `selectedTasksIds`; remove an emptied rule, then an emptied condition.
4. For any other task input with `sourceTask == <removedId>`, repoint it to a surviving producer or clear it.
5. **Bindings:** if the task referenced root bindings—resource-task `data.name` / `data.folderPath` equal to `=bindings.<id>`, or connector-task `connection` / `folderKey` context entries—delete each root `bindings[]` entry no remaining task, trigger, or rule references.
6. **Solution resources:** only when step 5 deleted a binding, run in order:

   ```bash
   uip maestro case bindings sync "<caseplan.case>" --output json
   uip solution resources refresh --solution-folder "<SolutionDir>" --output json
   uip solution resources list --solution-folder "<SolutionDir>" --source local --output json
   ```

   For each listed `process` / `app` / `connection` without a match in `bindings_v2.json` `resources[]`, run `uip solution resources remove "<Key from the list output>" --solution-folder "<SolutionDir>" --output json`, then run `resources refresh` once more. `refresh` never prunes and `validate` remains `Valid` with the orphan present; Studio Web then fails provisioning. Follow the match rules and never prune the two specified entries in [bindings-v2-sync.md § Prune orphaned solution resources](bindings-v2-sync.md#prune-orphaned-solution-resources).
7. [Close](#close--every-edit).

## R4 — Insert a stage between two stages

For `A → B` becoming `A → New → B`:

1. Add this node to `nodes`; do not add `entryConditions` / `exitConditions` until steps 2–3, and add no layout fields:

   ```json
   {
     "id": "Stage_<6 chars>",
     "type": "case-management:Stage",
     "data": {
       "label": "<exact name>",
       "description": "<from the request, or omit>",
       "isRequired": <true|false as requested; false if unspecified>,
       "parentElement": { "id": "root", "type": "case-management:root" },
       "isInvalidDropTarget": false,
       "isPendingParent": false,
       "tasks": []
     }
   }
   ```
2. Make the new stage enter when A completes:

   ```json
   "entryConditions": [
     { "id": "Condition_<6>", "displayName": "Entry rule 1", "isInterrupting": false,
       "rules": [[ { "id": "Rule_<6>", "rule": "selected-stage-completed", "selectedStageIds": ["<A id>"] } ]] }
   ]
   ```
3. Make it complete when required tasks finish:

   ```json
   "exitConditions": [
     { "id": "Condition_<6>", "displayName": "Exit rule 1", "type": "exit-only", "marksStageComplete": true,
       "rules": [[ { "id": "Rule_<6>", "rule": "required-tasks-completed" } ]] }
   ]
   ```
4. **Repoint B:** in B's entry rules, replace `<A id>` in `selectedStageIds` with the new stage's id; leaving A would let B start alongside the new stage.
5. Add requested tasks using [R1](#r1--add-a-wait-for-timer-task).
6. [Close](#close--every-edit).

## R5 — Remove a stage

For `A → X → B` becoming `A → B`:

1. Remove X's node from `nodes`.
2. **Repoint every successor:** each stage whose entry rule lists X in `selectedStageIds` must list X's predecessor (A), or use `case-entered` if X was first. A successor still pointing to X validates and never runs.
3. For any `metadata.caseExitRules[]` rule naming X in `selectedStageIds`, repoint it to the surviving stage now playing X's role, or remove it; retain at least one rule with `marksCaseComplete: true`.
4. X's tasks were removed with the node: for each, perform [R3](#r3--remove-a-task) steps 3–6 (condition references, consumer inputs, bindings, solution resources).
5. [Close](#close--every-edit).

## Close — every edit

1. Run `uip maestro case validate "<caseplan.case>" --strict --output json`. Fix its report and retry at most 3 times; then stop and AskUserQuestion `Retry with fix` / `Pause for manual edit` / `Abort`. A default-profile `Valid` is not completion.
2. If the edit added, removed, or repointed a binding and R3 step 6 did not run, run `uip maestro case bindings sync "<caseplan.case>" --output json`, then run `uip solution resources refresh --solution-folder "<SolutionDir>" --output json`.
3. Report per [brownfield.md § Completion Output](brownfield.md#completion-output).

<!-- END: edit-recipes-guide.md -->
