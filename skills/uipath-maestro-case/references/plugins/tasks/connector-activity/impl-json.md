# connector-activity task — Implementation (Direct JSON Write)

> **Node `type` value: `execute-connector-activity` (schema-kebab).** NEVER write `connector-activity` (plugin folder name) or `connector_activity` into the JSON `type` field. The CLI `--type connector-activity` flag is a separate concept — used only when calling `uip maestro case tasks describe` (legacy) or `uip maestro case spec --type activity` (current). See SKILL.md Rule 17 + Plugin Index.

> **Phase split.** Runs across both phases. Phase 2 writes `data.typeId` + `data.connectionId` only — no `case spec` call in Phase 2. Phase 3 calls `case spec --input-details` once, reads the populated `caseShape`, and mints the task. See [`../../../phased-execution.md`](../../../phased-execution.md).

Fetch the populated connector task scaffold via `uip maestro case spec --input-details`, then drop it into `caseplan.json`. Field discovery and reference resolution are done during [planning](planning.md) — implementation reads resolved values from `registry-resolved.json` and threads them through the spec call.

## Prerequisites from Planning

The SDD row provides:

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

### Step 1 — Build `--input-details` JSON from the resolved entry

**Filter preflight:** run Step 4 for any top-level `filter:` before Step 2.

Construct the input-details object from `registry-resolved.json`, rewriting every value containing a reference to its canonical sink form (connector body fields use `=js:(<expr>)`):

```jsonc
{
    // bodyParameters from the resolved input-values.bodyParameters (dotted keys preserved;
    // each value rewritten to canonical form per Step 1.a)
    "bodyParameters": "<input-values.bodyParameters with values rewritten>",
    // queryParameters from the resolved input-values.queryParameters (same rewrite rule)
    "queryParameters": "<input-values.queryParameters with values rewritten>",
    // pathParameters from the resolved input-values.pathParameters (same rewrite rule)
    "pathParameters":  "<input-values.pathParameters with values rewritten>",
    // filter — FilterTree object from registry-resolved.json (or omit when not authored)
    "filter": "<filter from registry-resolved.json or omit>"
}
```

Synthetic HTTP request activities (`object-name === "httpRequest"` / `"http-request"`) reject `bodyParameters` — pass HTTP body via `queryParameters` instead, or omit. The CLI rejects bodyParameters at validation time.

Full input-details contract: [`case-spec-input-details.md`](../../../case-spec-input-details.md).

#### Step 1.a — Rewrite references to canonical sink form

Connector body sinks (`bodyParameters`, `queryParameters`, `pathParameters`) require `=js:(...)` wrap for every reference. Resolve cross-task refs first, then apply the wrap:

| Value in the SDD | Value passed to CLI |
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

The `[*]` in `inputs.bodyFields[].name` is **schema notation** (JSONPath-style "array of") for documentation only — NOT a valid input key. Array-of-object body fields MUST be expressed in `input-values.bodyParameters` as real JSON arrays under the parent name (see [`planning.md` § Array-of-object body fields](planning.md)). The planner is responsible for emitting the correct shape; this step is a safety net.

**Halt condition.** If any `bodyParameters` key contains literal `[*]`, halt with explicit error:
```
ERROR: bodyParameters key '<key>' contains literal '[*]'.
        Spec field was: <spec field name>. Expected: '<parent>' with a real JSON array value.
        Fix in the resolved input-values.bodyParameters; do NOT pass [*] keys to the CLI.
```

