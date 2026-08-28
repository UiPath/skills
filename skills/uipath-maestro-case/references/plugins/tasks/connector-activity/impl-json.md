# connector-activity task — Implementation (Direct JSON Write)

> **Node `type` value: `execute-connector-activity` (schema-kebab).** NEVER write `connector-activity` (plugin folder name) or `connector_activity` into the JSON `type` field. The CLI `--type connector-activity` flag is a separate concept — used only when calling `uip maestro case tasks describe` (legacy) or `uip maestro case spec --type activity` (current). See SKILL.md Rule 16 + Plugin Index.

> **Phase split.** Runs across both phases. Phase 2 writes `data.typeId` + `data.connectionId` only — no `case spec` call in Phase 2. Phase 3 calls `case spec --input-details` once, reads the populated `caseShape`, and mints the task. See [`../../../phased-execution.md`](../../../phased-execution.md).

Fetch the populated connector task scaffold via `uip maestro case spec --input-details`, then drop it into `caseplan.json`. Field discovery and reference resolution are done during [planning](planning.md) — implementation reads resolved values from `tasks.md` and threads them through the spec call.

## Prerequisites from Planning

The `tasks.md` entry provides:

| Field | Example |
|---|---|
| `type-id` | `"c7ce0a96-2091-3d94-b16f-706ebb1eb351"` |
| `connection-id` | `"bc095c1f-671f-4669-8634-b7164fa46aa0"` |
| `connector-key` | `"uipath-microsoft-outlook365"` |
| `object-name` | `"send-mail-v2"` |
| `input-values` | `{"bodyParameters":{"message.toRecipients":"user@example.com"},"queryParameters":{...}}` (already resolved IDs, dotted body keys) |
| `filter` (optional) | `{"groupOperator":"And","filters":[...]}` (FilterTree object — present only when planning Step 7 authored a filter) |
| `isRequired` | `true` |
| `runOnlyOnce` | `false` |

## Configuration Workflow

### Step 1 — Build `--input-details` JSON from tasks.md

**Filter preflight:** run Step 4 for any top-level `filter:` before Step 2.

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

Before passing `bodyParameters` to the CLI, scan for keys containing literal `[*]`. Halt if any are present — the binding is malformed.

The `[*]` in `inputs.bodyFields[].name` is **schema notation** (JSONPath-style "array of") for documentation only — NOT a valid input key. Array-of-object body fields MUST be expressed in tasks.md `input-values.bodyParameters` as real JSON arrays under the parent name (see [`planning.md` § Array-of-object body fields](planning.md)). The planner is responsible for emitting the correct shape; this step is a safety net.

**Halt condition.** If any `bodyParameters` key contains literal `[*]`, halt with explicit error:
```
ERROR: bodyParameters key '<key>' contains literal '[*]'.
        Spec field was: <spec field name>. Expected: '<parent>' with a real JSON array value.
        Fix in tasks.md input-values.bodyParameters; do NOT pass [*] keys to the CLI.
```

