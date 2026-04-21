---
direct-json: supported
---

# stage-entry-conditions — JSON Implementation

Authoritative when the matrix in [`case-editing-operations.md`](../../../case-editing-operations.md) lists `conditions/stage-entry-conditions = JSON`. Cross-cutting direct-JSON rules live in [`case-editing-operations-json.md`](../../../case-editing-operations-json.md). For the CLI fallback, see [`impl-cli.md`](impl-cli.md).

## Purpose

Attach one entry condition (with one initial rule) to a Stage or ExceptionStage node's `data.entryConditions[]`. Controls when the stage may be entered.

## Input spec (from `tasks.md`)

| Field | Required | Notes |
|---|---|---|
| `target-stage` | yes | Resolves to a captured `Stage_xxxxxx` / ExceptionStage ID from the stages plugin. |
| `display-name` | optional | String. When absent, the condition is written without `displayName`. |
| `is-interrupting` | optional | Boolean. When absent, the key is **omitted** — do not emit `isInterrupting: false`. Only write the key when `sdd.md` declares the field. |
| `rule-type` | yes | One of `case-entered`, `selected-stage-completed`, `selected-stage-exited`, `user-selected-stage`, `wait-for-connector`. |
| `selected-stage` | conditional | Required for `selected-stage-completed` and `selected-stage-exited`. Resolves to a captured stage ID. |
| `condition-expression` | conditional | Required for `wait-for-connector`. Optional (but persisted when provided) for the other four rule-types. |

## ID generation

