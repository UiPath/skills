# Case Editing Operations

All mutations to `caseplan.json` performed via direct read/write/edit of the file. This document covers cross-cutting mechanics; per-node JSON shapes live in each plugin's `impl-json.md`.

---

## Responsibilities of Direct JSON Authoring

When editing `caseplan.json` directly, the agent is responsible for these mechanics:

| Concern | Requirement |
|---|---|
| ID generation | Generate IDs per the ID Generation section below using the `prefixedId(prefix, count)` algorithm |
| `elementId` on tasks | Compute and write `${stageId}-${taskId}` on every task |
| Edge handles | Construct handle strings as `${nodeId}____<source\|target>____<direction>` (exactly 4 underscores on each side) |
| Stage position | Count existing stages first; compute `{ x: 100 + existingStageCount * 500, y: 200 }`; then write |
| Stage render fields | Emit `style`, `measured`, `width`, `zIndex`, `data.parentElement`, `data.isInvalidDropTarget`, `data.isPendingParent` on every new Stage node |
| Connector task default entry condition | Emit the default `current-stage-entered` entry condition on every connector task |
| Edge cleanup on stage removal | Find and remove every edge where `source` or `target` equals the removed stage's ID |
| Root-level bindings cleanup | Prune `root.data.uipath.bindings` entries no longer referenced by any task |
| Lane array expansion | Ensure `stageNode.data.tasks` is expanded to include `laneIndex` before pushing |
| `id-map.json` sidecar | Initialize on T01 (case plugin); append per plugin as IDs are generated; flush to disk at end of run (or after each plugin for durability) |
| `caseplan.json` file creation | T01 (case plugin) writes the file from scratch; downstream plugins mutate in place |

---

## Pre-flight Checklist

Before every write to `caseplan.json`, confirm each item. These are the failure modes the CLI normally prevents.

1. **Canonical `caseplan.json` location.** The file lives at `<SolutionDir>/<ProjectName>/caseplan.json` (next to `project.uiproj`). Every Read/Write must target that exact path — not a stray copy in the solution root or working directory.
   - **For the `case` plugin (T01)**: neither `caseplan.json` nor the 5 scaffold files (`project.uiproj`, `operate.json`, `entry-points.json`, `bindings_v2.json`, `package-descriptor.json`) exist before the plugin runs. `uip solution new` (Step 6.0, CLI) creates the solution dir + `.uipx` only. T01 creates the project dir and writes all 6 files directly — § Scaffold writes the 5 boilerplate files, § Write caseplan.json writes the root skeleton. See [plugins/case/impl-json.md](plugins/case/impl-json.md). Pre-scaffold check: `<SolutionDir>/<SolutionName>.uipx` exists AND none of the 5 scaffold files exist yet in `<SolutionDir>/<ProjectName>/`.
   - **For every other plugin**: `caseplan.json` must already exist (the `case` plugin always runs first as T01). If absent, run the `case` plugin first; do not attempt to synthesize a different JSON shape.

2. **IDs match CLI format.** Generate IDs using the `prefixedId` algorithm (see "ID Generation" below). The frontend's `generateNextId(prefix, count)` expects this exact format — deviation risks Studio Web rejection.

3. **Render fields present on every new Stage:**
   - `style: { width: 304, opacity: 0.8 }`
   - `measured: { width: 304, height: 128 }`
   - `width: 304`
   - `zIndex: 1001`
   - `data.parentElement: { id: "root", type: "case-management:root" }`
   - `data.isInvalidDropTarget: false`
   - `data.isPendingParent: false`

4. **Position computed, not hard-coded.** Count `schema.nodes.filter(n => n.type === "case-management:Stage" || n.type === "case-management:ExceptionStage")` BEFORE writing a new stage. Compute `position.x = 100 + count * 500`, `position.y = 200`.

5. **Regular Stage vs Exception Stage at creation time.** Regular `case-management:Stage` nodes are written without `entryConditions` / `exitConditions` keys. `case-management:ExceptionStage` nodes initialize both as empty arrays at creation time. Regular stages acquire those keys later when the condition plugins write them. Do not emit empty arrays on regular Stage.

6. **Edge handles use exactly 4 underscores each side.** `${sourceId}____source____${direction}`, `${targetId}____target____${direction}`. Directions: `right` | `left` | `top` | `bottom`. Defaults: source=`right`, target=`left`.

