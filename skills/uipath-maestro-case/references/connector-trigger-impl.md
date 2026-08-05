# Connector Trigger — Shared Phase 3 Implementation

Shared **write** logic for connector-based triggers: the single `case spec --input-details` call, binding-ID mint, `caseShape.context` splice + placeholder substitution, the connector-bound condition-rule target, the placeholder stub, and root bindings.

Planning — TypeCache lookup, connection pick, spec discovery, reference resolution, the required-param gate, SDD mapping, and input-values + filter authoring — is in the companion [connector-trigger-planning.md](connector-trigger-planning.md), which also holds the `tasks.md` field list this file reads from.

Used by three:
- [connector-trigger task](plugins/tasks/connector-trigger/impl-json.md) — in-stage `wait-for-connector` task (target: `task.data`)
- [event trigger](plugins/triggers/event/impl-json.md) — case-level `Intsvc.EventTrigger` (target: trigger node `data.inputs`)
- **connector-bound condition rule** — a `wait-for-connector` rule in any condition scope (target: `rule.uipath`) — see [§ Target: connector-bound condition rule](#target-connector-bound-condition-rule)

---

## Phase 3 Implementation — Single CLI Call

> **Each connector target runs its own `case spec`.** Even when targets share the same `connection-id`, `caseShape` is target-specific (different `objectName`, `eventOperation`, inputs, and outputs). Never reuse another target's spec response or cache. “Single” means one target-local call per attempt; a required-field correction reruns that target and replaces its cache.

### Step 1 — Build `--input-details` JSON from tasks.md

Construct the input-details object literally from `tasks.md`:

```jsonc
{
    // eventParameters from tasks.md input-values.eventParameters (or omit when no event params authored)
    "eventParameters": "<input-values.eventParameters or omit>",
    // filter — FilterTree object from tasks.md (or omit when not authored)
    "filter": "<filter from tasks.md or omit>"
}
```

Full input-details contract: [`case-spec-input-details.md`](case-spec-input-details.md).

### Step 2 — Run `case spec` with input-details

```bash
uip maestro case spec --type trigger \
  --activity-type-id "<type-id>" \
  --connection-id "<connection-id>" \
  --object-name "<selected object when required>" \
  --input-details "<json from Step 1>" \
  --output json
```

The Phase 3 call omits `--skip-case-shape` (incompatible with `--input-details`). The CLI returns the full `caseShape` populated with values from `--input-details`. Add `--object-name "<picked entity>"` for entity-typed Curated triggers ([planning § 2 Resolve the connection](connector-trigger-planning.md#2-resolve-the-connection)).

Immediately use **Write** to persist the complete, unmodified response at `tasks/spec-cache.<elementId>.json`, where `<elementId>` identifies this target. Record `{ cachePath, targetKind, targetId, elementId }` in the working audit state. Do not hold, summarize, or reconstruct the payload in reasoning. A different target always gets a different cache.

The relevant raw-cache paths are:

> **`case spec --output json` returns PascalCase keys.** The `.Data.*` read paths below reflect that (`.Data.CaseShape.Context`, not `.Data.caseShape.context`). A camelCase jq path returns `null`. The spliced subtree is re-cased to camelCase on the way to disk — see [§ Normalize key casing](#normalize-key-casing-pascalcase--camelcase).

| Variable | Source |
|---|---|
| `spec.identity` | `.Data.Identity` — connectorKey, connectorName, objectName, full TypeCache entry |
| `spec.connection.id` | `.Data.Connection.Id` — connection UUID (matches `--connection-id`) |
| `spec.connection.folderKey` | `.Data.Connection.FolderKey` — needed for the FolderKey binding (may be `null`) |
| `spec.caseShape.inputs[]` | `.Data.CaseShape.Inputs` — single `body` entry. Body holds `parameters` (from eventParameters) and/or `filters.expression` (compiled JMESPath) when authored |
| `spec.caseShape.outputs[]` | `.Data.CaseShape.Outputs` — `response` (with displayName like "Email Received") + `Error` |
| `spec.caseShape.context[]` | `.Data.CaseShape.Context` — FE-canonical context array. Carries `{{CONN_BINDING_ID}}` / `{{FOLDER_BINDING_ID}}` placeholders, plus a `metadata.body.bindings[Property]` entry with `{{TRIGGER_REGISTRATION_KEY}}` placeholder when the trigger has event parameters |
| `spec.diagnostics.fallbacks[]` | `.Data.Diagnostics.Fallbacks` — surface to `build-issues.md` when non-empty |

### Step 2.a — Revalidate required event parameters (HARD GATE)

Read this target's raw cache. For every required parameter collected from the lean planning spec, verify a non-empty value in the matching entry under `Data.CaseShape.Inputs`. If any is missing, ask for the named values, rebuild `--input-details`, rerun only this target's spec call, and immediately replace its cache with the new complete response; never patch the cached payload.

If the user declines or the rerun still lacks a required value, retain the last successfully written complete cache for audit, route the selected target to its placeholder, and stop its enrichment. An audit-only cache must never enrich a placeholder.

### Step 3 — Mint binding IDs and (when applicable) trigger registration key

Mint a prefixed ID for the connection binding and, only when `Data.Connection.FolderKey` is non-null, a distinct folder-binding ID:

| Binding | ID format |
|---|---|
| Connection binding | `b` + 8 alphanumeric chars (e.g. `bA1B2C3D4`) |
| Folder binding | `b` + 8 alphanumeric chars (different from connection binding) |

These ids are **picked inline by the agent** (per SKILL.md Rule 13) — no subprocess.

When the trigger has event parameters (i.e. `caseShape.context[name="metadata"].body.bindings` is non-empty), also mint the **eventTriggerKey** the FE expects for trigger registration:

```
<connection-id>_<startNode.id>
```

`startNode.id` is the case's start-node id (existing in `caseplan.json`). This matches FE's `PackagingUtil.ts:227` convention. **Per-plugin override:** for case-level event triggers, `startNode.id` is the trigger node's own id (the event trigger IS the start node for its case-entry path) — see [event/impl-json.md § Step 4](plugins/triggers/event/impl-json.md#step-4--mint-binding-ids-and-trigger-registration-key).

Save them as `<connBindingId>`, `<folderBindingId>`, `<eventTriggerKey>` for Step 4.

### Step 4 — Substitute placeholders in `caseShape.context`

The CLI emits placeholders the skill resolves at write-time:

| Placeholder | Where | Replace with |
|---|---|---|
| `{{CONN_BINDING_ID}}` | `caseShape.context[name="connection"].value` (string `=bindings.{{CONN_BINDING_ID}}`) | `<connBindingId>` |
| `{{FOLDER_BINDING_ID}}` | `caseShape.context[name="folderKey"].value` (string `=bindings.{{FOLDER_BINDING_ID}}`); entry only present when `spec.connection.folderKey !== null` | `<folderBindingId>` |
| `{{TRIGGER_REGISTRATION_KEY}}` | `caseShape.context[name="metadata"].body.bindings[*].metadata.ParentResourceKey` (string `EventTrigger.{{TRIGGER_REGISTRATION_KEY}}`); entry only present when `caseShape.context[name="metadata"].body.bindings` exists (i.e. trigger has event parameters) | `<eventTriggerKey>` |

At mutation time, **Read** this target's raw cache and splice the complete `Data.CaseShape.Context`, `Data.CaseShape.Inputs`, and `Data.CaseShape.Outputs` subtrees required by its target owner. The rest of the response remains discovery metadata and is never written to `caseplan.json`.

The three subtrees and every nested object are CLI-authoritative. Permitted mutations are only:

1. replace `{{CONN_BINDING_ID}}`, optional `{{FOLDER_BINDING_ID}}`, and optional `{{TRIGGER_REGISTRATION_KEY}}`;
2. normalize object-key casing as specified below;
3. mint target-owned `var` / `id` / `elementId` fields;
4. project/deduplicate outputs; and
5. place the result inside the selected target envelope.

Preserve every other current or future key. Never retype a subtree from reasoning, selectively copy an allowlist, recase a value, or parse/rewrite a JSON string stored as a value.

#### Normalize key casing (PascalCase → camelCase)

`case spec --output json` serializes its whole payload in **PascalCase** — `Data.CaseShape.Context`; context / input / output entries `{ "Name", "Type", "Value", "Target", "Body", "DisplayName", "Source" }`; nested config (`"ActivityPropertyConfiguration"`, `"ActivityMetadata"`, `"UiPathActivityTypeId"`, …); response-schema body (`"Type"`, `"Properties"`, `"Definitions"`, `"Title"`, `"Items"`). The caseplan.json disk schema requires **camelCase** (`name`, `type`, `value`, `body`, `displayName`, `source`, `context`, `properties`, …). This holds regardless of how this doc's examples are cased — the live CLI emits PascalCase; the disk schema reads camelCase.

After splicing the spec subtree (`context` / `inputs` / `outputs` and their nested `body`), lower-case the **first character of every object KEY**, preserving the rest: `Name`→`name`, `DisplayName`→`displayName`, `UiPathActivityTypeId`→`uiPathActivityTypeId`, `Properties`→`properties`.

- **Keys only — never values.** Values are case-sensitive identifiers (`"name": "Subject"`, `"source": "=response.Subject"`, the `=jsonString:` / `=js:` blobs). Re-casing a value breaks runtime variable matching — `findVariableByVariableId` compares byte-for-byte ([global-vars/impl-json.md § Name matching](plugins/variables/global-vars/impl-json.md)). The `=jsonString:` config blob is a string value; its internal JSON is already camelCase — leave it untouched.
- **Scope: the spliced spec subtree only.** The skill-authored caseplan envelope (nodes, edges, variables, bindings, task scaffolding) is already camelCase — do not re-case it.
- **Compatible with splice-verbatim (above).** Splice the full subtree first (never drop or retype content), then re-case keys. A keys-only transform is structural, not a memory reconstruction.

<a id="step-5--mint-var--id--elementid-on-inputs-and-outputs"></a>

### Step 5 — Dispatch target-owned ID and output handling

Do not mint the normalized arrays before entering the selected target owner:

- the event-trigger target mints configuration-input IDs only and keeps its derived spec outputs unminted for the global-variable dispatcher;
- the in-stage wait task mints both arrays with its task `elementId`; and
- the connector-rule target mints both arrays with `<ownerNodeId>-<ruleId>`.

Conventions (shared with activity):
- `var` = `v` + 8 alphanumeric chars (unique across the case — see [global-vars/impl-json.md § Uniqueness Rule](plugins/variables/global-vars/impl-json.md#uniqueness-rule))
- `id` = same as `var`
- `elementId` = the task's elementId (in-stage `wait-for-connector` task), the trigger node's id (case-level event trigger), or `<ownerNodeId>-<ruleId>` (connector-bound condition rule — see [§ Target: connector-bound condition rule](#target-connector-bound-condition-rule))

For **outputs** apply the dedup rule: collect existing output `var` values across every task / trigger / **connector-bound condition rule** already in `caseplan.json`; if a `var` already exists (e.g. `response`, `error` collide across multiple connector tasks / triggers / rules), append a counter starting at 2 (`response2`, `error2`). Update `var`, `id`, `value`, `target` (when present); keep `name`, `displayName`, `source` unchanged. **Rule outputs participate in the same global pool** — the dedup must walk condition `rules[][].uipath.outputs[]` across all 4 condition scopes (stage-entry / stage-exit / case-exit / task-entry, case-exit rules living under `metadata.caseExitRules`) in **both directions**: when a rule mints outputs, dedupe against tasks + triggers + rules; when a task / trigger mints outputs, dedupe against existing rule outputs. See [global-vars/impl-json.md § Uniqueness Rule](plugins/variables/global-vars/impl-json.md#uniqueness-rule) for the full enumeration.

> **Trigger-NODE inputs only:** the case-level event-**trigger node** gets no `elementId` on its inputs (different from in-stage task inputs). This does **NOT** apply to connector-bound **condition rules** — a rule's inputs AND outputs BOTH get `elementId = <ownerNodeId>-<ruleId>` (= `root-<ruleId>` for case-exit). See [§ Target: connector-bound condition rule](#target-connector-bound-condition-rule), and each plugin's `impl-json.md` for the target-specific shape.

---

## Target: connector-bound condition rule

A `wait-for-connector` rule inside a condition (`…conditions[].rules[i][j]`) binds the connector under the rule's **`uipath`** — structurally the same block the in-stage task writes under `data`. **The CLI cannot author this** (`buildRule` in `case-tool` emits a bare `{ rule, id, conditionExpression }` with no `uipath`); write `rule.uipath` directly per this recipe. Used by all four condition plugins.

### Differences vs the in-stage task

| Aspect | In-stage task | Connector-bound rule |
|---|---|---|
| Container | `task.data` | `rule.uipath` |
| `serviceType` | `Intsvc.WaitForEvent` | `Intsvc.WaitForEvent` (same) |
| `elementId` on inputs/outputs | `<stageId>-<taskId>` | `<ownerNodeId>-<ruleId>` |
| Task-level fields (`type`, `displayName`, `isRequired`, `shouldRunOnlyOnce`) | yes | none — it's a rule, not a node |
| `conditionExpression` | n/a | optional extra `=js:` gate on **case state** (`vars.X` / `metadata`) — NOT the event payload (no `event` namespace) |

`<ownerNodeId>` = the **stage id** for stage-entry / stage-exit / task-entry rules (all stage-scoped); **`root`** for case-exit rules (which live under `metadata.caseExitRules`).

### Condition-rule phase contract

- **Phase 2 Step 10:** write every `wait-for-connector` rule with the canonical stub from [§ Placeholder fallback](#placeholder-fallback), even when the connector resolved in planning. The enclosing condition, rule ID, expression, scope, and placement are final at this point. Do not run `case spec`, add connector bindings, or dispatch outputs.
- **Phase 3 Step 10.5:** for a resolved connector, run the procedure below and replace only `rule.uipath`. Preserve all enclosing Phase 2 state. For an unresolved connector or failed `case spec`, keep the stub, log it, and report it as not runnable.

The same stub therefore has two lifetimes: temporary for a resolved connector awaiting Phase 3, permanent for an unresolved connector. Only the permanent case is an unresolved-resource issue.

### Procedure (Phase 3)

1. Resolve the connector in planning exactly as the task does — [connector-trigger-planning.md § Planning Pipeline](connector-trigger-planning.md#planning-pipeline). The condition plugin's `planning.md` records the same fields (`type-id` (activity-type-id), `connector-key`, `connection-id`, `object-name`, `event-operation`, `event-mode`, `input-values`, optional `filter`) — T-entry layout: [connector-trigger-planning.md § tasks.md fields](connector-trigger-planning.md#tasksmd-fields-planning). **Event parameters and filter accept `=vars.X` / `=js:` expressions exactly like the task** — they compile into `rule.uipath.context` / filter via `case spec --type trigger --input-details` (`input-values` + filter). Only the literal request `body` input is value-less (an event sends no body).
2. Run the rule's own Phase 3 pipeline through Step 2.a and immediately write `tasks/spec-cache.<ownerNodeId>-<ruleId>.json` after every successful call.
3. Only after the gate succeeds, Read that cache; splice and normalize all three `Data.CaseShape` subtrees per Steps 3–4. Substitute the connector/folder placeholders and, when present, the registration-key placeholder exactly as the task does.
4. For this target's Step 5 branch, mint `var = id = v<8 characters>` on every input/output, set `elementId = <ownerNodeId>-<ruleId>`, and apply the shared output-dedup constraint. A cache retained after a declined gate is audit-only and routes to the placeholder.
5. Replace the existing stub's `uipath` with the populated block below. The full shape is shown for context; do not rewrite the enclosing rule or condition:

```json
{
  "id": "<ruleId>",
  "rule": "wait-for-connector",
  "uipath": {
    "serviceType": "Intsvc.WaitForEvent",
    "context": "<caseShape.context — placeholders substituted>",
    "inputs":  "<caseShape.inputs  — var/id/elementId minted>",
    "outputs": "<caseShape.outputs — var/id/elementId minted, dedup applied>",
    "bindings": []
  },
  "conditionExpression": "<optional =js: gate on case state, e.g. vars.X — NOT the event payload>"
}
```

5b. If the T-entry has `outputs:`, dispatch `rule.uipath.outputs[]` per [io-binding/impl-json.md § Output Binding Shapes for Connector Condition Rules](plugins/variables/io-binding/impl-json.md#output-binding-shapes-for-connector-condition-rules) — rewrite each already-minted output entry per its `->` / `=` operator. Skip when the rule has no `uipath.outputs[]` (stub placeholder — the stub always emits `uipath`, but with empty `outputs[]`).

6. Append root bindings (ConnectionId + FolderKey) and run the deferred Step 10.5 `bindings_v2` sync — identical to the task ([§ Root-level bindings](#root-level-bindings)).

**Rule `id` requirements.** Rule `id`s are opaque to the FE (no format validation on import) — `Rule_xxxxxx` and `rxxxxxxxx` both work. Two hard requirements: (a) `elementId = <ownerNodeId>-<ruleId>` built from the exact id written; (b) **`rule.id` must be unique within the case** — the BPMN node id `ConnectorEvent_${rule.id}_${elementId}` derives from it, so a collision corrupts the case graph.

### Caveats

- **Not a case-start trigger.** A connector rule compiles to an in-flight wait (ReceiveTask / event subprocess), so it gets **no entry-points.json entry** and **no rule-specific registration key** — FE `PackagingUtil` trigger registration is gated on `Intsvc.EventTrigger` start events only, which a rule is not. If the `case spec` caseShape carries a `metadata.body.bindings[Property]` registration entry (event-parameter connectors), substitute it exactly as the task does (Step 3 / Step 4); there is nothing rule-specific.
- **Full `validate` requires `rule.uipath` + `context`** — absent → `connector activity missing`. It does NOT check the `uipath` *internals* (a wrong `serviceType` passes), so a clean validate confirms the block is *present*, not that the connector *resolves* — confirm in Studio Web. `--skeleton-v2` checks rule presence when supported; the legacy Phase 2 fallback `--skeleton` skips condition rules.

### Placeholder fallback

Phase 2 uses this exact shape for every connector-bound condition rule. Two paths make it permanent: **Scenario A** — connector not found in TypeCache ([planning § 1 No-match](connector-trigger-planning.md#1-find-the-trigger-in-typecache), after the Rule 17 gate); **Scenario B** — connector found but connection unresolved, only after the [planning § 2 create offer](connector-trigger-planning.md#2-resolve-the-connection) is **declined** or fails. When `Connections` is empty, offer to create one first — do not jump straight to a permanent placeholder.

Emit a **stub `uipath`**, never a bare rule. The stub is the minimum shape accepted by validation: `serviceType` plus the two `context` entries named `connectorKey` and `operation`, each with literal value `"placeholder"`, and empty `inputs` / `outputs` / `bindings`. Do not pad it with resolved fields (`connection`, `objectName`, …); Phase 3 replaces the entire `uipath` block when resolution succeeds.

```json
{
  "id": "<ruleId>",
  "rule": "wait-for-connector",
  "uipath": {
    "serviceType": "Intsvc.WaitForEvent",
    "context": [
      { "name": "connectorKey", "value": "placeholder", "type": "string" },
      { "name": "operation",    "value": "placeholder", "type": "string" }
    ],
    "inputs": [],
    "outputs": [],
    "bindings": []
  },
  "conditionExpression": "<carry from the T-entry if present>"
}
```

This stub is a **deliberate mock**. While temporary, it is simply Phase 2 build state. If it remains after Phase 3, Studio Web flags it and the rule **fails at debug/run**. A remaining stub has no real outputs, Connection/Folder bindings, IS-cache entry, or rule-specific `bindings_v2` resource. Stamp unresolved `tasks.md` entries with Rule 8 markers, log them, and list them in the completion report as **"replace the `placeholder` connector values before debug / publish-to-run."** Upgrade later by re-running the [§ Procedure](#procedure-phase-3).

A fallback reached before any successful spec response has no raw cache. A post-spec required-field fallback retains the last complete target cache for audit only; that cache must never enrich the placeholder.

---

## Root-level bindings

Read [bindings/impl-json.md § Full binding shape — connector tasks](plugins/variables/bindings/impl-json.md) for the canonical 7-field shape on each entry (all required — omitting any causes Studio Web render failure). Per-trigger value sources:

- `<connection-id>` (drives `resourceKey` on both bindings + ConnectionBinding `default`): from this trigger's `tasks.md` entry
- `<connectorKey>` (drives ConnectionBinding templated `name`): from `tasks.md`
- `<folderKey>` (FolderKey binding `default`): from `Data.Connection.FolderKey` in this target's raw cache. **Omit the FolderKey binding entirely when this value is null** (matches `binding-builder.ts:73-83`).

Dedup per [§ Deduplication](plugins/variables/bindings/impl-json.md). Source-of-truth code: `binding-builder.ts` in `uipcli-case-validate/packages/case-tool/src/utils/`.

After writing root bindings, populate IS connection cache per [bindings-v2-sync.md § Populate IS connection cache](bindings-v2-sync.md). Skip if `case spec` failed.

> **`bindings_v2.json` regeneration is deferred and batched.** Runs at three points, not per-target: end of Phase 2 Step 9 (non-connector tasks), end of Phase 3 Step 9.7 (connector tasks + triggers), and end of Phase 3 **Step 10.5** (upgraded connector condition rules across all 4 scopes). See [bindings-v2-sync.md § When to Run](bindings-v2-sync.md#when-to-run).

---

## What NOT to Do (shared)

- **Do NOT call legacy `uip maestro case tasks describe --type connector-trigger` or `uip is triggers describe`.** `case spec --type trigger` replaces both. The legacy commands still work but produce a different shape that doesn't include `caseShape` or placeholders.
- **Do NOT reconstruct any `CaseShape` subtree from agent memory.** Persist the full response at gather time; at mutation time, Read it and splice the complete `Data.CaseShape.Context`, `Inputs`, and `Outputs` subtrees. See Step 4.
- **Do NOT write the spec's PascalCase keys to disk verbatim.** `case spec` emits PascalCase (`Name`/`Type`/`Value`/`Body`/`DisplayName`/`Source`/`Properties`/…); the caseplan disk schema is camelCase. After splicing, lower-case the first character of every object key in the spec subtree — keys only, never values. See [§ Normalize key casing](#normalize-key-casing-pascalcase--camelcase).
- **Do NOT use `CuratedTrigger` or `Intsvc.Trigger` activityType.** The CLI overrides to `CuratedWaitFor` (in-stage task) or emits the trigger shape directly. Trust the CLI's `essentialConfiguration` value.
- **Do NOT hand-write JMESPath filter expressions.** Build a structured filter tree and pass it under `--input-details.filter`; the CLI compiles all three sinks.
- **Do NOT use `filterExpression` as a `--input-details` input.** The CLI rejects raw `filterExpression` strings (MST-8802). Pass the structured tree only.
- **Do NOT pass `ceqlExpression` for triggers** — that's the activity-side rejection key. Triggers compile to JMESPath via the `filter` tree.
- **Do NOT duplicate a required event-param value in the freeform `filter` tree.** The CLI AND-joins required event params into the filter expression automatically (see [planning § Mandatory-filter contract](connector-trigger-planning.md#mandatory-filter-contract-required-event-params)); duplicating the clause double-applies it and narrows event matching to a strict subset of intended events. Set required event-param values via `eventParameters` ONLY.
- **Never reuse a reference ID from a prior case or session.** Reference IDs (mailbox folders, Slack channels, Jira projects) are scoped to the authenticated account behind each connection. Always resolve fresh via `uip is resources run list` against the current `--connection-id`. See [/uipath:uipath-platform — reference-resolution.md § Reference IDs Are Connection-Scoped (CRITICAL)](../../uipath-platform/references/integration-service/reference-resolution.md#reference-ids-are-connection-scoped-critical).
- **Do NOT auto-inject `entryConditions`** (for in-stage tasks). The implementation step in [implementation.md](implementation.md) handles them.

## Known Limitation (shared)

The CLI-produced `essentialConfiguration` uses `essentialConfiguration` only (not `optionalConfiguration`). Triggers work at **runtime** but the FE editor may not render certain fields until the user re-configures the trigger in the UI. DAP repopulates these on form open.
<!-- END: connector-trigger-impl.md -->
