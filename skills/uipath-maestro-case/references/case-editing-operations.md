# Case Editing Operations

All mutations to `caseplan.json` performed via direct read/write/edit of the file. This document covers cross-cutting mechanics; per-node JSON shapes live in each plugin's `impl-json.md`.

---

## Responsibilities of Direct JSON Authoring

When editing `caseplan.json` directly, the agent is responsible for these mechanics:

| Concern | Requirement |
|---|---|
| Task schema (`taskTypeId`, `inputs`, `outputs`) | Never hand-author. Source from `registry-resolved.json` / `uip maestro case tasks describe` — see [registry-discovery.md](registry-discovery.md). Hand-written schemas fail validation. |
| ID generation | Generate IDs per the ID Generation section below using the `prefixedId(prefix, count)` algorithm |
| `elementId` on tasks | Compute and write `${stageId}-${taskId}` on every task |
| Stage data fields | Emit `data.parentElement`, `data.isInvalidDropTarget`, `data.isPendingParent` on every new Stage node. Do NOT emit `style`, `measured`, `width`, `zIndex`, or `position` — see Layout fields below (Rule 18/19) |
| Edges | Not authored (Rule 20) — `schema.edges` stays `[]`; no cleanup needed on stage removal |
| Root-level bindings cleanup | Prune entries from top-level `bindings` no longer referenced by any task |
| Lane array expansion | Ensure `stageNode.data.tasks` is expanded to include `laneIndex` before pushing |
| `id-map.json` sidecar | Initialize on T01 (case plugin); append per plugin as IDs are generated; flush to disk at end of run (or after each plugin for durability) |
| `caseplan.json` file creation | T01 (case plugin) writes the file from scratch; downstream plugins mutate in place |
| Layout fields | Do NOT emit node-level `position`, `style`, `measured`, `width`, `height`, `zIndex`. Do NOT emit edge `data.waypoints`. Emit top-level `layout: {}` — FE auto-layouts on canvas load (Rule 18). |

---

## layout-strip (Rule 18)

The following Pre-flight Checklist items become **NOOPs** because layout state lives in top-level `layout`, not on each node:

- **Item 3 (Stage render fields)** — do NOT emit `style`, `measured`, `width`, `zIndex` on Stage nodes. nodes carry `data.parentElement`, `data.isInvalidDropTarget`, `data.isPendingParent` only.
- **Item 4 (Position computation)** — do NOT compute or emit `position.x`, `position.y` on Stage nodes (or Trigger nodes). FE auto-layouts on canvas load.
- **Edges** — none authored (Rule 20), so no edge `data.waypoints` to emit; skill emits empty `layout: {}` regardless.

Skill emits empty `layout: {}` at top level — never populates `layout.nodes` or `layout.edges`. Layout authoring is a canvas-time concern, not a skill concern.

## Pre-flight Checklist

Before every write to `caseplan.json`, confirm each item. These are the failure modes the CLI normally prevents.

1. **Canonical `caseplan.json` location.** The file lives at `<SolutionDir>/<ProjectName>/caseplan.json` (next to `project.uiproj`). Every Read/Write must target that exact path — not a stray copy in the solution root or working directory.
   - **For the `case` plugin (T01)**: neither `caseplan.json` nor the 5 scaffold files (`project.uiproj`, `operate.json`, `entry-points.json`, `bindings_v2.json`, `package-descriptor.json`) exist before the plugin runs. `uip solution init` (Step 6.0, CLI) creates the solution dir + `.uipx` only. T01 creates the project dir and writes all 6 files directly — § Scaffold writes the 5 boilerplate files, § Write caseplan.json writes the root placeholder. See [plugins/case/impl-json.md](plugins/case/impl-json.md). Pre-scaffold check: `<SolutionDir>/<SolutionName>.uipx` exists AND none of the 5 scaffold files exist yet in `<SolutionDir>/<ProjectName>/`.
   - **For every other plugin**: `caseplan.json` must already exist (the `case` plugin always runs first as T01). If absent, run the `case` plugin first; do not attempt to synthesize a different JSON shape.

