# Caseplan Editing Operations

Cross-cutting mechanics for mutating `caseplan.json` via Read/Write/Edit. Per-node shapes live in each plugin's `impl-json.md`.

---

## Responsibilities When Writing caseplan.json

Every write must supply the fields below. Studio Web frontend expects them; missing any risks validation failure or broken render.

| Concern | What you write |
|---|---|
| ID generation | Generate per `prefixedId(prefix, count)` — see "ID Generation" below |
| `elementId` on tasks | Compute `${stageId}-${taskId}` and write on every task |
| Edge handles | `${nodeId}____<source\|target>____<direction>` — exactly 4 underscores each side |
| Stage position | Count existing stages, compute `{ x: 100 + count * 500, y: 200 }` |
| Stage render fields | `style`, `measured`, `width`, `zIndex`, `data.parentElement`, `data.isInvalidDropTarget`, `data.isPendingParent` on every Stage node |
| Connector task default entry condition | Inject `current-stage-entered` entry condition on every connector task |
| Edge cleanup on node removal | Remove every edge whose `source` or `target` equals the removed node ID |
| Root-level bindings cleanup | Prune `root.data.uipath.bindings` entries no longer referenced by any task |
| `bindings_v2.json` sync | Each connector plugin regenerates after writing root bindings — see [bindings-v2-sync.md](bindings-v2-sync.md) |
| Connection resource files | Connector plugins create under `resources/solution_folder/connection/` — see [bindings-v2-sync.md](bindings-v2-sync.md) |
| Lane array expansion | Expand `stageNode.data.tasks` to cover `laneIndex` before pushing |
| `id-map.json` sidecar | Initialize on T01 (case plugin); append per plugin; flush to disk |
| `caseplan.json` file creation | T01 (case plugin) writes from scratch; downstream plugins mutate in place |

---

## Pre-flight Checklist

Before every write, confirm each item.

1. **Canonical `caseplan.json` location.** The file lives at `<SolutionDir>/<ProjectName>/caseplan.json` (next to `project.uiproj`). Every Read/Write must target that exact path.
   - **For the `case` plugin (T01)**: neither `caseplan.json` nor the 5 scaffold files (`project.uiproj`, `operate.json`, `entry-points.json`, `bindings_v2.json`, `package-descriptor.json`) exist before the plugin runs. `uip solution new` (Step 6.0) creates the solution dir + `.uipx` only. T01 creates the project dir and writes all 6 files directly — § Scaffold writes the 5 boilerplate files, § Write caseplan.json writes the root skeleton. See [plugins/case/impl-json.md](plugins/case/impl-json.md). Pre-scaffold check: `<SolutionDir>/<SolutionName>.uipx` exists AND none of the 5 scaffold files exist yet in `<SolutionDir>/<ProjectName>/`.
   - **For every other plugin**: `caseplan.json` must already exist (the `case` plugin always runs first as T01). If absent, run the `case` plugin first; do not attempt to synthesize a different JSON shape.

2. **IDs match expected format.** Generate IDs using the `prefixedId` algorithm below. The frontend's `generateNextId(prefix, count)` expects this exact format — deviation risks Studio Web rejection.

3. **Render fields present on every new Stage:**
   - `style: { width: 304, opacity: 0.8 }`
   - `measured: { width: 304, height: 128 }`
   - `width: 304`
   - `zIndex: 1001`
   - `data.parentElement: { id: "root", type: "case-management:root" }`
   - `data.isInvalidDropTarget: false`
   - `data.isPendingParent: false`

4. **Position computed, not hard-coded.** Count `schema.nodes.filter(n => n.type === "case-management:Stage" || n.type === "case-management:ExceptionStage")` BEFORE writing a new stage. Compute `position.x = 100 + count * 500`, `position.y = 200`.

5. **Regular Stage vs Exception Stage at creation time.** ExceptionStage initializes `entryConditions` / `exitConditions` as `[]`. Regular `case-management:Stage` is written without those keys — they appear later when stage-entry-conditions or stage-exit-conditions are added. Match this creation-time shape: no empty arrays on regular Stage.

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
    - **Exception — stages plugin:** A stages-only caseplan is also known-invalid (stages have no incoming edges yet). The plugin's validation parity is captured in the fixture instead.

---

## ID Generation

All IDs follow the `prefixedId(prefix, count)` scheme: a fixed prefix + `count` random characters drawn uniformly from `[A-Za-z0-9]` (62 chars). Source: `cli/packages/case-tool/src/utils/shortId.ts`.

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

