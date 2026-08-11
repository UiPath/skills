# Case Editing Operations

All mutations to `caseplan.json` performed via direct read/write/edit of the file. This document covers cross-cutting mechanics; per-node JSON shapes live in each plugin's `impl-json.md`.

---

## Responsibilities of Direct JSON Authoring

When editing `caseplan.json` directly, the agent is responsible for these mechanics:

| Concern | Requirement |
|---|---|
| Task owner schema and `inputs` / `outputs` | Never hand-author. Source from `registry-resolved.json` / `uip maestro case tasks describe`, then apply the selected task owner's fields — see [registry-discovery.md](registry-discovery.md). Hand-written schemas fail validation. |
| ID generation | Generate IDs per the ID Generation section below using the `prefixedId(prefix, count)` algorithm |
| `elementId` on tasks | Compute and write `${stageId}-${taskId}` on every task |
| Stage data fields | Emit `data.parentElement`, `data.isInvalidDropTarget`, `data.isPendingParent` on every new Stage node. Do NOT emit `style`, `measured`, `width`, `zIndex`, or `position` — see Layout fields below (Rule 18/19) |
| Root shape | Current disk paths are top-level `nodes`, `edges`, `bindings`, and `variables.{inputs,outputs,inputOutputs}`. There is no `schema` or `root` wrapper. |
| Edges | Not authored (Rule 20) — top-level `edges` stays `[]`; imported edges may be removed but never created |
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

5. **Edges are not authored (Rule 20).** Top-level `edges` stays `[]` — do not construct edge handles or append edge objects. Stage transitions derive from entry/exit conditions.

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

Pseudocode blocks in this document and in per-plugin `impl-json.md` files are **specifications of intent**, not commands to execute. Read them, apply the logic in-head, then use Read/Write/Edit to realize the mutation. When an older plugin example names a wrapper absent from the current root shape, use the current top-level paths above.

**Bash is still used for**: UUID v4 generation only (`node -e "console.log(crypto.randomUUID())"` for `operate.json.projectId` and `entry-points.json` `uniqueId`; subprocess MUST NOT `require('fs')`, `require('child_process')`, or use any redirection operator), `uip solution init` / `uip solution projects add` / `uip solution upload`, `uip maestro case validate`, `uip maestro case debug`, `uip maestro case registry` discovery, and read-only metadata fetches (`uip maestro case tasks describe`, `is resources describe`, `is triggers describe`). Never for file mutation.

**Prefixed IDs (`Stage_`, `t`, `Rule_`, `Condition_`, `trigger_`, `c`, `r`, `b`, `sla_`, `esc_`, `StickyNote_`) are picked inline by the agent — no subprocess.** See § ID Generation algorithm above.

### Per-section batch write contract — canonical

`caseplan.json` mutations follow a **per-section batched Edit** contract. The unit is one `tasks.md` section (e.g., §4.4 stages, §4.6 task-shapes, §4.7 conditions, §4.8 SLA), not one T-entry.

Procedure per section:

1. **One Read** of `caseplan.json` at section entry — authoritative state.
2. **Section-sized writes** — pick by T-entry count:
   - **Small sections (<10 T-entries)** — N Edits in sequence, one per T-entry. Edit targets the smallest unambiguous slice of JSON the T-entry mutates (one node, one array field, one task's `data.inputs`).
   - **Large sections (≥10 T-entries)** — single whole-section write replacing the section's container (e.g., the top-level `nodes` array for stages, a stage's full `data.tasks` array for tasks within that stage). Compose the complete post-section state in reasoning from the Read snapshot, then emit via one Edit (replacing the container slice) or one Write (whole-file rewrite) — Write only when the per-section Edit slice is too large to express as a single unambiguous `old_string`/`new_string` pair.
