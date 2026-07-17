# connector-trigger task — Implementation (Direct JSON Write)

> **Node `type` value: `wait-for-connector` (schema-kebab).** NEVER write `connector-trigger` (plugin folder name) into the JSON `type` field. The CLI `--type connector-trigger` flag is a separate concept — used only when calling the legacy `uip maestro case tasks describe` command. The current path uses `uip maestro case spec --type trigger`. See SKILL.md Rule 16 + Plugin Index.

> **Phase split.** Phase 2 writes `data.typeId` + `data.connectionId` only. Phase 3 consumes the T-entry's cached populated `caseShape`, substitutes placeholders, and finalizes the task inside its owning-stage Edit. See [`../../../schema-cache-guide.md`](../../../schema-cache-guide.md).

Load the populated trigger task scaffold from `tasks/schema-cache.json`, then compose it into the owning stage as a `wait-for-connector` task. Field discovery, reference resolution, and exact-request gathering happen before stage mutation.

For shared CLI invocation, placeholder substitution, anti-patterns, and the canonical form for filter expressions with variable references, see [connector-trigger-common.md](../../../connector-trigger-common.md). For the per-sink canonical-form table covering all expression-syntax decisions in this skill, see [bindings-and-expressions.md § Canonical form per sink](../../../bindings-and-expressions.md#canonical-form-per-sink). This doc covers only the **task-specific** parts.

## Prerequisites from Planning

The `tasks.md` entry provides:

| Field | Example |
|---|---|
| `type-id` | `"7dc57f24-894c-5ae2-a902-66056fa40609"` |
| `connection-id` | `"fc82e610-c454-4bc7-a1a5-b5aa529d1ba6"` |
| `connector-key` | `"uipath-microsoft-outlook365"` |
| `object-name` | `"Message"` |
| `event-operation` | `"EMAIL_RECEIVED"` |
| `event-mode` | `"polling"` or `"webhooks"` |
| `input-values` | `{"eventParameters":{"parentFolderId":"AAMkADNm..."}}` (already resolved IDs) |
| `filter` (optional) | `{"groupOperator":"And","filters":[...]}` (FilterTree object — present only when planning Step 7 authored a filter) |
| `isRequired` | `true` |
| `runOnlyOnce` | `false` |

## Configuration Workflow

### Step 1 — Build `--input-details` JSON from tasks.md

Construct the input-details object literally from `tasks.md`:

```jsonc
{
    // eventParameters from tasks.md input-values.eventParameters (or omit when absent)
    "eventParameters": "<input-values.eventParameters or omit>",
    // filter — FilterTree object from tasks.md (or omit when not authored)
    "filter": "<filter from tasks.md or omit>"
}
```

Full input-details contract: [`case-spec-input-details.md`](../../../case-spec-input-details.md).

### Step 2 — Load the exact populated response

Read the T-entry's `connector-shape-key` from `tasks/schema-cache.json` and verify the stored request exactly matches the Step 1 input details plus type/activity/connection/object identity. On a cache hit, do not call CLI. On a miss, return to the gather pass, fetch once, persist the complete response, then resume. See [common § Phase 3 Implementation Step 2](../../../connector-trigger-common.md#step-2--load-the-populated-case-spec-response).

### Step 3 — Required-event-param validation (HARD GATE)

This is a hard gate — do NOT proceed to write the task until every required event parameter has a non-empty value in the populated `caseShape.inputs[name="eventParameters"].body`.

1. From the lean planning-phase spec (run with `--skip-case-shape` per [common § Planning Pipeline 5](../../../connector-trigger-common.md#5-validate-required-event-parameters-hard-gate)), collect `inputs.eventParameters[?required]`.
2. After Step 2's call (with the populated caseShape), scan `caseShape.inputs[name="eventParameters"].body` and verify every required event parameter has a value.
3. If any required event parameter is missing, **AskUserQuestion** — list the missing parameters with their `name` and what kind of value is expected.
4. Re-run Step 2 after collecting the missing values, OR fall back to placeholder task per Rule 8 if user declines to provide a value.

> **Do NOT guess or skip missing required event parameters.** Trigger registration fails at runtime when a required event parameter is missing.

### Step 4 — Mint binding IDs and trigger registration key

Per [common § Step 3](../../../connector-trigger-common.md#step-3--mint-binding-ids-and-when-applicable-trigger-registration-key). Note for in-stage triggers: `<eventTriggerKey>` uses `<connection-id>_<startNode.id>` — `startNode.id` is the case-level start node, NOT the stage id (matches FE convention).

### Step 5 — Substitute placeholders in `caseShape.context`

Per [common § Step 4](../../../connector-trigger-common.md#step-4--substitute-placeholders-in-caseshapecontext). Three placeholders: `{{CONN_BINDING_ID}}`, `{{FOLDER_BINDING_ID}}` (when present), `{{TRIGGER_REGISTRATION_KEY}}` (when the trigger has event parameters).

### Step 6 — Mint `var` / `id` / `elementId` on inputs and outputs

Generate task ID (`t` + 8 alphanumeric chars) and elementId (`<stageId>-<taskId>`).

For each entry in `caseShape.inputs[]`:
- `var` = `v` + 8 alphanumeric chars
- `id` = same as `var`
- `elementId` = the task's elementId

For each entry in `caseShape.outputs[]`: same fields, **plus the dedup rule** per [common § Step 5](../../../connector-trigger-common.md#step-5--mint-var--id--elementid-on-inputs-and-outputs) (`response` / `error` collide across multiple connector tasks/triggers).

**Output binding.** Apply [io-binding/impl-json.md § Output Binding Shapes](../../variables/io-binding/impl-json.md#output-binding-shapes). The Step 0 schema for this plugin is `caseShape.outputs[]` from `case spec` (Step 2 above). The dedup rule above applies first; output binding consumes the deduped names.

### Step 7 — Build task for owning-stage composition

```json
{
  "id": "<taskId>",
  "type": "wait-for-connector",
  "displayName": "<display-name from tasks.md>",
  "elementId": "<stageId>-<taskId>",
  "isRequired": "<from tasks.md, default true>",
  "shouldRunOnlyOnce": "<from tasks.md runOnlyOnce, default false>",
  "data": {
    "serviceType": "Intsvc.WaitForEvent",
    "context": "<caseShape.context — placeholders substituted in Step 5>",
    "inputs":  "<caseShape.inputs  — var/id/elementId minted in Step 6>",
    "outputs": "<caseShape.outputs — var/id/elementId minted, dedup applied in Step 6>",
    "bindings": []
  }
}
```

Place the task in the target stage's composed `tasks[]` array. Default: own task set (one task per lane). **Exception:** if this task is a parallel member of a `runs-sequentially` group, push into the shared lane of that group. Do not issue a task-only Edit; the complete stage is written once by the Phase 3 stage pass.

### Step 8 — Accumulate root-level bindings

Per [common § Root-level bindings](../../../connector-trigger-common.md#root-level-bindings). Two entries (ConnectionId, FolderKey), `resourceKey` = `connection-id`. Deduplicate against existing root bindings.

### Step 9 — Defer sidecar sync

Hold the root bindings for Phase 3 root finalization, then populate the IS connection cache from the cached `Kxx` response and regenerate `bindings_v2.json` once per [bindings-v2-sync.md](../../../bindings-v2-sync.md). Skip this consumer if populated schema gathering failed.

## Graceful degradation

**Always create the task** — even on errors. Start with `data: { "serviceType": "Intsvc.WaitForEvent" }` and progressively populate.

| Step failed | What gets populated | Log |
|---|---|---|
| populated schema gather fails | Phase 2 shape preserved — `data.typeId` + `data.connectionId` only, no Phase 3 inputs/outputs/context enrichment. Distinct from a Rule 8 placeholder (`data: {}`) — typeId/connectionId are resolved, only the spec-driven enrichment is skipped. Log per Rule 8 reporting | `[SKIPPED] case spec failed — typeId/connectionId preserved, no enrichment` |
| Required-event-param gate fails (user declines) | Placeholder per Rule 8 OR re-prompt | `[SKIPPED] required event parameter <name> missing — placeholder task per Rule 8` |
| All succeed | Full population per Steps 4-9 including bindings_v2 sync | — |

All issues appended to the shared issue list per [logging/impl-json.md](../../logging/impl-json.md).

## Post-Write Verification

1. `type` is `"wait-for-connector"` and `data.serviceType` is `"Intsvc.WaitForEvent"`
2. `data.context[]` populated from `caseShape.context` with placeholders substituted (`=bindings.<connBindingId>`, etc.)
3. `data.context[name="metadata"].body.activityPropertyConfiguration.configuration` is a `=jsonString:…` string (CLI-produced; do not modify)
4. When the trigger has event parameters: `data.context[name="metadata"].body.bindings[Property].metadata.ParentResourceKey` is `EventTrigger.<eventTriggerKey>` (substituted from `EventTrigger.{{TRIGGER_REGISTRATION_KEY}}`)
5. Root bindings exist for ConnectionId + folderKey with the minted ids; `data.bindings[]` is empty `[]`
6. Each entry in `data.inputs[]` / `data.outputs[]` has `var` / `id` / `elementId` minted; uniqueness rule applied for outputs
7. `bindings_v2.json` `resources` array matches top-level `bindings[]` after the deferred sync