**Do NOT** shell out to `python`, `node`, `jq`, `sed`, `awk`, or any other process to read, parse, transform, or write the JSON. No helper scripts, no inline one-liners that modify files, no `python3 -c '... json.load ... json.dump ...'`. The agent holds the parsed object in its own reasoning; the file system is touched only via Read/Write/Edit.

This is a hard constraint — it keeps every mutation reviewable in the tool-call transcript and prevents silent state changes the user cannot audit.

Pseudocode blocks in this document and in per-plugin `impl-json.md` files (`issues.append(...)`, `existingTriggers = schema.nodes.filter(...)`, etc.) are **specifications of intent**, not commands to execute. Read them, apply the logic in-head, then use Read/Write/Edit to realize the mutation.

**Bash is still used for**: ID randomness (`node -e "..."` one-liners that print to stdout only — see "Generate a fresh ID" below), `uip maestro case validate`, and `uip maestro case registry` discovery. Never for file mutation.

### Read → modify → write

Always read `caseplan.json` fully with the Read tool, modify the in-memory object in reasoning, and write the whole file back with the Write tool. For narrowly-scoped, unambiguous single-field updates, the Edit tool is also acceptable. Re-read before the next mutation; do not hold the parsed object across tool calls.

**One category per cycle.** Each plugin category (stages, edges, triggers, tasks, conditions-per-scope, SLA, variables) gets its own Read → mutate → Write round-trip covering every T-entry in that category. **Do not compose across categories in memory and flush once** — that breaks per-category rollback and hides intermediate state.

**Edit-tool-first.** When a mutation is a narrowly-scoped, unambiguous single-field change (e.g., binding a task input `value`, setting `isRequired: true` on a specific task), prefer the `Edit` tool — it avoids the full-file Read cost and shows the exact diff in the tool-call transcript. Use Read+Write when the mutation is structural (appending a new node / edge / condition array) or when Edit's `old_string` can't be made unique in the file.

Re-read `caseplan.json` before starting each new category — do not hold the parsed object across categories.

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
5. Prepend the node to `schema.nodes` (Stage convention).
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

See [skeleton-tasks.md § Upgrade Procedure](skeleton-tasks.md). Edit the task's `data` field in place to add `taskTypeId`, schema-driven `inputs`/`outputs`, and any required context — keeping the task's `id` and `elementId` unchanged so any conditions referencing it remain valid.

### Re-wire a stage's outgoing edge

Edges are immutable on source/target — delete + re-add to re-wire.

---

## Validation Cadence

Run `uip maestro case validate <file> --output json` after every plugin's batch of mutations — not after every individual write. Intermediate states can be invalid (e.g., an edge pointing at a target that will be added next); validate is authoritative at the plugin boundary.

On failure: fix the reported issue (usually a missing field, malformed handle, or orphan ID) and re-validate. Up to 3 retries per plugin; if still failing, halt and AskUserQuestion per SKILL.md Rule #20.

---

## Anti-Patterns

- **Do NOT shell out to `python`, `node`, `jq`, `sed`, `awk`, or any other subprocess to mutate `caseplan.json` or its siblings.** Use Read + Write/Edit only. Subprocess scripts bypass the tool-call audit trail and make the mutation invisible in the transcript. See "Tool usage — mandatory" above.
- **Do NOT write helper scripts (`.py`, `.js`, `.sh`) that open / parse / modify / save JSON files.** Even one-shot scripts are forbidden — the agent is the processor, Read/Write/Edit are the only I/O primitives.
- **Do NOT hand-edit IDs with human-readable patterns** (e.g., `my_stage_1`). The frontend's `generateNextId` expects the `prefixedId` format.
- **Do NOT forget `style`/`measured`/`width`/`zIndex` on stages.** Validate passes, but Studio Web renders broken.
- **Do NOT put `entryConditions`/`exitConditions` on regular Stages.** Only ExceptionStage has them at creation time.
- **Do NOT skip the default entry condition on connector tasks.** The frontend expects it.
- **Do NOT write partial JSON with Edit tool regex.** Round-trip through Read → reason → Write (or Edit for narrowly-scoped unambiguous replacements).
- **Do NOT run validation after every single write.** Validate at plugin boundaries, not per-field.
- **Do NOT batch across categories into one JSON write.** Each category (stages, edges, tasks, conditions, SLA, variables) gets its own Read → mutate → Write cycle. No "compose all stages + edges + tasks in memory, flush once" — that destroys per-category rollback. Batching T-entries _within_ a single category (e.g., all stages in one Write) is fine.
