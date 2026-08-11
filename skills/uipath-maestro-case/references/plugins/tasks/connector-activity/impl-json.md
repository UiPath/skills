# connector-activity task — Implementation (Direct JSON Write)

> **Node `type` value: `execute-connector-activity` (schema-kebab).** NEVER write `connector-activity` (plugin folder name) or `connector_activity` into the JSON `type` field. The CLI `--type connector-activity` flag is a separate concept — used only when calling `uip maestro case tasks describe` (legacy) or `uip maestro case spec --type activity` (current). See SKILL.md Rule 16 + Plugin Index.

> **Phase split.** Runs across both phases. Phase 2 writes and places the task with `data.typeId` + `data.connectionId` only — no `case spec` call in Phase 2. Phase 3 calls `case spec --input-details`, reads the populated `caseShape`, and enriches that existing task; a required-field correction replaces the cache through a fresh call. See [`../../../phased-execution.md`](../../../phased-execution.md).

Fetch the populated connector data via `uip maestro case spec --input-details`, then splice it into the existing Phase 2 task. Field discovery and reference resolution are done during [planning](planning.md) — implementation reads resolved values from `tasks.md` and threads them through the spec call.

## Prerequisites from Planning

The `tasks.md` entry provides:

| Field | Example |
|---|---|
| `type-id` | `"c7ce0a96-2091-3d94-b16f-706ebb1eb351"` |
| `connection-id` | `"bc095c1f-671f-4669-8634-b7164fa46aa0"` |
| `connector-key` | `"uipath-microsoft-outlook365"` |
| `object-name` | `"send-mail-v2"` |
| `input-values` | `{"bodyParameters":{"message.toRecipients":"user@example.com"},"queryParameters":{...}}` (already resolved IDs, dotted body keys) |
| `file-inputs` (optional) | `{"file":"=vars.evidenceDoc"}` (multipart only; exact parameter name to whole file-variable reference) |
| `filter` (optional) | `{"groupOperator":"And","filters":[...]}` (FilterTree object — present only when planning Step 7 authored a filter) |
| `isRequired` | `true` |
| `runOnlyOnce` | `false` |

## Phase 2 — Write and place the task envelope

During implementation Step 9 Phase B, mint the task ID and `elementId`, write the envelope fields from the T-entry, and set resolved `data` to `typeId` + `connectionId` only. Append that envelope exactly once, applying its `activation-mode` + `entry-rule` through the central task-placement contract. An unresolved T-entry uses the Rule 8 placeholder instead.

## Phase 3 — Configure the existing task

### Step 1 — Build `--input-details` JSON from tasks.md

Construct the input-details object from `tasks.md`, rewriting every value containing a reference to its canonical sink form (connector body fields use `=js:(<expr>)`):

```jsonc
{
    // bodyParameters from tasks.md input-values.bodyParameters (dotted keys preserved;
    // each value rewritten to canonical form per Step 1.a)
    "bodyParameters": "<input-values.bodyParameters with values rewritten>",
    // queryParameters from tasks.md input-values.queryParameters (same rewrite rule)
    "queryParameters": "<input-values.queryParameters with values rewritten>",
    // pathParameters from tasks.md input-values.pathParameters (same rewrite rule)
    "pathParameters":  "<input-values.pathParameters with values rewritten>",
    // filter — FilterTree object from tasks.md (or omit when not authored)
    "filter": "<filter from tasks.md or omit>"
}
```

Synthetic HTTP request activities (`object-name === "httpRequest"` / `"http-request"`) reject `bodyParameters` — pass HTTP body via `queryParameters` instead, or omit. The CLI rejects bodyParameters at validation time.

Full input-details contract: [`case-spec-input-details.md`](../../../case-spec-input-details.md).

#### Step 1.a — Rewrite references to canonical sink form

Connector body sinks (`bodyParameters`, `queryParameters`, `pathParameters`) require `=js:(...)` wrap for every reference. Resolve cross-task refs first, then apply the wrap:

