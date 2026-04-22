# Case Editing Operations — Direct JSON Strategy

All mutations to `caseplan.json` performed via direct read/write/edit of the file, bypassing `uip maestro case` mutation commands. This document covers the cross-cutting mechanics; per-node JSON shapes live in each plugin's `impl-json.md`.

> **When to use this strategy:** Only for plugins marked `Strategy = JSON` in [case-editing-operations.md](case-editing-operations.md). Default is still CLI — see [case-editing-operations-cli.md](case-editing-operations-cli.md).

---

## Key Differences from CLI

When editing `caseplan.json` directly, you are responsible for everything the CLI handles automatically:

| Concern | CLI handles | Direct JSON — you must |
|---|---|---|
| ID generation | Auto-generated via `prefixedId(prefix, count)` | Generate matching IDs per the ID Generation section below |
| `elementId` on tasks | Auto-computed as `${stageId}-${taskId}` | Compute and write this field on every task |
| Edge handles | Auto-formatted as `${nodeId}____<source|target>____<direction>` | Construct handle strings with exactly 4 underscores on each side |
| Stage position | Auto-computed `{ x: 100 + existingStageCount * 500, y: 200 }` | Count existing stages first; compute; then write |
| Stage render fields | Auto-set (`style`, `measured`, `width`, `zIndex`, `data.parentElement`, `data.isInvalidDropTarget`, `data.isPendingParent`) | Emit every one of these fields on every new Stage node |
| Connector task default entry condition | Auto-injected (`current-stage-entered`) | Emit the default entry condition on every connector task |
| Edge cleanup on stage removal | Cascaded automatically | Find and remove every edge where `source` or `target` equals the removed stage's ID |
| Root-level bindings cleanup | Auto-managed when a connector task is removed | Prune `root.data.uipath.bindings` entries no longer referenced by any task |
| Lane array expansion | Auto-expanded when `--lane <n>` references an index past the current length | Ensure `stageNode.data.tasks` is expanded to include `laneIndex` before pushing |
| `id-map.json` sidecar | Not maintained by CLI | Write T-entry → generated ID mappings after the skill run |

---

## Pre-flight Checklist

Before every write to `caseplan.json`, confirm each item. These are the failure modes the CLI normally prevents.

1. **Canonical `caseplan.json` exists and is located.** Direct-JSON-write operates on a file that must already exist — the `case` plugin (scaffolding + `cases add`) stays on the CLI strategy and is the only path that creates `caseplan.json`. The file lives at `<SolutionDir>/<ProjectName>/caseplan.json` (next to `project.uiproj`). Every Read/Write must target that exact path — not a stray copy in the solution root or working directory. If the file doesn't exist yet, run the `case` plugin first; do not attempt to synthesize a fresh `caseplan.json` by direct-JSON-write.

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

5. **Regular Stage vs Exception Stage at creation time.** CLI `stages add` initializes `entryConditions` / `exitConditions` only for `case-management:ExceptionStage` (as `[]`). Regular `case-management:Stage` is written without those keys. They are created later — by `stage-entry-conditions add` / `stage-exit-conditions add` — and at that point regular stages DO carry them. Match the CLI's creation-time shape: no empty arrays on regular Stage.

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

13. **Validate after every plugin's batch.** Run `uip maestro case validate <file> --output json` after each plugin completes its mutations. Fixing errors early is cheaper than chasing a cascade.

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

After the skill run produces `caseplan.json`, write a sidecar `id-map.json` adjacent to it, mapping T-entries from `tasks.md` to generated IDs:

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

### Read → modify → write

Always read `caseplan.json` fully, modify the in-memory object, and write the whole file back. Don't try to patch individual fields with Edit tool regex — nested JSON structures are too fragile. Use Read → Write as the workflow. Re-read before the next mutation; do not hold the parsed object across tool calls.

### Generate a fresh ID

Per the algorithm above. Use Bash + node/python inline when you need true randomness, or compute in-head for single-run needs:

```bash
# Bash + node one-liner for Stage_ prefix, 6 chars
node -e "const c='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';let s='Stage_';for(let i=0;i<6;i++)s+=c[Math.floor(Math.random()*62)];console.log(s)"
```

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

See [skeleton-tasks.md § Upgrade Procedure](skeleton-tasks.md) for the CLI-driven flow. For direct-JSON-write, the equivalent is: edit the task's `data` field in place to add `taskTypeId`, schema-driven `inputs`/`outputs`, and any required context — keeping the task's `id` and `elementId` unchanged so any conditions referencing it remain valid.

### Re-wire a stage's outgoing edge

Edges are immutable on source/target at the CLI level (`edges edit` only allows label/handle changes). To re-wire: delete + re-add.

---

## Validation Cadence

Run `uip maestro case validate <file> --output json` after every plugin's batch of mutations — not after every individual write. Intermediate states can be invalid (e.g., an edge pointing at a target that will be added next); the CLI handles this tolerably well but validate is authoritative at the plugin boundary.

On failure: fix the reported issue (usually a missing field, malformed handle, or orphan ID) and re-validate. Up to 3 retries per plugin; if still failing, halt and AskUserQuestion per the skill's Critical Rule #20.

---

## Anti-Patterns

- **Do NOT hand-edit IDs with human-readable patterns** (e.g., `my_stage_1`). The frontend's `generateNextId` expects CLI's format.
- **Do NOT forget `style`/`measured`/`width`/`zIndex` on stages.** Validate passes, but Studio Web renders broken.
- **Do NOT put `entryConditions`/`exitConditions` on regular Stages.** Only ExceptionStage has them.
- **Do NOT skip the default entry condition on connector tasks.** The frontend expects it.
- **Do NOT write partial JSON with Edit tool regex.** Round-trip through Read → parse → modify → Write.
- **Do NOT run validation after every single write.** Validate at plugin boundaries, not per-field.
