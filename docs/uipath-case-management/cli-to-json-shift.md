# Design: CLI → Direct JSON Shift

Decision record for shifting `uipath-case-management` mutation operations from `uip maestro case` CLI calls to direct reads/writes of `caseplan.json`. Captures the shared understanding from the design session on 2026-04-20.

> **Scope of this document.** This is the design for the CLI → JSON mechanism shift only. The separate "one-shot build → 3-gate skeleton/enrich flow" discussion was explicitly parked and is not covered here.

---

## 1. Motivation

The current skill executes Phase 2 (`tasks.md → caseplan.json`) as a sequence of `uip maestro case` CLI calls. The CLI is:

- The only path today to a valid `caseplan.json`
- Sequential and slow — each mutation is an independent process invocation
- A changing external surface — the skill has already worked around CLI gaps (e.g., registry search)

Long-term, the `uip maestro case` CLI should keep only **operational** surface area (anything that talks HTTP to dependencies, or performs a filesystem lifecycle operation) — `registry pull`, `tasks describe`, `tasks enrich`, `get-connector`, `get-connection`, `validate`, `solution upload`, `debug`, `login`, scaffolding. Every mutation command should eventually be removed.

The skill becomes the authoritative mutation path.

## 2. Scope of the shift

**In scope — to replace with direct JSON writes:**

- `cases add`, `stages add`, `stages edit`, `stages remove`
- `edges add`, `edges edit`, `edges remove`
- `tasks add`, `tasks add-connector`, `tasks edit`, `tasks remove`
- `var bind`, `var unbind`
- `stage-entry-conditions add/remove`, `stage-exit-conditions add/remove`, `task-entry-conditions add/remove`, `case-exit-conditions add/remove`
- `sla set`, `sla rules add/remove`, `sla escalation add/remove`
- `sticky-notes add/edit/remove`

**Out of scope — stay CLI:**

- **Registry / discovery:** `registry pull`, `registry list/search`, `tasks describe`, `get-connector`, `get-connection`
- **Lifecycle:** `validate`, `debug`, `solution upload`, `login`, `case init`, `project add`, `solution new`
- **Enrichment:** `tasks enrich` — wraps a registry lookup; keep as CLI

## 3. `content/*.bpmn` timing

CLI mutation commands do NOT touch `content/*.bpmn`. The file is regenerated only by:

- `uip maestro case validate`
- `uip solution upload`

**Implication:** direct JSON writes between `validate`/`upload` checkpoints are safe — no bpmn staleness concern during mutations.

## 4. Correctness contract

Two-part bar:

1. **Structurally equivalent to CLI output.** Same schema, same fields, same relationships. Matches what the per-plugin `impl-json.md` specifies.
2. **Validator-and-renderer-accepted.** Passes `uip maestro case validate` and renders correctly in Studio Web.

Byte equality is not required (random IDs, field ordering).

### Equivalence property (≡)

For any starting state `S` and mutation `M`:

```
CLI(S, M) ≡ DirectWrite(S, M)
```