3. **Skip the re-Read between sibling Edits** — Edit's tool result confirms applied state in context; explicit re-Read is redundant for in-memory correctness.
4. **One `validate`** at section boundary (Pre-flight Item 12 above).
5. **Repair preservation ledger.** Before any whole-file repair Write, record from the section-entry Read every unaffected root key and value, node/task ID, node and task order, `data.tasks` task-set grouping, condition/rule ID and DNF grouping, top-level binding ID, variable/formal-slot/companion ID, selected-resource task ID, imported edge, and sibling sidecar entry. Immediately re-Read after the Write and compare the ledger. Restore any dropped or reconstructed value before validation. Unknown/future fields are data, not disposable noise. A targeted edit never rebuilds an unrelated sibling; use a narrow Edit whenever the target can be anchored by stable ID.

**Same-file sequential Edits — anchoring.** N Edits against `caseplan.json` in one section serialize in order; each later Edit runs against the text the earlier ones already changed. `caseplan.json` has keys that recur across nodes (`"tasks"`, `"data"`, `"entryConditions"`, `"exitConditions"`, `"inputs"`) — a bare recurring key is NOT a safe anchor.

- **Anchor each Edit on a unique value** — the target stage/task's `"id": "<Stage_… | t…>"` — then extend `old_string` to the slice you mutate. Never anchor on a bare `"tasks": [` or `"entryConditions": [`.
- **Extend until the match is unique within the whole file**, not just within the intended node.
- An `old_string` that overlaps text a prior Edit in the same turn removed or shifted fails with "string not found" — order Edits so each targets an untouched slice, or re-Read if a later Edit depends on an earlier one's output.

**Tool primitive choice.** Edit is the default — it preserves untouched fields automatically. Whole-file Write rebuilds the file from agent reasoning and risks silently dropping fields the agent forgot; use it only when (a) the section has ≥10 T-entries AND (b) the agent has the complete file state in context from the Read at step 1 AND (c) every untouched root-level field, sibling section, and node not mutated by this section will be copied verbatim. When in doubt, fall back to N Edits — the 12-item Pre-flight Checklist exists because field drops have happened, and Edit is the structural defense.

**Status text bundling.** Any progress text the agent emits before a section's first Edit/Write MUST share the same assistant turn as the tool_use (text block + tool_use block in one content array). Standalone text-only turns between Edits are forbidden — they each cost ~5s inference latency + full prompt cache replay for no work. Cap inline status to ≤1 sentence / ~20 tokens. Per-T-entry audit lives in TaskUpdate, NOT in narration.

**Planning monologues forbidden.** Pre-Write/pre-Edit text turns that announce intent ("Caveman push:", "Approach:", "Strategy:", "Big single Write:", "Writing full caseplan.json structurally", "Now I'll batch all stages") are forbidden, whether bundled or standalone. The tool call itself IS the announcement — TaskUpdate carries the T-by-T narrative, the Edit/Write tool input is self-describing. If the status text the agent wants to emit exceeds one short sentence, the correct action is to cut it, not to bundle it. Multi-paragraph status text is always a violation.

**Hard token cap on any single text block.** Outside the allow-list below, no text block may exceed **200 tokens**. Inside the allow-list, no text block may exceed **500 tokens**, ever. A text block >200 tokens outside the allow-list, or >500 inside it, is by definition a planning monologue regardless of content or framing. Allow-list (and only this list): the once-per-run kickoff flow overview, hard-stop AskUserQuestion preambles, Phase 5/6 completion reports, `Publish for review` DesignerUrl print, post-validate result summaries.

**Forbidden announcement verbs.** Text blocks (bundled or standalone) starting with `Building`, `Composing`, `Writing`, `Drafting`, `Generating`, `Now I'll`, `Next:`, `Next step:`, `Approach:`, `Strategy:`, `Plan:`, `Caveman push:`, `Big single Write:`, `Let me`, or any other narration of the imminent tool call are FORBIDDEN regardless of length. Restating the upcoming tool_use in prose is pure cost. Allowed exceptions remain: the once-per-run kickoff flow overview, AskUserQuestion preambles, completion reports (Phase 5/6 exit), `Publish for review` DesignerUrl print, and post-validate result summaries (`N errors, M warnings — fixing X` is fine; `Composing fix for ...` is not).

