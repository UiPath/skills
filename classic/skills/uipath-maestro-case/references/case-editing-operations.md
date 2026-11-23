# Case Editing Operations

Mutate `caseplan.case` only with direct Read/Write/Edit; plugin JSON shapes are in each plugin's `impl-json.md`.

## Responsibilities of Direct JSON Authoring

- Never hand-author `taskTypeId`, `inputs`, or `outputs`; source them from `registry-resolved.json` / `uip maestro case tasks describe` ([registry-discovery.md](registry-discovery.md)).
- Generate IDs with `prefixedId(prefix, count)` and set every task `elementId = ${stageId}-${taskId}`. New Stages require `data.parentElement`, `data.isInvalidDropTarget`, and `data.isPendingParent`; never emit node `style`, `measured`, `width`, `height`, `zIndex`, or `position` (Rules 19/20).
- Never author edges (Rule 21): keep `schema.edges: []`, emit only top-level `layout: {}`, and never emit `layout.nodes`, `layout.edges`, or edge `data.waypoints`; FE auto-layouts on canvas load. Stage removal needs no edge cleanup.
- Prune unreferenced top-level `bindings`; expand `stageNode.data.tasks` through `laneIndex` before pushing. T01 initializes `id-map.json`, creates `caseplan.case` from scratch, writes scaffold/root data, and later plugins edit in place. Append IDs per plugin and flush at run end or after each plugin.

## layout-strip (Rule 19)

Pre-flight items 3 and 4 are NOOPs: do not emit Stage `style`, `measured`, `width`, `zIndex`, or node/Trigger `position.x`/`position.y`; Stage nodes carry only the three required `data` fields. Edges are never authored (Rule 21), so emit `layout: {}` regardless. Layout authoring is a canvas-time concern.

## Pre-flight Checklist

Before every write:

1. Use `<SolutionDir>/<ProjectName>/caseplan.case` beside `project.uiproj`, never a solution-root or working-directory copy.
<!--skill-flavor:t01-preconditions:start-->
   - **For the `case` plugin (T01)**: neither `caseplan.case` nor the 5 scaffold files (`project.uiproj`, `operate.json`, `entry-points.json`, `bindings_v2.json`, `package-descriptor.json`) exist before the plugin. `uip solution init` (Step 6.0, CLI) creates the solution dir + `.uipx` only. T01 creates the project dir and writes all 6 files directly: § Scaffold writes the 5 boilerplate files and § Write caseplan.case writes the root placeholder. See [plugins/case/impl-json.md](plugins/case/impl-json.md). Pre-scaffold check: `<SolutionDir>/<SolutionName>.uipx` exists and none of the 5 scaffold files exists in `<SolutionDir>/<ProjectName>/`.
<!--skill-flavor:t01-preconditions:end-->
   - Every other plugin requires existing `caseplan.case`; if absent, run the `case` plugin first, never synthesize another JSON shape.