2. **IDs match CLI format.** Generate IDs using the `prefixedId` algorithm (see "ID Generation" below). The frontend's `generateNextId(prefix, count)` expects this exact format — deviation risks Studio Web rejection.

3. **Stage `data` fields present on every new Stage:**
   - `data.parentElement: { id: "root", type: "case-management:root" }`
   - `data.isInvalidDropTarget: false`
   - `data.isPendingParent: false`

   Do NOT emit node-level `position`, `style`, `measured`, `width`, `height`, `zIndex` (Rule 18 layout-strip).

4. **Primary Stage vs Secondary Stage at creation time.** Both are `case-management:Stage` nodes; a secondary stage is distinguished by `data.stageType: "secondary"`. Primary stages (no `data.stageType`) are written without `entryConditions` / `exitConditions` keys. Secondary stages (`data.stageType: "secondary"`) initialize both as empty arrays at creation time. Primary stages acquire those keys later when the condition plugins write them. Do not emit empty arrays on primary Stage.

5. **Edges are not authored (Rule 20).** `schema.edges` stays `[]` — do not construct edge handles or append edge objects. Stage transitions derive from entry/exit conditions.

6. **Edge type inference (RETIRED).** No edges are written (Rule 20), so there is no edge type to infer.

7. **Every regular stage has at least one entry condition.** With edges retired, stage entry conditions are the sole reachability contract — orphan stages don't execute. The first stage carries `case-entered`; every other regular stage carries `selected-stage-completed` / `selected-stage-exited` naming a reachable predecessor. When adding a stage, also plan its entry condition (Step 10).

8. **Preserve task structure and order.** Increment `laneIndex` per task only for the structural/layout array when needed. A strict sequential chain uses consecutive single-task sets (`[[A], [B], [C]]`); intentionally parallel siblings share a task set at stage start (`[[A, B], [C]]`) or after an immediate predecessor (`[[A], [B, C], [D]]`). Sequence behavior comes from each task's entry condition and its order in `stageNode.data.tasks`; lane-sharing alone does not express sequence.

9. **Task `elementId` = `${stageId}-${taskId}`.** Compute and write this composite string on every new task.

10. **Entry conditions are SDD-driven — never auto-injected by task type.** A task's `entryConditions[]` are written solely by the task-entry-conditions plugin (Step 10) from the SDD's authored Entry Condition rows — including a connector task's `current-stage-entered`, which the SDD declares as an explicit first row like any ungated task. Do NOT inject a default entry condition at task-creation time based on task type: it produces a duplicate condition and breaks `displayName` indexing (the index is the 1-based position within `entryConditions[]`). Connector and non-connector tasks are treated identically here.

11. **Cross-task bindings reference existing IDs.** Before writing a `var bind` entry, confirm the source stage ID and source task ID both exist in `caseplan.json`.