7. **Edge type inferred from source.** Look up the source node's `type` in `schema.nodes`. If it's `case-management:Trigger`, the edge type is `case-management:TriggerEdge`. Otherwise `case-management:Edge`.

8. **Every stage has at least one inbound edge.** Orphan stages don't execute. When adding a stage, also plan its inbound edge.

9. **One task per lane (layout convention).** Increment `laneIndex` per task within a stage starting at 0. Expand `stageNode.data.tasks` to cover the lane index before pushing.

10. **Task `elementId` = `${stageId}-${taskId}`.** Compute and write this composite string on every new task.

11. **Connector task default entry condition.** Every `execute-connector-activity` or `wait-for-connector` task gets an auto-injected entry condition:
    ```json
    { "id": "c<8chars>", "displayName": "Entry rule 1",
      "rules": [[{ "id": "r<8chars>", "rule": "current-stage-entered" }]] }
    ```
    Non-connector tasks do NOT get this default.

12. **Cross-task bindings reference existing IDs.** Before writing a `var bind` entry, confirm the source stage ID and source task ID both exist in `caseplan.json`.

13. **Validate after every plugin's batch — with exceptions.** Run `uip maestro case validate <file> --output json` after each plugin completes its mutations. Fixing errors early is cheaper than chasing a cascade.
    - **Exception — case plugin (T01):** A case-only caseplan is known-invalid by design (no stage nodes + trigger has no outgoing edges). Skip `uip maestro case validate` after T01; a cheap `JSON.parse` + root/trigger shape check is the substitute — see [plugins/case/impl-json.md § Post-write validation](plugins/case/impl-json.md#post-write-validation).
    - **Exception — stages plugin (pilot):** A stages-only caseplan is also known-invalid (stages have no incoming edges yet). The plugin's validation parity is captured in the fixture instead.

---

## ID Generation

All IDs follow the CLI's `prefixedId(prefix, count)` scheme: a fixed prefix + `count` random characters drawn uniformly from `[A-Za-z0-9]` (62 chars). Source: `cli/packages/case-tool/src/utils/shortId.ts`.

| Entity | Prefix | Suffix length | Example |
|---|---|---|---|
| Stage (regular + exception) | `Stage_` | 6 | `Stage_aB3kL9` |
| Trigger (secondary — any subtype: manual / timer / event) | `trigger_` | 6 | `trigger_xY2mNp` |
| Initial trigger (first trigger in the case) | fixed literal `trigger_1` | — | `trigger_1` |
| Edge | `edge_` | 6 | `edge_Qz7hVr` |
| Task | `t` | 8 | `t8GQTYo8O` |
| Task entry condition | `c` | 8 | `c4fGhJ2Mn` |
| Task entry rule | `r` | 8 | `rK9xQw3Lp` |
| Stage / case / task file-level condition | `Condition_` | 6 | `Condition_xC1XyX` |
| Rule inside those conditions | `Rule_` | 6 | `Rule_jdBFrJ` |
| Sticky note | `StickyNote_` | 6 | `StickyNote_aBcDeF` |
| SLA escalation | `esc_` | 6 | `esc_gH2jKl` |
| Binding | `b` | 8 | `b3KmNp7Q9` |

### Algorithm

Match the CLI exactly:

1. Start with the prefix string.
2. Generate `count * 2` random bytes (over-sampled to reduce refills).
3. For each byte, if the byte value is < `248` (the largest multiple of 62 ≤ 256), take `byte % 62` and look up the character in `[A-Za-z0-9]`. Otherwise skip the byte.
4. Stop once `count` characters have been appended.

Every skill run generates fresh random IDs — no determinism.

### Sidecar `id-map.json`

`id-map.json` is built up incrementally during the run, flushed adjacent to `caseplan.json`. Lifecycle:

1. **T01 (case plugin)** creates the file with the literal root entry: `{ "T01": { "kind": "case", "id": "root" } }`. No trigger is emitted at T01 — the triggers plugin records its entry at T02.
2. **Downstream plugins** read the file, append entries for generated IDs (stage, edge, task, condition, etc.), write back. Each plugin writes the map before handing off to the next so cross-plugin references can resolve via the on-disk file.
3. **End of run:** the file is complete and lives alongside `caseplan.json`.

Mapping T-entries from `tasks.md` to generated IDs:

```json
{
  "T02": { "kind": "trigger", "id": "trigger_xY2mNp" },
  "T04": { "kind": "stage",   "id": "Stage_aB3kL9" },
  "T05": { "kind": "stage",   "id": "Stage_cD4mNt" },
  "T06": { "kind": "edge",    "id": "edge_Qz7hVr" },
  "T10": { "kind": "task",    "id": "t8GQTYo8O", "stageId": "Stage_aB3kL9" }
}
```

Used for: debugging, downstream cross-task reference resolution within the same skill run, correlating `registry-resolved.json` entries with the final case file.

---

## Primitive Operations

### Tool usage — mandatory

All mutations to `caseplan.json` (and sibling files like `entry-points.json`, `id-map.json`) MUST go through Claude's built-in tools only:

- **Read** to load the file.
- **Write** to rewrite the whole file.
- **Edit** for narrowly-scoped, unambiguous in-place replacements.

**Do NOT** shell out to `python`, `node`, `jq`, `sed`, `awk`, or any other process to read, parse, transform, or write the JSON. No helper scripts, no inline one-liners that modify files, no `python3 -c '... json.load ... json.dump ...'`, no `node -e "...fs.writeFileSync...".` The agent holds the parsed object in its own reasoning; the file system is touched only via Read/Write/Edit.

This is a hard constraint — it keeps every mutation reviewable in the tool-call transcript and prevents silent state changes the user cannot audit.

**Anti-patterns that count as file mutation (forbidden — write the file via the Write/Edit tool instead):**

- `node -e "const fs=require('fs'); ... fs.writeFileSync(...)"` — the `node -e` permission is for stdout-only helpers, not file I/O.
- `node -e "..."` / `python -c "..."` / `jq '...' caseplan.json` followed by `> caseplan.json`, `>> caseplan.json`, or `| tee caseplan.json` — shell redirection onto a skill artifact is mutation, regardless of which interpreter ran.
- `cat caseplan.json | jq '...'` even if you only "intend to print" — `jq` is forbidden; use Read.
- `sed -i` / `awk -i inplace` / `python -c "open('caseplan.json','w')..."` — same family, all forbidden.
- `bash -c "...>caseplan.json..."` — wrapping the redirection in another shell does not exempt it.

Pseudocode blocks in this document and in per-plugin `impl-json.md` files (`issues.append(...)`, `existingTriggers = schema.nodes.filter(...)`, etc.) are **specifications of intent**, not commands to execute. Read them, apply the logic in-head, then use Read/Write/Edit to realize the mutation.

**Bash is still used for**: ID randomness (`node -e "..."` one-liners that print to stdout only — see "Generate a fresh ID" below; subprocess MUST NOT `require('fs')`, `require('child_process')`, or use any redirection operator), `uip solution new` / `uip solution project add` / `uip solution upload`, `uip maestro case validate`, `uip maestro case debug`, `uip maestro case registry` discovery, and read-only metadata fetches (`uip maestro case tasks describe`, `is resources describe`, `is triggers describe`). Never for file mutation.

### Read → modify → write

Always read `caseplan.json` fully with the Read tool, modify the in-memory object in reasoning, and write the whole file back with the Write tool. For narrowly-scoped, unambiguous single-field updates, the Edit tool is also acceptable. Re-read before the next mutation; do not hold the parsed object across tool calls.

**One T-entry per cycle.** Each T-entry from `tasks.md` gets its own Read → mutate → Write round-trip. Do not batch multiple T-entries (e.g., "add all 5 stages in one write") — the transcript must show one tool-call pair per declarative unit, so every mutation is independently reviewable and revertable. Within a single T-entry, all fields that logically belong to that entry (a stage node plus its render fields, a task plus its default entry condition, etc.) are written together in that one Write.

### Generate a fresh ID

Per the algorithm above. Use a Bash + `node -e` one-liner that **only prints the ID to stdout** — the agent consumes the printed value and embeds it via Write/Edit. No file I/O inside the subprocess.

```bash
# Bash + node one-liner for Stage_ prefix, 6 chars — stdout only, no file access
node -e "const c='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';let s='Stage_';for(let i=0;i<6;i++)s+=c[Math.floor(Math.random()*62)];console.log(s)"
```

If the Bash tool is unavailable for any reason, fall back to a pseudo-random ID composed in reasoning from the algorithm above — still no subprocess touching the file.

### Add a node (Trigger / Stage / ExceptionStage)

1. Read `caseplan.json`.
2. Determine render fields per plugin's JSON Recipe.
3. For Stages: count existing stages, compute `position.x = 100 + count * 500`, `position.y = 200`.
4. Generate a fresh node ID.
5. Append the node to `schema.nodes` (stages use `.unshift()` in the CLI — prepend — but either position works for the frontend; prepend to match CLI output exactly).
6. Write `caseplan.json`.

### Add an edge

1. Read `caseplan.json`.
2. Verify `source` and `target` IDs both exist in `schema.nodes`.
3. Look up the source node's `type` to infer edge type (Trigger → `TriggerEdge`, else `Edge`).
4. Generate a fresh edge ID.
5. Construct the edge object with `sourceHandle` and `targetHandle` (4 underscores each side).
6. Append to `schema.edges`.
7. Write.

### Add a task to a stage

1. Read `caseplan.json`.
2. Locate the stage node by ID.
3. Ensure `stageNode.data.tasks` exists; ensure `stageNode.data.tasks[laneIndex]` exists (expand with empty arrays if needed).
4. Generate a task ID.
5. Compute `elementId = ${stageId}-${taskId}`.
6. Build the task object per the plugin's JSON Recipe.
7. For connector tasks, add the auto-injected default entry condition.
8. Push onto `stageNode.data.tasks[laneIndex]`.
9. Write.

### Bind an input

Variable bindings live on the task's `data.inputs[<index>]` entries — each input has either a literal/expression `value` or a cross-task source reference (`sourceStage`, `sourceTask`, `sourceOutput`). Modify the input entry in place and write.

Details per plugin — see [bindings-and-expressions.md](bindings-and-expressions.md).

### Delete a node

1. Read `caseplan.json`.
2. Remove the node from `schema.nodes` by ID.
3. Remove every edge where `source` or `target` equals the removed node's ID.
4. If the node was a stage containing a connector task, prune `root.data.uipath.bindings` entries referenced only by that task.
5. Write.

### Delete an edge

1. Read.
2. Filter `schema.edges` by the edge ID.
3. Write.

---

## Composite Operations

### Insert a stage between two existing stages

1. Find and remove the edge connecting the two existing stages.
2. Add the new stage node (with render fields).
3. Add two edges: upstream → new stage, new stage → downstream.

### Replace a skeleton task with an enriched task

See [skeleton-tasks.md § Upgrade Procedure](skeleton-tasks.md). The upgrade edits the task's `data` field in place to add `taskTypeId`, schema-driven `inputs`/`outputs`, and any required context — keeping the task's `id` and `elementId` unchanged so any conditions referencing it remain valid.

### Re-wire a stage's outgoing edge

To re-wire an edge's source/target: delete the edge entry from `schema.edges[]` and write a fresh one. Label/handle changes can be applied in place.

---

## Validation Cadence

Run `uip maestro case validate <file> --output json` after every plugin's batch of mutations — not after every individual write. Intermediate states can be invalid (e.g., an edge pointing at a target that will be added next); validate is authoritative at the plugin boundary.

On failure: fix the reported issue (usually a missing field, malformed handle, or orphan ID) and re-validate. Up to 3 retries per plugin; if still failing, halt and AskUserQuestion per the skill's Critical Rule #20.

---

## Anti-Patterns

- **Do NOT shell out to `python`, `node`, `jq`, `sed`, `awk`, or any other subprocess to mutate `caseplan.json` or its siblings.** Use Read + Write/Edit only. Subprocess scripts bypass the tool-call audit trail and make the mutation invisible in the transcript. See "Tool usage — mandatory" above.
- **Do NOT write helper scripts (`.py`, `.js`, `.sh`) that open / parse / modify / save JSON files.** Even one-shot scripts are forbidden — the agent is the processor, Read/Write/Edit are the only I/O primitives.
- **Do NOT hand-edit IDs with human-readable patterns** (e.g., `my_stage_1`). The frontend's `generateNextId` expects CLI's format.
- **Do NOT forget `style`/`measured`/`width`/`zIndex` on stages.** Validate passes, but Studio Web renders broken.
- **Do NOT put `entryConditions`/`exitConditions` on regular Stages.** Only ExceptionStage has them.
- **Do NOT skip the default entry condition on connector tasks.** The frontend expects it.
- **Do NOT write partial JSON with Edit tool regex.** Round-trip through Read → reason → Write (or Edit for narrowly-scoped unambiguous replacements).
- **Do NOT run validation after every single write.** Validate at plugin boundaries, not per-field.
- **Do NOT batch multiple T-entries into one JSON write.** Each T-entry from `tasks.md` gets its own Read → mutate → Write cycle. No "compose all stages + edges + tasks in memory, flush once" — that destroys the per-mutation audit trail.