The CLI accepts the literal `field[*]` key (well-formed JSON) and validate passes, but runtime APIs reject with HTTP 400 `UnableToDeserializePostBody`. The check repeats as a post-write verification — see [§ Post-Write Verification](#post-write-verification) item #12.

#### Step 1.c — Copy `input-values` verbatim; the escaping is already done (MANDATORY)

`registry-resolved.json` is JSON and its `input-values` is a real JSON object, so a `=js:` value in it already carries `\\n` where the JavaScript needs `\n`. This step is JSON to JSON: **copy it byte for byte and re-escape nothing.** Adding a level here writes `\\\\n`, which reaches the runtime as a literal backslash-n printed in the message body — wrong output with no error anywhere. Dropping a level writes `\n`, which JSON decodes to a raw line break and faults the element with `Invalid or unexpected token`.

The one place a level is added is planning, where the sdd.md cell becomes ledger JSON: [`planning.md` § 8 Build input-values](planning.md#8-build-input-values).

**Pass the payload single-quoted.** Bash strips one backslash level inside double quotes, so `--input-details "…\\n…"` delivers `\n` and reintroduces the fault. Single quotes pass it through unchanged.

### Step 2 — Run `case spec` with input-details

```bash
uip maestro case spec --type activity \
  --activity-type-id "<type-id>" \
  --connection-id "<connection-id>" \
  --input-details '<json from Step 1>' \
  --output json > tasks/spec-cache.<elementId>.json
```

**Precondition.** `.Data.CaseShape.context` must resolve. If it is `null`, the CLI is too old to emit `caseShape` in its final shape — upgrade; never adapt the splice to an older response.

**The redirect is the only way this file is created.** It holds the CLI's raw response envelope (`Result` / `Code` / `Data`) byte-for-byte. Do NOT author it, and do NOT invent a wrapper of your own around `caseShape` — a hand-built cache is not a cache, and every downstream check compares against it.

**Do not hand-write this file.** The response reaches tens of KB (68 KB for Slack `send_message_to_channel_v2`). A copy written from reasoning drops subtrees silently — observed: an 8.4 KB cache holding 4 of 102 `ResponseFields`, leaving the built node with 4 of 13 response properties while `validate` stayed green. This `>` is the one redirect [SKILL.md](../../../../SKILL.md) Rule 13 permits.

The Phase 3 call omits `--skip-case-shape` (incompatible with `--input-details` — see [case-spec-input-details.md § Validation rules](../../../case-spec-input-details.md#validation-rules-invalidinputdetailserror-on-violation)). The CLI returns the full `caseShape` populated with values from `--input-details`.

**Save the whole response envelope, verbatim, to `tasks/spec-cache.<elementId>.json`** with the Write tool (Rule 14 — not `cp` from `/tmp`, not a redirect) — one file per task. That file is the input to `uip maestro case splice` in Step 5; do not unwrap, re-case, or edit it. The envelope key is `Data.CaseShape` (PascalCase, like every `Data` wrapper); the shape inside it is camelCase (`context` / `inputs` / `outputs`). Read paths:

| Variable | Source |
|---|---|
| `spec.identity` | `.Data.Identity` — connectorKey, connectorName, connectorVersion, objectName, objectDisplayName, full TypeCache entry |
| `spec.connection.folderKey` | `.Data.Connection.FolderKey` — needed for the FolderKey binding |
| `spec.caseShape.inputs[]` | `.Data.CaseShape.inputs` — pre-filled body / queryParameters / pathParameters / file inputs |
| `spec.caseShape.outputs[]` | `.Data.CaseShape.outputs` — response (JSON Schema body) / curated / Error |
| `spec.caseShape.context[]` | `.Data.CaseShape.context` — FE-canonical array; its `connection` / `folderKey` values are `{{CONN_BINDING_ID}}` / `{{FOLDER_BINDING_ID}}` sentinels that `splice` resolves |
| `spec.diagnostics.fallbacks[]` | `.Data.Diagnostics.Fallbacks` — surface to `build-issues.md` when non-empty. |

> **Each connector task runs its own `case spec`.** Even when two tasks share the same `connection-id`, `caseShape` is task-shape-specific (different `objectName`, `httpMethod`, `inputs`, `outputs`). Never reuse another task's spec output.

### Step 3 — Required-field validation (HARD GATE)

This is a hard gate — do NOT proceed to write the task until every required field has a non-empty value in the `caseShape.inputs[].body`.

1. From the lean planning-phase spec (run with `--skip-case-shape` in [planning](planning.md) Step 3), collect `inputs.*[?required]`.
2. After Step 2's call (with the populated caseShape), scan `caseShape.inputs[].body` and verify every required field has a value.
3. If any required field is missing, **AskUserQuestion** — list the missing fields with their `displayName` and what kind of value is expected. Free-form input is appropriate when the value space is open-ended (channel names, message bodies, IDs); when a finite set of sensible values exists (e.g. an `enum`), present them via AskUserQuestion per the dropdown rule in [SKILL.md](../../../../SKILL.md).
4. Re-run Step 2 after collecting the missing values, OR fall back to placeholder task per Rule 9 if user declines to provide a value.

> **Do NOT guess or skip missing required fields.** A missing required field will cause a runtime error. It is always better to ask than to assume.

### Step 4 — FilterBuilder detection (when planning authored a filter)

When the resolved entry carries a `filter` object, the activity's operation must declare a `FilterBuilder` design parameter. The CLI rejects the filter at configure time when no FilterBuilder param exists; the planning step 7 should already have caught this by checking `spec.filter` presence, but verify here as a safety net.

- `spec.filter` present (with `builder: "ceql"` and `fields[]`) → CEQL filter is supported. Pass the structured tree under `--input-details.filter`. The CLI compiles it into both halves of the contract: the runtime CEQL string at `caseShape.inputs[name="queryParameters"].body.<filterParamName>` AND the design-time tree under `essentialConfiguration.savedFilterTrees.<filterParamName>` (inside the `=jsonString:` blob in `caseShape.context[name="metadata"].body.activityPropertyConfiguration.configuration`).
- **Do NOT pass raw CEQL under `queryParameters` for a FilterBuilder operation.** Plain filter fields are normal native-syntax inputs, not authored FilterTrees.
- Tree shape, operator table, examples → [/uipath:uipath-platform — Filter Trees (CEQL)](../../../../../uipath-platform/references/integration-service/activities.md#filter-trees-ceql).

If `spec.filter` is undefined, a top-level `filter:` is malformed. Repair it before Step 2:

1. Find the matching plain query/body field and retain its sink.
2. Copy the exact native value from the SDD Inputs row (or same-session confirmed model); never derive it from the FilterTree.
3. In the same resolved entry, remove `filter:`, add the value to the declared `input-values` sink, preserve siblings, then restart Step 1.

If the field or exact value is unavailable or ambiguous, halt and ask; non-interactive runs report a blocker. Never drop the requirement or invent downstream filtering.

### Step 5 — Write the task skeleton, then `splice`

**5.a — Skeleton (agent-authored, from the SDD).** Write the task with an empty `data` block and the fields only the SDD knows:

```json
{
  "id": "<taskId — t + 8 alphanumeric chars>",
  "type": "execute-connector-activity",
  "displayName": "<display name from sdd.md>",
  "elementId": "<stageId>-<taskId>",
  "isRequired": "<from sdd.md Required, default true>",
  "shouldRunOnlyOnce": "<from sdd.md Run Only Once, default false>",
  "description": "<the task's **Description:** line from sdd.md, word for word>",
  "data": {}
}
```

- `description`: the task's `**Description:**` line from sdd.md, word for word. Do not shorten or reword it. `**Design Rationale:**` is a different line and goes to `tasks/build-issues.md`; use it here only when the block writes no `**Description:**`.

Append the task to the target stage's `data.tasks` structure using `activation-mode` + `entry-rule`, not `lane` alone. Strict `sequential` tasks append as new single-task inner arrays in planned order. `parallel-after-predecessor` siblings share the planned same next inner array even though their entry rule is `runs-sequentially`. Adhoc, event-driven, fan-in, conditional-gate, and standalone tasks get their own single-task inner array. Only `activation-mode: parallel` or `parallel-after-predecessor` tasks with explicit same-lane intent and rationale may share an inner array. Add `runs-sequentially` to the task's entry conditions when the frontend toggle or ordered task-set rule is selected; if `lane` conflicts with mode, mode wins.

**5.b — Splice (CLI-authored).** One call fills `data` from the saved spec and appends the connection's root bindings:

```bash
uip maestro case splice "<caseplan.json>" \
  --node "<taskId>" \
  --spec "tasks/spec-cache.<elementId>.json" \
  --connection-id "<connection-id from registry-resolved.json>" \
  --folder-key "<.Data.Connection.FolderKey from the spec — omit the flag only when it is null>" \
  --output json
```

It writes `data.serviceType`, `data.context` with the two sentinels resolved to `=bindings.<id>`, `data.inputs` / `data.outputs` with `id` / `var` / `elementId` minted, and the ConnectionId + FolderKey root bindings (each with its `default`; reused, not duplicated, when the connection already has a pair). Keys inside `body` are copied untouched. Re-running with the same arguments is byte-identical, so a Phase 4 repair may splice again after a fresh `case spec`. Read `Data.Summary` (`ContextEntries`, `Inputs`, `Outputs`, `ConnectionBindingId`, `FolderBindingId`, `BindingsReused`) and record it in `build-issues.md`.

Never hand-write `data.context`, `data.inputs`, `data.outputs`, or the connection's root bindings for a connector task — every field `splice` writes is CLI-authoritative. **Do not open `connector-trigger-impl.md`, `connector-trigger/impl-json.md`, `case-spec-input-details.md`, or `bindings/impl-json.md` for this task after splicing: nothing in them applies to a spliced task.** They describe the manual transport for the event-trigger node and connector-bound rules, and the binding shape splice already wrote. Never edit the spec envelope to make `splice` accept it; a rejected spec means it was saved without `caseShape` (run `case spec` again without `--skip-case-shape`). `--connection-id` must be the connection the spec was fetched for; splice refuses a mismatch and names both ids.

**5.c — What stays with the agent after splice**, each as a narrow Edit on the spliced task:

- **Output binding.** For every output the SDD references — bare name or first segment of a `->` path — apply [io-binding/impl-json.md § Output Binding Shapes](../../variables/io-binding/impl-json.md#output-binding-shapes) to the entry `splice` wrote, keeping its `id` / `var` / `elementId`. Outputs the SDD does not reference stay as splice minted them.
- **Output name collisions.** `caseShape.outputs[]` returns `response` / `Error` for every connector task. Apply the [uniqueness rule](../../variables/global-vars/impl-json.md#uniqueness-rule) across all tasks already in `caseplan.json`: on a collision append a counter suffix starting at 2 to `var`, `id`, `value`, and `target` (as `=<new var>`); `name`, `displayName`, and `source` stay unchanged.
- **Multipart file inputs** — 5.d below.

#### Step 5.d — Multipart file inputs (after splice)

When `caseShape.inputs[]` contains an entry with `target: "file"` (multipart sink — emitted by `case spec` for activities whose IS spec has `multipart.parameters[].isFile === true`, e.g., Outlook Send Email):

- `target` is a **literal string** `"file"` (the IS request-shape multipart sink name), NOT an expression. Preserve verbatim — do not prepend `=`.
- `value` MUST be `"=vars.<fileVarId>"` (whole-record reference). The FE picker is `selectionOnly` for file inputs (`IntsvcActivityPropertiesUtils.tsx:272-279`) — only a file-typed case Variable can be wired; freeform expressions are rejected at picker time. Sub-field references (`=vars.<id>.FullName`) are NOT valid for file inputs — the runtime adapter expects the full JobAttachment record to dereference.
- No `source`, no `body`, no `displayName` on the multipart file input entry — `case spec` returns just `{name, type, target}`; `splice` minted `var` / `id` / `elementId`; set `value` with one Edit and stop.
- The runtime adapter dereferences `=vars.<fileVarId>` to the JobAttachment record at execution time and streams bytes from the JobAttachment store into the multipart `file` part of the outbound HTTP request.

### Step 6 — Sync IS connection cache

After writing root bindings, populate IS connection cache per [bindings-v2-sync.md § Populate IS connection cache](../../../bindings-v2-sync.md). Skip if `case spec` failed.

> **`bindings_v2.json` regeneration is deferred** — runs once at end of Step 9.7 in [implementation.md](../../../implementation.md) (after all connector tasks), not per-task. See [bindings-v2-sync.md § When to Run](../../../bindings-v2-sync.md).

## Graceful degradation

**Always create the task** — even on errors. Start with `data: { "serviceType": "Intsvc.ActivityExecution" }` and progressively populate.

| Step failed | What gets populated | Log |
|---|---|---|
| `case spec` fails | Phase 2 shape preserved — `data.typeId` + `data.connectionId` only, no Phase 3 inputs/outputs/context enrichment. Distinct from a Rule 9 placeholder (`data: {}`) — typeId/connectionId are resolved, only the spec-driven enrichment is skipped. Log per Rule 9 reporting | `[SKIPPED] case spec failed — typeId/connectionId preserved, no enrichment` |
| Required-field gate fails (user declines) | Placeholder per Rule 9 OR re-prompt | `[SKIPPED] required field <name> missing — placeholder task per Rule 9` |
| All succeed | Skeleton + `splice` (Step 5), Step 6 sync | — |

All issues appended to the shared issue list per [logging/impl-json.md](../../logging/impl-json.md).

## Post-Write Verification

1. `type` is `"execute-connector-activity"`
2. `data.serviceType` is `"Intsvc.ActivityExecution"`
3. `data.context[]` has: `connectorKey`, `connection`, `resourceKey`, `folderKey` (when applicable), `objectName`, `method`, `path`, `metadata` — but NOT `operation` or `_label`
4. `data.context[name="connection"].value` is `=bindings.<ConnectionBindingId from splice Summary>`; no `{{` sentinel remains anywhere in `data`
5. `data.context[name="folderKey"].value` is `=bindings.<FolderBindingId from splice Summary>`; entry absent when `spec.connection.folderKey` was null
6. `data.context[name="metadata"].body.activityPropertyConfiguration.configuration` is a `=jsonString:…` string (CLI-produced; do not modify)
7. Root bindings exist for ConnectionId + folderKey with the ids splice reported, each carrying `default`
8. `data.bindings[]` is empty `[]`
9. Each entry in `data.inputs[]` and `data.outputs[]` has `var` / `id` / `elementId` (written by splice; uniqueness rule applied for outputs in Step 5.c)
10. At Phase 3 exit, [implementation.md § Step 12 Check 12](../../../implementation.md#step-12--end-of-phase-3-validator-pass) re-asserts 3–8 across every connector node
11. `bindings_v2.json` `resources` array matches top-level `bindings[]` after the deferred sync
12. **No literal `[*]` keys in `data.inputs[name="body"].body` (or any input body).** Scan recursively (JSON.stringify + regex `"[^"]*\\[\\*\\][^"]*"\\s*:`). If any key contains literal `[*]`, halt — Step 1.b translation was skipped or incomplete. The body MUST use real arrays under parent names (e.g., `"toRecipients": [{...}]`), never `"toRecipients[*]": {...}`. Validate passes regardless; runtime APIs reject with HTTP 400.
13. **Lossless inputs (HARD GATE).** Every resolved `input-values` field must appear unchanged in the matching `data.inputs[].body`; a top-level `filter:` also requires `spec.filter` and successful compilation. Otherwise halt and repair—never warn and continue.
14. **Spliced subtree is byte-identical to the cache (HARD GATE).** Compare the written `data.context` / `data.inputs` / `data.outputs` against `tasks/spec-cache.<elementId>.json` — identical apart from the placeholder substitutions and the minted `var`/`id`/`elementId`. `validate` does NOT catch content-level loss: a missing `multipartParameters` passes validate and fails at runtime with `400 "Unable to parse multipart body"`.
## What NOT to Do

- **Do NOT add `operation` or `_label` to `data.context[]`.** The FE only adds `operation` for triggers; activity context must not have it.
- **Do NOT add `designTimeMetadata` to the metadata body.** The FE does not include it for case management tasks.
- **Do NOT add top-level `errorState` to the metadata body.** Error state belongs inside `activityPropertyConfiguration.errorState` only — that's already the shape in `caseShape.context`.
- **Do NOT copy root bindings into `data.bindings[]`.** Leave it as `[]`. The FE crashes if activity tasks have task-level binding copies.
- **Do NOT hand-write `data.context`, `data.inputs`, `data.outputs`, or the connection's root bindings.** `uip maestro case splice` writes them from the saved spec envelope (Step 5.b). Any agent-composed version is reconstruction from memory, which is where nested subtrees get dropped.
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