**Audit trail via TaskUpdate.** Reviewers see T-by-T progress in the todo log, not in the file diff. Each plugin seeds TaskCreate items keyed by T-number; mark each `in_progress` before composing the entry's mutation in reasoning, `completed` after the Edit/Write returns success. The transcript shows one or N writes per section — what changes is the dropped re-Read between siblings and the dropped standalone narration turns.

**CLI-gated sections — gather-then-write.** Where each T-entry needs its own CLI call before its JSON shape is known (Phase 2 §4.6 non-connector `tasks describe`; Phase 3 §9.7 connector `case spec`): run all CLI calls first, collect results in reasoning, then enter the Read → N-Edits → validate batch.

**Recovery.** On any mid-batch interruption (Edit failure, context compact, abort): re-Read `caseplan.json` + `tasks.md`, scan for next un-applied T-entry, resume from there. No sidecar checkpoint file. For CLI-gated sections, re-run the CLI calls for un-applied entries — typically cheap.

**Scope.** This contract applies to **`caseplan.json`**. `tasks.md` (Phase 1) and `registry-resolved.json` follow the mirror section-batched contract in [planning.md §4.0a](planning.md) — same one-Read-per-section + N-Edit-appends shape, with markdown Edit-append as the primitive (no whole-section Write needed; markdown appends are cheap regardless of count).

**Whole-file Write outside T01.** Permitted only at section boundaries for sections with ≥10 T-entries, per the procedure above. Forbidden mid-section (between T-entries within the same section) — that bypasses the Read snapshot and risks field drops.

**Cap single Write output at ~15K tokens / ~40KB.** When a section's combined output would exceed this, do NOT collapse into one Write — preserve the per-section cadence: Phase 2 writes root, nodes, variables, task shapes, SLA/escalations, and conditions (connector-backed rules use the canonical stub); Phase 3 fills connector context/input/output and other task values, then upgrades resolved connector-rule stubs. A single Write turn beyond ~15K out tok pays ~150s inference latency and concentrates field-drop risk. For a case with ≥40 tasks or ≥8 stages, never emit the fully populated `caseplan.json` in one Write — use the Phase 2 sections followed by Phase 3 detail Edits.

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
4. Append the node to top-level `nodes`; preserve the existing node order.
5. Edit `caseplan.json` — narrow slice targeting top-level `nodes`. Never whole-file Write.

### Add an edge — RETIRED

Not authored (Rule 20). To make a stage reachable, add a `stage-entry-conditions` rule on the target stage (Step 10), not an edge.

### Add a task to a stage

1. Read `caseplan.json`.
2. Locate the stage node by ID.
3. Ensure `stageNode.data.tasks` exists. Use the task's activation mode and entry rule before honoring lane placement: strict sequential / `runs-sequentially`, adhoc, event-driven, fan-in, conditional-gate, and standalone tasks append as new single-task inner arrays. Reuse an existing `stageNode.data.tasks[laneIndex]` only for tasks explicitly planned as `parallel` or `parallel-after-predecessor` siblings with same-lane intent and rationale.
4. Generate a task ID.
5. Compute `elementId = ${stageId}-${taskId}`.
6. Build the task object per the plugin's JSON Recipe. Do NOT add `entryConditions` here — the task-entry-conditions plugin (Step 10) writes them from the SDD's authored rows, for every task type alike.
7. Push onto `stageNode.data.tasks[laneIndex]` only for explicitly parallel or parallel-after-predecessor siblings; otherwise write `[task]` as its own inner task set. If `laneIndex` conflicts with activation mode, activation mode wins and note the lane correction in the completion report.
8. Edit — narrow slice targeting that stage node's `data.tasks[laneIndex]`. Never whole-file Write.

### Update one property in place

Use this primitive only when the selected owner declares the scalar independent of companions, consumers, sidecars, resource/schema identity, or routing. A specialized brownfield row always wins. Read the target object, anchor by its stable `id`, and replace only the requested property. Preserve the object envelope, sibling properties, containing `data.tasks` task-set and order, every condition, all root fields, sidecars, bindings, variables, and topology byte-for-byte. Run the selected plugin's post-write invariants, then validate once after the edit batch.

