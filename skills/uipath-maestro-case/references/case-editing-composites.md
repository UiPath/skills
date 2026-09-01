# Case Editing — Composite Operations

> **"Edit" below means a targeted patch of one slice, not a tool name.** Use the `Edit` tool, or a single-hunk `apply_patch` if your harness has no `Edit` tool. A patch whose hunk spans the whole file is a whole-file Write in patch form and is forbidden the same way. Full tool table: [case-editing-primitives.md § Skeleton-then-Edit](case-editing-primitives.md#skeleton-then-edit--the-only-cadence-for-caseplanjson).

<!-- Split out of case-editing-operations.md so each part can be read whole. Foundations and the quick reference are in [case-editing-operations.md](case-editing-operations.md); the add/delete/bind atoms these recipes compose are in [case-editing-primitives.md](case-editing-primitives.md). -->

> **Prerequisite:** every recipe below composes the atoms in [case-editing-primitives.md](case-editing-primitives.md) and obeys the per-section batch write contract there.

## Composite Operations

### Insert a stage between two existing stages

1. Add the new stage node (with `data.*` fields only — no layout fields, per Rule 18).
2. Add a `stage-entry-conditions` rule on the new stage referencing the upstream stage (`selected-stage-completed`).
3. Re-point the downstream stage's entry condition to reference the new stage instead of the upstream stage.

No edges are involved — reachability is entirely condition-driven.

### Replace a placeholder task with an enriched task

See [placeholder-tasks.md § Upgrade Procedure](placeholder-tasks.md). The upgrade edits the task's `data` field in place to add `taskTypeId`, schema-driven `inputs`/`outputs`, and any required context — keeping the task's `id` and `elementId` unchanged so any conditions referencing it remain valid.

### Re-sync a task after its source schema changed

The task's source resource (action-app / agent / process / api-workflow / connector activity) added, removed, renamed, or retyped an input/output. The task's `taskTypeId` / `data.inputs` / `data.outputs` are now stale. Edit in place — keep `id` and `elementId` so conditions and `=vars.*` / `=bindings.*` references stay valid.

1. **Re-fetch the current schema** (read-only CLI — never hand-author, per § Responsibilities):
   - Non-connector task: `uip maestro case registry pull --force`, then `uip maestro case tasks describe ... --output json`.
   - Connector activity / trigger: `uip maestro case spec --type ... --output json` (unified endpoint — see [connector-integration.md](connector-integration.md)).
2. Read `caseplan.json`; locate the task by `id`.
3. Edit the task's `data` slice to match the fetched schema: update `taskTypeId` if it changed; add / remove / rename `data.inputs[]` and `data.outputs[]`. Keep `id` and `elementId = ${stageId}-${taskId}` unchanged.
4. **Re-bind affected inputs.** For each added / renamed / retyped input, fix its `data.inputs[i]` entry (literal/expression `value` or cross-task `sourceStage`/`sourceTask`/`sourceOutput`) per [bindings-and-expressions.md](bindings-and-expressions.md). Prefix: `=vars.X` / `=bindings.X` for a single lookup, `=js:...` for dotted access or operators.
5. **Repoint consumers of removed/renamed outputs.** Any other task input or condition referencing a dropped output now dangles — repoint or remove it. Prune top-level `bindings` entries no longer referenced.
6. **If the resource binding set changed (connector or non-connector), regenerate `bindings_v2.json`** ([bindings-v2-sync.md](bindings-v2-sync.md)) and run `uip solution resources refresh` before debug/publish (Rule 14) — same scope as § Repoint a non-connector task step 5 and the brownfield After-edits step 2. If the change repointed or dropped a binding, also prune the orphan ([bindings-v2-sync.md § Prune orphaned solution resources](bindings-v2-sync.md#prune-orphaned-solution-resources)). A pure schema-only re-sync (same resource, `data.inputs`/`data.outputs` reshaped but no `bindings[]` entry added/removed/repointed) leaves `bindings_v2.json` unchanged — skip the refresh in that case.
7. Edit — narrow slices targeting the task's `data` (and any consumer / bindings slices). Never whole-file Write. Validate at the section boundary.

### Repoint a non-connector task at a different resource

Swap which process / agent / RPA / api-workflow / case-management resource a task runs. The node references its resource indirectly — `data.name` / `data.folderPath` are `=bindings.<id>` pointers into top-level `bindings[]` ([process impl-json](plugins/tasks/process/impl-json.md), [bindings impl-json](plugins/variables/bindings/impl-json.md)). The new resource almost always has a different I/O schema, so this is a **superset of § Re-sync a task after its source schema changed** plus a binding swap. Keep the task `id` / `elementId` / `entryConditions` so references stay valid.

1. **Re-resolve the new resource** — `uip maestro case registry pull --force`, then search the cache files ([registry-discovery.md](registry-discovery.md)) for the new name + folder. Capture its `entityKey`, resolved `name`, and `folders[0].fullyQualifiedName` (the resolved folder path — never the raw SDD folder). Record the swap in `registry-resolved.json`.
2. **Swap the resource bindings — respect dedup.** The task's two binding entries (`propertyAttribute` `name` / `folderPath`) share `resourceKey = <folderPath>.<name>`.
   - Old pair referenced **only** by this task → update each entry's `default` (new name / folder) and `resourceKey` (`<newFolderPath>.<newName>`) in place.
   - Old pair **shared** with other tasks (deduped by `default + resource + resourceKey`) → do NOT mutate in place. Create or reuse a binding pair for the new resource, repoint this task's `data.name` / `data.folderPath` to the new ids, then prune the old pair if no task references it any longer (caseplan `bindings[]` only — the solution resource goes in step 5).
3. **Re-sync the schema.** Follow § Re-sync a task after its source schema changed steps 1–5 against the new resource: `uip maestro case tasks describe --type <type> --id <newEntityKey> --output json`, update `data.inputs` / `data.outputs`, re-bind inputs, repoint downstream consumers of dropped outputs.
4. **If the task type also changes** (e.g. process → agent): update the node `type`, the bindings' `resource` / `resourceSubType` per the new type's [impl-json](plugins/tasks/), and rebuild `data` per that type's recipe — still keeping `id` / `elementId` / `entryConditions`.
5. Regenerate `bindings_v2.json` ([bindings-v2-sync.md](bindings-v2-sync.md)) and run `uip solution resources refresh` before debug/publish (Rule 14) — the swap changes which Orchestrator resource declaration the case needs. Then prune the resource the swap orphaned ([bindings-v2-sync.md § Prune orphaned solution resources](bindings-v2-sync.md#prune-orphaned-solution-resources)).
6. Edit — narrow slices for the task `data`, the bindings array, and any consumer slices. Never whole-file Write. Validate at the section boundary.

### Move a task to a different stage or lane

Relocate a task within the case. **Keep the task `id`** so conditions and cross-task bindings referencing it stay valid — but every `elementId` is stage-scoped and MUST be recomputed.

1. Read `caseplan.json`. Locate the task in its source `stageNode.data.tasks[oldLane]`.
2. **Recompute every stage-scoped `elementId` — the step most easily missed** (a move looks like layout, but `elementId` encodes the owning stage):
   - the task itself: `elementId = ${destStageId}-${taskId}`
   - any `wait-for-connector` entry-condition rule on the task, and each entry in that rule's `uipath.outputs[]`: `elementId = ${destStageId}-${ruleId}`
   - (root `inputOutputs[]` companions are `elementId: "root"` — NOT stage-scoped, leave them.)
3. Remove the task from the source `data.tasks[oldTaskSet]` and insert it into the destination task set in the preserved `data.tasks` order. Parallel task sets remain allowed, but shared destination task sets are valid only for explicitly parallel or parallel-after-predecessor siblings. For `runs-sequentially` strict-chain tasks or other non-parallel entry modes, insert the task as its own single-task set; lane/task-set placement is structural, while entry conditions carry sequencing.
4. **Repoint cross-task bindings that consume this task's outputs.** Any other task input with `sourceTask == <taskId>` keeps `sourceTask`, but its `sourceStage` must change to `<destStageId>`. Confirm ordering still holds — a consumer can only read a task that runs before it; moving the task later in the flow can invalidate the binding.
5. **Re-check the moved task's `entryConditions[]`:**
   - `current-stage-entered` — no change; it follows the task to the destination stage.
   - `selected-tasks-completed` — `selectedTasksIds` left behind in the source stage now gate across stages; repoint to a task in the destination or remove if the dependency no longer applies.
   - `runs-sequentially` — the moved task must be in its own single-task set unless it is explicitly part of a parallel-after-predecessor sibling set; re-evaluate lane membership (step 3) in both stages so strict sequential chains stay as consecutive single-task sets.
   - **Reverse sweep — tasks left behind in the source stage.** Any task remaining in the source stage whose `selected-tasks-completed.selectedTasksIds` names the moved task now gates *across stages* (the gater stayed put, the gated task left). Repoint each such reference to a surviving source-stage task, or remove it if the dependency no longer applies. This is the inverse of the moved task's own gater re-check above — easy to miss because step 5 otherwise looks only at the moved task.
6. Update the task's `id-map.json` entry `stageId` if the sidecar is present.
7. Edit — narrow slices for the source and destination `data.tasks`, the recomputed `elementId`s, and any consumer-binding slices. Never whole-file Write. Validate at the section boundary.

### Rename or delete a global variable or argument

The runtime resolver matches `=vars.<id>` by **exact string equality on `Variable.id`** ([global-vars impl-json](plugins/variables/global-vars/impl-json.md)). Renaming or removing a variable dangles every consumer, and `validate` does not reliably catch a dangling `=vars.*` — sweep them by hand.

1. Read `caseplan.json`. Note the variable's `id` (the resolver key) and its owning array: top-level `variables.{inputs,outputs,inputOutputs}[]`, a `task.data.outputs[]` self-declaration, or a trigger output.
2. **Sweep every consumer of `=vars.<id>` / `=bindings.<id>`:**
   - task `data.inputs[].value`
   - condition / rule `conditionExpression` (stage entry/exit, task entry, case exit) — including `=js:...` expressions that reference `vars.<id>` inside a larger expression
   - connector body fields and `rule.uipath.context` entries
   - the `inputOutputs[]` companion (`id == <name>`) and any `var` pointer aimed at this slot
3. **Rename:** update `id` (and mirror `var` / `target` where they equal it — `name` / `source` keep their original value, per the global-vars Uniqueness Rule) in the owning array, then update every swept consumer to the new identifier.
   **Delete:** remove the declaration from its owning array and its `inputOutputs[]` companion, then repoint or remove every swept consumer. An input left bound to a deleted variable must get a new `value` or be cleared.
4. Connector consumers only — if a swept reference was a connector binding, regenerate `bindings_v2.json` ([bindings-v2-sync.md](bindings-v2-sync.md)) and run `uip solution resources refresh` before debug/publish. If a Connection binding was dropped, also prune the orphan ([bindings-v2-sync.md § Prune orphaned solution resources](bindings-v2-sync.md#prune-orphaned-solution-resources)).
5. Edit — narrow slices per consumer location and the owning array. Never whole-file Write. Validate at the section boundary.

### Change a variable's type or default

Mutate a variable's `type` / `body` / `default` in place — keep its `id` so every `=vars.<id>` reference stays valid. **Cannot be faked by delete + re-add**: re-adding re-mints a fresh `id` and dangles every consumer (§ Rename or delete). The `type` is duplicated across several coordinated slots ([global-vars/impl-json.md](plugins/variables/global-vars/impl-json.md)); change all of them in one pass or the FE picker and runtime disagree.

1. Read `caseplan.json`. Identify the variable's category and every slot that carries its `type`:
   - **Internal variable** (`variables.inputOutputs[]`): the single companion entry's `type` (+ `body` when `type == "jsonSchema"`).
   - **Out argument** (`variables.outputs[]` formal + `inputOutputs[]` companion): both entries' `type`; the companion's `body` for `jsonSchema`.
   - **In argument** (three entries — `root.inputs[]` formal slot, `root.inputOutputs[]` companion, `triggerNode.data.inputs.outputs[]` bridge): change `type` on **all three**. The bridge's `type` must match or the fire-time copy mis-types.
2. **Type change** — set the new `type` on every slot from step 1. For `type == "jsonSchema"`, set `body` to the new schema on the formal slot and companion (the FE picker reads `body` to discover sub-fields). For `type == "file"`, apply the file-type carve-outs ([global-vars/impl-json.md § In argument](plugins/variables/global-vars/impl-json.md)): companion + formal slot get `body: <FILE_TYPE_JSON_SCHEMA>`, and an In-arg's `default` MUST stay `""`.
3. **Default change** — set `default` on the formal slot (`root.inputs[]` for an In-arg, the `variables.outputs[]`/`inputOutputs[]` entry otherwise). A file-typed variable rejects any `default` other than `""`.
4. **Re-validate every `=vars.<id>` consumer against the new type.** A condition/SLA expression that compared the variable as one type (`=js:vars.amount > 5`) may now be malformed against the new type (e.g., string). Repoint or fix each consumer; `validate` does not catch a type-mismatched `=js:*` expression.
5. Edit — narrow slices for each coordinated slot and any reworked consumer. Never whole-file Write. Validate at the section boundary.

### Modify or remove an SLA or escalation

The add path is [plugins/sla/impl-json.md](plugins/sla/impl-json.md); this is the in-place modify / remove. SLA rules live in `metadata.slaRules[]` (root target) or `node.data.slaRules[]` (stage target); each rule carries an `escalationRule[]`. Each rule has a **required** `id` (`sla_` + 8 chars, schema v26); escalations carry an `esc_` id. Address a rule by `id` or array index.

1. Read `caseplan.json`. Locate the SLA array — `metadata.slaRules[]` for the root target, else the stage node's `data.slaRules[]` (find by `data.label`).
2. **Modify a rule:** edit the target rule's `count` / `unit` / `expression` in place. Keep the default rule (`expression == "=js:true"`) **last**; never reorder it ahead of a conditional rule.
3. **Remove a rule:** delete the rule object from `slaRules[]` (its nested `escalationRule[]` goes with it — drop those `esc_` ids from `id-map.json`). If removing leaves the target with **no** SLA rules, remove the `slaRules` key entirely ([sla/impl-json.md](plugins/sla/impl-json.md) emission rule 5) — do not leave an empty array or an orphan default. If conditional rules remain, the `=js:true` default must still be present and last.
4. **Modify an escalation:** edit its `action.recipients[]`, `triggerInfo.type`, or `atRiskPercentage` in place. `atRiskPercentage` is present only when `triggerInfo.type == "at-risk"` — drop the field when switching to `sla-breached`. Omit `displayName` entirely rather than emitting `undefined`.
5. **Remove an escalation:** delete the entry from its parent rule's `escalationRule[]` by `esc_` id; drop the `esc_` id from `id-map.json`. Leave `escalationRule: []` on the rule (never omit the key — [sla/impl-json.md](plugins/sla/impl-json.md) emission rule 4).
6. Edit — narrow slices targeting the specific rule / escalation entry. Never whole-file Write. Validate at the section boundary.

### Replace a trigger with a different type

Swap a trigger's type in place (e.g., manual → timer, or manual → event) — keep the node `id` so `id-map.json` and any references stay valid.

1. Read `caseplan.json`.
2. Locate the Trigger node by `id`. Rewrite its `data.inputs` to the target type's shape per the target plugin's recipe — [triggers/manual](plugins/triggers/manual/impl-json.md), [triggers/timer](plugins/triggers/timer/impl-json.md), [triggers/event](plugins/triggers/event/impl-json.md). The target type dictates the move:
   - **→ manual:** **delete the `data.inputs` key entirely** — a manual trigger has no `data.inputs` ([manual/impl-json.md](plugins/triggers/manual/impl-json.md) "No `data.inputs` key"). Do not leave an empty or stale block.
   - **→ timer:** set `data.inputs = { serviceType: "timer", … }` per the timer recipe.
   - **→ event:** set `data.inputs = { serviceType: "Intsvc.EventTrigger", … }` per the event recipe (or the placeholder shape if the connector is unresolved).

   Preserve `data.display.label`, `data.typeVersion`, `data.description`, and `data.parentElement` (secondary triggers).
3. **Run the In-arg / trigger-output variable cascade when the bridge host changes.** The In-arg bridge lives on `triggerNode.data.inputs.outputs[]` ([global-vars/impl-json.md § In argument](plugins/variables/global-vars/impl-json.md)). Replacing → manual removes `data.inputs` and therefore the only host for `outputs[]`, silently orphaning every bridge and its trigger-sourced companion. For each bridge dropped by the type change, sweep `=vars.<name>` consumers and prune/repoint the `root.inputs[]` formal slot + `root.inputOutputs[]` companion per § Rename or delete a global variable or argument (Delete path). When the target type still hosts `outputs[]` (timer / event), re-emit the bridges on the new `data.inputs.outputs[]`.
4. Update the matching `entry-points.json` entry. The `filePath` `#<triggerId>` fragment stays (id unchanged). **Note:** manual and timer entry-points `input`/`output` are always empty `{ "type": "object", "properties": {} }` ([manual/impl-json.md](plugins/triggers/manual/impl-json.md#recipe--entry-pointsjson-append-to-entrypoints), [timer/impl-json.md § entry-points.json append](plugins/triggers/timer/impl-json.md)) — only `displayName` can change for those targets. Event triggers may carry a non-empty io shape.
5. **If the type change added or dropped a Connection binding** (manual/timer → event adds one; event → manual/timer drops one), regenerate `bindings_v2.json` ([bindings-v2-sync.md](bindings-v2-sync.md)) and run `uip solution resources refresh` before debug/publish (Rule 14). On a drop, then prune the orphaned Connection ([bindings-v2-sync.md § Prune orphaned solution resources](bindings-v2-sync.md#prune-orphaned-solution-resources)).
6. Edit — narrow slices targeting that node's `data.inputs`, the `entry-points.json` entry, and any swept variable slices. Never whole-file Write.
7. Validate at the section boundary.

### Re-target an event trigger (same type, different event)

Keep an event trigger as an event trigger but point it at a different connector event (different object / operation / filter). Distinct from § Replace a trigger with a different type (which changes the *type*). Keep the node `id`.

1. **Re-fetch the case-spec** for the new event — `uip maestro case spec --type trigger --output json` (never hand-author connector schemas; see [connector-integration.md](connector-integration.md) and [plugins/triggers/event/impl-json.md](plugins/triggers/event/impl-json.md)).
2. Read `caseplan.json`; locate the Trigger node by `id`. Rebuild `data.inputs` (`serviceType: "Intsvc.EventTrigger"` + the new `context[]` / `inputs[]` / `outputs[]` / `bindings[]`) from the fetched spec.
3. **Regenerate the trigger's root bindings + variable bridges.** A different event changes the Connection/Folder bindings and the trigger-output → companion wiring. Re-run the trigger-output dispatch ([global-vars/impl-json.md Loop A](plugins/variables/global-vars/impl-json.md)): drop bridges/companions for outputs the old event produced and the new event no longer does (sweep `=vars.*` consumers per § Rename or delete a global variable or argument), add the new ones.
4. **Update `entry-points.json`** `input`/`output` if the event's io shape changed; the `#<triggerId>` fragment stays.
5. **Regenerate `bindings_v2.json`** + repopulate the IS connection cache ([bindings-v2-sync.md](bindings-v2-sync.md)) and run `uip solution resources refresh` before debug/publish (Rule 14) — the new event needs its own Connection resource declaration. Then prune the orphaned Connection ([bindings-v2-sync.md § Prune orphaned solution resources](bindings-v2-sync.md#prune-orphaned-solution-resources)).
6. Edit — narrow slices for the node's `data.inputs`, root bindings / `inputOutputs[]`, and `entry-points.json`. Never whole-file Write. Validate at the section boundary.

> If the connector / connection is unresolved, downgrade to the event placeholder shape ([plugins/triggers/event/impl-json.md § Placeholder fallback](plugins/triggers/event/impl-json.md)) rather than fabricating IDs.

### Convert a Stage to/from an Exception Stage

An exception (secondary) stage is **not** a distinct node type — it is a regular `case-management:Stage` node carrying `data.stageType: "secondary"`. `stageType` is the enum `["primary", "secondary"]`; primary stages **omit** the field entirely. So the node `type` never changes — the **only** JSON delta is the presence/value of `data.stageType`. Keep the node `id` so tasks, conditions, and `=vars.*` references stay valid (delete + re-add is forbidden, [brownfield.md](brownfield.md) "preserve IDs").

1. Read `caseplan.json`; locate the stage node by `id` (always `type: "case-management:Stage"`).
2. **Primary → Secondary (exception):** add `data.stageType: "secondary"`. Leave `data.entryConditions` / `data.exitConditions` as they are — a secondary stage is condition-entered, so ensure it has ≥1 entry condition (add one per [plugins/conditions/stage-entry-conditions/impl-json.md](plugins/conditions/stage-entry-conditions/impl-json.md) if it has none).
3. **Secondary → Primary:** **remove the `data.stageType` key** (primary stages omit it — do not set `"primary"` explicitly unless the file already does). Re-check the stage's reachability: a primary stage still needs ≥1 entry condition (`case-entered` if first, else `selected-stage-completed` / `selected-stage-exited`).
4. `isInterrupting` is **not** part of this delta — it lives on the entry-condition *rule*, not the stage node. Leave it alone.
5. Edit — narrow slice targeting that node's `data.stageType` key (and any reworked entry condition). Never whole-file Write. Validate at the section boundary.

### Re-wire a stage transition — RETIRED (no edges)

Transitions are not edges. To change where a stage flows, edit the relevant stage's entry/exit conditions (the target stage's `stage-entry-conditions` rule, and the source's `stage-exit-conditions` when it diverges). See the conditions plugins.

---

---

**Atoms:** [case-editing-primitives.md](case-editing-primitives.md). **Foundations and quick reference:** [case-editing-operations.md](case-editing-operations.md).

<!-- END: case-editing-composites.md -->
