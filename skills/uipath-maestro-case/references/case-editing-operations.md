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

4. **Primary Stage vs Secondary Stage at creation time.** Both are `case-management:Stage` nodes; a secondary stage is distinguished by `data.stageType: "secondary"`. Primary stages (no `data.stageType`) are written without `entryConditions` / `exitConditions` keys. Secondary stages (`data.stageType: "secondary"`) initialize both as empty arrays at creation time. Primary stages acquire those keys later when the condition plugins write them. Do not emit empty arrays on primary Stage.

5. **Edges are not authored (RETIRED).** `schema.edges` stays `[]` — do not construct edge handles or append edge objects. Stage transitions derive from entry/exit conditions.

6. **Edge type inference (RETIRED).** No edges are written, so there is no edge type to infer. (Was: Trigger source → `TriggerEdge`, else `Edge`.)

7. **Every regular stage has at least one entry condition.** With edges retired, stage entry conditions are the sole reachability contract — orphan stages don't execute. The first stage carries `case-entered`; every other regular stage carries `selected-stage-completed` / `selected-stage-exited` naming a reachable predecessor. When adding a stage, also plan its entry condition (Step 10).

8. **One task per lane (default).** Increment `laneIndex` per task within a stage starting at 0. Expand `stageNode.data.tasks` to cover the lane index before pushing. **Exception:** within a `runs-sequentially` group, tasks meant to run in parallel share the same `laneIndex` (shared lane = parallel siblings inside the sequential group, semantic). Solo runs-sequentially tasks still get own lane.

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
  "T10": { "kind": "task",    "id": "t8GQTYo8O", "stageId": "Stage_aB3kL9" }
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

**Same-file sequential Edits — anchoring.** N Edits against `caseplan.json` in one section serialize in order; each later Edit runs against the text the earlier ones already changed. `caseplan.json` has keys that recur across nodes (`"tasks"`, `"data"`, `"entryConditions"`, `"exitConditions"`, `"inputs"`) — a bare recurring key is NOT a safe anchor.

- **Anchor each Edit on a unique value** — the target stage/task's `"id": "<Stage_… | t…>"` — then extend `old_string` to the slice you mutate. Never anchor on a bare `"tasks": [` or `"entryConditions": [`.
- **Extend until the match is unique within the whole file**, not just within the intended node.
- An `old_string` that overlaps text a prior Edit in the same turn removed or shifted fails with "string not found" — order Edits so each targets an untouched slice, or re-Read if a later Edit depends on an earlier one's output.

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