### Bind an input

Variable bindings live on the task's `data.inputs[<index>]` entries — each input has either a literal/expression `value` or a cross-task source reference (`sourceStage`, `sourceTask`, `sourceOutput`). Modify the input entry in place via Edit — narrow slice targeting that input entry. Never whole-file Write.

Details per plugin — see [bindings-and-expressions.md](bindings-and-expressions.md).

### Canonical consumer sweep

Run this one inventory before removing, renaming, moving, retyping, or replacing any producer, resolver key, task, stage, trigger, binding, SLA, or escalation. Search the complete `caseplan.json`, `entry-points.json`, and existing `id-map.json`; do not synthesize an absent sidecar or substitute an operation-specific shortlist.

- exact lookup strings `=vars.<id>` and `=bindings.<id>`, and the same identifiers anywhere inside `=js:` strings, including task values, connector bodies/context, condition expressions in stage-entry, stage-exit, task-entry, and case-exit scopes, SLA expressions, and custom outputs;
- cross-task triples `sourceStage` / `sourceTask` / `sourceOutput`, output `id` / `var` / `originalVar` / `value` / `source` / `target` links (rewrite a bare mirrored `value` with its `var`), and every `selectedTasksIds`, `selectedStageId`, or `exitToStageId` reference;
- connector task, trigger, and condition-rule context/input/output consumers; top-level binding pairs grouped by `resourceKey`; and the matching `bindings_v2.json` resource projection;
- `variables.inputs`, `variables.outputs`, and `variables.inputOutputs` formal slots/companions, plus trigger `data.inputs.outputs` bridges;
- every `slaId` and `escalationId` consumer; every trigger `#<triggerId>` entry in `entry-points.json`; and, for In/Out arguments, the projected name/type/default/body/required contract in each affected `entryPoints[].input` / `.output` schema.
- every `id-map.json` entry whose owned `id` / `ruleId` or structural `stageId` / `targetId` names an affected object.

Classify each hit as preserve, rewrite/repoint, or remove before mutation. Prune a binding pair or variable companion only after a second scan of all remaining tasks, triggers, four condition scopes, and SLA rules proves its reference/producer count is zero. Regenerate `bindings_v2.json` only when top-level `bindings` changed. Preserve DNF outer/inner array order while changing rules.

### Delete a node