- Condition prefix: `Condition_`, suffix length 6 → `Condition_xxxxxx`
- Rule prefix: `Rule_`, suffix length 6 → `Rule_xxxxxx`
- Algorithm: per [`case-editing-operations-json.md § ID Generation`](../../../case-editing-operations-json.md#id-generation)

Record `T<n> → Condition_xxxxxx` in `id-map.json` (kind `stage-entry-condition`, plus `stageId` for the attachment target).

## Attachment rules

1. Locate the stage node by `target-stage` ID in `schema.nodes`. It must be `case-management:Stage` or `case-management:ExceptionStage`.
2. If `data.entryConditions` is absent (regular Stage, no prior conditions), create it as `[]` before appending. Do not touch `entryConditions` on any other node type.
3. Append the new condition object via `.push()` (insertion-order preserved — matches the CLI).

Do **not** modify any other fields on the stage (position, label, isRequired, etc.).

## Recipe — Condition object (shared across rule-types)

```json
{
  "id": "<Condition_xxxxxx>",
  "displayName": "<from sdd.md — omit key if not provided>",
  "rules": [
    [ <rule object from matrix below> ]
  ]
}
```

Append `"isInterrupting": true` (or `false`) **only** when `sdd.md` declared the field. Emit it **after** `rules` to match the CLI's field order.

**Field order inside the condition object:** `id` → `displayName` → `rules` → `isInterrupting` (when present). JSON consumers do not require this order, but preserving it simplifies the golden diff against the CLI.

**Rules structure is DNF** — outer array is OR, inner arrays are AND. The `add` path always writes `rules: [[<rule>]]` (one group, one rule). Additional rules (added later via `edit --rule-type`) are appended as **new outer-array groups**, not nested in the existing group:

```json
"rules": [
  [ { ..."rule 1" } ],
  [ { ..."rule 2 (added later)" } ]
]
```

## Recipe — Rule object per rule-type

All five rule-types share `rule` (string literal matching the rule-type) and `id` (`Rule_xxxxxx`). Extra fields depend on the rule-type:

| `rule-type` | Rule JSON shape |
|---|---|
| `case-entered` | `{ "rule": "case-entered", "id": "<Rule_xxxxxx>" }` |
| `selected-stage-completed` | `{ "rule": "selected-stage-completed", "id": "<Rule_xxxxxx>", "selectedStageId": "<Stage_xxxxxx>" }` |
| `selected-stage-exited` | `{ "rule": "selected-stage-exited", "id": "<Rule_xxxxxx>", "selectedStageId": "<Stage_xxxxxx>" }` |
| `user-selected-stage` | `{ "rule": "user-selected-stage", "id": "<Rule_xxxxxx>" }` |
| `wait-for-connector` | `{ "rule": "wait-for-connector", "id": "<Rule_xxxxxx>", "conditionExpression": "<expr>" }` |

Emit `conditionExpression` **only** when `sdd.md` provides it. JavaScript's `JSON.stringify` drops `undefined` values, so the CLI omits the key whenever no expression was passed — the JSON recipe matches by simply not writing the key.

For `selected-stage-*` rule-types, `selectedStageId` is required. It must match an ID already present in `schema.nodes` (a previously captured Stage / ExceptionStage).

## Recipe — Full example

Stage `Stage_0F0DDI` receives an interrupting `selected-stage-exited` entry condition referencing `Stage_c4Vx6R`:

```json
{
  "id": "Condition_NynOjv",
  "displayName": "After Upstream exits",
  "rules": [
    [
      {
        "rule": "selected-stage-exited",
        "id": "Rule_SLlw0L",
        "selectedStageId": "Stage_c4Vx6R"
      }
    ]
  ],
  "isInterrupting": true
}
```

Pushed onto `nodes[<Stage_0F0DDI>].data.entryConditions`.

## Semantic position

- The condition is appended to `stageNode.data.entryConditions[]` (not prepended). CLI uses `.push()`.
- Multiple conditions on the same stage produce multiple array entries. Order follows the `tasks.md` T-entry order.
- `entryConditions` is created on the regular Stage on first add. ExceptionStage already carries `entryConditions: []` from its creation, so the array is guaranteed to exist.

## Post-write validation

After writing, confirm:

- The target stage's `data.entryConditions[]` contains an object with the generated `Condition_xxxxxx` ID.
- The condition's `rules[0][0].rule` matches the declared rule-type.
- For `selected-stage-*` rule-types, `rules[0][0].selectedStageId` points to an existing Stage / ExceptionStage node.
- For `wait-for-connector`, `rules[0][0].conditionExpression` is a non-empty string.
- `isInterrupting` is present iff `sdd.md` declared it; absent otherwise.

Run `uip maestro case validate <file> --output json` after all stage-entry-conditions for this plugin's batch are added. Validation does not fail on isolated entry conditions — only on orthogonal concerns (orphan stages, missing edges, missing tasks, missing exit conditions on ExceptionStage). Expect the usual "no incoming edges / no tasks" failures at this stage of the build.

## Edit semantics — appending a rule to an existing condition

CLI `stage-entry-conditions edit <file> <stage-id> <condition-id> --rule-type <new-type>` appends a new rule as a **new outer-group** (new OR-clause). Direct-JSON-write matches:

1. Locate the condition by `id` in `data.entryConditions`.
2. `condition.rules.push([<new rule object>])` — wrap in a new single-element array.
3. Update `displayName` / `isInterrupting` in place when those flags are provided.

Removing rules requires `remove` + re-`add` on the CLI path. Direct-JSON-write can splice `rules[]` in place, but the current migration target is `add`-only; `remove` stays on the CLI path until its migration PR.

## Known CLI divergences

None today. The JSON recipe is structurally equivalent to the CLI output (IDs aside). Differences to be aware of:

- `isInterrupting` is conditional — the CLI writes it only when `--is-interrupting` is passed. The JSON recipe must preserve this conditional-omission behavior rather than defaulting to `false` (otherwise the golden diff drifts). When `sdd.md` does not declare `is-interrupting`, the field stays absent; at runtime the case engine treats absence as `false`.
- Field order inside the condition object (`id` → `displayName` → `rules` → `isInterrupting`) is a CLI artifact of key-insertion order. The JSON recipe matches for diff cleanliness; downstream consumers do not depend on it.

## Compatibility

Captured against the `0.3.4` CLI source build at `~/Documents/GitHub/cli` (the `0.1.21` binary on PATH lacks `maestro case`). See [`docs/uipath-case-management/migration-fixtures/stage-entry-conditions/`](../../../../../../docs/uipath-case-management/migration-fixtures/stage-entry-conditions/) for fixtures.

- [x] **Golden diff:** normalized `json-write-output.json` matches `cli-output.json` after Stage / Condition / Rule ID normalization — `docs/uipath-case-management/migration-fixtures/stage-entry-conditions/diff.sh` passes.
- [x] **Rule-type coverage:** all five stage-entry rule-types (`case-entered`, `selected-stage-completed`, `selected-stage-exited`, `user-selected-stage`, `wait-for-connector`) are exercised in the fixture and produce matching JSON shapes.
- [x] **Validation parity:** both outputs produce the same expected failure profile (3 errors + 2 warnings — orphan stages, missing edges/tasks). `uip maestro case validate` raises no complaint about any of the entry conditions themselves.
- [ ] **Downstream CLI mutation append:** `uip maestro case stage-entry-conditions edit --rule-type <...>` applied against the direct-JSON-written condition — not yet exercised.
- [ ] **Round-trip:** CLI-written condition → direct-JSON-write adds a second condition on the same stage → `uip maestro case validate` passes — not yet exercised.
- [ ] **Studio Web render:** `uip solution upload` and visual confirmation — not yet exercised.