### Add a node (Trigger / Stage)

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
3. **If the deleted node is a stage with successors, repoint them — do NOT skip.** Edges are retired, so a successor reaches only via an entry-condition rule naming the deleted stage in `selectedStageId`. Find every stage whose `data.entryConditions[].rules[][]` has a `selected-stage-completed` / `selected-stage-exited` rule with `selectedStageId == <removedStageId>`, and repoint each to a surviving predecessor (the deleted stage's own predecessor, or `case-entered` if the deleted stage was first). Leaving them unrepointed orphans every successor — the case can validate structurally yet the successors never execute. Inverse of § Insert a stage between two existing stages.
4. Edges are not authored — `schema.edges` is `[]`, nothing to remove. (Defensive: if an imported file has a stray edge referencing the removed node's ID, drop it.)
5. **If the deleted node is a Trigger, prune its `entry-points.json` entry.** Triggers live in `schema.nodes`, so trigger removal routes here — but every trigger plugin mandates a matching `entry-points.json` entry ([manual/impl-json.md § Recipe — entry-points.json](plugins/triggers/manual/impl-json.md#recipe--entry-pointsjson-append-to-entrypoints), timer, event). Remove the entry whose `filePath` ends in `#<removedTriggerId>` from `entry-points.json.entryPoints`. Leaving it orphans a `#<triggerId>` fragment pointing at a node that no longer exists.
6. **If the deleted node is a Trigger with In-args / trigger outputs, run the variable cascade.** An In-arg emits three entries keyed by the trigger ([global-vars/impl-json.md § In argument](plugins/variables/global-vars/impl-json.md)): the formal slot in `root.inputs[]` (`elementId == <triggerId>`), the companion in `root.inputOutputs[]` (`elementId == "root"`), and the bridge on `triggerNode.data.uipath.outputs[]`. The bridge dies with the node, but the formal slot and companion survive — leaving every `=vars.<name>` consumer reading undefined (`validate` does not catch dangling `=vars.*`). For the deleted trigger:
   - Prune `root.inputs[]` entries with `elementId == <removedTriggerId>`.
   - For each, read its companion's name, then sweep consumers of `=vars.<name>` and prune the `root.inputOutputs[]` companion (`id == <name>`, `elementId == "root"`) when no other producer remains — per § Rename or delete a global variable or argument (Delete path).
   - Step 7's companion-prune below is scoped to connector *rule* outputs (`elementId == "root"`); this trigger branch covers the In-arg companions specifically.
7. If the node was a stage containing a connector task **or a connector condition rule** (in `entryConditions[]` / `exitConditions[]` / task `entryConditions[]`), prune entries from the top-level `bindings` referenced only by that task/rule. A connector rule contributes the same Connection/Folder binding pair as a task — `rule.uipath.context[name="connection"|"folderKey"]` references `=bindings.<bindingId>`. Walk every remaining task/trigger/rule; an entry whose `resourceKey` is no longer referenced anywhere is the one to prune. Case-exit rules are NOT in scope here — they live on root, not inside a node; use § Delete a condition rule for those.
8. If the removed node held connector rule outputs that were bound to case variables (B/C feature), prune their `root.inputOutputs[]` companions. The companion's `elementId` is `"root"` — `<removedStageId>-<ruleId>` is the rule output entry's `elementId`, not the companion's. For each removed rule output at `elementId = <removedStageId>-<ruleId>`, read its `var`, then prune the companion whose `id == <var>` and `elementId == "root"` that no longer has a producer.
9. Regenerate `bindings_v2.json` per [bindings-v2-sync.md § Cleanup on task or rule removal](bindings-v2-sync.md#cleanup-on-task-or-rule-removal).
10. Edit — separate slices for `schema.nodes`, `entry-points.json` (trigger only), `root.inputs[]` / `inputOutputs[]`, and the bindings array. Never whole-file Write.

### Delete a task

Remove a task from a stage. Tasks live in `stageNode.data.tasks[laneIndex][]` — **never** in `schema.nodes` — so § Delete a node cannot reach them. Deleting a task also dangles every reference to its `TaskId`; sweep them all, then re-pack lanes.

1. Read `caseplan.json`. Locate the task in its owning `stageNode.data.tasks[laneIndex]` and note its `id` (the `TaskId`) and `elementId`.
2. **Remove the task** from `data.tasks[laneIndex]`.
3. **Re-pack lanes.** Removing the only task in a lane leaves an empty inner array. Drop the empty lane and re-index the surviving lanes so `laneIndex` stays contiguous from 0 (Pre-flight Item 8). A lane shared by `runs-sequentially` parallel siblings keeps its other members — only drop the lane when it becomes empty.
4. **Prune conditions that reference the dead `TaskId`:**
   - Any task's `entryConditions[].rules[][]` `selected-tasks-completed` rule whose `selectedTasksIds` names the deleted task — remove the id from the array; if it empties, remove the rule (and the parent condition object when it empties), per § Delete a condition rule's DNF removal mechanic.
   - Any `conditionExpression` (`=js:...`) referencing the deleted task's outputs — repoint or remove.
5. **Repoint cross-task bindings that consumed this task's outputs.** Any other task input with `sourceTask == <deletedTaskId>` (and `sourceStage == <ownerStageId>`) now dangles — repoint to a surviving producer or clear the binding. A consumer left bound to a deleted producer reads undefined at runtime; `validate` does not catch it.
6. **Connector-task cascade (connector tasks only).** If the deleted task was a connector-activity / wait-for-connector task, prune its top-level `bindings[]` (Connection/Folder pair no longer referenced by any task/trigger/rule), prune any `root.inputOutputs[]` companions tied to its rule outputs, and regenerate `bindings_v2.json` — same cascade as § Delete a node steps 5–7.
7. Update the task's `id-map.json` entry (remove it) if the sidecar is present.
8. Edit — narrow slices for the source `data.tasks` (removal + lane re-pack), each swept condition, each repointed consumer binding, and (connector only) the bindings array / `inputOutputs[]`. Never whole-file Write. Validate at the section boundary.

> **Reverse of § Add a task to a stage.** § Move a task always re-pushes to a destination; § Delete a task is the terminal removal — there is no destination, so the cascade prunes references instead of repointing them to a new stage.

### Delete a condition rule

Remove a single rule from a condition (without deleting the parent stage / task / case-exit). Applies to **any** rule scope — stage entry/exit, task entry, case exit — and to both plain and connector-bound rules. The generic DNF removal (steps 1–3) is all a **plain** rule needs; the binding cascade (steps 4–6) is **connector-only** and a no-op for plain rules.

1. Read `caseplan.json`.
2. Locate the rule by `id`. **FE composes one rule per condition** (OR-style across multiple condition objects), so the target is almost always a condition object that contains exactly this one rule. The underlying shape is DNF (`rules[][]`), so honor it: if other rules share the inner AND-array, remove just the rule; if the rule is the sole entry, remove the entire condition object.
3. Remove the rule (or the parent condition object when it becomes empty). **Plain (non-connector) rules stop here** — skip steps 4–6. **For case-exit completion rules, first run the ≥1-completion-rule guard** in § Delete a case-exit completion rule below.
4. **(Connector rules only)** Walk all remaining tasks/triggers/rules; prune root `bindings[]` entries whose `resourceKey` is no longer referenced.
5. **(Connector rules only)** Prune `root.inputOutputs[]` companions tied to this rule's outputs. The companion's `elementId` is `"root"`; `<ownerNodeId>-<ruleId>` is the rule output entry's `elementId`, not the companion's. For each of this rule's outputs at `elementId = <ownerNodeId>-<ruleId>`, read its `var`, then prune the companion whose `id == <var>` and `elementId == "root"` when its case variable has no other producer.
6. **(Connector rules only)** Regenerate `bindings_v2.json` per [bindings-v2-sync.md § Cleanup on task or rule removal](bindings-v2-sync.md#cleanup-on-task-or-rule-removal).
7. Edit — separate slices for the conditions array, and (connector only) the bindings array and `inputOutputs[]`. Never whole-file Write.

#### Modify a condition rule in place

Change a rule's behavior without removing it — keep the rule `id` so any reference stays valid.

1. Read `caseplan.json`; locate the rule by `id` in its `rules[][]` DNF array.
2. Edit the rule fields in place:
   - **Operator / expression:** rewrite `conditionExpression` (`=js:<expr>`) — use strict `===` / `!==`, parenthesize each sub-clause of a combined boolean ([bindings-and-expressions.md § Canonical form per sink](bindings-and-expressions.md#canonical-form-per-sink)). Re-validate any `=vars.<id>` referenced still type-checks.
   - **`rule` type:** swap the `rule` value (e.g., `selected-stage-completed` ↔ `selected-stage-exited`) and add/drop the side field the new type requires (`selectedStageId`, `selectedTasksIds`). For case-exit, honor the rule-type × `marksCaseComplete` matrix ([case-exit-conditions/impl-json.md](plugins/conditions/case-exit-conditions/impl-json.md#rule-type--markscasecomplete-matrix)).
   - **`marksCaseComplete` (case-exit only):** flipping `true`→`false` may remove the last completion rule — run the ≥1-completion-rule guard in § Delete a case-exit completion rule first.
3. Connector-bound rules: if the connector configuration (`rule.uipath`) changed, re-fetch via `uip maestro case spec` (never hand-author) and re-run the bindings cascade (steps 4–6 above).
4. Edit — narrow slice targeting that rule. Never whole-file Write. Validate at the section boundary.

### Delete a case-exit completion rule

Remove a plain completion / exit rule from `metadata.caseExitRules[]`. **Guard: a case must keep ≥1 rule with `marksCaseComplete: true`** — `validate` rejects an all-`marksCaseComplete:false` case ("Case has no completion rules").

1. Read `caseplan.json`; locate the rule in `metadata.caseExitRules[]`.
2. **Before removing, check the invariant.** If the rule being removed is the only entry with `marksCaseComplete: true`, removing it leaves the case with no completion path. Do NOT silently remove — AskUserQuestion: `Replace it with a different completion rule` / `Keep it` / `Remove anyway (case will fail validation)`. Removing the last completer is almost always a mistake; surfacing it here avoids the After-edits retry thrash (validate would reject it on the next loop).
3. Remove the condition object from `metadata.caseExitRules[]` (DNF removal per § Delete a condition rule steps 2–3). Connector-bound case-exit rules also run the connector cascade (steps 4–6).
4. Edit — narrow slice targeting `metadata.caseExitRules`. Never whole-file Write. Validate at the section boundary.

### Delete an edge — defensive only

The skill never creates edges, so `schema.edges` should already be `[]`. If a stray edge is found (e.g., in an imported file): Read, filter `schema.edges` by the edge ID, Edit the narrow slice. Never whole-file Write.

---

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
6. **If the resource binding set changed (connector or non-connector), regenerate `bindings_v2.json`** ([bindings-v2-sync.md](bindings-v2-sync.md)) and run `uip solution resources refresh` before debug/publish (Rule 14) — same scope as § Repoint a non-connector task step 5 and the brownfield After-edits step 2. A pure schema-only re-sync (same resource, `data.inputs`/`data.outputs` reshaped but no `bindings[]` entry added/removed/repointed) leaves `bindings_v2.json` unchanged — skip the refresh in that case.
7. Edit — narrow slices targeting the task's `data` (and any consumer / bindings slices). Never whole-file Write. Validate at the section boundary.

### Repoint a non-connector task at a different resource

Swap which process / agent / RPA / api-workflow / case-management resource a task runs. The node references its resource indirectly — `data.name` / `data.folderPath` are `=bindings.<id>` pointers into top-level `bindings[]` ([process impl-json](plugins/tasks/process/impl-json.md), [bindings impl-json](plugins/variables/bindings/impl-json.md)). The new resource almost always has a different I/O schema, so this is a **superset of § Re-sync a task after its source schema changed** plus a binding swap. Keep the task `id` / `elementId` / `entryConditions` so references stay valid.

1. **Re-resolve the new resource** — `uip maestro case registry pull --force`, then search the cache files ([registry-discovery.md](registry-discovery.md)) for the new name + folder. Capture its `entityKey`, resolved `name`, and `folders[0].fullyQualifiedName` (the resolved folder path — never the raw SDD folder). Record the swap in `registry-resolved.json`.
2. **Swap the resource bindings — respect dedup.** The task's two binding entries (`propertyAttribute` `name` / `folderPath`) share `resourceKey = <folderPath>.<name>`.
   - Old pair referenced **only** by this task → update each entry's `default` (new name / folder) and `resourceKey` (`<newFolderPath>.<newName>`) in place.
   - Old pair **shared** with other tasks (deduped by `default + resource + resourceKey`) → do NOT mutate in place. Create or reuse a binding pair for the new resource, repoint this task's `data.name` / `data.folderPath` to the new ids, then prune the old pair if no task references it any longer.
3. **Re-sync the schema.** Follow § Re-sync a task after its source schema changed steps 1–5 against the new resource: `uip maestro case tasks describe --type <type> --id <newEntityKey> --output json`, update `data.inputs` / `data.outputs`, re-bind inputs, repoint downstream consumers of dropped outputs.
4. **If the task type also changes** (e.g. process → agent): update the node `type`, the bindings' `resource` / `resourceSubType` per the new type's [impl-json](plugins/tasks/), and rebuild `data` per that type's recipe — still keeping `id` / `elementId` / `entryConditions`.
5. Regenerate `bindings_v2.json` ([bindings-v2-sync.md](bindings-v2-sync.md)) and run `uip solution resources refresh` before debug/publish (Rule 14) — the swap changes which Orchestrator resource declaration the case needs.
6. Edit — narrow slices for the task `data`, the bindings array, and any consumer slices. Never whole-file Write. Validate at the section boundary.

### Move a task to a different stage or lane

Relocate a task within the case. **Keep the task `id`** so conditions and cross-task bindings referencing it stay valid — but every `elementId` is stage-scoped and MUST be recomputed.

1. Read `caseplan.json`. Locate the task in its source `stageNode.data.tasks[oldLane]`.
2. **Recompute every stage-scoped `elementId` — the step most easily missed** (a move looks like layout, but `elementId` encodes the owning stage):
   - the task itself: `elementId = ${destStageId}-${taskId}`
   - any `wait-for-connector` entry-condition rule on the task, and each entry in that rule's `uipath.outputs[]`: `elementId = ${destStageId}-${ruleId}`
   - (root `inputOutputs[]` companions are `elementId: "root"` — NOT stage-scoped, leave them.)
3. Remove the task from the source `data.tasks[oldLane]`; expand the destination `stageNode.data.tasks` to cover `newLane`, then push the task onto `data.tasks[newLane]`. One task per lane (default); within a `runs-sequentially` group, parallel siblings share a lane (Pre-flight Item 8).
4. **Repoint cross-task bindings that consume this task's outputs.** Any other task input with `sourceTask == <taskId>` keeps `sourceTask`, but its `sourceStage` must change to `<destStageId>`. Confirm ordering still holds — a consumer can only read a task that runs before it; moving the task later in the flow can invalidate the binding.
5. **Re-check the moved task's `entryConditions[]`:**
   - `current-stage-entered` — no change; it follows the task to the destination stage.
   - `selected-tasks-completed` — `selectedTasksIds` left behind in the source stage now gate across stages; repoint to a task in the destination or remove if the dependency no longer applies.
   - `runs-sequentially` — the move splits the source group; re-evaluate lane membership (step 3) in both stages.
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
4. Connector consumers only — if a swept reference was a connector binding, regenerate `bindings_v2.json` ([bindings-v2-sync.md](bindings-v2-sync.md)) and run `uip solution resources refresh` before debug/publish.
5. Edit — narrow slices per consumer location and the owning array. Never whole-file Write. Validate at the section boundary.

### Change a variable's type or default

Mutate a variable's `type` / `body` / `default` in place — keep its `id` so every `=vars.<id>` reference stays valid. **Cannot be faked by delete + re-add**: re-adding re-mints a fresh `id` and dangles every consumer (§ Rename or delete). The `type` is duplicated across several coordinated slots ([global-vars/impl-json.md](plugins/variables/global-vars/impl-json.md)); change all of them in one pass or the FE picker and runtime disagree.

1. Read `caseplan.json`. Identify the variable's category and every slot that carries its `type`:
   - **Internal variable** (`variables.inputOutputs[]`): the single companion entry's `type` (+ `body` when `type == "jsonSchema"`).
   - **Out argument** (`variables.outputs[]` formal + `inputOutputs[]` companion): both entries' `type`; the companion's `body` for `jsonSchema`.
   - **In argument** (three entries — `root.inputs[]` formal slot, `root.inputOutputs[]` companion, `triggerNode.data.uipath.outputs[]` bridge): change `type` on **all three**. The bridge's `type` must match or the fire-time copy mis-types.
2. **Type change** — set the new `type` on every slot from step 1. For `type == "jsonSchema"`, set `body` to the new schema on the formal slot and companion (the FE picker reads `body` to discover sub-fields). For `type == "file"`, apply the file-type carve-outs ([global-vars/impl-json.md § In argument](plugins/variables/global-vars/impl-json.md)): companion + formal slot get `body: <FILE_TYPE_JSON_SCHEMA>`, and an In-arg's `default` MUST stay `""`.
3. **Default change** — set `default` on the formal slot (`root.inputs[]` for an In-arg, the `variables.outputs[]`/`inputOutputs[]` entry otherwise). A file-typed variable rejects any `default` other than `""`.
4. **Re-validate every `=vars.<id>` consumer against the new type.** A condition/SLA expression that compared the variable as one type (`=js:vars.amount > 5`) may now be malformed against the new type (e.g., string). Repoint or fix each consumer; `validate` does not catch a type-mismatched `=js:*` expression.
5. Edit — narrow slices for each coordinated slot and any reworked consumer. Never whole-file Write. Validate at the section boundary.

### Modify or remove an SLA or escalation

The add path is [plugins/sla/impl-json.md](plugins/sla/impl-json.md); this is the in-place modify / remove. SLA rules live in `metadata.slaRules[]` (root target) or `node.data.slaRules[]` (stage target); each rule carries an `escalationRule[]`. Conditional rules have **no `id`** — address them by array index; escalations carry an `esc_` id.

1. Read `caseplan.json`. Locate the SLA array — `metadata.slaRules[]` for the root target, else the stage node's `data.slaRules[]` (find by `data.label`).
2. **Modify a rule:** edit the target rule's `count` / `unit` / `expression` in place. Keep the default rule (`expression == "=js:true"`) **last**; never reorder it ahead of a conditional rule.
3. **Remove a rule:** delete the rule object from `slaRules[]` (its nested `escalationRule[]` goes with it — drop those `esc_` ids from `id-map.json`). If removing leaves the target with **no** SLA rules, remove the `slaRules` key entirely ([sla/impl-json.md](plugins/sla/impl-json.md) emission rule 5) — do not leave an empty array or an orphan default. If conditional rules remain, the `=js:true` default must still be present and last.
4. **Modify an escalation:** edit its `action.recipients[]`, `triggerInfo.type`, or `atRiskPercentage` in place. `atRiskPercentage` is present only when `triggerInfo.type == "at-risk"` — drop the field when switching to `sla-breached`. Omit `displayName` entirely rather than emitting `undefined`.
5. **Remove an escalation:** delete the entry from its parent rule's `escalationRule[]` by `esc_` id; drop the `esc_` id from `id-map.json`. Leave `escalationRule: []` on the rule (never omit the key — [sla/impl-json.md](plugins/sla/impl-json.md) emission rule 4).
6. Edit — narrow slices targeting the specific rule / escalation entry. Never whole-file Write. Validate at the section boundary.

### Replace a trigger with a different type

Swap a trigger's type in place (e.g., manual → timer, or manual → event) — keep the node `id` so `id-map.json` and any references stay valid.

1. Read `caseplan.json`.
2. Locate the Trigger node by `id`. Rewrite its `data.uipath` to the target type's shape per the target plugin's recipe — [triggers/manual](plugins/triggers/manual/impl-json.md), [triggers/timer](plugins/triggers/timer/impl-json.md), [triggers/event](plugins/triggers/event/impl-json.md). The target type dictates the move:
   - **→ manual:** **delete the `data.uipath` key entirely** — a manual trigger has no `data.uipath` ([manual/impl-json.md](plugins/triggers/manual/impl-json.md) "No `data.uipath` key"). Do not leave an empty or stale block.
   - **→ timer:** set `data.uipath = { serviceType: "Intsvc.TimerTrigger", … }` per the timer recipe.
   - **→ event:** set `data.uipath = { serviceType: "Intsvc.EventTrigger", … }` per the event recipe (or the placeholder shape if the connector is unresolved).

   Preserve `data.label`, `data.description`, and `data.parentElement` (secondary triggers).
3. **Run the In-arg / trigger-output variable cascade when the bridge host changes.** The In-arg bridge lives on `triggerNode.data.uipath.outputs[]` ([global-vars/impl-json.md § In argument](plugins/variables/global-vars/impl-json.md)). Replacing → manual removes `data.uipath` and therefore the only host for `outputs[]`, silently orphaning every bridge and its trigger-sourced companion. For each bridge dropped by the type change, sweep `=vars.<name>` consumers and prune/repoint the `root.inputs[]` formal slot + `root.inputOutputs[]` companion per § Rename or delete a global variable or argument (Delete path). When the target type still hosts `outputs[]` (timer / event), re-emit the bridges on the new `data.uipath.outputs[]`.
4. Update the matching `entry-points.json` entry. The `filePath` `#<triggerId>` fragment stays (id unchanged). **Note:** manual and timer entry-points `input`/`output` are always empty `{ "type": "object", "properties": {} }` ([manual/impl-json.md](plugins/triggers/manual/impl-json.md#recipe--entry-pointsjson-append-to-entrypoints), [timer/impl-json.md § entry-points.json append](plugins/triggers/timer/impl-json.md)) — only `displayName` can change for those targets. Event triggers may carry a non-empty io shape.
5. Edit — narrow slices targeting that node's `data.uipath`, the `entry-points.json` entry, and any swept variable slices. Never whole-file Write.
6. Validate at the section boundary.

### Re-target an event trigger (same type, different event)

Keep an event trigger as an event trigger but point it at a different connector event (different object / operation / filter). Distinct from § Replace a trigger with a different type (which changes the *type*). Keep the node `id`.

1. **Re-fetch the case-spec** for the new event — `uip maestro case spec --type trigger --output json` (never hand-author connector schemas; see [connector-integration.md](connector-integration.md) and [plugins/triggers/event/impl-json.md](plugins/triggers/event/impl-json.md)).
2. Read `caseplan.json`; locate the Trigger node by `id`. Rebuild `data.uipath` (`serviceType: "Intsvc.EventTrigger"` + the new `context[]` / `inputs[]` / `outputs[]` / `bindings[]`) from the fetched spec.
3. **Regenerate the trigger's root bindings + variable bridges.** A different event changes the Connection/Folder bindings and the trigger-output → companion wiring. Re-run the trigger-output dispatch ([global-vars/impl-json.md Loop A](plugins/variables/global-vars/impl-json.md)): drop bridges/companions for outputs the old event produced and the new event no longer does (sweep `=vars.*` consumers per § Rename or delete a global variable or argument), add the new ones.
4. **Update `entry-points.json`** `input`/`output` if the event's io shape changed; the `#<triggerId>` fragment stays.
5. **Regenerate `bindings_v2.json`** + repopulate the IS connection cache ([bindings-v2-sync.md](bindings-v2-sync.md)) and run `uip solution resources refresh` before debug/publish (Rule 14) — the new event needs its own Connection resource declaration.
6. Edit — narrow slices for the node's `data.uipath`, root bindings / `inputOutputs[]`, and `entry-points.json`. Never whole-file Write. Validate at the section boundary.

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

## Validation Cadence

Run `uip maestro case validate <file> --output json` after each `tasks.md` section's batch completes — not after every Edit. Intermediate states can be invalid (e.g., a stage whose entry condition references a stage that will be added next); validate is authoritative at the section boundary.

On failure: fix the reported issue (usually a missing field, malformed ID, or orphan reference) and re-validate. Up to 3 retries per section; if still failing, halt and AskUserQuestion the user with the remaining errors and options to retry, pause, or abort.

---

## Anti-Patterns

- **Do NOT shell out to `python`, `node`, `jq`, `sed`, `awk`, or any other subprocess to mutate `caseplan.json` or its siblings.** Use Read + Write/Edit only. Subprocess scripts bypass the tool-call audit trail and make the mutation invisible in the transcript. See "Tool usage — mandatory" above.
- **Do NOT write helper scripts (`.py`, `.js`, `.sh`) that open / parse / modify / save JSON files.** Even one-shot scripts are forbidden — the agent is the processor, Read/Write/Edit are the only I/O primitives.
- **Do NOT hand-edit IDs with human-readable patterns** (e.g., `my_stage_1`). The frontend's `generateNextId` expects CLI's format.
- **Do NOT emit node-level layout fields** (`position`, `style`, `measured`, `width`, `height`, `zIndex`) — these belong in top-level `layout`, not on the node (Rule 18).
- **Do NOT put `entryConditions`/`exitConditions` on primary Stages.** Only secondary stages (`data.stageType: "secondary"`) have them.
- **Do NOT auto-inject a task `entryCondition` at task-creation time based on task type.** Entry conditions come from the SDD via the task-entry-conditions plugin (Step 10), uniformly across task types. Injecting one early duplicates the Step 10 write and corrupts `displayName` indexing.
- **Do NOT write partial JSON with Edit tool regex.** Round-trip through Read → reason → Edit per the per-section batch contract.
- **Do NOT run validation after every single Edit.** Validate at section boundaries, not per-T-entry.
- **Do NOT use whole-file Write mid-section.** Whole-file Write between sibling T-entries inside a section bypasses the section-entry Read snapshot and risks silently dropping fields. Use Edit per T-entry, OR collapse the entire section into one whole-section Write at section boundary when T-entry count ≥10 (per § Per-section batch write contract).
- **Do NOT skip TaskUpdate per T-entry.** TaskUpdate is the audit trail under the per-section batched contract — reviewers track T-by-T progress there, not in per-T-entry file diffs. The audit trail must remain T-by-T even when the file diff collapses to one whole-section write.
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