12. **Validate after every section's batch — with exceptions.** Run `uip maestro case validate <file> --output json` after each `tasks.md` section batch completes (per § Per-section batch write contract below). One validate per section, not one per T-entry. Fixing errors at the section boundary is cheaper than chasing a cascade.
    - **Exception — case plugin (T01):** A case-only caseplan is known-invalid by design (no stage nodes, so the case cannot be entered). Skip `uip maestro case validate` after T01; a cheap `JSON.parse` + root/trigger shape check is the substitute — see [plugins/case/impl-json.md § Post-write validation](plugins/case/impl-json.md#post-write-validation).
    - **Exception — stages plugin (pilot):** A stages-only caseplan is also known-invalid (stages have no entry conditions yet). The plugin's validation parity is captured in the fixture instead.

---

## ID Generation

All IDs follow the CLI's `prefixedId(prefix, count)` scheme: a fixed prefix + `count` random characters drawn uniformly from `[A-Za-z0-9]` (62 chars). Source: `cli/packages/case-tool/src/utils/shortId.ts`.

| Entity | Prefix | Suffix length | Example | Notes |
|---|---|---|---|---|
| Case (top-level `id`) | `case-` | 10 | `case-aBcDeFgHiJ` | |
| Stage (primary + secondary) | `Stage_` | 6 | `Stage_aB3kL9` | |
| Trigger (secondary — any subtype: manual / timer / event) | `trigger_` | 6 | `trigger_xY2mNp` | |
| Initial trigger (first trigger in the case) | fixed literal `trigger_1` | — | `trigger_1` | |
| Task | `t` | 8 | `t8GQTYo8O` | |
| Task entry condition | `c` | 8 | `c4fGhJ2Mn` | |
| Task entry rule | `r` | 8 | `rK9xQw3Lp` | |
| Stage / case / task file-level condition | `Condition_` | 6 | `Condition_xC1XyX` | |
| Rule inside those conditions | `Rule_` | 6 | `Rule_jdBFrJ` | |
| Sticky note | `StickyNote_` | 6 | `StickyNote_aBcDeF` | |
| SLA rule entry | `sla_` | 8 | `sla_7bK2mNp9` | Required on every `slaRules[]` entry (schema v26). |
| SLA escalation | `esc_` | 6 | `esc_gH2jKl` | |
| Binding | `b` | 8 | `b3KmNp7Q9` | |
| Variable formal arg slot (`variables.inputs[]` / `variables.outputs[]` `id`) | `v` | 8 | `vK3mNp9Qx` | In/Out-arg formal slot. Surfaces in case BPMN as `<uipath:input id>` + dot-referenced via `=vars.<id>` — MUST be letter-leading. See [global-vars](plugins/variables/global-vars/impl-json.md#formal-arg-slot-id-format). |

> **Leading-letter requirement.** Any id that surfaces as a BPMN element / input id, or is referenced via `=vars.<id>` / `=bindings.<id>` dot notation, MUST start with a letter or underscore (C# identifier + XML NCName rules). Every prefix above is letter-leading, which satisfies this — never mint a **prefix-less** random id for a variable / argument slot; a digit-leading id fails BPMN with `illegal ID`.

### Algorithm — inline, no subprocess

Prefixed IDs are picked **inline by the agent** while writing the JSON. No `node -e`, no Bash subprocess. The schema requires only: prefix + `count` chars from `[A-Za-z0-9]` + within-case uniqueness. Cryptographic randomness is NOT required (the CLI uses `Math.random()`-grade entropy too).

Steps:

1. Start with the prefix string.
2. Pick `count` chars from `[A-Za-z0-9]` (62 chars). Constraints:
   - **Mix uppercase, lowercase, and digits** in every ID. Pure-letter or pure-digit suffixes look like patterns, not IDs.
   - **No sequential alphabet** (`abcdef`, `xyz123`) and no obvious dictionary words (`secret`, `loginX`).
   - **No reuse within the same caseplan.** Before embedding the ID, scan all existing `id` values in the just-Read `caseplan.json` (and `id-map.json` if loaded). If collision, pick again.
   - **Different IDs in the same write must differ from each other**, not just from existing IDs.
3. Concatenate prefix + chars. Embed via Write/Edit.

The 62-char alphabet at length 6 = 56B combinations; at length 8 = 218T. Collision risk inside a single caseplan (~30 IDs) is negligible — the per-write existing-ID scan in step 2 is the safety net.

> **UUID v4 fields are different.** `operate.json.projectId` and `entry-points.json` `uniqueId` follow `xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx` with version + variant bits. Agent-picking those is too error-prone — keep the `node -e "console.log(crypto.randomUUID())"` stdout-only Bash one-liner for those two fields. Prefixed-IDs (`Stage_`, `t`, `Rule_`, etc.) are inline.

Every skill run generates fresh IDs — no determinism.

### Sidecar `id-map.json`

`id-map.json` is built up incrementally during the run, flushed adjacent to `caseplan.json`. Lifecycle:

1. **T01 (case plugin)** creates the file with the literal root entry: `{ "T01": { "kind": "case", "id": "root" } }`. No trigger is emitted at T01 — the triggers plugin records its entry at T02.
2. **Downstream plugins** read the file, append entries for generated IDs (stage, task, condition, etc.), write back. Each plugin writes the map before handing off to the next so cross-plugin references can resolve via the on-disk file.
3. **End of run:** the file is complete and lives alongside `caseplan.json`.

Mapping T-entries from `tasks.md` to generated IDs:

```json
{
  "T02": { "kind": "trigger", "id": "trigger_xY2mNp" },
  "T04": { "kind": "stage",   "id": "Stage_aB3kL9" },
  "T05": { "kind": "stage",   "id": "Stage_cD4mNt" },
  "T10": { "kind": "task",    "id": "t8GQTYo8O", "stageId": "Stage_aB3kL9" },
  "T12": { "kind": "condition", "id": "Condition_f7KqR2", "ruleId": "Rule_jdBFrJ", "scope": "task-entry", "targetId": "t8GQTYo8O", "stageId": "Stage_aB3kL9" }
}
```

Used for: debugging, downstream cross-task reference resolution within the same skill run, correlating `registry-resolved.json` entries with the final case file.

---

## Expression Prefixes

Every `=`-prefixed value written into `caseplan.json` (`data.inputs[].value`, condition/rule `conditionExpression`, connector body fields) must use the wrap form its **sink** dispatches to — wrong wrap is a silent runtime fault. The two-line rule:

- **Value lookup** (`data.inputs[].value` referencing one identifier): `=vars.<id>` or `=bindings.<id>` — no dots, no operators.
- **JS eval** (everything else — `conditionExpression`, connector body fields, dotted access, operators, `=metadata.*`): `=js:<expr>`. Conditions reference only `vars.X` and `metadata` (no `event` namespace).

Full sink-to-form table, the lookup-vs-JS-eval dispatch, and connector-trigger filter forms: [bindings-and-expressions.md § Canonical form per sink](bindings-and-expressions.md#canonical-form-per-sink).

---

## Validation Cadence

Run `uip maestro case validate <file> --output json` after each `tasks.md` section's batch completes — not after every Edit. Intermediate states can be invalid (e.g., a stage whose entry condition references a stage that will be added next); validate is authoritative at the section boundary.

On failure: fix the reported issue (usually a missing field, malformed ID, or orphan reference) and re-validate. Up to 3 retries per section; if still failing, halt and AskUserQuestion the user with the remaining errors and options to retry, pause, or abort.

---

## Anti-Patterns

- **Do NOT shell out to `python`, `node`, `jq`, `sed`, `awk`, or any other subprocess to mutate `caseplan.json` or its siblings.** Use Read + Write/Edit only. Subprocess scripts bypass the tool-call audit trail and make the mutation invisible in the transcript. See "Tool usage — mandatory" above.
- **Do NOT write helper scripts (`.py`, `.js`, `.sh`) that open / parse / modify / save JSON files.** Even one-shot scripts are forbidden — the agent is the processor, Read/Write/Edit are the only I/O primitives.
- **Do NOT hand-edit IDs with human-readable patterns** (e.g., `my_stage_1`). The frontend's `generateNextId` expects CLI's format.
- **Do NOT emit node-level layout fields** (`position`, `style`, `measured`, `width`, `height`, `zIndex`) — these belong in top-level `layout`, not on the node (Rule 18).
- **Do NOT initialize empty `entryConditions`/`exitConditions` arrays on primary Stages.** The condition plugins add authored arrays in Step 10; secondary stages (`data.stageType: "secondary"`) initialize both arrays when created.
- **Do NOT auto-inject a task `entryCondition` at task-creation time based on task type.** Entry conditions come from the SDD via the task-entry-conditions plugin (Step 10), uniformly across task types. Injecting one early duplicates the Step 10 write and corrupts `displayName` indexing.
- **Do NOT write partial JSON with Edit tool regex.** Round-trip through Read → reason → Edit per the per-section batch contract.
- **Do NOT run validation after every single Edit.** Validate at section boundaries, not per-T-entry.
- **Do NOT use whole-file Write on a populated `caseplan.json`.** It bypasses the section-entry Read snapshot, risks silently dropping fields, and costs output tokens proportional to the whole file. Patch per T-entry, always — `Edit`, or a single-hunk `apply_patch` on a harness with no `Edit` tool. The only whole-file Writes in a build are the T01 scaffold and the Step 7 stage skeleton (per § Per-section batch write contract).
- **Do NOT skip TaskUpdate per T-entry.** TaskUpdate is the audit trail under the per-section batched contract — reviewers track T-by-T progress there.
- **Do NOT emit standalone text-only assistant turns between Edits.** Each costs ~5s inference + ~250K cache replay for zero work. Bundle status text into the same turn as the next tool_use (text block + tool_use block in one content array), or omit entirely — TaskUpdate already shows progress.

---

## Quick Reference — Operation to Plugin

Each operation's JSON shape lives in its plugin's `impl-json.md`. This file covers only the cross-cutting mechanics above.

| I need to... | Go to |
|---|---|
| Scaffold the case root + sidecar files (T01) | [plugins/case/impl-json.md](plugins/case/impl-json.md) |
| Add a Stage (primary / secondary) | [plugins/stages/impl-json.md](plugins/stages/impl-json.md) |
| Add a manual / timer / event trigger | [triggers/manual](plugins/triggers/manual/impl-json.md) · [triggers/timer](plugins/triggers/timer/impl-json.md) · [triggers/event](plugins/triggers/event/impl-json.md) |
| Add an action / agent / RPA / process task | [tasks/action](plugins/tasks/action/impl-json.md) · [tasks/agent](plugins/tasks/agent/impl-json.md) · [tasks/rpa](plugins/tasks/rpa/impl-json.md) · [tasks/process](plugins/tasks/process/impl-json.md) |
| Add an api-workflow / case-management / wait-for-timer task | [tasks/api-workflow](plugins/tasks/api-workflow/impl-json.md) · [tasks/case-management](plugins/tasks/case-management/impl-json.md) · [tasks/wait-for-timer](plugins/tasks/wait-for-timer/impl-json.md) |
| Add a connector-activity task / connector trigger | [tasks/connector-activity](plugins/tasks/connector-activity/impl-json.md) · [tasks/connector-trigger](plugins/tasks/connector-trigger/impl-json.md) |
| Write stage entry / exit conditions | [stage-entry-conditions](plugins/conditions/stage-entry-conditions/impl-json.md) · [stage-exit-conditions](plugins/conditions/stage-exit-conditions/impl-json.md) |
| Write task entry / case exit conditions | [task-entry-conditions](plugins/conditions/task-entry-conditions/impl-json.md) · [case-exit-conditions](plugins/conditions/case-exit-conditions/impl-json.md) |
| Add SLA / escalation | [plugins/sla/impl-json.md](plugins/sla/impl-json.md) |
| Add logging | [plugins/logging/impl-json.md](plugins/logging/impl-json.md) |
| Add global variables / I/O binding / variable bindings | [global-vars](plugins/variables/global-vars/impl-json.md) · [io-binding](plugins/variables/io-binding/impl-json.md) · [bindings](plugins/variables/bindings/impl-json.md) |
| Bind an input value or expression | [bindings-and-expressions.md](bindings-and-expressions.md) |
| Sync `bindings_v2.json` | [bindings-v2-sync.md](bindings-v2-sync.md) |
| Upgrade a placeholder task | [placeholder-tasks.md](placeholder-tasks.md) |
| Resolve task schemas from the registry | [registry-discovery.md](registry-discovery.md) |

---

**Operation catalogues live in sibling files** — read the one you need, to its own END marker:

- [case-editing-primitives.md](case-editing-primitives.md) — tool-usage mandate, the per-section batch write contract, and the add / delete / bind atoms
- [case-editing-composites.md](case-editing-composites.md) — the 14 multi-step recipes (insert stage, replace placeholder, re-sync, repoint, move, rename, change type, SLA, triggers, convert stage)

<!-- END: case-editing-operations.md -->