Under a normalizer that:
- Remaps generated IDs to canonical forms derived from display names
- Sorts object keys alphabetically
- Re-derives handle strings from normalized IDs (they're mechanical: `${id}____source____${direction}`)
- Ignores whitespace/formatting

Everything else — field presence, field values, nesting, arrays where order is semantic (`tasks[lane][index]`) — must match exactly.

### Authoritative spec

Per-plugin `impl-json.md` is the source of truth. If CLI diverges from spec, that's a CLI bug to file — direct-JSON-write conforms to spec, not to observed CLI behavior.

## 5. IDs — match CLI's `prefixedId` exactly

The CLI's `cli/packages/case-tool/src/utils/shortId.ts` generates IDs as `prefix + N random chars from [A-Za-z0-9]`. Source comment: *"matching the frontend's `generateNextId(prefix, count)`"* — frontend depends on this format.

| Entity | Prefix | Suffix length |
|---|---|---|
| Stage (regular + exception) | `Stage_` | 6 |
| Trigger (added after initial) | `trigger_` | 6 |
| Edge | `edge_` | 6 |
| Task | `t` | 8 |
| Task entry condition | `c` | 8 |
| Task entry rule | `r` | 8 |
| Stage/case/task condition | `Condition_` | 6 |
| Rule inside those conditions | `Rule_` | 6 |
| Sticky note | `StickyNote_` | 6 |
| SLA escalation | `esc_` | 6 |
| Binding | `b` | 8 |

Generation: every skill run uses fresh random IDs (no determinism). A sidecar `id-map.json` is written after the skill run mapping `T-entry ID → generated node ID` — enables cross-plugin reference resolution and debugging.

## 6. Render fields per node type (from CLI code)

### Regular Stage (must emit all)

```jsonc
{
  "id": "Stage_xxxxxx",
  "type": "case-management:Stage",
  "position": { "x": 100 + existingStageCount * 500, "y": 200 },
  "style": { "width": 304, "opacity": 0.8 },
  "measured": { "width": 304, "height": 128 },
  "width": 304,
  "zIndex": 1001,
  "data": {
    "label": "<label>",
    "description": "<description from sdd.md — always emit>",
    "isRequired": <true|false from sdd.md; false if unspecified>,
    "parentElement": { "id": "root", "type": "case-management:root" },
    "isInvalidDropTarget": false,
    "isPendingParent": false,
    "tasks": []
  }
}
```

**Regular Stage is created without `entryConditions` / `exitConditions`.** The CLI's `stages add` initializes those arrays only for ExceptionStage. Regular stages acquire them later via `stage-entry-conditions add` / `stage-exit-conditions add` — not at creation time.

### Exception Stage (same as regular, plus)

```jsonc
{
  "type": "case-management:ExceptionStage",
  "data": {
    // ...all regular fields...
    "entryConditions": [],
    "exitConditions": []
  }
}
```

### Trigger (minimal — no render fields beyond position)

```jsonc
{
  "id": "trigger_xxxxxx",
  "type": "case-management:Trigger",
  "position": { "x": 200, "y": 0 },
  "data": {
    "label": "<label>",
    "description": "<optional>"
  }
}
```

### Edge

```jsonc
{
  "id": "edge_xxxxxx",
  "type": "case-management:Edge",            // or TriggerEdge when source is a Trigger
  "source": "<sourceId>",
  "target": "<targetId>",
  "sourceHandle": "<sourceId>____source____right",   // 4 underscores each side
  "targetHandle": "<targetId>____target____left",
  "data": { "label": "<optional>" }
}
```

- Default directions: source=`right`, target=`left`
- `zIndex` omitted unless explicitly set
- Edge type inferred: Trigger source → TriggerEdge; Stage source → Edge

### Task

- `elementId = "${stageId}-${taskId}"` — composite of parent stage + task ID
- No `x`/`y` on the task; positioning is via lane array `stageNode.data.tasks[laneIndex].push(task)`
- Lane array is auto-expanded to cover `laneIndex` if needed

### Connector task auto-injected default entry condition

Every connector task (both `execute-connector-activity` and `wait-for-connector`) receives a default entry condition on creation:

```jsonc
{
  "id": "c<8chars>",
  "displayName": "Entry rule 1",
  "rules": [
    [{ "id": "r<8chars>", "rule": "current-stage-entered" }]
  ]
}
```

Non-connector tasks do NOT get this default. Direct-JSON-write for connector tasks must emit it.

### Stateful position computation

Stage `position.x` depends on the count of existing stages (`schema.nodes.filter(isStageNode).length`). Direct-JSON-write must count first, then compute `x = 100 + count * 500`, before writing.

## 7. Unresolvable-resource skeleton tasks

The existing skeleton-task concept (a task with `data: {}` when its registry resource is unresolved) is preserved unchanged. CLI emits this shape today when `--task-type-id` is omitted; direct-JSON-write reproduces it the same way. No new staging states or placeholder expressions.

## 8. Docs structure (mirrors uipath-maestro-flow)

Three new cross-cutting references, plus per-plugin updates:

```
references/
  case-editing-operations.md           ← strategy matrix (CLI vs JSON per plugin)
  case-editing-operations-json.md      ← cross-cutting ops, Key Differences, Pre-flight Checklist, ID scheme
  case-editing-operations-cli.md       ← CLI path (extracted from implementation.md)
  plugins/<type>/impl-cli.md           ← CLI execution doc (always exists)
  plugins/<type>/impl-json.md          ← JSON Recipe; appears once the plugin migrates
```

### Per-plugin file structure

Each plugin carries its CLI doc in `impl-cli.md` and — once migrated — a parallel `impl-json.md` with the JSON Recipe. Cross-links between the two keep agents oriented when they land in either file.

`impl-json.md` sections:

1. Purpose — one-line summary
2. Input spec — fields consumed from `tasks.md` entry
3. JSON Recipe — canonical emitted JSON block with placeholders + prose describing semantic position in `caseplan.json`
4. ID generation — prefix(es) emitted by this plugin
5. Post-write validation — confirmations to run after the write
6. Known CLI divergences — deliberate deviations where the JSON path fills a CLI gap
7. Compatibility — filled in once plugin is migrated + tested (normalized diff passes; downstream CLI ops accept output)

### Migration signaling

Two redundant views of per-plugin migration status:

1. **Central registry table** in `case-editing-operations.md` — single-page view.
2. **Frontmatter flag** `direct-json: supported` at the top of each plugin's `impl-json.md`. The presence of `impl-json.md` is itself the signal; the frontmatter just makes it explicit when read in isolation.

## 9. Execution mechanism

The LLM performs direct read/write/edit of `caseplan.json` using the standard Read/Write/Edit tools. No helper scripts. Rationale: this repo has no build system; adding a helper would mean bash+jq tooling to maintain. The Read/Write/Edit flow is what skill agents already use for every other file.

## 10. Migration strategy

- **Default posture:** CLI. Plugins opt in to direct JSON one at a time.
- **Phasing:** by plugin. Spec-only phasing with runtime co-existence — both CLI and JSON paths can coexist in the same skill run, relying on the interchangeability contract (§4).
- **Pilot plugin:** `stages`. Exercises ID generation, cross-reference integrity, nested structures, position computation, render fields.
- **Rollout PR:** one PR containing scaffolding + stages migration + goldens. No pre-spikes; fail fast in the pilot and revisit design if something breaks.
- **Cascade order (rough):** edges → global-vars → conditions → sla → tasks (non-connector) → tasks (connector) → triggers.

## 11. Compatibility testing per plugin

Every plugin migration PR ships:

1. **Golden fixture** under `docs/uipath-case-management/migration-fixtures/<plugin>/` (outside the skill — verification-only, removed once every plugin has migrated):
   - `input.sdd-fragment.md` — minimal sdd exercising that plugin
   - `cli-output.json` — captured from fresh CLI run
   - `json-write-output.json` — produced by direct-JSON-write
   - `diff.sh` — normalizes random IDs, asserts equivalence

2. **Downstream-compat checks in `impl-json.md`:**
   - CLI read commands succeed (`validate`, `tasks describe` where applicable)
   - CLI mutations can append to our output (proves co-authorship)

3. **"Compatibility" section in `impl-json.md`** declares what passed, when.

## 12. Known-wrong docs to fix

The `case-schema.md` examples and several plugin `impl.md` files show placeholder IDs (`stg00000001`, `trig0000000`, `edg00000001`, `tsk00000001`, `el_0001`) that are NOT what CLI produces. Full list and corrections below.

| File | Issue | Fix |
|---|---|---|
| `references/case-schema.md` | Fictional IDs; `elementId: el_0001`; missing render fields on Stage shape; `entryConditions`/`exitConditions` shown on regular Stage at creation time (CLI initializes them only for ExceptionStage; regular stages acquire them later via conditions plugins) | Replace IDs with CLI format; add render fields table; split Stage vs ExceptionStage creation-time shapes and note that regular Stage gains those keys later |
| `references/plugins/stages/impl.md` | Lines 49, 66: wrong IDs; position shown without formula; missing render fields; regular Stage creation example wrongly includes empty `entryConditions`/`exitConditions` at `stages add` time | Replace Resulting JSON Shape with CLI-accurate shapes; document stateful position formula |
| `references/plugins/edges/impl.md` | Verify handle format uses exactly 4 underscores each side | Document default directions |
| `references/plugins/tasks/*/impl.md` | `elementId: "el_0001"` placeholder | Replace with `${stageId}-${taskId}` composite |
| `references/plugins/triggers/manual/impl.md` | Verify fixed `{x: 200, y: 0}` | Confirm no other render fields |
| `references/plugins/tasks/connector-activity/impl.md` + `connector-trigger/impl.md` | Missing auto-injected default entry condition | Add note; direct-JSON-write must emit `current-stage-entered` default |
| `references/skeleton-tasks.md` | IDs already correct | No changes needed |

## 12a. Additional CLI-code findings (beyond the design session)

While drilling into `cli/packages/case-tool/src`, a few more discrepancies with current skill docs surfaced that should be corrected during or before the stages pilot:

1. **`root.version` is `"v17"`, not `"v12"`.** Current `case-schema.md` says v12; `cli/packages/case-tool/src/commands/cases.ts:51` shows v17.
2. **`root.publishVersion: 2`** — exists on new cases; not mentioned in skill docs.
3. **`root.data.intsvcActivityConfig: "v2"`** — exists; not mentioned.
4. **Initial trigger is hard-coded** `{ id: "trigger_1", position: {x: 0, y: 0}, data: { label: "Trigger 1" } }` — no `style`, no `measured`, no `parentElement`, no `uipath.serviceType`. Shape differs from secondary triggers added via `triggers add-manual`.
5. **Secondary trigger `style`/`measured` are `{width: 96, height: 96}`** (constant `TRIGGER_SIZE`). Secondary trigger position: `x: -100` fixed; `y: 200` or `max(existingY) + 140`.
6. **Default `root.data.uipath.variables`** appears to start as `{ inputOutputs: [] }` only (not `{inputs, outputs, inputOutputs}`). Worth verifying when adding the global-vars plugin.

These are follow-up fixes, not blockers for the stages pilot.

## 13. Open empirical questions (deferred)

The earlier spike list was dropped — we find these in the pilot instead. For reference:

1. Does `uip maestro case validate` tolerate an `adhoc` rule with no `conditionExpression`? (Matters for the parked 3-gate flow.)
2. Does `uip maestro case tasks enrich` operate statelessly against any valid `caseplan.json`, or does it maintain internal state about which tasks it created?
3. Does `uip maestro case var bind` work against a hand-written + enriched task?
4. Does Studio Web accept IDs in the exact CLI format when produced by our direct-JSON-write? (Very likely yes since we match CLI's algorithm — but unverified.)

## 14. Deferred: one-shot → 3-gate flow

The user's second design idea — a multi-gate flow where gate 2 publishes a "structural" caseplan to Studio Web for preview before gate 3 enrichment — is parked. This shift provides the foundation: direct-JSON-write lets each gate own its file-emission responsibility cleanly. The 3-gate design gets its own session.
