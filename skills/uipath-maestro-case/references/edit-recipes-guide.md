# Edit Recipes — Brownfield Lookup Table

Complete recipes for the most common structural edits to an existing `caseplan.json` — adding, changing, and removing tasks and stages. **A row here is sufficient on its own:** when a recipe covers the edit, follow it and read no other reference unless the recipe names one (Rule 25 exception). Anything not covered — SLA responses, conditions, triggers, variables — routes through [brownfield.md § Common edits](brownfield.md#common-edits) as before.

Every recipe assumes [brownfield.md § Read this first](brownfield.md#read-this-first): mutate with Read and Edit only, keep every existing `id`, never Write the whole file, no edges.

## Lookup

| Edit | Recipe |
|---|---|
| Add a wait-for-timer task to a stage | [R1](#r1--add-a-wait-for-timer-task) |
| Add a resource task (process, agent, rpa, action, api-workflow, case-management) | [R1](#r1--add-a-wait-for-timer-task) steps 1–2 and 4–6, with the shape from that type's `plugins/tasks/<type>/impl-json.md` (read it to END) |
| Change a task's `isRequired`, `shouldRunOnlyOnce`, `description`, or `displayName` | [R2](#r2--change-a-task-envelope-field) |
| Remove a task (any type, including one bound to a resource) | [R3](#r3--remove-a-task) |
| Insert a regular stage between two stages | [R4](#r4--insert-a-stage-between-two-stages) |
| Remove a stage and reconnect its neighbours | [R5](#r5--remove-a-stage) |
| Finish any edit | [Close](#close--every-edit) |

**ID formats:** stage `Stage_` + 6 chars; stage- and case-level condition `Condition_` + 6, rule `Rule_` + 6; task `t` + 8; task-level condition `c` + 8, rule `r` + 8. Random alphanumeric, unique case-wide. `elementId` of a task is `<stageId>-<taskId>`.

## R1 — Add a wait-for-timer task

1. Locate the stage node by `id`; ensure `data.tasks` exists.
2. Placement: a task gets its **own** inner array (`data.tasks.push([task])`). Share an existing inner array only when the request explicitly makes it a parallel sibling of the tasks already there. When in doubt, its own array.
3. Shape — `data` holds only `timerType` and the duration; every other field is a top-level sibling:

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

   Durations are ISO 8601: `PT3M`, `PT1H30M`, `P2D`; weeks as `P7D`. Set `isRequired` / `shouldRunOnlyOnce` only as the request states; defaults are `false`.
4. **Every added task carries its own entry condition** — a task with none validates clean and never starts. Use `current-stage-entered` unless the request orders it after a sibling (`selected-tasks-completed` with `selectedTasksIds: ["<siblingTaskId>"]`, same stage only).
5. `displayName` must be unique across all stages and contain no `:`.
6. [Close](#close--every-edit).

## R2 — Change a task envelope field

1. Locate the task inside its stage's `data.tasks[lane][]` by `displayName`.
2. Edit only the named field in place. Keep `id`, `elementId`, `data`, and `entryConditions`.
3. Renaming (`displayName`): keep it unique case-wide and `:`-free; condition `selectedTasksIds` reference the `id`, so they need no change.
4. [Close](#close--every-edit).

## R3 — Remove a task

1. Locate the task in `stageNode.data.tasks[lane]`; note its `id` and `elementId`.
2. Remove it. If its inner array is now empty, drop that inner array; keep the order of the rest.
3. Remove the task's `id` from every `selected-tasks-completed` rule's `selectedTasksIds`; a rule left empty goes, and a condition left with no rules goes.
4. Any other task input with `sourceTask == <removedId>` now reads nothing — repoint it to a surviving producer or clear it.
5. **Bindings.** If the task referenced root bindings (`data.name` / `data.folderPath` = `=bindings.<id>` for a resource task; `connection` / `folderKey` context entries for a connector task), delete those root `bindings[]` entries when no remaining task, trigger, or rule references them.
6. **Solution resources** — only when step 5 deleted a binding. Run, in order:

   ```bash
   uip maestro case bindings sync "<caseplan.json>" --output json
   uip solution resources refresh --solution-folder "<SolutionDir>" --output json
   uip solution resources list --solution-folder "<SolutionDir>" --source local --output json
   ```

   For each listed `process` / `app` / `connection` entry with no match in `bindings_v2.json` `resources[]`, run `uip solution resources remove "<Key from the list output>" --solution-folder "<SolutionDir>" --output json`, then `resources refresh` once more. `refresh` never prunes and `validate` stays `Valid` with the orphan present; Studio Web then fails provisioning. Match rules and the two entries never to prune: [bindings-v2-sync.md § Prune orphaned solution resources](bindings-v2-sync.md#prune-orphaned-solution-resources).
7. [Close](#close--every-edit).

## R4 — Insert a stage between two stages

For `A → B` becoming `A → New → B`:

1. Add the stage node to `nodes` — no `entryConditions` / `exitConditions` keys until steps 2–3 write them, no layout fields:

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

2. Entry on the new stage — enters when A completes:

   ```json
   "entryConditions": [
     { "id": "Condition_<6>", "displayName": "Entry rule 1", "isInterrupting": false,
       "rules": [[ { "id": "Rule_<6>", "rule": "selected-stage-completed", "selectedStageIds": ["<A id>"] } ]] }
   ]
   ```

3. Exit on the new stage — completes when its required tasks are done:

   ```json
   "exitConditions": [
     { "id": "Condition_<6>", "displayName": "Exit rule 1", "type": "exit-only", "marksStageComplete": true,
       "rules": [[ { "id": "Rule_<6>", "rule": "required-tasks-completed" } ]] }
   ]
   ```

4. **Repoint B:** in B's entry rules, replace `<A id>` with the new stage's id in `selectedStageIds`. Leaving A there lets B start alongside the new stage.
5. Tasks the request puts in the new stage: [R1](#r1--add-a-wait-for-timer-task).
6. [Close](#close--every-edit).

## R5 — Remove a stage

For `A → X → B` becoming `A → B`:

1. Remove X's node from `nodes`.
2. **Repoint every successor.** Each stage whose entry rule lists X in `selectedStageIds` now lists X's own predecessor (A) instead — or uses `case-entered` if X was the first stage. A successor left pointing at X validates and never runs.
3. Any `metadata.caseExitRules[]` rule naming X in `selectedStageIds`: repoint to the surviving stage that now plays X's role, or remove it — keeping at least one rule with `marksCaseComplete: true`.
4. X's tasks went with the node: for each one, do [R3](#r3--remove-a-task) steps 3–6 (condition references, consumer inputs, bindings, solution resources).
5. [Close](#close--every-edit).

## Close — every edit

1. `uip maestro case validate "<caseplan.json>" --strict --output json`. Fix what it reports; retry at most 3 times, then stop and AskUserQuestion `Retry with fix` / `Pause for manual edit` / `Abort`. A default-profile `Valid` is not completion.
2. If the edit added, removed, or repointed a binding and R3 step 6 has not run: `uip maestro case bindings sync "<caseplan.json>" --output json`, then `uip solution resources refresh --solution-folder "<SolutionDir>" --output json`.
3. Report per [brownfield.md § Completion Output](brownfield.md#completion-output).

<!-- END: edit-recipes-guide.md -->