The CLI accepts the literal `field[*]` key (well-formed JSON) and validate passes, but runtime APIs reject with HTTP 400 `UnableToDeserializePostBody`. The check repeats as a post-write verification — see [Step 8 Post-Write Verification](#post-write-verification) item #12.

### Step 2 — Run `case spec` with input-details

```bash
uip maestro case spec --type activity \
  --activity-type-id "<type-id>" \
  --connection-id "<connection-id>" \
  --input-details "<json from Step 1>" \
  --output json > tasks/spec-cache.<elementId>.json
```

**Precondition.** `.Data.CaseShape.context` must resolve. If it is `null`, the CLI is too old to emit `caseShape` in its final shape — upgrade; never adapt the splice to an older response.

**The redirect is the only way this file is created.** It holds the CLI's raw response envelope (`Result` / `Code` / `Data`) byte-for-byte. Do NOT author it, and do NOT invent a wrapper of your own around `caseShape` — a hand-built cache is not a cache, and every downstream check compares against it.

**Do not hand-write this file.** The response reaches tens of KB (68 KB for Slack `send_message_to_channel_v2`). A copy written from reasoning drops subtrees silently — observed: an 8.4 KB cache holding 4 of 102 `ResponseFields`, leaving the built node with 4 of 13 response properties while `validate` stayed green. This `>` is the one redirect [SKILL.md](../../../../SKILL.md) Rule 13 permits.

The Phase 3 call omits `--skip-case-shape` (incompatible with `--input-details` — see [case-spec-input-details.md § Validation rules](../../../case-spec-input-details.md#validation-rules-invalidinputdetailserror-on-violation)). The CLI returns the full `caseShape` populated with values from `--input-details`.

Save the response. The interesting parts:


| Variable | Source |
|---|---|
| `spec.identity` | `.Data.Identity` — connectorKey, connectorName, connectorVersion, objectName, objectDisplayName, full TypeCache entry |
| `spec.connection.folderKey` | `.Data.Connection.FolderKey` — needed for the FolderKey binding |
| `spec.caseShape.inputs[]` | `.Data.CaseShape.inputs` — pre-filled body / queryParameters / pathParameters / file inputs |
| `spec.caseShape.outputs[]` | `.Data.CaseShape.outputs` — response (JSON Schema body) / curated / Error |
| `spec.caseShape.context[]` | `.Data.CaseShape.context` — 8-entry FE-canonical array, with `{{CONN_BINDING_ID}}` / `{{FOLDER_BINDING_ID}}` placeholders |
| `spec.diagnostics.fallbacks[]` | `.Data.Diagnostics.Fallbacks` — surface to `build-issues.md` when non-empty. |

> **Each connector task runs its own `case spec`.** Even when two tasks share the same `connection-id`, `caseShape` is task-shape-specific (different `objectName`, `httpMethod`, `inputs`, `outputs`). Never reuse another task's spec output.

### Step 3 — Required-field validation (HARD GATE)

This is a hard gate — do NOT proceed to write the task until every required field has a non-empty value in the `caseShape.inputs[].body`.

1. From the lean planning-phase spec (run with `--skip-case-shape` in [planning](planning.md) Step 3), collect `inputs.*[?required]`.
2. After Step 2's call (with the populated caseShape), scan `caseShape.inputs[].body` and verify every required field has a value.
3. If any required field is missing, **AskUserQuestion** — list the missing fields with their `displayName` and what kind of value is expected. Free-form input is appropriate when the value space is open-ended (channel names, message bodies, IDs); when a finite set of sensible values exists (e.g. an `enum`), present them via AskUserQuestion per the dropdown rule in [SKILL.md](../../../../SKILL.md).
4. Re-run Step 2 after collecting the missing values, OR fall back to placeholder task per Rule 8 if user declines to provide a value.

> **Do NOT guess or skip missing required fields.** A missing required field will cause a runtime error. It is always better to ask than to assume.

### Step 4 — FilterBuilder detection (when planning authored a filter)

When `tasks.md` carries a `filter:` object, the activity's operation must declare a `FilterBuilder` design parameter. The CLI rejects the filter at configure time when no FilterBuilder param exists; the planning step 7 should already have caught this by checking `spec.filter` presence, but verify here as a safety net.

- `spec.filter` present (with `builder: "ceql"` and `fields[]`) → CEQL filter is supported. Pass the structured tree under `--input-details.filter`. The CLI compiles it into both halves of the contract: the runtime CEQL string at `caseShape.inputs[name="queryParameters"].body.<filterParamName>` AND the design-time tree under `essentialConfiguration.savedFilterTrees.<filterParamName>` (inside the `=jsonString:` blob in `caseShape.context[name="metadata"].body.activityPropertyConfiguration.configuration`).
- **Do NOT pass raw CEQL under `queryParameters` for a FilterBuilder operation.** Plain filter fields are normal native-syntax inputs, not authored FilterTrees.
- Tree shape, operator table, examples → [/uipath:uipath-platform — Filter Trees (CEQL)](../../../../../uipath-platform/references/integration-service/activities.md#filter-trees-ceql).

If `spec.filter` is undefined, a top-level `filter:` is malformed. Repair it before Step 2:

1. Find the matching plain query/body field and retain its sink.
2. Copy the exact native value from the SDD Inputs row (or same-session confirmed model); never derive it from the FilterTree.
3. In the same T-entry, remove `filter:`, add the value to the declared `input-values` sink, preserve siblings, then restart Step 1.

If the field or exact value is unavailable or ambiguous, halt and ask; non-interactive runs report a blocker. Never drop the requirement or invent downstream filtering.

### Step 5 — Mint binding IDs

Mint two prefixed IDs for the connection + folder bindings:

| Binding | ID format |
|---|---|
| Connection binding | `b` + 8 alphanumeric chars (e.g. `bA1B2C3D4`) |
| Folder binding | `b` + 8 alphanumeric chars (different from connection binding) |

These ids are **picked inline by the agent** (per SKILL.md Rule 13) — no subprocess.

Save them as `<connBindingId>` and `<folderBindingId>` for Step 6.

### Step 6 — Substitute binding placeholders in `caseShape.context`

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

The **entire** `caseShape.context[]` array is CLI-authoritative. The ONLY permitted modifications are the placeholder substitutions in the table above — see [common § Write `context` / `inputs` / `outputs` from the spec-cache](../../../connector-trigger-impl.md#write-context--inputs--outputs-from-the-spec-cache).

> **Splice, never compose.** Persist the full `case spec` response at Step 2, then copy from that file at Step 8 — never from reasoning. Contract and rationale: [common § Write `context` / `inputs` / `outputs` from the spec-cache](../../../connector-trigger-impl.md#write-context--inputs--outputs-from-the-spec-cache).

### Step 7 — Mint `var` / `id` / `elementId` on inputs and outputs

Generate task ID (`t` + 8 alphanumeric chars) and elementId (`<stageId>-<taskId>`).

For each entry in `caseShape.inputs[]`:
- `var` = `v` + 8 alphanumeric chars (unique across the case — see uniqueness rule in [global-vars/impl-json.md](../../variables/global-vars/impl-json.md))
- `id` = same as `var`
- `elementId` = the task's elementId

For each entry in `caseShape.outputs[]`:
- Same fields, plus the **dedup rule**: `caseShape.outputs[]` returns generic names like `response` and `error` for every connector task. When multiple connector tasks exist in the same case, these collide. Apply the [uniqueness rule](../../variables/global-vars/impl-json.md#uniqueness-rule): collect all existing output `var` values across every task already in `caseplan.json`; if a `var` already exists, append a counter suffix starting at 2 (e.g., `response` → `response2`, `error` → `error2`). Update `var`, `id`, `value`, and `target` (as `=<new var>`) with the suffixed name. `name`, `displayName`, and `source` stay unchanged.

**Output binding.** Apply [io-binding/impl-json.md § Output Binding Shapes](../../variables/io-binding/impl-json.md#output-binding-shapes). The Step 0 schema for this plugin is `caseShape.outputs[]` from `case spec` (Step 2 above). The dedup rule above applies first; output binding consumes the deduped names.

#### Step 7.a — Multipart file inputs

When `caseShape.inputs[]` contains an entry with `target: "file"` (multipart sink — emitted by `case spec` for activities whose IS spec has `multipart.parameters[].isFile === true`, e.g., Outlook Send Email):

- `target` is a **literal string** `"file"` (the IS request-shape multipart sink name), NOT an expression. Preserve verbatim — do not prepend `=`.
- `value` MUST be `"=vars.<fileVarId>"` (whole-record reference). The FE picker is `selectionOnly` for file inputs (`IntsvcActivityPropertiesUtils.tsx:272-279`) — only a file-typed case Variable can be wired; freeform expressions are rejected at picker time. Sub-field references (`=vars.<id>.FullName`) are NOT valid for file inputs — the runtime adapter expects the full JobAttachment record to dereference.
- No `source`, no `body`, no `displayName` on the multipart file input entry — `case spec` returns just `{name, type, target}`; mint `var` / `id` / `elementId` / `value` per Step 7 and stop.
- The runtime adapter dereferences `=vars.<fileVarId>` to the JobAttachment record at execution time and streams bytes from the JobAttachment store into the multipart `file` part of the outbound HTTP request.

### Step 8 — Build `data` and write to caseplan.json (verbatim splice)

Copy the three `caseShape` subtrees per [common § Write `context` / `inputs` / `outputs` from the spec-cache](../../../connector-trigger-impl.md#write-context--inputs--outputs-from-the-spec-cache). Step 7's minted fields (`var`/`id`/`elementId`) are additive; nothing else changes.

Generate the task skeleton:

```json
{
  "id": "<taskId>",
  "type": "execute-connector-activity",
  "displayName": "<display-name from tasks.md>",
  "elementId": "<stageId>-<taskId>",
  "isRequired": "<from tasks.md, default true>",
  "shouldRunOnlyOnce": "<from tasks.md runOnlyOnce, default false>",
  "data": {
    "serviceType": "Intsvc.ActivityExecution",
    "context": "<caseShape.context — placeholders substituted in Step 6>",
    "inputs":  "<caseShape.inputs  — var/id/elementId minted in Step 7>",
    "outputs": "<caseShape.outputs — var/id/elementId minted, dedup applied in Step 7>",
    "bindings": []
  }
}
```

Append the task to the target stage's `data.tasks` structure using `activation-mode` + `entry-rule`, not `lane` alone. Strict `sequential` tasks append as new single-task inner arrays in planned order. `parallel-after-predecessor` siblings share the planned same next inner array even though their entry rule is `runs-sequentially`. Adhoc, event-driven, fan-in, conditional-gate, and standalone tasks get their own single-task inner array. Only `activation-mode: parallel` or `parallel-after-predecessor` tasks with explicit same-lane intent and rationale may share an inner array. Add `runs-sequentially` to the task's entry conditions when the frontend toggle or ordered task-set rule is selected; if `lane` conflicts with mode, mode wins.

### Step 9 — Append root-level bindings

Read [bindings/impl-json.md § Full binding shape — connector tasks](../../variables/bindings/impl-json.md) for the canonical 7-field shape on each entry (all required — omitting any causes Studio Web render failure). Per-task value sources:

- `<connection-id>` (drives `resourceKey` on both bindings + ConnectionBinding `default`): from this task's `tasks.md` entry
- `<connectorKey>` (drives ConnectionBinding templated `name`): from `tasks.md`
- `<folderKey>` (FolderKey binding `default`): from `spec.connection.folderKey` in Step 2 response. **Omit the FolderKey binding entirely when this value is null** (matches `binding-builder.ts:73-83`).
- Binding IDs `<connBindingId>` / `<folderBindingId>` come from Step 5.

Dedup per [§ Deduplication](../../variables/bindings/impl-json.md). Source-of-truth code: `binding-builder.ts` in `uipcli-case-validate/packages/case-tool/src/utils/`.

### Step 10 — Sync IS connection cache

After writing root bindings, populate IS connection cache per [bindings-v2-sync.md § Populate IS connection cache](../../../bindings-v2-sync.md). Skip if `case spec` failed.

> **`bindings_v2.json` regeneration is deferred** — runs once at end of Step 9.7 in [implementation.md](../../../implementation.md) (after all connector tasks), not per-task. See [bindings-v2-sync.md § When to Run](../../../bindings-v2-sync.md).

## Graceful degradation

**Always create the task** — even on errors. Start with `data: { "serviceType": "Intsvc.ActivityExecution" }` and progressively populate.

| Step failed | What gets populated | Log |
|---|---|---|
| `case spec` fails | Phase 2 shape preserved — `data.typeId` + `data.connectionId` only, no Phase 3 inputs/outputs/context enrichment. Distinct from a Rule 8 placeholder (`data: {}`) — typeId/connectionId are resolved, only the spec-driven enrichment is skipped. Log per Rule 8 reporting | `[SKIPPED] case spec failed — typeId/connectionId preserved, no enrichment` |
| Required-field gate fails (user declines) | Placeholder per Rule 8 OR re-prompt | `[SKIPPED] required field <name> missing — placeholder task per Rule 8` |
| All succeed | Full population per Steps 5-10 including bindings_v2 sync | — |

All issues appended to the shared issue list per [logging/impl-json.md](../../logging/impl-json.md).

## Post-Write Verification

1. `type` is `"execute-connector-activity"`
2. `data.serviceType` is `"Intsvc.ActivityExecution"`
3. `data.context[]` has: `connectorKey`, `connection`, `resourceKey`, `folderKey` (when applicable), `objectName`, `method`, `path`, `metadata` — but NOT `operation` or `_label`
4. `data.context[name="connection"].value` is `=bindings.<connBindingId>` (substituted from `{{CONN_BINDING_ID}}`)
5. `data.context[name="folderKey"].value` is `=bindings.<folderBindingId>` (substituted from `{{FOLDER_BINDING_ID}}`); entry absent when `spec.connection.folderKey` was null
6. `data.context[name="metadata"].body.activityPropertyConfiguration.configuration` is a `=jsonString:…` string (CLI-produced; do not modify)
7. Root bindings exist for ConnectionId + folderKey with the minted ids
8. `data.bindings[]` is empty `[]`
9. Each entry in `data.inputs[]` and `data.outputs[]` has `var` / `id` / `elementId` minted (uniqueness rule applied for outputs)
10. At Phase 3 exit, [implementation.md § Step 12 Check 12](../../../implementation.md#step-12--end-of-phase-3-validator-pass) re-asserts 3–8 across every connector node
11. `bindings_v2.json` `resources` array matches top-level `bindings[]` after the deferred sync
12. **No literal `[*]` keys in `data.inputs[name="body"].body` (or any input body).** Scan recursively (JSON.stringify + regex `"[^"]*\\[\\*\\][^"]*"\\s*:`). If any key contains literal `[*]`, halt — Step 1.b translation was skipped or incomplete. The body MUST use real arrays under parent names (e.g., `"toRecipients": [{...}]`), never `"toRecipients[*]": {...}`. Validate passes regardless; runtime APIs reject with HTTP 400.
13. **Lossless inputs (HARD GATE).** Every `tasks.md input-values` field must appear unchanged in the matching `data.inputs[].body`; a top-level `filter:` also requires `spec.filter` and successful compilation. Otherwise halt and repair—never warn and continue.
14. **Spliced subtree is byte-identical to the cache (HARD GATE).** Compare the written `data.context` / `data.inputs` / `data.outputs` against `tasks/spec-cache.<elementId>.json` — identical apart from the placeholder substitutions and the minted `var`/`id`/`elementId`. `validate` does NOT catch content-level loss: a missing `multipartParameters` passes validate and fails at runtime with `400 "Unable to parse multipart body"`.

## What NOT to Do

- **Do NOT add `operation` or `_label` to `data.context[]`.** The FE only adds `operation` for triggers; activity context must not have it.
- **Do NOT add `designTimeMetadata` to the metadata body.** The FE does not include it for case management tasks.
- **Do NOT add top-level `errorState` to the metadata body.** Error state belongs inside `activityPropertyConfiguration.errorState` only — that's already the shape in `caseShape.context`.
- **Do NOT copy root bindings into `data.bindings[]`.** Leave it as `[]`. The FE crashes if activity tasks have task-level binding copies.
- **Do NOT compose or transform the spliced subtree** — see [common § Write `context` / `inputs` / `outputs` from the spec-cache](../../../connector-trigger-impl.md#write-context--inputs--outputs-from-the-spec-cache).
- **Do NOT translate, drop, or reroute an SDD filter.** Use FilterTree only with `spec.filter`; otherwise preserve the exact SDD value in a declared plain sink or halt (Step 4).
- **Do NOT pass `ceqlExpression` directly under `--input-details`.** Derived only.
- **Do NOT pass `bodyParameters` for synthetic HTTP request activities.** Use `queryParameters` instead, or omit.
- **Do NOT pass literal `field[*]` keys in `bodyParameters`.** The `[*]` in `inputs.bodyFields[].name` is JSONPath-style schema notation meaning "array of"; it is NOT a valid input key. Express array-of-object body fields as real JSON arrays under the parent name (see [planning.md](planning.md)). Pre-input scan in [Step 1.b](#step-1b--array-of-object-body-fields-pre-input-scan-mandatory) halts on any literal `[*]` key.
- **Do NOT auto-inject `entryConditions`.** Step 10 in [implementation.md](../../../implementation.md) handles them — injecting here creates duplicates.
- **Never reuse a reference ID from a prior case or session.** Reference IDs (e.g., Jira project keys, Slack channel IDs) are scoped to the authenticated account behind each connection. Always resolve fresh via `uip is resources run list` against the current `--connection-id`. See [/uipath:uipath-platform — reference-resolution.md § Reference IDs Are Connection-Scoped (CRITICAL)](../../../../../uipath-platform/references/integration-service/reference-resolution.md#reference-ids-are-connection-scoped-critical).
- **Do NOT call legacy `uip maestro case tasks describe` or `uip is resources describe`.** `case spec --input-details` replaces both. The legacy commands still work but produce a different shape that doesn't include `caseShape` / placeholders.

## Known Limitations

- The CLI-produced `essentialConfiguration` uses `essentialConfiguration` only (not `optionalConfiguration`). Tasks work at runtime (debug/publish) but the FE editor may not render certain fields until the user re-configures the task in the UI. DAP repopulates these on form open.

<!-- END: impl-json.md -->
