# Case Editing Operations

All mutations to `caseplan.json` performed via direct read/write/edit of the file. This document covers cross-cutting mechanics; per-node JSON shapes live in each plugin's `impl-json.md`.

---

## Responsibilities of Direct JSON Authoring

When editing `caseplan.json` directly, the agent is responsible for these mechanics:

| Concern | Requirement |
|---|---|
| ID generation | Generate IDs per the ID Generation section below using the `prefixedId(prefix, count)` algorithm |
| `elementId` on tasks | Compute and write `${stageId}-${taskId}` on every task |
| Stage position | Count existing stages first; compute `{ x: 100 + existingStageCount * 500, y: 200 }`; then write |
| Stage render fields | Emit `style`, `measured`, `width`, `zIndex`, `data.parentElement`, `data.isInvalidDropTarget`, `data.isPendingParent` on every new Stage node |
| Edges | Not authored — `schema.edges` stays `[]`. No edge handles, no edge objects, no cleanup needed on stage removal |
| Root-level bindings cleanup | Prune entries from top-level `bindings` no longer referenced by any task |
| Lane array expansion | Ensure `stageNode.data.tasks` is expanded to include `laneIndex` before pushing |
| `id-map.json` sidecar | Initialize on T01 (case plugin); append per plugin as IDs are generated; flush to disk at end of run (or after each plugin for durability) |
| `caseplan.json` file creation | T01 (case plugin) writes the file from scratch; downstream plugins mutate in place |
| Layout fields | Do NOT emit node-level `position`, `style`, `measured`, `width`, `height`, `zIndex`. Do NOT emit edge `data.waypoints`. Emit top-level `layout: {}` — FE auto-layouts on canvas load (Rule 18). |

---

## layout-strip (Rule 19)

The following Pre-flight Checklist items become **NOOPs** because layout state lives in top-level `layout`, not on each node:

- **Item 3 (Stage render fields)** — do NOT emit `style`, `measured`, `width`, `zIndex` on Stage nodes. nodes carry `data.parentElement`, `data.isInvalidDropTarget`, `data.isPendingParent` only.
- **Item 4 (Position computation)** — do NOT compute or emit `position.x`, `position.y` on Stage nodes (or Trigger nodes). FE auto-layouts on canvas load.
- **Edges** — none are authored (`schema.edges` stays `[]`), so there are no edge `data.waypoints` to emit; skill emits empty `layout: {}` regardless.

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

4. **Regular Stage vs Exception Stage at creation time.** Regular `case-management:Stage` nodes are written without `entryConditions` / `exitConditions` keys. `case-management:ExceptionStage` nodes initialize both as empty arrays at creation time. Regular stages acquire those keys later when the condition plugins write them. Do not emit empty arrays on regular Stage.

6. **Edges are not authored (RETIRED).** `schema.edges` stays `[]` — do not construct edge handles or append edge objects. Stage transitions derive from entry/exit conditions.

7. **Edge type inference (RETIRED).** No edges are written, so there is no edge type to infer. (Was: Trigger source → `TriggerEdge`, else `Edge`.)

8. **Every regular stage has at least one entry condition.** With edges retired, stage entry conditions are the sole reachability contract — orphan stages don't execute. The first stage carries `case-entered`; every other regular stage carries `selected-stage-completed` / `selected-stage-exited` naming a reachable predecessor. When adding a stage, also plan its entry condition (Step 10).

8. **One task per lane (default).** Increment `laneIndex` per task within a stage starting at 0. Expand `stageNode.data.tasks` to cover the lane index before pushing. **Exception:** within a `runs-sequentially` group, tasks meant to run in parallel share the same `laneIndex` (shared lane = parallel siblings inside the sequential group, semantic). Solo runs-sequentially tasks still get own lane.

9. **Task `elementId` = `${stageId}-${taskId}`.** Compute and write this composite string on every new task.

11. **Entry conditions are SDD-driven — never auto-injected by task type.** A task's `entryConditions[]` are written solely by the task-entry-conditions plugin (Step 10) from the SDD's authored Entry Condition rows — including a connector task's `current-stage-entered`, which the SDD declares as an explicit first row like any ungated task. Do NOT inject a default entry condition at task-creation time based on task type: it produces a duplicate condition and breaks `displayName` indexing (the index is the 1-based position within `entryConditions[]`). Connector and non-connector tasks are treated identically here.

