# Connector Trigger — Shared Pipeline

Canonical planning and implementation owner for all connector-trigger metadata:

- case-level event trigger;
- in-stage `wait-for-connector` task; and
- `wait-for-connector` rule in any condition scope.

All three use the same TypeCache, target-local `case spec` discovery, and FE-canonical CaseShape consumption. Their target envelopes remain distinct: task `data`, trigger-node `data.inputs`, and condition-rule `uipath`. Connector-bound rules additionally use a Phase 2 stub before their Phase 3 upgrade.

After this common pipeline, read only the selected target file for its envelope, placement, IDs, sidecars, and deviations. Do not load another trigger target.

---

## Planning Pipeline

### 1. Find the trigger in TypeCache

Consume the canonical Rule 3 / Rule 17 contract; do not redefine it:

- Before a successful current-session `registry pull`, a missing `~/.uip/case-resources/typecache-triggers-index.json` is a failed precondition. Complete the normal login + pull gate once.
- After that success, a still-missing index or empty exact-name match is a genuine zero match. Add one `(name, type)` item to the single Rule 17 batch, label it `placeholder only`, and wait for the batch choice before emitting a fallback.
- `registry pull --force` runs only when the user selects the Force-pull branch.

When the batch assigns the non-creatable trigger to fallback (`Use placeholders for all`, or the mixed Create branch), mark all connector-derived fields `<UNRESOLVED: no typecache trigger for <query>>` and use the selected target's placeholder. Otherwise, read the index directly, match the SDD `displayName`, `connectorKey`, or `eventOperation`, and record `uiPathActivityTypeId`.

### 2. Resolve the connection

Each target runs its own call; never reuse another target's response:

```bash
uip maestro case registry get-connection \
  --type typecache-triggers \
  --activity-type-id "<uiPathActivityTypeId>" --output json
```

If the SDD names a connection, require an exact `Connections[].name` match. Otherwise ask even when one connection exists: list existing names plus `Create a new connection`; when empty, offer Create / Skip.

An empty `Connections` array is **not** a TypeCache zero: the connector type exists, so Rule 17 does not run. On Create, run `uip is connections create "<Config.connectorKey>" --output json` in the background and use its `Data.ConnectionId` directly. Non-zero exit, `Result: Failure`, or missing ID is failure: surface `Message`/`Instructions`, offer Retry / Skip, and use the selected target's placeholder only after Skip or repeated failure. In headless runs, surface the authorization URL or ask the user to run the same command. Record `connection-id`, `connector-key`, `object-name`, and `event-operation`.

For an entity-typed Curated trigger whose `objectName` is templated, select the entity with `uip is triggers objects <connector-key> <eventOperation> --output json`. For `Config.activityType: GenericTrigger`, discover and verify an object against this connection:

```bash
uip is resources list "<Config.connectorKey>" \
  --connection-id "<connection-id>" --output json
uip is resources describe "<Config.connectorKey>" "<selected-object>" \
  --connection-id "<connection-id>" --output json
```

Persist the selection and pass `--object-name` on both spec calls. If a required Curated entity or Generic object cannot be selected, mark both `type-id` and `object-name` `<UNRESOLVED: no selectable trigger object>` so every target consumer takes its placeholder. Omitting a required object produces an opaque fetch failure.

### 3. Discover the trigger contract via `case spec`

Planning runs a lean, target-local call:

```bash
uip maestro case spec --type trigger \
  --activity-type-id "<uiPathActivityTypeId>" \
  --connection-id "<connection-id>" \
  --object-name "<selected object when required>" \
  --skip-case-shape --output json
```

Read `inputs.eventParameters[]`, `outputs.responseFields[]`, `operation.eventMode`, `filter`, `references[]`, and `diagnostics`. The Case-local `--input-details` schema owner is [`case-spec-input-details.md`](case-spec-input-details.md).

### 4. Resolve reference fields in event parameters

