# event trigger — Implementation (Direct JSON Write)

Configure the case-level event trigger by writing directly into `caseplan.json`. Discovery and resolution follow [connector-trigger-guide.md](../../../connector-trigger-guide.md). The detail pass calls `case spec --type trigger --input-details` once and consumes the populated `caseShape`.

For shared CLI invocation, placeholder substitution, anti-patterns, and the canonical form for filter expressions with variable references, see [connector-trigger-impl.md](../../../connector-trigger-impl.md). For the per-sink canonical-form table covering all expression-syntax decisions in this skill, see [bindings-and-expressions.md § Canonical form per sink](../../../bindings-and-expressions.md#canonical-form-per-sink). This doc covers only the **trigger-node-specific** parts.

> **Layout-strip (Rule 18).** Omit `position`, `style`, `measured`, `width`, `height`, `zIndex` from the trigger node. Keep `data.parentElement`, `data.isInvalidDropTarget`, `data.isPendingParent`, `data.typeVersion`, `data.display`, `data.description`, `data.inputs`.

## Prerequisites from Planning

The resolution-evidence entry provides: activity type ID, connection ID, connector key, object name, event operation/mode, input values, and filter.

## Step 1 — Build `--input-details` JSON from resolution evidence

Construct the input-details object literally from the matching evidence entry:

```jsonc
{
    "eventParameters": "<input-values.eventParameters or omit>",
    "filter": "<filter from resolution evidence or omit>"
}
```

Full input-details contract: [`case-spec-input-details.md`](../../../case-spec-input-details.md).

## Step 2 — Run `case spec` with input-details

Single CLI call replaces the legacy `get-connection` + `case tasks describe --type connector-trigger` two-call pattern. See [common § Phase 3 Implementation Step 2](../../../connector-trigger-impl.md#step-2--run-case-spec-with-input-details) for the command and response handling.

## Step 3 — Required-event-param validation (HARD GATE)

This is a hard gate — do NOT proceed to write the trigger node until every required event parameter has a non-empty value in the populated `caseShape.inputs[name="eventParameters"].body`.

1. From the lean resolution spec (`--skip-case-shape`; [required-parameter gate](../../../connector-trigger-guide.md#5-validate-required-event-parameters-hard-gate)), collect `inputs.eventParameters[?required]`.
2. After Step 2's call (with the populated caseShape), scan `caseShape.inputs[name="eventParameters"].body` and verify every required event parameter has a value.
3. If any required event parameter is missing, **AskUserQuestion** — list the missing parameters with their `name` and what kind of value is expected.
4. Re-run Step 2 after collecting the missing values, OR fall back to placeholder per the Placeholder fallback section below if user declines.

> **Do NOT guess or skip missing required event parameters.** Trigger registration fails at runtime when a required event parameter is missing.

## Step 4 — Mint binding IDs and trigger registration key

Per [common § Step 3](../../../connector-trigger-impl.md#step-3--mint-binding-ids-and-when-applicable-trigger-registration-key). For event triggers, `<eventTriggerKey>` uses `<connection-id>_<startNode.id>` where `startNode.id` is the trigger node's own id (since the event trigger IS the start node for its case-entry path) — matches FE convention at `PackagingUtil.ts:227`.

## Step 5 — Substitute placeholders in `caseShape.context`

Per [common § Step 4](../../../connector-trigger-impl.md#step-4--substitute-placeholders-in-caseshapecontext).

## Step 6 — Mint `var` / `id` on trigger CONFIG inputs

For each entry in `caseShape.inputs[]` (these are trigger configuration: `eventParameters`, `filter`, etc.):
- `var` = `v` + 8 alphanumeric chars
- `id` = same as `var`
- **No `elementId`** on trigger inputs (different from in-stage task inputs).

> **`caseShape.outputs[]` are NOT minted here.** All writes to `triggerNode.data.inputs.outputs[]` are owned by the variables recipe. Capture the un-minted outputs in `case-build/trigger-spec-cache.json` for that recipe.

## Step 7 — Build trigger node and write to caseplan.json

### 7a. Identify or create the trigger node

For a **single-trigger case**, configure the existing `trigger_1` node. For **multi-trigger cases**, create a new node:
- ID: `trigger_` + 6 alphanumeric chars
- No node-level layout fields (Rule 18 — `position`, `style`, `measured`, etc. omitted)

Set the trigger's exact SDD name. Record `trigger:<name> → trigger_xxxxxx` in `id-map.json`; blank `sourceTriggers` resolves to the normalized contract's primary trigger.

### 7b. `data` structure

```json
{
  "typeVersion": "1.0.0",
  "display": { "label": "<display-name>" },
  "inputs": {
    "serviceType": "Intsvc.EventTrigger",
    "context": "<caseShape.context — placeholders substituted in Step 5>",
    "inputs":  "<caseShape.inputs  — var/id minted in Step 6; NO elementId>",
    "outputs": [],
    "bindings": []
  }
}
```

> Since v24 all trigger runtime config lives under `data.inputs` (the old `data.uipath` bag flattened in). The event trigger's CONFIG-input array is therefore `data.inputs.inputs`, its outputs `data.inputs.outputs`, its context `data.inputs.context`.
> `data.inputs.outputs` is initialized empty (`[]`). The variables plugin populates it in Phase 3 Step 6.2 using the sidecar from Step 8 below.

## Step 8 — Write trigger-spec-cache.json sidecar

Write the un-minted `caseShape` into `case-build/trigger-spec-cache.json`, keyed by exact SDD trigger name.

```jsonc
// case-build/trigger-spec-cache.json
{
  "Invoice received": {
    "context": "<caseShape.context — post-substitution from Step 5>",
    "inputs":  "<caseShape.inputs — un-minted, with body schema intact>",
    "outputs": "<caseShape.outputs — un-minted, with body schema intact>"
  },
  "Manual review": { ... }
}
```

**Important — un-minted shape:**

- Do NOT mint `var` / `id` / `elementId` on the `outputs[]` entries written to the sidecar — the variables plugin mints them at Step 6.2 according to whether the SDD references each output. The plain field name from the schema is preserved (e.g., `name: "subject"`).
- Do NOT strip `body` from the outputs — the variables plugin needs the full JSON Schema when emitting the root companion (especially for `jsonSchema`-typed outputs).

**Sidecar lifecycle:**

- **Persistence.** The sidecar persists across hard stops (Phase 2 publish-for-review, etc.) so Phase 3 re-entry doesn't lose spec data. Do NOT regenerate on re-entry — read the existing file.
- **Regeneration.** Rule 6 (`Continue with regenerate from scratch`) replaces the sidecar entirely (Write, not append), starting from an empty `{}`. Rule 7 (`Continue without regenerate`) preserves the existing sidecar.
- **Multi-trigger append.** Each invocation merges by exact SDD trigger name. Preserve SDD order. Re-running one trigger replaces only its own key, making the sidecar idempotent.
- **Abort cleanup.** On `Abort` (per [`phased-execution.md`](../../../phased-execution.md) abort semantics), the sidecar persists alongside other artifacts — `phased-execution.md` mandates no artifact deletion on abort; user owns partial state. On the next run with regenerate-from-scratch (Rule 6) the sidecar is overwritten; otherwise it is reused.
- **Edit discipline.** Per Rule 13, edit via Read + Write/Edit only. Do NOT use jq, sed, or any other tool that bypasses the file-state tracker.

The variables plugin consumes this in Phase 3 Step 6.2 — see [`../../variables/global-vars/impl-json.md` § Inputs the plugin reads](../../variables/global-vars/impl-json.md) and § Dispatcher Loop.

## Step 9 — Append root-level bindings

Per [common § Root-level bindings](../../../connector-trigger-impl.md#root-level-bindings). Two entries (ConnectionId, FolderKey), `resourceKey` = `connection-id`. Deduplicate against existing root bindings.

## Step 10 — Sync IS connection cache

After writing root bindings, populate IS connection cache per [bindings-v2-sync.md § Populate IS connection cache](../../../bindings-v2-sync.md). Skip if `case spec` failed.

## Placeholder fallback (unresolved connector / connection)

When resolution evidence is unresolved for activity type, connection, or connector key, skip spec generation and write the accepted placeholder node instead.

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

**Sibling artifacts:** append the matching `entry-points.json` entry per [manual/impl-json.md § Recipe — entry-points.json](../manual/impl-json.md#recipe--entry-pointsjson-append-to-entrypoints). No trigger-edge is created (Rule 20) — the first stage's `case-entered` entry condition starts the case. No root bindings, no `inputOutputs[]` entries from this trigger.

**Log:** `[SKIPPED] Event trigger "<display-name>" written as placeholder — connector "<connector-key>" / connection unresolved.`

**Upgrade:** regenerate from scratch (Rule 5) — no in-place mutation path. Trigger config is sibling-file-coupled (`entry-points.json`, root variable bindings); a partial in-place edit leaves siblings stale.

## Graceful degradation — unified placeholder conditions

Three distinct conditions can trigger placeholder fallback for an event trigger. All three downgrade to the same placeholder shape (per § Placeholder fallback above); only the surfacing message and the AskUserQuestion offered differ.

| Trigger | What's happening | Placeholder action | Log |
|---|---|---|---|
| **Resolution entry unresolved** | Registry lookup found no connector/connection and fallback was accepted | Write the placeholder node directly | `[SKIPPED] Event trigger "<display-name>" written as placeholder — connector "<connector-key>" / connection unresolved.` |
| **Detail spec failure after resolution** | Connection was deleted or the spec call failed | Record the exact error; downgrade only if the user's fallback choice permits it | `[SKIPPED] case spec failed — event trigger downgraded to placeholder` |
| **Required-event-param gate failure at Phase 3** (spec call succeeded, but `caseShape.inputs[name="eventParameters"].body` is missing required fields after AskUserQuestion either declined or didn't fully resolve) | Required event parameter never collected | If user picked decline or re-prompt failed, fall through to placeholder | `[SKIPPED] required event parameter <name> missing — event trigger downgraded to placeholder` |

**Why full placeholder (not `typeId`/`connectionId` preservation)?** Event triggers are sibling-file-coupled (`entry-points.json` entry, root variable bindings for In args). A partial in-place edit leaves siblings stale. Phase-3 `case spec` failure on event triggers therefore downgrades fully to placeholder — asymmetric with connector-task graceful-degradation, which preserves `data.typeId + data.connectionId` because the in-stage parent node can render without sibling-file coupling (see [`../../tasks/connector-activity/impl-json.md`](../../tasks/connector-activity/impl-json.md) for the connector-task fallback table — it preserves more state because the coupling profile is different).

All issues appended per [logging/impl-json.md](../../logging/impl-json.md).

## Post-Write Verification

1. `data.inputs.serviceType` is `"Intsvc.EventTrigger"` (not `WaitForEvent` or `CuratedTrigger`).
2. **Fully configured** (all under `data.inputs`): `context[]`, `inputs[]` (CONFIG inputs only — no `elementId`), `outputs[]` (empty array — populated later by variables plugin Step 6.2), and `bindings[] = []` all present per §7b. `data.typeVersion` is `"1.0.0"`; `data.display.label` set.
3. **`case-build/trigger-spec-cache.json` exists** with this trigger's exact SDD name as a top-level key, containing un-minted `context`, `inputs`, and `outputs`.
4. **`id-map.json`** contains `"trigger:<exact SDD name>": { "kind": "trigger", "id": "<triggerId>" }` for this trigger.
5. **Placeholder:** all four `data.inputs` fields beyond `serviceType` **absent** (not empty arrays); no root bindings entries from this trigger; no `trigger-spec-cache.json` entry from this trigger; `[SKIPPED]` log entry present.
6. `data.inputs.context[name="metadata"].body.activityPropertyConfiguration.configuration` is a `=jsonString:…` string (CLI-produced; do not modify).
7. When the trigger has event parameters: `data.inputs.context[name="metadata"].body.bindings[Property].metadata.ParentResourceKey` is `EventTrigger.<eventTriggerKey>` (substituted from `EventTrigger.{{TRIGGER_REGISTRATION_KEY}}`).
8. `schema.edges` stays `[]` (Rule 20) — no edge from this trigger.
9. `entry-points.json` has a matching entry referencing the trigger node ID.
10. At Phase 3 exit, [implementation.md § Step 12 Check 12](../../../implementation.md#step-12--end-of-phase-3-validator-pass) re-asserts 2–7 for a resolved trigger.

Run `uip maestro case validate <file> --output json` after all triggers for this plugin's batch are added.

<!-- END: impl-json.md -->