11. **Cross-task bindings reference existing IDs.** Before writing a `var bind` entry, confirm the source stage ID and source task ID both exist in `caseplan.json`.

13. **Validate after every section's batch — with exceptions.** Run `uip maestro case validate <file> --output json` after each `tasks.md` section batch completes (per § Per-section batch write contract below). One validate per section, not one per T-entry. Fixing errors at the section boundary is cheaper than chasing a cascade.
    - **Exception — case plugin (T01):** A case-only caseplan is known-invalid by design (no stage nodes, so the case cannot be entered). Skip `uip maestro case validate` after T01; a cheap `JSON.parse` + root/trigger shape check is the substitute — see [plugins/case/impl-json.md § Post-write validation](plugins/case/impl-json.md#post-write-validation).
    - **Exception — stages plugin (pilot):** A stages-only caseplan is also known-invalid (stages have no entry conditions yet). The plugin's validation parity is captured in the fixture instead.

---

## ID Generation

All IDs follow the CLI's `prefixedId(prefix, count)` scheme: a fixed prefix + `count` random characters drawn uniformly from `[A-Za-z0-9]` (62 chars). Source: `cli/packages/case-tool/src/utils/shortId.ts`.

| Entity | Prefix | Suffix length | Example | Notes |
|---|---|---|---|---|
| Case (top-level `id`) | `case-` | 10 | `case-aBcDeFgHiJ` | |
| Stage (regular + exception) | `Stage_` | 6 | `Stage_aB3kL9` | |
| Trigger (secondary — any subtype: manual / timer / event) | `trigger_` | 6 | `trigger_xY2mNp` | |
| Initial trigger (first trigger in the case) | fixed literal `trigger_1` | — | `trigger_1` | |
| Task | `t` | 8 | `t8GQTYo8O` | |
| Task entry condition | `c` | 8 | `c4fGhJ2Mn` | |
| Task entry rule | `r` | 8 | `rK9xQw3Lp` | |
| Stage / case / task file-level condition | `Condition_` | 6 | `Condition_xC1XyX` | |
| Rule inside those conditions | `Rule_` | 6 | `Rule_jdBFrJ` | |
| Sticky note | `StickyNote_` | 6 | `StickyNote_aBcDeF` | |
| SLA escalation | `esc_` | 6 | `esc_gH2jKl` | |
| Binding | `b` | 8 | `b3KmNp7Q9` | |

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
  "T10": { "kind": "task",    "id": "t8GQTYo8O", "stageId": "Stage_aB3kL9" }
}
```

Used for: debugging, downstream cross-task reference resolution within the same skill run, correlating `registry-resolved.json` entries with the final case file.

---

## Primitive Operations

### Tool usage — mandatory

All mutations to `caseplan.json` (and sibling files like `entry-points.json`, `id-map.json`) MUST go through Claude's built-in tools only:

- **Read** to load the file.
- **Edit** for narrowly-scoped, unambiguous in-place replacements — default for all mutations after T01, and required for sections with <10 T-entries.
- **Write** for the T01 scaffold (initial empty-file creation by the `case` plugin) and for whole-section batched writes when a section has ≥10 T-entries — see § Per-section batch write contract for the bounded conditions under which whole-section Write replaces N sibling Edits.

**Do NOT** shell out to `python`, `node`, `jq`, `sed`, `awk`, or any other process to read, parse, transform, or write the JSON. No helper scripts, no inline one-liners that modify files, no `python3 -c '... json.load ... json.dump ...'`, no `node -e "...fs.writeFileSync...".` The agent holds the parsed object in its own reasoning; the file system is touched only via Read/Write/Edit.

This is a hard constraint — it keeps every mutation reviewable in the tool-call transcript and prevents silent state changes the user cannot audit.

**Anti-patterns that count as file mutation (forbidden — write the file via the Write/Edit tool instead):**

- `node -e "const fs=require('fs'); ... fs.writeFileSync(...)"` — the `node -e` permission is for stdout-only helpers, not file I/O.
- `node -e "..."` / `python -c "..."` / `jq '...' caseplan.json` followed by `> caseplan.json`, `>> caseplan.json`, or `| tee caseplan.json` — shell redirection onto a skill artifact is mutation, regardless of which interpreter ran.
- `cat caseplan.json | jq '...'` even if you only "intend to print" — `jq` is forbidden; use Read.
- `sed -i` / `awk -i inplace` / `python -c "open('caseplan.json','w')..."` — same family, all forbidden.
- `bash -c "...>caseplan.json..."` — wrapping the redirection in another shell does not exempt it.

Pseudocode blocks in this document and in per-plugin `impl-json.md` files (`issues.append(...)`, `existingTriggers = schema.nodes.filter(...)`, etc.) are **specifications of intent**, not commands to execute. Read them, apply the logic in-head, then use Read/Write/Edit to realize the mutation.

**Bash is still used for**: UUID v4 generation only (`node -e "console.log(crypto.randomUUID())"` for `operate.json.projectId` and `entry-points.json` `uniqueId`; subprocess MUST NOT `require('fs')`, `require('child_process')`, or use any redirection operator), `uip solution init` / `uip solution project add` / `uip solution upload`, `uip maestro case validate`, `uip maestro case debug`, `uip maestro case registry` discovery, and read-only metadata fetches (`uip maestro case tasks describe`, `is resources describe`, `is triggers describe`). Never for file mutation.

**Prefixed IDs (`Stage_`, `t`, `Rule_`, `Condition_`, `trigger_`, `c`, `r`, `b`, `esc_`, `StickyNote_`) are picked inline by the agent — no subprocess.** See § ID Generation algorithm above.

### Per-section batch write contract — canonical

`caseplan.json` mutations follow a **per-section batched Edit** contract. The unit is one `tasks.md` section (e.g., §4.4 stages, §4.6 task-shapes, §4.7 conditions, §4.8 SLA), not one T-entry.

Procedure per section:

1. **One Read** of `caseplan.json` at section entry — authoritative state.
2. **Section-sized writes** — pick by T-entry count:
   - **Small sections (<10 T-entries)** — N Edits in sequence, one per T-entry. Edit targets the smallest unambiguous slice of JSON the T-entry mutates (one node, one array field, one task's `data.inputs`).
   - **Large sections (≥10 T-entries)** — single whole-section write replacing the section's container (e.g., entire `schema.nodes` array for stages, a stage's full `data.tasks` array for tasks within that stage). Compose the complete post-section state in reasoning from the Read snapshot, then emit via one Edit (replacing the container slice) or one Write (whole-file rewrite) — Write only when the per-section Edit slice is too large to express as a single unambiguous `old_string`/`new_string` pair.
3. **Skip the re-Read between sibling Edits** — Edit's tool result confirms applied state in context; explicit re-Read is redundant for in-memory correctness.
4. **One `validate`** at section boundary (Pre-flight Item 12 above).

**Tool primitive choice.** Edit is the default — it preserves untouched fields automatically. Whole-file Write rebuilds the file from agent reasoning and risks silently dropping fields the agent forgot; use it only when (a) the section has ≥10 T-entries AND (b) the agent has the complete file state in context from the Read at step 1 AND (c) every untouched root-level field, sibling section, and node not mutated by this section will be copied verbatim. When in doubt, fall back to N Edits — the 12-item Pre-flight Checklist exists because field drops have happened, and Edit is the structural defense.

**Status text bundling.** Any progress text the agent emits before a section's first Edit/Write MUST share the same assistant turn as the tool_use (text block + tool_use block in one content array). Standalone text-only turns between Edits are forbidden — they each cost ~5s inference latency + full prompt cache replay for no work. Cap inline status to ≤1 sentence / ~20 tokens. Per-T-entry audit lives in TaskUpdate, NOT in narration.

**Planning monologues forbidden.** Pre-Write/pre-Edit text turns that announce intent ("Caveman push:", "Approach:", "Strategy:", "Big single Write:", "Writing full caseplan.json structurally", "Now I'll batch all stages") are forbidden, whether bundled or standalone. The tool call itself IS the announcement — TaskUpdate carries the T-by-T narrative, the Edit/Write tool input is self-describing. If the status text the agent wants to emit exceeds one short sentence, the correct action is to cut it, not to bundle it. Multi-paragraph status text is always a violation.

**Hard token cap on any single text block.** Outside the allow-list below, no text block may exceed **200 tokens**. Inside the allow-list, no text block may exceed **500 tokens**, ever. A text block >200 tokens outside the allow-list, or >500 inside it, is by definition a planning monologue regardless of content or framing. Allow-list (and only this list): hard-stop AskUserQuestion preambles, Phase 5/6 completion reports, `Publish for review` DesignerUrl print, post-validate result summaries.

**Forbidden announcement verbs.** Text blocks (bundled or standalone) starting with `Building`, `Composing`, `Writing`, `Drafting`, `Generating`, `Now I'll`, `Next:`, `Next step:`, `Approach:`, `Strategy:`, `Plan:`, `Caveman push:`, `Big single Write:`, `Let me`, or any other narration of the imminent tool call are FORBIDDEN regardless of length. Restating the upcoming tool_use in prose is pure cost. Allowed exceptions remain: AskUserQuestion preambles, completion reports (Phase 5/6 exit), `Publish for review` DesignerUrl print, and post-validate result summaries (`N errors, M warnings — fixing X` is fine; `Composing fix for ...` is not).