| Value in tasks.md | Value passed to CLI |
|---|---|
| `"=vars.X"` | `"=js:(vars.X)"` |
| `"=metadata.X"` | `"=js:(metadata.X)"` |
| `"=bindings.X"` | `"=js:(bindings.X)"` |
| `"=<other-prefix>.X"` (e.g. `=response.X`, `=Error.X`, `=datafabric.X`, `=orchestrator.JobAttachments[0]`) | `"=js:(<other-prefix>.X)"` — strip leading `=`, wrap in `=js:(...)` |
| `"<- "Stage"."Task".out"` | resolve through the common [output-reference-ID algorithm](../../variables/io-binding/impl-json.md#output-reference-id-authoritative) to `"=vars.<outputReferenceId>"` → `"=js:(vars.<outputReferenceId>)"` |
| `"=js:(<expr>)"` (pre-wrapped operator expression) | pass-through unchanged |
| `"<literal value>"` (no leading `=`) | pass-through unchanged |

Full per-sink rule and FE source-of-truth: [bindings-and-expressions.md § Canonical form per sink](../../../bindings-and-expressions.md#canonical-form-per-sink).

#### Step 1.b — Array-of-object body fields: pre-input scan (MANDATORY)

When the resolved body schema contains `[*]`, load [complex inputs § Step 1.b](complex-inputs-guide.md#step-1b--array-of-object-body-fields-pre-input-scan-mandatory) and run its mandatory scan before the spec call. Otherwise skip both the guide and this step.

### Step 2 — Run `case spec` with input-details

```bash
uip maestro case spec --type activity \
  --activity-type-id "<type-id>" \
  --connection-id "<connection-id>" \
  --object-name "<object-name when present; required for Generic>" \
  --input-details "<json from Step 1>" \
  --output json
```

Use the planning-persisted `object-name` unchanged; it is mandatory for `Config.activityType === "Generic"` and may be omitted only when planning recorded none. The Phase 3 call omits `--skip-case-shape` (incompatible with `--input-details` — see [case-spec-input-details.md § Validation rules](../../../case-spec-input-details.md#validation-rules-invalidinputdetailserror-on-violation)). The CLI returns the full `caseShape` populated with values from `--input-details`.

Immediately use **Write** to persist the complete, unmodified response at `tasks/spec-cache.<elementId>.json`. Record `{ cachePath, targetKind: "connector-activity", targetId, elementId }` in the working audit state. Do not hold, summarize, or reconstruct the payload in reasoning. At mutation time, Read this task's cache; another connector target always gets its own spec call and cache.

The relevant raw-cache paths are:

> **`case spec --output json` returns PascalCase keys.** The `.Data.*` read paths below reflect that (`.Data.CaseShape.Context`, not `.Data.caseShape.context`). A camelCase jq path returns `null`. The spliced subtree is re-cased to camelCase on the way to disk — see Step 6.

| Variable | Source |
|---|---|
| `spec.identity` | `.Data.Identity` — connectorKey, connectorName, connectorVersion, objectName, objectDisplayName, full TypeCache entry |
| `spec.connection.folderKey` | `.Data.Connection.FolderKey` — needed for the FolderKey binding |
| `spec.caseShape.inputs[]` | `.Data.CaseShape.Inputs` — pre-filled body / queryParameters / pathParameters / file inputs |
| `spec.caseShape.outputs[]` | `.Data.CaseShape.Outputs` — response (JSON Schema body) / curated / Error |
| `spec.caseShape.context[]` | `.Data.CaseShape.Context` — 8-entry FE-canonical array, with `{{CONN_BINDING_ID}}` / `{{FOLDER_BINDING_ID}}` placeholders |
| `spec.diagnostics.fallbacks[]` | `.Data.Diagnostics.Fallbacks` — surface to `build-issues.md` when non-empty. |

> **Each connector task runs its own `case spec`.** Even when two tasks share the same `connection-id`, `caseShape` is task-shape-specific (different `objectName`, `httpMethod`, `inputs`, `outputs`). Never reuse another task's spec output.

### Step 3 — Required-field validation (HARD GATE)

This is a hard gate — do NOT proceed to write the task until every required field has a non-empty value in the `caseShape.inputs[].body`.

1. From the lean planning-phase spec (run with `--skip-case-shape` in [planning](planning.md) Step 3), collect `inputs.*[?required]`.
2. Read this task's raw cache and scan `Data.CaseShape.Inputs[].Body`; verify every required field has a value.
3. If any required field is missing, **AskUserQuestion** — list the missing fields with their `displayName` and what kind of value is expected. Free-form input is appropriate when the value space is open-ended (channel names, message bodies, IDs); when a finite set of sensible values exists (e.g. an `enum`), present them via AskUserQuestion per the dropdown rule in [SKILL.md](../../../../SKILL.md).
4. Re-run Step 2 after collecting the missing values, OR fall back to placeholder task per Rule 8 if user declines to provide a value. A fallback after a successful Step 2 retains that complete raw cache for audit.

> **Do NOT guess or skip missing required fields.** A missing required field will cause a runtime error. It is always better to ask than to assume.

### Step 4 — FilterBuilder detection (when planning authored a filter)

When `tasks.md` carries `filter:`, load [complex inputs § Step 4](complex-inputs-guide.md#step-4--filterbuilder-detection) and run that branch. Otherwise skip both the guide and this step.

### Step 5 — Mint binding IDs

Mint two prefixed IDs for the connection + folder bindings:

| Binding | ID format |
|---|---|
| Connection binding | `b` + 8 alphanumeric chars (e.g. `bA1B2C3D4`) |
| Folder binding | `b` + 8 alphanumeric chars (different from connection binding) |

These ids are **picked inline by the agent** (per SKILL.md Rule 13) — no subprocess.

Save them as `<connBindingId>` and `<folderBindingId>` for Step 6.

### Step 6 — Read the raw cache, splice the CaseShape, and substitute placeholders

`caseShape.context[]` carries placeholders at the spec output:

```jsonc
[
    { "name": "connection", "type": "string", "value": "=bindings.{{CONN_BINDING_ID}}" },
    { "name": "folderKey",  "type": "string", "value": "=bindings.{{FOLDER_BINDING_ID}}" },  // present only when spec.connection.folderKey !== null
    // …other entries (connectorKey, resourceKey, objectName, method, path, metadata) — values are fully resolved already
]
```

Replace the two placeholders with the minted ids:

- `{{CONN_BINDING_ID}}` → `<connBindingId>` (Step 5)
- `{{FOLDER_BINDING_ID}}` → `<folderBindingId>` (Step 5; entry only present when folderKey was non-null)

At write time, **Read** `tasks/spec-cache.<elementId>.json` and splice the complete `Data.CaseShape.Context`, `Data.CaseShape.Inputs`, and `Data.CaseShape.Outputs` subtrees required by the task. The rest of the response is discovery metadata and is not written to `caseplan.json`.

All three subtrees, including every nested current or future key, are CLI-authoritative. The only permitted changes are the placeholder substitutions above, recursively normalizing object-key casing, minting `var` / `id` / `elementId`, output projection/deduplication, the conditional guide's multipart file-value binding, and placement in the task envelope. Never reconstruct a subtree from reasoning or enumerate an allowlist of keys.

> **Normalize key casing (PascalCase → camelCase).** After splicing `context` / `inputs` / `outputs` and their nested bodies, recursively lower-case only the first character of every object **key** (`DisplayName`→`displayName`, `UiPathActivityTypeId`→`uiPathActivityTypeId`). Arrays keep order. Never change values or parse/rewrite `=jsonString:` / `=js:` values.

### Step 7 — Mint `var` / `id` / `elementId` on inputs and outputs

Reuse the Phase 2 task ID (`t` + 8 alphanumeric chars) and `elementId = <stageId>-<taskId>`; it is the same identity used in this task's raw-cache filename.

For each entry in `caseShape.inputs[]`:
- `var` = `v` + 8 alphanumeric chars (unique across the case — see uniqueness rule in [global-vars/impl-json.md](../../variables/global-vars/impl-json.md))
- `id` = same as `var`
- `elementId` = the task's elementId

For each entry in `caseShape.outputs[]`:
- Same fields, plus the **dedup rule**: `caseShape.outputs[]` returns generic names like `response` and `error` for every connector task. When multiple connector tasks exist in the same case, these collide. Apply the [uniqueness rule](../../variables/global-vars/impl-json.md#uniqueness-rule): collect all existing output `var` values across every task already in `caseplan.json`; if a `var` already exists, append a counter suffix starting at 2 (e.g., `response` → `response2`, `error` → `error2`). Update `var`, `id`, `value`, and `target` (as `=<new var>`) with the suffixed name. `name`, `displayName`, and `source` stay unchanged.

**Output binding.** Apply [io-binding/impl-json.md § Output Binding Shapes](../../variables/io-binding/impl-json.md#output-binding-shapes). The Step 0 schema for this plugin is `caseShape.outputs[]` from `case spec` (Step 2 above). The dedup rule above applies first; output binding consumes the deduped names.

#### Step 7.a — Multipart file inputs

When the normalized raw-cache inputs contain `target: "file"` (or planning recorded multipart), load [complex inputs § Step 7.a](complex-inputs-guide.md#step-7a--multipart-file-binding) and run that branch. Otherwise skip both the guide and this step.

### Step 8 — Targeted Edit of existing `data`

Preserve the Phase 2 task identity, envelope, entry conditions, and placement. Edit only its `data` property to the following cache-derived result:

```json
{
  "typeId": "<type-id>",
  "connectionId": "<connection-id>",
  "serviceType": "Intsvc.ActivityExecution",
  "context": "<caseShape.context — placeholders substituted in Step 6>",
  "inputs":  "<caseShape.inputs  — var/id/elementId minted in Step 7>",
  "outputs": "<caseShape.outputs — var/id/elementId minted, dedup applied in Step 7>",
  "bindings": []
}
```

### Step 9 — Append root-level bindings

Read [bindings/impl-json.md § Full binding shape — connector tasks](../../variables/bindings/impl-json.md) for the canonical 7-field shape on each entry (all required — omitting any causes Studio Web render failure). Per-task value sources:

- `<connection-id>` (drives `resourceKey` on both bindings + ConnectionBinding `default`): from this task's `tasks.md` entry
- `<connectorKey>` (drives ConnectionBinding templated `name`): from `tasks.md`
- `<folderKey>` (FolderKey binding `default`): from `Data.Connection.FolderKey` in this task's raw cache. **Omit the FolderKey binding entirely when this value is null** (matches `binding-builder.ts:73-83`).
- Binding IDs `<connBindingId>` / `<folderBindingId>` come from Step 5.

Dedup per [§ Deduplication](../../variables/bindings/impl-json.md). Source-of-truth code: `binding-builder.ts` in `uipcli-case-validate/packages/case-tool/src/utils/`.

### Step 10 — Sync IS connection cache

After writing root bindings, populate IS connection cache per [bindings-v2-sync.md § Populate IS connection cache](../../../bindings-v2-sync.md). Skip if `case spec` failed.

> **`bindings_v2.json` regeneration is deferred** — runs once at end of Step 9.7 in [implementation.md](../../../implementation.md) (after all connector tasks), not per-task. See [bindings-v2-sync.md § When to Run](../../../bindings-v2-sync.md).

## Graceful degradation

The Phase 2 task already exists. On failure, preserve or replace that envelope only as specified below; never append a second task.

| Step failed | What gets populated | Log |
|---|---|---|
| `case spec` fails | Phase 2 shape preserved — `data.typeId` + `data.connectionId` only, no Phase 3 inputs/outputs/context enrichment. Distinct from a Rule 8 placeholder (`data: {}`) — typeId/connectionId are resolved, only the spec-driven enrichment is skipped. Log per Rule 8 reporting | `[SKIPPED] case spec failed — typeId/connectionId preserved, no enrichment` |
| Required-field gate fails (user declines) | Placeholder per Rule 8 OR re-prompt; retain any successfully written raw cache | `[SKIPPED] required field <name> missing — placeholder task per Rule 8` |
| All succeed | Full population per Steps 5-10 including bindings_v2 sync | — |

All issues appended to the shared issue list per [logging/impl-json.md](../../logging/impl-json.md).

## Post-Write Verification

Checks 2–11 apply only to a fully configured task. A Rule 8 fallback follows the placeholder contract even when it retains an audit cache; a failed spec leaves only the resolved Phase 2 fields.

1. After any successful spec call, `tasks/spec-cache.<elementId>.json` contains the last complete, unmodified response and its raw CaseShape paths use PascalCase; a required-field fallback retains it.
2. `type` is `"execute-connector-activity"`; real `data.typeId`, `data.connectionId`, and `data.serviceType: "Intsvc.ActivityExecution"` are present.
3. `data.context[]` is the complete cache-derived array. Currently emitted entries include `connectorKey`, `connection`, `resourceKey`, optional `folderKey`, `objectName`, `method`, `path`, and `metadata`; any additional CLI-authored entry is preserved.
4. `data.context[name="connection"].value` is `=bindings.<connBindingId>` (substituted from `{{CONN_BINDING_ID}}`)
5. `data.context[name="folderKey"].value` is `=bindings.<folderBindingId>` (substituted from `{{FOLDER_BINDING_ID}}`); entry absent when `spec.connection.folderKey` was null
6. `data.context[name="metadata"].body.activityPropertyConfiguration.configuration` is a `=jsonString:…` string (CLI-produced; do not modify)
7. Root bindings exist for ConnectionId + folderKey with the minted ids
8. `data.bindings[]` is empty `[]`
9. Each entry in `data.inputs[]` and `data.outputs[]` has `var` / `id` / `elementId` minted (uniqueness rule applied for outputs)
10. `bindings_v2.json` `resources` array matches top-level `bindings[]` after the deferred sync
11. Every activated array/filter/multipart branch passes [complex inputs § Branch verification](complex-inputs-guide.md#branch-verification).

## What NOT to Do

- **Do NOT synthesize `operation` or `_label` in `data.context[]`.** If either is present in the raw `Data.CaseShape.Context`, preserve it like every other CLI-authored entry.
- **Do NOT synthesize `designTimeMetadata` in the metadata body.** Preserve it if the raw cache emits it.
- **Do NOT invent or relocate top-level `errorState`.** Preserve its raw-cache placement; currently the CLI emits it inside `activityPropertyConfiguration.errorState`.
- **Do NOT copy root bindings into `data.bindings[]`.** Leave it as `[]`. The FE crashes if activity tasks have task-level binding copies.
- **Do NOT reconstruct any `CaseShape` subtree from agent memory.** Persist the full response at gather time; at mutation time, Read it and splice the complete `Data.CaseShape.Context`, `Inputs`, and `Outputs` subtrees. See Step 6.
- **Do NOT write the spec's PascalCase keys to disk verbatim.** Normalize keys only as defined in Step 6; never recase values.
- **Do NOT pass `bodyParameters` for synthetic HTTP request activities.** Use `queryParameters` instead, or omit.
- **Do NOT auto-inject `entryConditions`.** Step 10 in [implementation.md](../../../implementation.md) handles them — injecting here creates duplicates.
- **Never reuse a reference ID from a prior connection or session.** Resolve it fresh against this task's current `connection-id`.
- **Do NOT use legacy `uip maestro case tasks describe` or `uip is resources describe` as the operation-contract source.** `case spec --input-details` owns that shape; Generic object selection is the sole `resources list` / `resources describe` discovery exception.

## Known Limitations

- The CLI-produced `essentialConfiguration` uses `essentialConfiguration` only (not `optionalConfiguration`). Tasks work at runtime (debug/publish) but the FE editor may not render certain fields until the user re-configures the task in the UI. DAP repopulates these on form open.

<!-- END: impl-json.md -->