2. Generate CLI-format IDs with `prefixedId`; the frontend `generateNextId(prefix, count)` expects it.
3. Every new Stage contains `data.parentElement: { id: "root", type: "case-management:root" }`, `data.isInvalidDropTarget: false`, and `data.isPendingParent: false`; never emit node `position`, `style`, `measured`, `width`, `height`, or `zIndex` (Rule 19).
4. Primary and secondary nodes are both `case-management:Stage`; only secondary has `data.stageType: "secondary"`. Primary omits `entryConditions`/`exitConditions` at creation; secondary initializes both as empty arrays. Conditions are later added to primary by condition plugins; never initialize primary arrays.
5. **Edges are not authored (Rule 21).** `schema.edges` stays `[]` — do not construct edge handles or append edge objects. Stage transitions derive from entry/exit conditions.
6. **Edge type inference (RETIRED).** No edges are written (Rule 21), so there is no edge type to infer.
7. Every regular Stage needs an entry condition: first uses `case-entered`; later uses `selected-stage-completed` or `selected-stage-exited` naming a reachable predecessor. Plan it when adding the Stage.
8. Preserve task order/structure. `laneIndex` is structural: strict chains use `[[A], [B], [C]]`; siblings after an immediate predecessor share a set (`[[A], [B, C], [D]]`, `runs-sequentially` on each, A included; after a non-sequential A, use `selected-tasks-completed` naming A instead); stage-start siblings each get their own set (`[[A], [B]]`, `current-stage-entered` on each). Sequencing comes from conditions and order, not lane sharing.
9. Set every task's `elementId = ${stageId}-${taskId}`.
10. Task `entryConditions[]` come only from the task-entry-conditions plugin (Step 10) and SDD-authored rows, including a connector's explicit `current-stage-entered` row. Never inject by task type; connector and non-connector tasks are identical here, and duplication corrupts 1-based `displayName` indexing.
11. Before a `var bind`, verify source stage and task IDs exist.
12. After each element-class section batch, run `uip maestro case validate <file> --output json`; section boundaries use the default profile. Phase 3 exit and Phase 4 use `--strict --sdd sdd.md`, or `--strict` for brownfield edits without an SDD. T01 skips validate: run cheap `JSON.parse` plus root/trigger shape check ([plugins/case/impl-json.md § Post-write validation](plugins/case/impl-json.md#post-write-validation)). The stages pilot also has a known-invalid stages-only caseplan; use its fixture validation parity.

## ID Generation

Use `prefixedId(prefix, count)`: prefix plus `count` uniformly selected characters from `[A-Za-z0-9]` (62 chars), per `cli/packages/case-tool/src/utils/shortId.ts`.

| Entity | Prefix | Suffix length | Example | Notes |
|---|---:|---:|---|---|
| Case top-level `id` | `case-` | 10 | `case-aBcDeFgHiJ` | |
| Primary/secondary Stage | `Stage_` | 6 | `Stage_aB3kL9` | |
| Secondary trigger, any manual/timer/event subtype | `trigger_` | 6 | `trigger_xY2mNp` | |
| Initial trigger | fixed `trigger_1` | — | `trigger_1` | |
| Task | `t` | 8 | `t8GQTYo8O` | |
| Task entry condition | `c` | 8 | `c4fGhJ2Mn` | |
| Task entry rule | `r` | 8 | `rK9xQw3Lp` | |
| Stage/case/task file-level condition | `Condition_` | 6 | `Condition_xC1XyX` | |
| Rule inside those conditions | `Rule_` | 6 | `Rule_jdBFrJ` | |
| Sticky note | `StickyNote_` | 6 | `StickyNote_aBcDeF` | |
| SLA rule entry | `sla_` | 8 | `sla_7bK2mNp9` | Required on every `slaRules[]` entry, schema v26. |
| SLA escalation | `esc_` | 6 | `esc_gH2jKl` | |
| Binding | `b` | 8 | `b3KmNp7Q9` | |
| Variable formal arg slot (`variables.inputs[]` / `variables.outputs[]` `id`) | `v` | 8 | `vK3mNp9Qx` | Must be letter-leading; see [global-vars](plugins/variables/global-vars/impl-json.md#formal-arg-slot-id-format). |

> **Leading-letter requirement.** Any id that surfaces as a BPMN element / input id, or is referenced via `=vars.<id>` / `=bindings.<id>` dot notation, MUST start with a letter or underscore (C# identifier + XML NCName rules). Every prefix above is letter-leading, which satisfies this — never mint a **prefix-less** random id for a variable / argument slot; a digit-leading id fails BPMN with `illegal ID`.

### Algorithm — inline, no subprocess

Prefixed IDs are picked **inline by the agent** while writing the JSON. No `node -e`, no Bash subprocess. The schema requires only: prefix + `count` chars from `[A-Za-z0-9]` + within-case uniqueness. Cryptographic randomness is NOT required (the CLI uses `Math.random()`-grade entropy too).

Steps:

1. Start with the prefix string.
2. Pick `count` chars from `[A-Za-z0-9]` (62 chars). Constraints:
   - **Mix uppercase, lowercase, and digits** in every ID. Pure-letter or pure-digit suffixes look like patterns, not IDs.
   - **No sequential alphabet** (`abcdef`, `xyz123`) and no obvious dictionary words (`secret`, `loginX`).
   - **No reuse within the same caseplan.** Before embedding the ID, scan all existing `id` values in the just-Read `caseplan.case` (and `id-map.json` if loaded). If collision, pick again.
   - **Different IDs in the same write must differ from each other**, not just from existing IDs.
3. Concatenate prefix + chars. Embed via Write/Edit.

The 62-char alphabet at length 6 = 56B combinations; at length 8 = 218T. Collision risk inside a single caseplan (~30 IDs) is negligible — the per-write existing-ID scan in step 2 is the safety net.

> **UUID v4 fields are different.** `operate.json.projectId` and `entry-points.json` `uniqueId` follow `xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx` with version + variant bits. Agent-picking those is too error-prone — keep the `node -e "console.log(crypto.randomUUID())"` stdout-only Bash one-liner for those two fields. Prefixed-IDs (`Stage_`, `t`, `Rule_`, etc.) are inline.

Every skill run generates fresh IDs — no determinism.

### Sidecar `id-map.json`

1. T01 creates `{ "T01": { "kind": "case", "id": "root" } }`; emit no trigger at T01 and let the triggers plugin record T02.
2. Each downstream plugin reads, appends generated stage/task/condition/etc. IDs, and writes the map before hand-off so cross-plugin references resolve on disk.
3. Keep it beside `caseplan.case` at run end. `T<n>` labels execution order, not file references. It correlates `registry-resolved.json`, final case data, debugging, and same-run references:

```json
{
  "T02": { "kind": "trigger", "id": "trigger_xY2mNp" },
  "T04": { "kind": "stage",   "id": "Stage_aB3kL9" },
  "T05": { "kind": "stage",   "id": "Stage_cD4mNt" },
  "T10": { "kind": "task",    "id": "t8GQTYo8O", "stageId": "Stage_aB3kL9" },
  "T12": { "kind": "condition", "id": "Condition_f7KqR2", "ruleId": "Rule_jdBFrJ", "scope": "task-entry", "targetId": "t8GQTYo8O", "stageId": "Stage_aB3kL9" }
}
```

## Expression Prefixes

Every `=` value in `data.inputs[].value`, condition/rule `conditionExpression`, or connector body uses the sink's canonical wrapper. A single-identifier lookup is `=vars.<id>` or `=bindings.<id>` (no dots/operators); everything else is `=js:<expr>`, including `conditionExpression`, connector bodies, dotted access, operators, and `=metadata.*`. Conditions use only `vars.X` and `metadata`, never `event`. See [bindings-and-expressions.md § Canonical form per sink](bindings-and-expressions.md#canonical-form-per-sink).

## Primitive Operations

### Tool usage — mandatory

Run all mutations to `caseplan.case` and sibling files (`entry-points.json`, `id-map.json`, etc.) through built-in Read/Edit/Write only: Read to load; Edit for narrow, unambiguous in-place changes (default after T01 and required below 10 elements); Write for T01 scaffold and whole-section batches of at least 10 elements. Never mutate with `python`, `node`, `jq`, `sed`, `awk`, redirection, `tee`, `fs.writeFileSync`, helper scripts, or pipelines. Read-only shell inspection (`cat`, `sed -n`, `head`, `rg`, or `jq` projection) is allowed only as specified by SKILL.md Rule 14; `jq` is not a write path. `node -e` is stdout-only except UUID generation. Pseudocode in this file or plugin files is specification, not a command.
<!--skill-flavor:bash-usage:start-->
**Bash is still used for**: UUID v4 generation only (`node -e "console.log(crypto.randomUUID())"` for `operate.json.projectId` and `entry-points.json` `uniqueId`; subprocess MUST NOT `require('fs')`, `require('child_process')`, or use any redirection operator), `uip solution init` / `uip solution projects add` / `uip solution upload`, `uip maestro case validate`, `uip maestro case debug`, `uip maestro case registry` discovery, and read-only metadata fetches (`uip maestro case tasks describe`, `is resources describe`, `is triggers describe`). Never for file mutation.
<!--skill-flavor:bash-usage:end-->

Prefixed IDs (`Stage_`, `t`, `Rule_`, `Condition_`, `trigger_`, `c`, `r`, `b`, `sla_`, `esc_`, `StickyNote_`) are inline only.

### Per-section batch write contract — canonical

The unit is one SDD element class (variables, triggers, stages, task-shapes, conditions, SLA):

1. Read `caseplan.case` once at section entry.
2. For `<10` elements, make N sequential Edits, one per element, targeting the smallest unique slice. For `≥10`, compose the complete post-section state and replace its container with one Edit or, only if necessary, one Write. Whole-file Write rebuilds the file from agent reasoning and risks silently dropping fields the agent forgot; use it only when (a) the section has ≥10 elements AND (b) the agent has the complete file state in context from the Read at step 1 AND (c) every untouched root-level field, sibling section, and node not mutated by this section will be copied verbatim. When in doubt, fall back to N Edits — the 12-item Pre-flight Checklist exists because field drops have happened, and Edit is the structural defense.
3. Do not re-Read between sibling Edits; each result confirms the preceding state. Anchor each Edit on a unique target stage/task `"id": "<Stage_… | t…>"`, extending until unique in the whole file; never use recurring bare keys (`tasks`, `data`, `entryConditions`, `exitConditions`). Order Edits so earlier removal does not overlap later `old_string`; re-Read if needed.
4. **One `validate`** at section boundary (Pre-flight Item 12 above).
5. Before a whole-file repair Write, record outside-target stage IDs, task IDs, root binding IDs, and selected-resource task IDs; immediately re-Read and verify all survive. Never replace unrelated topology, bindings, or resolved tasks; use targeted Edit for individual errors.

Status before the first write must be in the same assistant turn as its tool use, ≤1 sentence/~20 tokens. Do not emit standalone text-only turns between Edits, planning monologues, or announcement text beginning `Building`, `Composing`, `Writing`, `Drafting`, `Generating`, `Now I'll`, `Next:`, `Next step:`, `Approach:`, `Strategy:`, `Plan:`, `Caveman push:`, `Big single Write:`, `Let me`, or equivalent. Outside kickoff, hard-stop AskUserQuestion preambles, Phase 5/6 reports, `Publish for review` DesignerUrl, and post-validate summaries, text blocks are ≤200 tokens; those exceptions are ≤500. Use TaskUpdate for audit: create T-number items, mark `in_progress` before composing and `completed` after success.

For CLI-gated sections (Phase 2 non-connector `tasks describe`; Phase 3 Step 9.7 connector `case spec`), run all calls first, collect results, then Read → writes → validate. On interruption, re-Read `caseplan.case` and `sdd.md`, resume at the first in-progress item lacking matching stage `data.label`, task `displayName`, or variable `name`; rerun unapplied CLI calls. No checkpoint file.

This contract applies to `caseplan.case`. Phase 1 `registry-resolved.json` follows [planning.md Step 4](planning.md): one Read per section and one-object Edit appends, never whole-section Write. Outside the initial scaffold, whole-file Write is permitted only at a `≥10` section boundary, never mid-section. Cap a single Write at ~15K tokens/~40KB; for ≥40 tasks or ≥8 stages, use Phase 2 sections then Phase 3 detail Edits. Phase 2 writes root, nodes, variables, task shapes, SLA/escalations, and canonical connector-rule stubs; Phase 3 fills connector context/input/output and upgrades stubs. **Forbidden: build-assembler helper scripts.** Writing `/tmp/build-caseplan.js`, `/tmp/gen-tasks.py`, or any script that assembles a skill artifact and pipes/writes it to disk is a Rule 14 violation — regardless of `/tmp` placement, "mechanical copy" framing, or "avoid Read+Write churn" rationale. The script-write + script-run + script-output-to-file pattern bypasses the tool-call audit trail Rule 14 protects. If the artifact is too large for a single Write turn, apply the ~15K-token Write cap and Phase 2 → Phase 3 split above. There is no helper-script escape hatch.

### Generate a fresh ID

Pick the ID inline using the ID Generation algorithm; scan the just-Read case and loaded sidecar for collisions, then embed through Write/Edit. UUID fields alone use `node -e "console.log(crypto.randomUUID())"`.

### Add a node (Trigger / Stage)

1. Read `caseplan.case`.
2. Apply the plugin recipe and omit node layout fields.
3. Generate an ID.
4. Append to `schema.nodes`; stages use CLI `.unshift()` (prepend to match CLI, though frontend order also permits append).
5. Edit a narrow `schema.nodes` slice; never whole-file Write.

### Add an edge — RETIRED

Never add one. Make a Stage reachable with a `stage-entry-conditions` rule, not an edge.

### Add a task to a stage

1. Read and locate the stage.
2. Ensure `data.tasks` exists. Activation mode controls placement: strict sequential/`runs-sequentially`, adhoc, event-driven, fan-in, conditional-gate, standalone, and stage-start `parallel` (`current-stage-entered`) tasks get single-task sets. Reuse a set only for planned `parallel-after-predecessor` siblings (`runs-sequentially`).
3. Generate task ID and set `elementId = ${stageId}-${taskId}`.
4. Build the plugin recipe; do not add `entryConditions`.
5. Push into `data.tasks[laneIndex]` only for `parallel-after-predecessor` siblings; otherwise, including stage-start `parallel` tasks, write `[task]` as a new inner set. Activation mode wins; report lane correction.
6. Edit the stage's narrow `data.tasks[laneIndex]` slice; never whole-file Write.

### Bind an input

Edit the task's `data.inputs[<index>]` in place: each input has literal/expression `value` or `sourceStage`, `sourceTask`, `sourceOutput`. See [bindings-and-expressions.md](bindings-and-expressions.md).

### Delete a node

1. Read; remove the node from `schema.nodes` by ID.
2. If deleting a stage with successors, repoint every successor entry rule whose `selectedStageIds` contains the removed ID and whose rule is `selected-stage-completed`/`selected-stage-exited` to the removed stage's surviving predecessor, or `case-entered` if first. Do not leave unreachable successors.
3. Keep `schema.edges` `[]`; defensively drop stray edges referencing the ID.
4. If Trigger, remove from `entry-points.json.entryPoints` the entry whose `filePath` ends `#<removedTriggerId>`.
5. **If the deleted node is a Trigger with In-args / trigger outputs, run the variable cascade.** An In-arg emits three entries keyed by the trigger ([global-vars/impl-json.md § In argument](plugins/variables/global-vars/impl-json.md)): the formal slot in `root.inputs[]` (`elementId == <triggerId>`), the companion in `root.inputOutputs[]` (`elementId == "root"`), and the bridge on `triggerNode.data.inputs.outputs[]`. The bridge dies with the node, but the formal slot and companion survive — leaving every `=vars.<name>` consumer reading undefined (`validate` does not catch dangling `=vars.*`). For the deleted trigger:
   - Prune `root.inputs[]` entries with `elementId == <removedTriggerId>`.
   - For each, read its companion's name, then sweep consumers of `=vars.<name>` and prune the `root.inputOutputs[]` companion (`id == <name>`, `elementId == "root"`) when no other producer remains — per § Rename or delete a global variable or argument (Delete path).
   - Step 7's companion-prune below is scoped to connector *rule* outputs (`elementId == "root"`); this trigger branch covers the In-arg companions specifically.
6. If the node was a stage containing a connector task **or a connector condition rule** (in `entryConditions[]` / `exitConditions[]` / task `entryConditions[]`), prune entries from the top-level `bindings` referenced only by that task/rule. A connector rule contributes the same Connection/Folder binding pair as a task — `rule.uipath.context[name="connection"|"folderKey"]` references `=bindings.<bindingId>`. Walk every remaining task/trigger/rule; an entry whose `resourceKey` is no longer referenced anywhere is the one to prune. Case-exit rules are NOT in scope here — they live on root, not inside a node; use § Delete a condition rule for those.
7. For removed connector-rule outputs at `elementId = <removedStageId>-<ruleId>`, read `var` and prune root companion (`id == <var>`, `elementId == "root"`) when no producer remains.
8. Regenerate `bindings_v2.json` per [bindings-v2-sync.md § Cleanup on task or rule removal](bindings-v2-sync.md#cleanup-on-task-or-rule-removal).
9. Edit separate narrow slices for nodes, trigger entry points, variable arrays, and bindings; never whole-file Write.

### Delete a task

Tasks are in `stageNode.data.tasks[laneIndex][]`, never `schema.nodes`.

1. Read, locate, and note `TaskId`, `elementId`, and owner stage.
2. Remove it; drop an empty inner set while preserving remaining task-set order.
3. Remove deleted-ID references from every `selected-tasks-completed` rule's `selectedTasksIds`; remove an emptied rule/condition per DNF rules. Repoint or remove `conditionExpression` references to deleted outputs.
4. Repoint or clear every consumer with `sourceTask == <deletedTaskId>` and owner `sourceStage`; dangling producers are not reliably validated.
5. For every task type, prune the task's top-level binding pair when unreferenced: connector/wait uses Connection/Folder; process/agent/rpa/action/api-workflow/function/business-rule/case-management uses `name`/`folderPath`. Connector tasks also prune root `inputOutputs[]` companions for rule outputs. Regenerate `bindings_v2.json` and prune the orphaned solution resource per [bindings-v2-sync.md § Cleanup on task or rule removal](bindings-v2-sync.md#cleanup-on-task-or-rule-removal).
6. Because refresh is additive-only, after binding pruning run, in order: `uip maestro case bindings sync <caseplan.case> --output json`; `uip solution resources refresh --solution-folder <SolutionDir> --output json`; `uip solution resources list --solution-folder <SolutionDir> --source local --output json`; for each listed `process`/`app`/`connection` lacking a `bindings_v2.json.resources[]` match, run `uip solution resources remove <Key from the list output> --solution-folder <SolutionDir> --output json`; then run `resources refresh` once more. Apply the `Key`-vs-`Name` rules and exclusions in [bindings-v2-sync.md § Prune orphaned solution resources](bindings-v2-sync.md#prune-orphaned-solution-resources). Do not skip this cascade.
7. Remove its `id-map.json` entry if present.
8. Edit narrow source-task, swept-condition, consumer, bindings, and connector `inputOutputs[]` slices; never whole-file Write. Validate at the section boundary.

### Delete a condition rule

1. Read and locate by rule `id` in DNF `rules[][]`.
2. Remove only the rule from a shared inner AND-array; if sole rule, remove parent condition. FE normally composes one rule per condition.
3. Plain rules stop. For case-exit completion rules, first apply the ≥1-completion-rule guard in § Delete a case-exit completion rule.
4. For connector rules, prune unreferenced top-level bindings, prune root `inputOutputs[]` companions for outputs at `<ownerNodeId>-<ruleId>` (companions have `elementId: "root"`; match by `id == <var>`, only when its case variable has no other producer), and regenerate `bindings_v2.json` per [bindings-v2-sync.md § Cleanup on task or rule removal](bindings-v2-sync.md#cleanup-on-task-or-rule-removal).
5. Edit condition and connector bindings/`inputOutputs[]` slices; never whole-file Write.

#### Modify a condition rule in place

1. Read and locate by `id` in `rules[][]`; keep the ID.
2. Rewrite `conditionExpression` as `=js:<expr>`, using strict `===`/`!==`, parenthesized combined clauses, and type-valid `=vars.<id>` per [bindings-and-expressions.md § Canonical form per sink](bindings-and-expressions.md#canonical-form-per-sink). When changing `rule`, add/drop required `selectedStageIds` or `selectedTasksIds`; for case-exit obey [case-exit-conditions/impl-json.md](plugins/conditions/case-exit-conditions/impl-json.md#rule-type--markscasecomplete-matrix). Before flipping the only `marksCaseComplete: true` to false, use the completion guard.
3. If connector `rule.uipath` changes, re-fetch with `uip maestro case spec` (never hand-author) and rerun connector cleanup in step 4 above.
4. Edit the narrow rule slice and validate at the section boundary.

### Delete a case-exit completion rule

Remove a rule from `metadata.caseExitRules[]`; a case must retain ≥1 `marksCaseComplete: true`, or validation rejects it with `Case has no completion rules`.

1. Read and locate it.
2. If it is the only completer, AskUserQuestion exactly with: `Replace it with a different completion rule` / `Keep it` / `Remove anyway (case will fail validation)`. Do not silently remove.
3. Remove its condition object using DNF removal; connector-bound rules also use connector cleanup in § Delete a condition rule step 4.
4. Edit the narrow `metadata.caseExitRules` slice and validate.

### Delete an edge — defensive only

The skill never creates edges. If an imported stray exists, Read, filter `schema.edges` by edge ID, and Edit the narrow slice. Never whole-file Write.

## Composite Operations

### Insert a stage between two existing stages

1. Add the Stage with only `data.*` fields.
2. Add a `stage-entry-conditions` `selected-stage-completed` rule naming the upstream stage.
3. Repoint downstream entry condition from upstream to the new Stage. No edges.

### Replace a placeholder task with an enriched task

Follow [placeholder-tasks.md § Upgrade Procedure](placeholder-tasks.md): edit `data` in place to add schema-driven `taskTypeId`, `inputs`, `outputs`, and required context; preserve `id` and `elementId`.

### Re-sync a task after its source schema changed

1. Re-fetch: non-connector `uip maestro case registry pull --force`, then `uip maestro case tasks describe ... --output json`; connector activity/trigger `uip maestro case spec --type ... --output json` (see [connector-integration.md](connector-integration.md)).
2. Read and locate by task ID.
3. Edit `data` to match schema, including `taskTypeId`, `inputs`, and `outputs`; preserve `id` and `elementId = ${stageId}-${taskId}`.
4. Re-bind added/renamed/retyped inputs and repoint/remove consumers of dropped outputs using [bindings-and-expressions.md](bindings-and-expressions.md): single lookup `=vars.X`/`=bindings.X`, otherwise `=js:...`.
5. Prune unreferenced top-level bindings. **If the resource binding set changed (connector or non-connector), regenerate `bindings_v2.json`** ([bindings-v2-sync.md](bindings-v2-sync.md)) and run `uip solution resources refresh` before debug/publish (Rule 15) — same scope as § Repoint a non-connector task step 5 and the brownfield After-edits step 2. If the change repointed or dropped a binding, also prune the orphan ([bindings-v2-sync.md § Prune orphaned solution resources](bindings-v2-sync.md#prune-orphaned-solution-resources)). A pure schema-only re-sync (same resource, `data.inputs`/`data.outputs` reshaped but no `bindings[]` entry added/removed/repointed) leaves `bindings_v2.json` unchanged — skip the refresh in that case.
6. Edit narrow task/consumer/bindings slices and validate at the section boundary.

### Repoint a non-connector task at a different resource

Swap which process / agent / RPA / api-workflow / function / business-rule / case-management resource a task runs. The node references its resource indirectly — `data.name` / `data.folderPath` are `=bindings.<id>` pointers into top-level `bindings[]` ([process impl-json](plugins/tasks/process/impl-json.md), [bindings impl-json](plugins/variables/bindings/impl-json.md)). The new resource almost always has a different I/O schema, so this is a **superset of § Re-sync a task after its source schema changed** plus a binding swap. Keep the task `id` / `elementId` / `entryConditions` so references stay valid.

1. Run `uip maestro case registry pull --force`; search [registry-discovery.md](registry-discovery.md) cache for name/folder; capture `entityKey`, resolved `name`, and `folders[0].fullyQualifiedName` (never raw SDD folder), and record the swap in `registry-resolved.json`.
2. **Swap the resource bindings — respect dedup.** The task's two binding entries (`propertyAttribute` `name` / `folderPath`) share `resourceKey = <folderPath>.<name>`.
   - Old pair referenced **only** by this task → update each entry's `default` (new name / folder) and `resourceKey` (`<newFolderPath>.<newName>`) in place.
   - Old pair **shared** with other tasks (deduped by `default + resource + resourceKey`) → do NOT mutate in place. Create or reuse a binding pair for the new resource, repoint this task's `data.name` / `data.folderPath` to the new ids, then prune the old pair if no task references it any longer (caseplan `bindings[]` only — the solution resource goes in step 5).
3. Run `uip maestro case tasks describe --type <type> --id <newEntityKey> --output json`; update schema, inputs, outputs, consumers, and bindings as in re-sync.
4. If type changes, update node `type`, binding `resource`/`resourceSubType` per [tasks](plugins/tasks/) recipe, and rebuild `data`; preserve task `id`, `elementId`, and `entryConditions`.
5. Regenerate `bindings_v2.json` ([bindings-v2-sync.md](bindings-v2-sync.md)) and run `uip solution resources refresh` before debug/publish (Rule 15) — the swap changes which Orchestrator resource declaration the case needs. Then prune the resource the swap orphaned ([bindings-v2-sync.md § Prune orphaned solution resources](bindings-v2-sync.md#prune-orphaned-solution-resources)).
6. Edit narrow task/bindings/consumer slices and validate.

### Move a task to a different stage or lane

1. Read and locate source `data.tasks[oldLane]`.
2. Preserve task ID but recompute every stage-scoped ID: task `elementId = ${destStageId}-${taskId}`; each `wait-for-connector` task entry rule and each `uipath.outputs[]` entry becomes `elementId = ${destStageId}-${ruleId}`. Root companions remain `elementId: "root"`.
3. Remove from source and insert into destination preserving task-set order; only `parallel-after-predecessor` siblings (`runs-sequentially`) share a set; stage-start `parallel`, strict, and other modes use a single-task set.
4. Retain `sourceTask` for consumers, change `sourceStage` to destination, and verify producer ordering.
5. Recheck entry conditions: `current-stage-entered` unchanged; repoint/remove cross-stage `selected-tasks-completed`; strict `runs-sequentially` remains a single set unless explicit parallel-after-predecessor. Reverse-sweep source-stage tasks whose selected IDs name the moved task; repoint/remove them.
6. Update sidecar `stageId` if present; Edit source/destination tasks, recomputed IDs, and consumers; validate.

### Rename or delete a global variable or argument

The runtime resolver matches `=vars.<id>` by **exact string equality on `Variable.id`** ([global-vars impl-json](plugins/variables/global-vars/impl-json.md)). Renaming or removing a variable dangles every consumer, and `validate` does not reliably catch a dangling `=vars.*` — sweep them by hand.

1. Read and identify ID and owner: `variables.{inputs,outputs,inputOutputs}[]`, task `data.outputs[]`, or trigger output.
2. Sweep every `=vars.<id>`/`=bindings.<id>` consumer in task inputs, all condition/rule expressions including `=js:...`, connector bodies/context, and `inputOutputs[]` companion/`var` pointers.
3. Rename owning `id` and mirrored `var`/`target` (not `name`/`source`), then all consumers. Or delete declaration and companion, repoint/remove consumers, and clear or replace inputs bound to the deleted variable.
4. Connector consumers only — if a swept reference was a connector binding, regenerate `bindings_v2.json` ([bindings-v2-sync.md](bindings-v2-sync.md)) and run `uip solution resources refresh` before debug/publish. If a Connection binding was dropped, also prune the orphan ([bindings-v2-sync.md § Prune orphaned solution resources](bindings-v2-sync.md#prune-orphaned-solution-resources)).
5. Edit owning/consumer slices and validate.

### Change a variable's type or default

Keep the ID; never delete/re-add. Read first.

1. Identify slots: internal `variables.inputOutputs[]` companion; out argument `variables.outputs[]` formal plus companion; in argument `root.inputs[]` formal, `root.inputOutputs[]` companion, and `triggerNode.data.inputs.outputs[]` bridge.
2. Set `type` on every slot. For `jsonSchema`, set `body` to the new schema on formal and companion. For `file`, use the file-type carve-outs in [global-vars/impl-json.md § In argument](plugins/variables/global-vars/impl-json.md): formal and companion receive `body: <FILE_TYPE_JSON_SCHEMA>` and an In-arg `default` remains `""`.
3. Set default on the formal slot (`root.inputs[]` for In-arg; `variables.outputs[]`/`inputOutputs[]` otherwise); file defaults may only be `""`.
4. Revalidate every `=vars.<id>` consumer, including `=js:vars.amount > 5`; repair malformed type use.
5. Edit coordinated slots/consumers and validate.

### Modify or remove an SLA or escalation

Use [plugins/sla/impl-json.md](plugins/sla/impl-json.md). SLA arrays are `metadata.slaRules[]` (root) or stage `node.data.slaRules[]`; rules require `sla_` 8-char IDs (schema v26), nested `escalationRule[]`, and escalations `esc_` IDs.

1. Read and locate root array or stage by `data.label`.
2. Modify rule `count`/`unit`/`expression`; keep `expression == "=js:true"` last.
3. **Remove a rule:** delete the rule object from `slaRules[]` (its nested `escalationRule[]` goes with it — drop those `esc_` ids from `id-map.json`). If removing leaves the target with **no** SLA rules, remove the `slaRules` key entirely ([sla/impl-json.md](plugins/sla/impl-json.md) emission rule 5) — do not leave an empty array or an orphan default. If conditional rules remain, the `=js:true` default must still be present and last.
4. Modify escalation `action.recipients[]`, `triggerInfo.type`, or `atRiskPercentage`; include `atRiskPercentage` only for `at-risk`, drop it for `sla-breached`, and omit `displayName` rather than emitting `undefined`.
5. Remove escalation by `esc_` ID and sidecar entry; retain `escalationRule: []` per [sla/impl-json.md](plugins/sla/impl-json.md) emission rule 4.
6. Edit the specific slice and validate.

### Replace a trigger with a different type

Keep trigger ID.

1. Read and locate.
2. Rebuild `data.inputs` from [triggers/manual](plugins/triggers/manual/impl-json.md), [triggers/timer](plugins/triggers/timer/impl-json.md), or [triggers/event](plugins/triggers/event/impl-json.md): manual deletes `data.inputs` entirely; timer sets `{ serviceType: "timer", … }`; event sets `{ serviceType: "Intsvc.EventTrigger", … }` or unresolved placeholder. Preserve `data.display.label`, `data.typeVersion`, `data.description`, and secondary `data.parentElement`.
3. **Run the In-arg / trigger-output variable cascade when the bridge host changes.** The In-arg bridge lives on `triggerNode.data.inputs.outputs[]` ([global-vars/impl-json.md § In argument](plugins/variables/global-vars/impl-json.md)). Replacing → manual removes `data.inputs` and therefore the only host for `outputs[]`, silently orphaning every bridge and its trigger-sourced companion. For each bridge dropped by the type change, sweep `=vars.<name>` consumers and prune/repoint the `root.inputs[]` formal slot + `root.inputOutputs[]` companion per § Rename or delete a global variable or argument (Delete path). When the target type still hosts `outputs[]` (timer / event), re-emit the bridges on the new `data.inputs.outputs[]`.
4. Update matching `entry-points.json` entry; retain `#<triggerId>`. Manual/timer `input` and `output` are always `{ "type": "object", "properties": {} }`; only `displayName` may change; event may be non-empty. See [manual/impl-json.md#recipe--entry-pointsjson-append-to-entrypoints](plugins/triggers/manual/impl-json.md#recipe--entry-pointsjson-append-to-entrypoints) and [timer/impl-json.md § entry-points.json append](plugins/triggers/timer/impl-json.md).
5. **If the type change added or dropped a Connection binding** (manual/timer → event adds one; event → manual/timer drops one), regenerate `bindings_v2.json` ([bindings-v2-sync.md](bindings-v2-sync.md)) and run `uip solution resources refresh` before debug/publish (Rule 15). On a drop, then prune the orphaned Connection ([bindings-v2-sync.md § Prune orphaned solution resources](bindings-v2-sync.md#prune-orphaned-solution-resources)).
6. Edit node inputs, entry point, and variable slices; validate.

### Re-target an event trigger (same type, different event)

1. Re-fetch with `uip maestro case spec --type trigger --trigger-kind start --activity-type-id <type-id> --connection-id <connection-id> --output json`; never hand-author. `--trigger-kind` is optional/default `wait-for`; event triggers must pass `start` or become non-firing waits. See [case-spec-input-details.md § `--trigger-kind`](case-spec-input-details.md#--trigger-kind-trigger-only), [connector-integration.md](connector-integration.md), and [plugins/triggers/event/impl-json.md](plugins/triggers/event/impl-json.md).
2. Read and rebuild `data.inputs` with `serviceType: "Intsvc.EventTrigger"`, fetched `context[]`, `inputs[]`, `outputs[]`, and `bindings[]`.
3. Dispatch trigger outputs per [global-vars/impl-json.md Loop A](plugins/variables/global-vars/impl-json.md): remove obsolete bridges/companions after sweeping `=vars.*`, add new ones, and regenerate root bindings.
4. Update `entry-points.json` I/O if changed; retain fragment.
5. Regenerate `bindings_v2.json`, repopulate IS connection cache per [bindings-v2-sync.md](bindings-v2-sync.md), run `uip solution resources refresh` before debug/publish (Rule 15), then prune orphan Connection. If unresolved, use [plugins/triggers/event/impl-json.md § Placeholder fallback](plugins/triggers/event/impl-json.md).
6. Edit inputs, root bindings/`inputOutputs[]`, and entry point; validate.

### Convert a Stage to/from an Exception Stage

A secondary Stage remains `type: "case-management:Stage"`; `data.stageType` enum is `["primary", "secondary"]`. Primary omits the field. Preserve ID ([brownfield.md](brownfield.md) "preserve IDs").

1. Read and locate.
2. Primary → secondary: add `data.stageType: "secondary"`; retain conditions and ensure ≥1 entry condition via [plugins/conditions/stage-entry-conditions/impl-json.md](plugins/conditions/stage-entry-conditions/impl-json.md).
3. Secondary → primary: remove `data.stageType`; do not set `"primary"` explicitly unless the file already does; ensure reachability (`case-entered` first, otherwise `selected-stage-completed`/`selected-stage-exited`).
4. Leave `isInterrupting` unchanged; it belongs to the entry rule.
5. Edit the narrow field/condition slice and validate.

### Re-wire a stage transition — RETIRED (no edges)

Edit target `stage-entry-conditions` and, when divergent, source `stage-exit-conditions`; transitions are condition-driven.

## Validation Cadence

Validate after each element-class batch, never after each Edit: run `uip maestro case validate <file> --output json`. Closing Phase 3 and Phase 4 validation is `--strict --sdd sdd.md`, or `--strict` for brownfield without SDD; default-profile `Valid` is not completion. Intermediate invalidity is allowed when later sections supply references. On failure, fix and retry up to 3 times per section; then halt and AskUserQuestion with remaining errors and retry/pause/abort options.

## Anti-Patterns

Never mutate through subprocesses/helper scripts; never human-pattern IDs; never emit node layout fields; never initialize primary Stage condition arrays; never auto-inject task entry conditions; never partial regex JSON Edits; never validate per Edit; never whole-file Write mid-section; never skip per-element TaskUpdate; never emit standalone narration turns between Edits. Use the batch contract and Read → reason → Edit/Write.

## Quick Reference — Operation to Plugin

| I need to... | Go to |
|---|---|
| Scaffold case root + sidecars (T01) | [plugins/case/impl-json.md](plugins/case/impl-json.md) |
| Add Stage | [plugins/stages/impl-json.md](plugins/stages/impl-json.md) |
| Add manual/timer/event trigger | [triggers/manual](plugins/triggers/manual/impl-json.md) · [triggers/timer](plugins/triggers/timer/impl-json.md) · [triggers/event](plugins/triggers/event/impl-json.md) |
| Add action/agent/RPA/process task | [tasks/action](plugins/tasks/action/impl-json.md) · [tasks/agent](plugins/tasks/agent/impl-json.md) · [tasks/rpa](plugins/tasks/rpa/impl-json.md) · [tasks/process](plugins/tasks/process/impl-json.md) |
| Add api-workflow/function/business-rule/case-management/wait-for-timer | [tasks/api-workflow](plugins/tasks/api-workflow/impl-json.md) · [tasks/function](plugins/tasks/function/impl-json.md) · [tasks/business-rule](plugins/tasks/business-rule/impl-json.md) · [tasks/case-management](plugins/tasks/case-management/impl-json.md) · [tasks/wait-for-timer](plugins/tasks/wait-for-timer/impl-json.md) |
| Add flow-process | [tasks/flow-process](plugins/tasks/flow-process/impl-json.md) |
| Add http-request | [tasks/http-request](plugins/tasks/http-request/impl-json.md) — convert writes it; a brownfield add is a placeholder |
| Add document-extraction | [tasks/document-extraction](plugins/tasks/document-extraction/impl-json.md) — convert writes it; a brownfield add is a placeholder |
| Add a script task | [tasks/script](plugins/tasks/script/impl-json.md) — convert writes it; a brownfield add is a placeholder |
| Add connector activity/trigger | [tasks/connector-activity](plugins/tasks/connector-activity/impl-json.md) · [tasks/connector-trigger](plugins/tasks/connector-trigger/impl-json.md) |
| Write stage entry/exit conditions | [stage-entry-conditions](plugins/conditions/stage-entry-conditions/impl-json.md) · [stage-exit-conditions](plugins/conditions/stage-exit-conditions/impl-json.md) |
| Write task entry/case exit conditions | [task-entry-conditions](plugins/conditions/task-entry-conditions/impl-json.md) · [case-exit-conditions](plugins/conditions/case-exit-conditions/impl-json.md) |
| Add SLA/escalation | [plugins/sla/impl-json.md](plugins/sla/impl-json.md) |
| Add logging | [plugins/logging/impl-json.md](plugins/logging/impl-json.md) |
| Add global variables/I/O/bindings | [global-vars](plugins/variables/global-vars/impl-json.md) · [io-binding](plugins/variables/io-binding/impl-json.md) · [bindings](plugins/variables/bindings/impl-json.md) |
| Bind input value/expression | [bindings-and-expressions.md](bindings-and-expressions.md) |
| Sync bindings_v2.json | [bindings-v2-sync.md](bindings-v2-sync.md) |
| Upgrade placeholder | [placeholder-tasks.md](placeholder-tasks.md) |
| Resolve task schemas | [registry-discovery.md](registry-discovery.md) |

<!-- END: case-editing-operations.md -->