**Audit trail via TaskUpdate.** Reviewers see T-by-T progress in the todo log, not in the file diff. Each plugin seeds TaskCreate items keyed by T-number; mark each `in_progress` before composing the entry's mutation in reasoning, `completed` after the Edit/Write returns success. The transcript shows one or N writes per section — what changes is the dropped re-Read between siblings and the dropped standalone narration turns.

**CLI-gated sections — gather-then-write.** Where each T-entry needs its own CLI call before its JSON shape is known (Phase 2 §4.6 non-connector `tasks describe`; Phase 3 §9.7 connector `case spec`): run all CLI calls first, collect results in reasoning, then enter the Read → N-Edits → validate batch.

**Recovery.** On any mid-batch interruption (Edit failure, context compact, abort): re-Read `caseplan.json` + `tasks.md`, scan for next un-applied T-entry, resume from there. No sidecar checkpoint file. For CLI-gated sections, re-run the CLI calls for un-applied entries — typically cheap.

**Scope.** This contract applies to **`caseplan.json`**. `tasks.md` (Phase 1) and `registry-resolved.json` follow the mirror section-batched contract in [planning.md §4.0a](planning.md) — same one-Read-per-section + N-Edit-appends shape, with markdown Edit-append as the primitive (no whole-section Write needed; markdown appends are cheap regardless of count).