For every event parameter carrying `reference.discoverCommand`, run that command exactly, against this target's `connection-id`. Match the SDD value through `lookupNames` and store `lookupValue`. Follow `Data.Pagination.NextPageToken` while `HasMore` is true; stop on the first exact match. If none resolves, ask from the observed candidates. Connection-scoped IDs are never reused across connections or sessions.

### 5. Validate required event parameters (HARD GATE)

Collect `inputs.eventParameters[?required]`. Every field needs an SDD value, resolved reference, or `defaultValue` before planning continues. Ask for missing values; present `enum` choices when finite. Never guess. Decline routes to the selected target's placeholder.

### 6. Map SDD inputs to event parameters vs filter fields

- `inputs.eventParameters[]` identifies static design-time scope. Record values under `input-values.eventParameters`.
- `filter.fields[]` identifies event-payload filters. Record a structured FilterTree under `filter`.

If an SDD field matches neither, ask rather than inventing a mapping. Event parameters are static IDs; runtime case references belong only in filter clauses.

### 7. Build input-values and filter

```json
{"eventParameters":{"parentFolderId":"AAMkADNm..."}}
```

Use the FilterTree schema and operators from [`case-spec-input-details.md`](case-spec-input-details.md#filtertree-shape). Emit `groupOperator` even for one clause. Every trigger-filter leaf passed to `case spec` must be literal: `isLiteral: true`, JSON-encoded `rawString`, and the unwrapped value.

#### Literal-only trigger-filter gate (HARD GATE)

The current CLI rejects `isLiteral: false` operands before metadata fetch. If the SDD requests `=vars.X`, `=metadata.X`, `=bindings.X`, or `=js:<expr>` as a filter value, ask for a concrete literal. If the user declines, use the selected target's placeholder; do not strip the clause, pass it to the CLI, or patch either cached filter sink after the spec call.

#### Mandatory-filter contract (REQUIRED event params)

Required event-parameter values automatically form a mandatory equality expression. The CLI AND-merges it with the user FilterTree. Never duplicate a required event parameter in the freeform tree; optional event parameters stay only in `body.queryParams`.

---

## Phase 3 Implementation — Single CLI Call

Every event trigger, wait task, and connector-bound rule executes this pipeline independently. Shared connection or type IDs do not authorize spec-response reuse.
“Single” means one target-local call per attempt; a required-field correction reruns that target and replaces its raw cache.

### Step 1 — Build `--input-details` JSON from tasks.md

Use `eventParameters` and the literal-only `filter` from the target's T-entry. Omit absent keys. If any leaf is non-literal, return to the planning hard gate before calling the CLI. Do not pass derived `filterExpression`.

### Step 2 — Run `case spec` with input-details

Run this target's own `get-connection` again, then:

```bash
uip maestro case spec --type trigger \
  --activity-type-id "<type-id>" \
  --connection-id "<connection-id>" \
  --object-name "<selected object when required>" \
  --input-details "<json from Step 1>" --output json
```

Immediately use **Write** to persist the complete, unmodified response at `tasks/spec-cache.<elementId>.json`, where `<elementId>` identifies this target. Record `{ cachePath, targetKind, targetId, elementId }` in the working audit state. Do not hold, summarize, or reconstruct the payload in reasoning. A different target always gets a different cache.

Raw output uses PascalCase. Relevant read paths are `Data.Identity`, `Data.Connection`, `Data.CaseShape.Context`, `Data.CaseShape.Inputs`, `Data.CaseShape.Outputs`, and `Data.Diagnostics.Fallbacks`. A `Data.caseShape` path is wrong.

### Step 2.a — Revalidate required event parameters (HARD GATE)

Read this target's raw cache. For every required parameter collected from the lean planning spec, verify a non-empty value at `Data.CaseShape.Inputs[Name="body"].Body.QueryParams[<parameter-name>]`. If any is missing, ask for the named values. Rebuild `--input-details`, rerun this target's own spec, and immediately replace its cache with the new complete response; never patch the cached payload. If the user declines or the rerun still lacks a required value, retain the last successfully written complete cache for audit, use the selected target's placeholder, and stop its enrichment.

### Step 3 — Mint binding IDs and (when applicable) trigger registration key

Mint distinct `b` + 8-character IDs inline for Connection and, when `Data.Connection.FolderKey` is non-null, FolderKey. When `Data.CaseShape.Context` contains `{{TRIGGER_REGISTRATION_KEY}}`, use `<connection-id>_<startNode.id>`. The event target overrides `startNode.id` with its own trigger-node ID; the in-stage task and connector rule use the case start-node ID.

### Step 4 — Substitute placeholders in `caseShape.context`

At mutation time, **Read** this target's raw cache and splice the complete `Data.CaseShape.Context`, `Inputs`, and `Outputs` subtrees required by its target file. The rest of the response remains discovery metadata and is never written to `caseplan.json`.

Permitted subtree mutations are only:

1. replace `{{CONN_BINDING_ID}}`, optional `{{FOLDER_BINDING_ID}}`, and optional `{{TRIGGER_REGISTRATION_KEY}}`;
2. mint target-owned `var` / `id` / `elementId` fields;
3. project/deduplicate outputs; and
4. place the result inside the selected target envelope.

Preserve every other current or future key. Never parse or rewrite a JSON string stored as a value.

#### Normalize key casing (PascalCase → camelCase)

After splicing, recursively lower-case only the first character of every **object key** in the three subtrees: `Name`→`name`, `DisplayName`→`displayName`, `UiPathActivityTypeId`→`uiPathActivityTypeId`. Arrays retain order. Values remain byte-for-byte unchanged, including identifiers, `source` strings, and `=jsonString:` / `=js:` values whose internal JSON must not be parsed.

<a id="step-5--mint-var--id--elementid-on-inputs-and-outputs"></a>

### Step 5 — Dispatch target-owned ID and output handling

Do not mint the normalized arrays before entering the selected target owner:

- the event target mints configuration-input IDs only and keeps its derived spec outputs unminted for the global-variable dispatcher;
- the in-stage task target mints both arrays with its task `elementId`; and
- the connector-rule target below mints both arrays with `<ownerNodeId>-<ruleId>`.

Where a target mints outputs, use inline `v` + 8-character IDs and dedupe against the global pool of root variables plus all task, trigger, and connector-rule outputs. On collision, suffix the later producer and update only that producer's `var`, `id`, `value`, and `target`; preserve `name`, `displayName`, and `source`.

---

## Trigger filter sinks (FYI — populated by CLI)

| Sink | Content |
|---|---|
| `context[metadata].body.activityPropertyConfiguration.configuration` | `=jsonString:` configuration containing the design-time FilterTree |
| `context[metadata].body.activityPropertyConfiguration.filterExpression` | mandatory + user JMESPath |
| `inputs[body].body.filters.expression` | the same mandatory + user JMESPath |

The two compiled sinks must remain identical. With required params only, both contain the mandatory expression; with neither input, both are absent.

## Root-level bindings

Read [bindings/impl-json.md § Full binding shape — connector tasks](plugins/variables/bindings/impl-json.md) for the canonical 7-field shape on each entry (all required — omitting any causes Studio Web render failure). Per-trigger value sources:

- `<connection-id>` (drives `resourceKey` on both bindings + ConnectionBinding `default`): from this trigger's `tasks.md` entry
- `<connectorKey>` (drives ConnectionBinding templated `name`): from `tasks.md`
- `<folderKey>` (FolderKey binding `default`): from `Data.Connection.FolderKey` in this target's raw cache. **Omit the FolderKey binding entirely when this value is null** (matches `binding-builder.ts:73-83`).

Dedup per [§ Deduplication](plugins/variables/bindings/impl-json.md). Source-of-truth code: `binding-builder.ts` in `uipcli-case-validate/packages/case-tool/src/utils/`.

After writing root bindings, populate IS connection cache per [bindings-v2-sync.md § Populate IS connection cache](bindings-v2-sync.md). Skip if `case spec` failed.

> **`bindings_v2.json` regeneration is deferred and batched.** Runs at three points, not per-target: end of Phase 2 Step 9 (non-connector tasks), end of Phase 3 Step 9.7 (connector tasks + triggers), and end of Phase 3 **Step 10.5** (upgraded connector condition rules across all 4 scopes). See [bindings-v2-sync.md § When to Run](bindings-v2-sync.md#when-to-run).

Target-local `bindings` stays `[]`.

---

## Target: connector-bound condition rule

The common pipeline owns its `rule.uipath` connector body. The selected condition plugin owns the containing condition, scope placement, condition/rule IDs, display fields, interrupt/completion flags, and any non-connector rule fields.

### Differences vs the in-stage task

| Aspect | In-stage task | Connector-bound rule |
|---|---|---|
| Container | `task.data` | `rule.uipath` |
| `serviceType` | `Intsvc.WaitForEvent` | `Intsvc.WaitForEvent` |
| input/output `elementId` | `<stageId>-<taskId>` | `<ownerNodeId>-<ruleId>` |
| task envelope fields | yes | none |

`<ownerNodeId>` is the stage ID for stage-entry, stage-exit, and task-entry scopes; it is `root` for case-exit.

### Condition-rule phase contract

- **Phase 2 Step 10:** write every `wait-for-connector` rule with the canonical stub from [§ Placeholder fallback](#placeholder-fallback), even when the connector resolved in planning. The enclosing condition, rule ID, expression, scope, and placement are final at this point. Do not run `case spec`, add connector bindings, or dispatch outputs.
- **Phase 3 Step 10.5:** for a resolved connector, run the procedure below and replace only `rule.uipath`. Preserve all enclosing Phase 2 state. For an unresolved connector or failed `case spec`, keep the stub, log it, and report it as not runnable.

The same stub therefore has two lifetimes: temporary for a resolved connector awaiting Phase 3, permanent for an unresolved connector. Only the permanent case is an unresolved-resource issue.

### Procedure (Phase 3)

1. Use the Planning Pipeline and record the common connector fields.
2. Run the rule's own Phase 3 pipeline through the Step 2.a required-field gate, immediately writing `tasks/spec-cache.<ownerNodeId>-<ruleId>.json` after each successful call.
3. Only after the gate succeeds, Read that cache; splice and normalize all three `Data.CaseShape` subtrees per Steps 3–4. For this target's Step 5 branch, mint `var = id = v<8 characters>` on every input/output, set `elementId = <ownerNodeId>-<ruleId>`, and apply the shared output-dedup constraint. A cache retained after a declined gate is audit-only and routes to the placeholder below.
4. Return only this value for the selected condition plugin's `rule.uipath`; that plugin writes the property and surrounding rule envelope:

```json
{
  "serviceType": "Intsvc.WaitForEvent",
  "context": "<complete normalized Context>",
  "inputs": "<complete normalized Inputs; minted>",
  "outputs": "<complete normalized Outputs; minted/deduped>",
  "bindings": []
}
```

5. If the T-entry has `outputs:`, dispatch `rule.uipath.outputs[]` per [io-binding/impl-json.md § Output Binding Shapes for Connector Condition Rules](plugins/variables/io-binding/impl-json.md#output-binding-shapes-for-connector-condition-rules) after minting and before root bindings. Preserve each declared `->` / `=` operator. Skip when the stub has no real outputs.

6. Append root bindings (ConnectionId + FolderKey) and run the deferred Step 10.5 `bindings_v2` sync — identical to the task ([§ Root-level bindings](#root-level-bindings)).

### tasks.md fields (planning)

The selected condition plugin owns its standard fields and adds the common trigger fields:

```markdown
- rule-type: wait-for-connector
- type-id: "<uiPathActivityTypeId>"
- connection-id: "<connection-id>"
- connector-key: "<connector-key>"
- object-name: "<object>"
- event-operation: "<event operation>"
- event-mode: "<polling|webhooks>"
- input-values: {"eventParameters":{...}}  # omit when none
- filter: {...}                            # omit when none
- condition-expression: "=js:vars.X..."   # optional case-state gate
- outputs:                                 # optional; preserve operators
  - "<schemaField> -> <caseVar>"
```

### Caveats

- **Not a case-start trigger.** A connector rule compiles to an in-flight wait (ReceiveTask / event subprocess), so it gets **no entry-points.json entry** and **no rule-specific registration key** — FE `PackagingUtil` trigger registration is gated on `Intsvc.EventTrigger` start events only, which a rule is not. If the `case spec` caseShape carries a `metadata.body.bindings[Property]` registration entry (event-parameter connectors), substitute it exactly as the task does (Step 3 / Step 4); there is nothing rule-specific.
- **Rule IDs are case-unique.** BPMN identity derives from `rule.id`; reuse corrupts the case graph.
- **Full `validate` requires `rule.uipath` + `context`** — absent → `connector activity missing`. It does NOT check the `uipath` *internals* (a wrong `serviceType` passes), so a clean validate confirms the block is *present*, not that the connector *resolves* — confirm in Studio Web. `--skeleton-v2` checks rule presence when supported; the legacy Phase 2 fallback `--skeleton` skips condition rules.

### Placeholder fallback

Phase 2 uses this exact shape for every connector-bound condition rule. It becomes permanent only after the Rule 17 batch assigns a TypeCache zero to fallback, connection creation is declined/fails, the target-local spec fails, or the required-field gate is declined. When `Connections` is empty, offer creation first; do not jump straight to a permanent placeholder.

Emit a **stub `uipath`**, never a bare rule. The stub is the minimum shape accepted by validation: `serviceType` plus the two `context` entries named `connectorKey` and `operation`, each with literal value `"placeholder"`, and empty `inputs` / `outputs` / `bindings`. Do not pad it with resolved fields (`connection`, `objectName`, …); Phase 3 replaces the entire `uipath` block when resolution succeeds.

```json
{
  "id": "<ruleId>",
  "rule": "wait-for-connector",
  "uipath": {
    "serviceType": "Intsvc.WaitForEvent",
    "context": [
      {"name":"connectorKey","value":"placeholder","type":"string"},
      {"name":"operation","value":"placeholder","type":"string"}
    ],
    "inputs": [],
    "outputs": [],
    "bindings": []
  },
  "conditionExpression": "<carry when present>"
}
```

This stub is a **deliberate mock**. While temporary, it is simply Phase 2 build state. If it remains after Phase 3, Studio Web flags it and the rule **fails at debug/run**. A remaining stub has no real outputs, Connection/Folder bindings, IS-cache entry, or rule-specific `bindings_v2` resource. Stamp unresolved `tasks.md` entries with Rule 8 markers, log them, and list them in the completion report as **"replace the `placeholder` connector values before debug / publish-to-run."** Upgrade later by re-running the [§ Procedure](#procedure-phase-3).
A fallback reached before any successful spec response has no raw cache; a post-spec required-field fallback retains the last complete target cache for audit only. That cache must never enrich the placeholder.

---

## What NOT to Do (shared)

- Do not call legacy connector `tasks describe` / `is triggers describe` paths.
- Do not reuse a spec response or spec cache across targets.
- Do not read `Data.caseShape`; raw cache paths are PascalCase.
- Do not reconstruct any CaseShape subtree or enumerate an allowlist of its keys.
- Do not recase values or parse JSON strings while recasing keys.
- Do not hand-write or patch a JMESPath expression after the spec call; author a FilterTree and preserve the CLI-authored sinks.
- Do not encode a dynamic trigger-filter operand as `isLiteral: false`; the planning hard gate must resolve it to a literal or placeholder first.
- Do not duplicate required event parameters in the freeform filter.
- Do not inject task entry conditions from the connector body owner.

## Known Limitation (shared)

The CLI may emit only `essentialConfiguration`, so Studio Web can require a form reopen before displaying some optional fields. Preserve the emitted subtree unchanged; do not synthesize `optionalConfiguration`.
