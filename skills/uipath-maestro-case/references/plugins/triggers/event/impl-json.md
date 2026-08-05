# event trigger — Implementation (Direct JSON Write)

This file owns the case-trigger node, trigger-only IDs, `entry-points.json` entry, derived trigger sidecar, and placeholder. The connector metadata algorithm and raw-cache contract are owned by [connector-trigger-impl.md](../../../connector-trigger-impl.md).

For shared CLI invocation, placeholder substitution, anti-patterns, and the canonical form for filter expressions with variable references, see [connector-trigger-impl.md](../../../connector-trigger-impl.md). For the per-sink canonical-form table covering all expression-syntax decisions in this skill, see [bindings-and-expressions.md § Canonical form per sink](../../../bindings-and-expressions.md#canonical-form-per-sink). This doc covers only the **trigger-node-specific** parts.

> **Layout-strip (Rule 18).** Omit `position`, `style`, `measured`, `width`, `height`, `zIndex` from the trigger node. Keep `data.parentElement`, `data.isInvalidDropTarget`, `data.isPendingParent`, `data.typeVersion`, `data.display`, `data.description`, `data.inputs`.

## Prerequisites from Planning

The T-entry supplies `type-id`, `connection-id`, `connector-key`, optional `object-name`, `event-operation`, `event-mode`, optional `input-values.eventParameters`, and optional `filter`.

## Phase 2 — Write the trigger envelope

For a single-trigger case, use `trigger_1`; for each additional trigger mint `trigger_` + 6 characters. Record `T<N> → triggerId` in `id-map.json`, append its `entry-points.json` entry, and create no edge (Rule 20).

For a resolved T-entry, initialize:

```json
{
  "id": "<triggerId>",
  "type": "uipath.case.trigger",
  "data": {
    "parentElement": { "id": "root", "type": "case-management:root" },
    "description": "<description>",
    "typeVersion": "1.0.0",
    "display": { "label": "<display-name>" },
    "inputs": { "serviceType": "Intsvc.EventTrigger", "outputs": [] }
  }
}
```

Do not call `case spec` in Phase 2. Step 6.2 may add spec-independent argument bridges to `outputs`; Phase 3 must preserve them. A planning-time unresolved T-entry uses the placeholder below instead.

Since v24 all trigger runtime configuration lives under `data.inputs`; the old `data.uipath` bag is not valid for this target. Record `T<N> → triggerId` in `id-map.json`, append its `entry-points.json` entry, and create no edge.

## Phase 3 — Configure the trigger

### Step 1 — Run the common target-local pipeline

Run [shared implementation § Phase 3 Implementation — Single CLI Call](../../../connector-trigger-impl.md#phase-3-implementation--single-cli-call) for this trigger, using `triggerId` as its cache `elementId`. Record the target identity as `{ targetKind: "event-trigger", targetId: T<N>, elementId: triggerId }`, and continue only after the shared required-field gate and cache-read/splice steps succeed.

### Step 4 — Mint binding IDs and trigger registration key

The common owner mints the binding IDs. For this target, `{{TRIGGER_REGISTRATION_KEY}}` uses `<connection-id>_<triggerId>` because the trigger node is its case-entry start node.

### Step 6 — Mint `var` / `id` on trigger CONFIG inputs

Mint `var = id = v<8 characters>` on every normalized configuration input. Trigger inputs have no `elementId`.

Set `data.inputs.context` and `data.inputs.inputs` from the normalized cache, and set `data.inputs.bindings: []`. Preserve the existing `data.inputs.outputs` array; do not replace it with raw `CaseShape.Outputs` or clear Phase 2 argument bridges. The global-variable dispatcher owns all trigger-output projection.

### Step 8 — Write trigger-spec-cache.json sidecar

This sidecar is a derived, unminted view for the global-variable dispatcher; it never replaces the per-trigger full-response cache.

From the same fresh **Read** of `tasks/spec-cache.<triggerId>.json`, derive the three normalized subtrees. Apply permitted context placeholder substitutions, but do not mint/project/dedupe `Inputs` or `Outputs`. Merge by T-number in ascending order:

```json
{
  "T02": {
    "context": "<normalized Context; placeholders substituted>",
    "inputs": "<normalized unminted Inputs>",
    "outputs": "<normalized unminted Outputs with full body schemas>"
  }
}
```

Use Read + Write/Edit only. Regenerate-from-scratch replaces the sidecar with `{}` before rebuilding. Continue-without-regenerate preserves unrelated entries, but a resolved single-trigger rerun replaces its T-number and every placeholder fallback removes its T-number before dispatch. Abort does not delete it.

After all resolved event targets have produced their raw caches and sidecar entries, implementation Step 9.7 invokes the global-variable owner's spec-dependent trigger-output dispatch. That dispatch reads this sidecar, adds projected/deduped outputs and companions, and preserves existing argument bridges.

### Step 9 — Append root-level bindings

Append canonical ConnectionId and optional FolderKey root bindings per [shared implementation § Root-level bindings](../../../connector-trigger-impl.md#root-level-bindings). Keep target-local `bindings` empty. Populate the IS cache and regenerate `bindings_v2.json` in the Step 9.7 batch.

## Placeholder fallback (unresolved connector / connection)

Use this shape when the common owner selects fallback, the Phase 3 spec call fails, or required parameters are declined:

```json
{
  "id": "<trigger_xxxxxx>",
  "type": "uipath.case.trigger",
  "data": {
    "parentElement": { "id": "root", "type": "case-management:root" },
    "description": "<description from sdd.md>",
    "typeVersion": "1.0.0",
    "display": { "label": "<display-name>" },
    "inputs": { "serviceType": "Intsvc.EventTrigger" }
  }
}
```

`data.inputs` carries **only** `serviceType` — no `context[]`, `inputs[]`, `outputs[]`, `bindings[]`, `metadata`. Equivalent intent to a connector-task `data: {}` placeholder; trigger nodes need `label` / `description` / `parentElement` to render at all.

The matching `entry-points.json` entry and `id-map.json` record remain, and no edge is created. Before any successful spec response, no target raw cache exists; after a successful write followed by required-field fallback, retain the last complete cache for audit only.

On every fallback, including continue-without-regenerate and single-trigger reruns, remove `tasks/trigger-spec-cache.json[T<N>]` and all fields from the trigger's `data.inputs` except `serviceType`. Before dispatching the remaining sidecar entries, invoke the global-variable owner to recompose its trigger outputs and root companions from `tasks.md` plus the reduced sidecar, so shared/deduplicated entries required by another trigger survive while this T-number's prior spec emissions disappear. Preserve spec-independent root argument declarations (formal slots plus companions); the placeholder rule intentionally omits their trigger bridge. Reconcile connector bindings and the IS cache through their owner, deleting only entries no remaining resolved target uses, then regenerate `bindings_v2.json`. The retained full-response target cache is audit evidence only and must never repopulate the removed sidecar entry.

Log `[SKIPPED] Event trigger "<display-name>" written as placeholder — <reason>.` Regenerate from scratch after the connector resolves; sibling-file coupling makes partial upgrade unsafe.

## Graceful degradation

| Trigger | Result |
|---|---|
| Planning-time `<UNRESOLVED>` | Skip Phase 3 and keep the placeholder envelope. |
| Phase 3 spec failure | Downgrade the scaffold to the same placeholder. |
| Required parameter declined | Downgrade to the same placeholder; retain any successfully written raw cache. |

Append all issues through the logging owner.

## Post-Write Verification

1. `data.inputs.serviceType` is `"Intsvc.EventTrigger"` (not `WaitForEvent` or `CuratedTrigger`).
2. A fully configured node has complete normalized `context`/`inputs`, preserved/projected `outputs`, and `bindings: []`, all under `data.inputs`; configuration inputs have `var`/`id` but no `elementId`.
3. The trigger's complete raw response exists at `tasks/spec-cache.<triggerId>.json`, and raw paths use PascalCase `Data.CaseShape`.
4. `tasks/trigger-spec-cache.json[T<N>]` is derived from that raw cache and retains unminted complete output bodies for the global-variable owner.
5. Context placeholders use this trigger's binding IDs and `<connection-id>_<triggerId>` registration key; CLI-authored JSON-string values remain untouched.
6. `id-map.json` and `entry-points.json` reference the trigger ID; `schema.edges` remains empty.
7. A placeholder has only `serviceType` under `data.inputs` and no sidecar/binding contributions; it retains a raw cache only when fallback followed a successful spec write.

Run full case validation after the event-trigger batch.

<!-- END: impl-json.md -->