**Whole-file Write outside T01.** Permitted only at section boundaries for sections with ≥10 T-entries, per the procedure above. Forbidden mid-section (between T-entries within the same section) — that bypasses the Read snapshot and risks field drops.

**Cap single Write output at ~15K tokens / ~40KB.** When a section's combined output would exceed this, do NOT collapse into one Write — split by phase: Phase 2 emits the skeleton (root + nodes + variables, `edges` stays `[]`, empty `data` on tasks); Phase 3 then fills `data.context` / `data.inputs` / `data.outputs` / conditions / SLA via per-section Edits onto the already-populated nodes. A single Write turn beyond ~15K out tok pays ~150s inference latency and concentrates field-drop risk; the Phase 2 → Phase 3 split spreads the same work across smaller turns with intermediate validate gates. Concretely, for a case with ≥40 tasks or ≥8 stages: never emit the full populated caseplan.json in one Write — always Phase 2 skeleton (small Write) → Phase 3 fill (per-section Edits on populated nodes).

**Forbidden: build-assembler helper scripts.** Writing `/tmp/build-caseplan.js`, `/tmp/gen-tasks.py`, or any script that assembles a skill artifact and pipes/writes it to disk is a Rule 13 violation — regardless of `/tmp` placement, "mechanical copy" framing, or "avoid Read+Write churn" rationale. The script-write + script-run + script-output-to-file pattern bypasses the tool-call audit trail Rule 13 protects. If the artifact is too large for a single Write turn, apply the ~15K-token Write cap and Phase 2 → Phase 3 split above. There is no helper-script escape hatch.