1. Read `caseplan.json` and run the canonical consumer sweep.
2. Remove the node from top-level `nodes` by ID without reordering survivors.
3. **Stage deletion rewires every affected consumer.** Collect all predecessor references on the deleted stage and every forward consumer of its ID: every successor stage-entry `selected-stage-completed` / `selected-stage-exited`, every source-stage exit `exitToStageId`, and condition references in all four scopes. Repoint each affected successor to the semantically corresponding surviving predecessor (or replace with `case-entered` only when the removed stage was the actual first stage). Preserve rule IDs, unrelated rules, DNF grouping/order, and every unaffected successor; never stop after the first match.
4. Top-level `edges` is normally `[]`. Defensively remove only imported edges that reference the removed node; never author a replacement edge.
5. **Trigger deletion:** remove only the matching `entry-points.json.entryPoints[]` item whose `filePath` ends in `#<removedTriggerId>`, preserving every other entry and envelope field.
6. **Trigger variable cascade.** For a removed trigger, remove `variables.inputs[]` formal slots with `elementId == <removedTriggerId>` and its `data.inputs.outputs[]` bridges. For each companion name, apply the canonical sweep, then prune the `variables.inputOutputs[]` companion only when no other producer remains.
7. **Connector cache/output cascade.** Retain any removed target's full-response `tasks/spec-cache.<elementId>.json` only as inactive audit evidence; remove it from working audit state and never use it to enrich another target. An event trigger also removes its T-entry from `trigger-spec-cache.json`; run the global-variable owner against the reduced sidecar so its spec-derived outputs/companions disappear while other triggers and spec-independent declarations survive. Do not synthesize absent caches.
8. Collect every top-level binding referenced by the removed node, including all nested connector and non-connector resource tasks, connector condition rules, and an event trigger's own context. After removal, scan every remaining task, trigger, and rule in all condition scopes; prune a binding pair and IS-cache contribution only when no remaining consumer references its IDs or `resourceKey`. Case-exit rules live in metadata rather than a stage, but still participate in the remaining-consumer scan.
9. If the removed node held connector rule outputs bound to case variables, prune the matching `variables.inputOutputs[]` companion (`elementId == "root"`) only after the canonical sweep proves no remaining producer or consumer requires it.
10. If `id-map.json` exists, remove mappings owned by the deleted node and its deleted descendants: entries whose `id` / `ruleId` is one of the removed node, task, condition, or rule IDs, or whose structural `stageId` / `targetId` points at that removed owner. Preserve every unrelated mapping.
11. Regenerate `bindings_v2.json` only if top-level `bindings` changed, per [bindings-v2-sync.md § Cleanup on task or rule removal](bindings-v2-sync.md#cleanup-on-task-or-rule-removal).
12. Edit separate, ID-anchored slices for top-level `nodes`, `entry-points.json` (trigger only), `variables.inputs` / `variables.inputOutputs`, existing caches/sidecars, existing `id-map.json`, and top-level `bindings`. Never whole-file Write.

### Delete a task

Remove a task from a stage. Tasks live only in the owning stage's nested `data.tasks` task sets, never in top-level `nodes`. Preserve the task-set contract and run the canonical sweep before deletion.

1. Read `caseplan.json`. Locate the task in its owning `stageNode.data.tasks[laneIndex]` and note its `id` (the `TaskId`) and `elementId`.
2. **Remove the task** from `data.tasks[laneIndex]`.
3. **Re-pack task sets.** Removing the only task in an inner `data.tasks` array leaves an empty task set. Drop the empty task set and preserve the remaining task-set order; never infer execution semantics from lane placement.
   - If the stage retains a `required-tasks-completed` completion rule and the deletion would leave no required task, preserve that rule and restore its contract: promote the user-designated surviving task when the request specifies one; otherwise ask which survivor becomes required or whether the completion behavior should change. Never silently delete or weaken the completion rule.
4. **Rewrite forward and reverse condition consumers of the dead `TaskId`:**
   - Any task's `entryConditions[].rules[][]` `selected-tasks-completed` rule whose `selectedTasksIds` names the deleted task — remove the id from the array; if it empties, remove the rule (and the parent condition object when it empties), per § Delete a condition rule's DNF removal mechanic.
   - Any `conditionExpression` (`=js:...`) referencing the deleted task's outputs — repoint or remove.
5. Use the canonical sweep to repoint/remove every cross-task triple and every exact/`=js:` output consumer. Do not limit the scan to task inputs; conditions, connectors, SLA expressions, custom outputs, variables, and trigger bridges are consumers too.
6. **Resource cascade.** For any connector or non-connector resource-bound task, prune its top-level binding pair only after complete remaining-consumer/reference-count scans across tasks, triggers, and all condition scopes. Connector-owned output companions receive the same zero-producer/consumer guard. Regenerate `bindings_v2.json` only if top-level `bindings` changed.
7. For a connector task, retire its target-local raw cache as audit-only through its source owner and remove its IS-cache contribution only when no remaining connector target uses it.
8. If `id-map.json` exists, remove the task's mapping plus mappings for deleted task-entry conditions/rules whose owned `id` / `ruleId` was nested under it or whose `targetId` names the deleted task. Preserve other mappings, including sibling tasks in the same stage.
9. Edit — narrow slices for the source `data.tasks` (removal + lane re-pack), each swept condition, each repointed consumer, existing connector caches, and any changed top-level bindings / `variables.inputOutputs[]`. Never whole-file Write. Validate at the section boundary.

> **Reverse of § Add a task to a stage.** § Move a task always re-pushes to a destination; § Delete a task is the terminal removal — there is no destination, so the cascade prunes references instead of repointing them to a new stage.

### Delete a condition rule

Remove a single rule from a condition (without deleting the parent stage / task / case-exit). Applies to **any** rule scope — stage entry/exit, task entry, case exit — and to both plain and connector-bound rules. The generic DNF removal (steps 1–3) is all a **plain** rule needs; the binding cascade (steps 4–6) is **connector-only** and a no-op for plain rules.

1. Read `caseplan.json`.
2. Locate the rule by `id`. **FE composes one rule per condition** (OR-style across multiple condition objects), but always honor the persisted DNF shape (`rules[][]`): remove the rule from its inner AND-array; if that inner array empties, remove only that outer OR branch; remove the condition object only when no outer branches remain.
3. Remove the rule, empty branch, or now-empty parent condition as determined above without flattening or reordering surviving DNF arrays. **Plain (non-connector) rules stop here** — skip steps 4–6. **For case-exit completion rules, first run the ≥1-completion-rule guard** in § Delete a case-exit completion rule below.
4. **(Connector rules only)** Apply the canonical sweep across all remaining tasks, triggers, four condition scopes, and SLA rules; prune a top-level binding pair only when its `resourceKey` reference count reaches zero.
5. **(Connector rules only)** Prune a `variables.inputOutputs[]` companion tied to this rule's outputs only when no remaining producer or consumer requires it.
6. **(Connector rules only)** Retire the rule's target-local raw cache as audit-only through the common owner, prune its IS-cache contribution only at zero remaining references, and regenerate `bindings_v2.json` when top-level bindings changed.
7. If `id-map.json` exists, remove the mapping whose `ruleId` names the deleted rule; if the parent condition was also removed, remove its owned `id` mapping too. Preserve every surviving rule/condition mapping.
8. Edit — separate slices for the conditions array, existing `id-map.json`, and (connector only) its cache, bindings array, and `inputOutputs[]`. Never whole-file Write.

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

The skill never creates edges, so top-level `edges` should already be `[]`. If a stray imported edge is explicitly removed, filter top-level `edges` by its ID with a narrow Edit; preserve every unrelated imported edge.

---

## Composite Operations

### Insert a stage between two existing stages

[Composite recipe](brownfield-operations-guide.md#insert-a-stage-between-two-existing-stages).

### Replace a placeholder task with an enriched task

[Composite recipe](brownfield-operations-guide.md#replace-a-placeholder-task-with-an-enriched-task).

### Re-sync a task after its source schema changed

[Composite recipe](brownfield-operations-guide.md#re-sync-a-task-after-its-source-schema-changed).

### Repoint a non-connector task at a different resource

[Composite recipe](brownfield-operations-guide.md#repoint-a-non-connector-task-at-a-different-resource).

### Move a task to a different stage or lane

[Composite recipe](brownfield-operations-guide.md#move-a-task-to-a-different-stage-or-lane).

### Rename or delete a global variable or argument

[Composite recipe](brownfield-operations-guide.md#rename-or-delete-a-global-variable-or-argument).

### Change a variable's type or default

[Composite recipe](brownfield-operations-guide.md#change-a-variables-type-or-default).

### Modify or remove an SLA or escalation

[Composite recipe](brownfield-operations-guide.md#modify-or-remove-an-sla-or-escalation).

### Replace a trigger with a different type

[Composite recipe](brownfield-operations-guide.md#replace-a-trigger-with-a-different-type).

### Re-target an event trigger (same type, different event)

[Composite recipe](brownfield-operations-guide.md#re-target-an-event-trigger-same-type-different-event).

### Convert a Stage to/from an Exception Stage

[Composite recipe](brownfield-operations-guide.md#convert-a-stage-tofrom-an-exception-stage).

### Re-wire a stage transition — RETIRED (no edges)

[Composite recipe](brownfield-operations-guide.md#re-wire-a-stage-transition--no-edges).

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

<!-- END: case-editing-operations.md -->