### Generate a fresh ID

**Inline — no subprocess.** Per § ID Generation § Algorithm above. Pick chars in-head following the constraints (mixed case + digits, no sequential, no dictionary words), scan existing IDs in the just-Read `caseplan.json` for collisions, embed via Write/Edit.

Examples — agent picks these directly when writing JSON:

```
Stage_  + "kQ7mNt"  → "Stage_kQ7mNt"
t       + "8GQTYo8O" → "t8GQTYo8O"
Rule_   + "jdBFrJ"  → "Rule_jdBFrJ"
```

> **UUID v4 only** (`operate.json.projectId`, `entry-points.json` `uniqueId`) uses `node -e "console.log(crypto.randomUUID())"` — see § Tool usage. Prefixed-IDs above never call Bash.

### Add a node (Trigger / Stage / ExceptionStage)

1. Read `caseplan.json`.
2. Determine `data` fields per plugin's JSON Recipe. Do not emit `position`, `style`, `measured`, `width`, `height`, `zIndex` at the node level (Rule 18).
3. Generate a fresh node ID.
4. Append the node to `schema.nodes` (stages use `.unshift()` in the CLI — prepend — but either position works for the frontend; prepend to match CLI output exactly).
5. Edit `caseplan.json` — narrow slice targeting `schema.nodes`. Never whole-file Write.

### Add an edge — RETIRED

The skill does not author edges. `schema.edges` stays `[]`. To make a stage reachable, add a `stage-entry-conditions` rule on the target stage (Step 10), not an edge.

### Add a task to a stage

1. Read `caseplan.json`.
2. Locate the stage node by ID.
3. Ensure `stageNode.data.tasks` exists; ensure `stageNode.data.tasks[laneIndex]` exists (expand with empty arrays if needed).
4. Generate a task ID.
5. Compute `elementId = ${stageId}-${taskId}`.
6. Build the task object per the plugin's JSON Recipe. Do NOT add `entryConditions` here — the task-entry-conditions plugin (Step 10) writes them from the SDD's authored rows, for every task type alike.
7. Push onto `stageNode.data.tasks[laneIndex]`.
8. Edit — narrow slice targeting that stage node's `data.tasks[laneIndex]`. Never whole-file Write.

### Bind an input

Variable bindings live on the task's `data.inputs[<index>]` entries — each input has either a literal/expression `value` or a cross-task source reference (`sourceStage`, `sourceTask`, `sourceOutput`). Modify the input entry in place via Edit — narrow slice targeting that input entry. Never whole-file Write.

Details per plugin — see [bindings-and-expressions.md](bindings-and-expressions.md).

### Delete a node

1. Read `caseplan.json`.
2. Remove the node from `schema.nodes` by ID.
3. Edges are not authored — `schema.edges` is `[]`, nothing to remove. (Defensive: if an imported file has a stray edge referencing the removed node's ID, drop it.)
4. If the node was a stage containing a connector task **or a connector condition rule** (in `entryConditions[]` / `exitConditions[]` / task `entryConditions[]`), prune entries from the top-level `bindings` referenced only by that task/rule. A connector rule contributes the same Connection/Folder binding pair as a task — `rule.uipath.context[name="connection"|"folderKey"]` references `=bindings.<bindingId>`. Walk every remaining task/trigger/rule; an entry whose `resourceKey` is no longer referenced anywhere is the one to prune. Case-exit rules are NOT in scope here — they live on root, not inside a node; use § Delete a connector condition rule for those.
5. If the removed node held connector rule outputs that were bound to case variables (B/C feature), prune their `root.inputOutputs[]` companions. The companion's `elementId` is `"root"` — `<removedStageId>-<ruleId>` is the rule output entry's `elementId`, not the companion's. For each removed rule output at `elementId = <removedStageId>-<ruleId>`, read its `var`, then prune the companion whose `id == <var>` and `elementId == "root"` that no longer has a producer.
6. Regenerate `bindings_v2.json` per [bindings-v2-sync.md § Cleanup on task or rule removal](bindings-v2-sync.md#cleanup-on-task-or-rule-removal).
7. Edit — separate slices for `schema.nodes`, the bindings array, and (if applicable) `inputOutputs[]`. Never whole-file Write.

### Delete a connector condition rule

When removing a single rule from a condition (without deleting the parent stage/task/case-exit), the cascade is the same as deleting a connector node — but scoped to one rule:

1. Read `caseplan.json`.
2. Locate the rule by `id`. **FE composes one rule per condition** (OR-style across multiple condition objects), so the target is almost always a condition object that contains exactly this one rule. The underlying shape is DNF (`rules[][]`), so honor it: if other rules share the inner AND-array, remove just the rule; if the rule is the sole entry, remove the entire condition object.
3. Remove the rule (or the parent condition object when it becomes empty).
4. Walk all remaining tasks/triggers/rules; prune root `bindings[]` entries whose `resourceKey` is no longer referenced.
5. Prune `root.inputOutputs[]` companions tied to this rule's outputs. The companion's `elementId` is `"root"`; `<ownerNodeId>-<ruleId>` is the rule output entry's `elementId`, not the companion's. For each of this rule's outputs at `elementId = <ownerNodeId>-<ruleId>`, read its `var`, then prune the companion whose `id == <var>` and `elementId == "root"` when its case variable has no other producer.
6. Regenerate `bindings_v2.json` per [bindings-v2-sync.md § Cleanup on task or rule removal](bindings-v2-sync.md#cleanup-on-task-or-rule-removal).
7. Edit — separate slices for the conditions array, the bindings array, and (if applicable) `inputOutputs[]`. Never whole-file Write.

### Delete an edge — defensive only

The skill never creates edges, so `schema.edges` should already be `[]`. If a stray edge is found (e.g., in an imported file): Read, filter `schema.edges` by the edge ID, Edit the narrow slice. Never whole-file Write.

---

## Composite Operations

### Insert a stage between two existing stages

1. Add the new stage node (with render fields).
2. Add a `stage-entry-conditions` rule on the new stage referencing the upstream stage (`selected-stage-completed`).
3. Re-point the downstream stage's entry condition to reference the new stage instead of the upstream stage.

No edges are involved — reachability is entirely condition-driven.

### Replace a placeholder task with an enriched task

See [placeholder-tasks.md § Upgrade Procedure](placeholder-tasks.md). The upgrade edits the task's `data` field in place to add `taskTypeId`, schema-driven `inputs`/`outputs`, and any required context — keeping the task's `id` and `elementId` unchanged so any conditions referencing it remain valid.

### Re-wire a stage transition — RETIRED (no edges)

Transitions are not edges. To change where a stage flows, edit the relevant stage's entry/exit conditions (the target stage's `stage-entry-conditions` rule, and the source's `stage-exit-conditions` when it diverges). See the conditions plugins.

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
- **Do NOT put `entryConditions`/`exitConditions` on regular Stages.** Only ExceptionStage has them.
- **Do NOT auto-inject a task `entryCondition` at task-creation time based on task type.** Entry conditions come from the SDD via the task-entry-conditions plugin (Step 10), uniformly across task types. Injecting one early duplicates the Step 10 write and corrupts `displayName` indexing.
- **Do NOT write partial JSON with Edit tool regex.** Round-trip through Read → reason → Edit per the per-section batch contract.
- **Do NOT run validation after every single Edit.** Validate at section boundaries, not per-T-entry.
- **Do NOT use whole-file Write mid-section.** Whole-file Write between sibling T-entries inside a section bypasses the section-entry Read snapshot and risks silently dropping fields. Use Edit per T-entry, OR collapse the entire section into one whole-section Write at section boundary when T-entry count ≥10 (per § Per-section batch write contract).
- **Do NOT skip TaskUpdate per T-entry.** TaskUpdate is the audit trail under the per-section batched contract — reviewers track T-by-T progress there, not in per-T-entry file diffs. The audit trail must remain T-by-T even when the file diff collapses to one whole-section write.
- **Do NOT emit standalone text-only assistant turns between Edits.** Each costs ~5s inference + ~250K cache replay for zero work. Bundle status text into the same turn as the next tool_use (text block + tool_use block in one content array), or omit entirely — TaskUpdate already shows progress.
