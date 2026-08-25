# Connector Trigger — Shared Phase 3 Implementation

Shared **write** logic for connector-based triggers: the single `case spec --input-details` call, binding-ID mint, `caseShape.context` splice + placeholder substitution, the connector-bound condition-rule target, the placeholder stub, and root bindings.

Planning — TypeCache lookup, connection pick, spec discovery, reference resolution, the required-param gate, SDD mapping, and input-values + filter authoring — is in the companion [connector-trigger-planning.md](connector-trigger-planning.md), which also holds the `tasks.md` field list this file reads from.

Used by three:
- [connector-trigger task](plugins/tasks/connector-trigger/impl-json.md) — in-stage `wait-for-connector` task (target: `task.data`)
- [event trigger](plugins/triggers/event/impl-json.md) — case-level `Intsvc.EventTrigger` (target: trigger node `data.inputs`)
- **connector-bound condition rule** — a `wait-for-connector` rule in any condition scope (target: `rule.uipath`) — see [§ Target: connector-bound condition rule](#target-connector-bound-condition-rule)

---

## Phase 3 Implementation — Single CLI Call

> **Each connector trigger runs its own `case spec`.** Even when two triggers share the same `connection-id`, `caseShape` is task-shape-specific (different `objectName`, `eventOperation`, `inputs`, `outputs`). Never reuse another task's spec output.

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
  --input-details "<json from Step 1>" \
  --output json
```

The Phase 3 call omits `--skip-case-shape` (incompatible with `--input-details`). The CLI returns the full `caseShape` populated with values from `--input-details`. Add `--object-name "<picked entity>"` for entity-typed Curated triggers ([planning § 2 Resolve the connection](connector-trigger-planning.md#2-resolve-the-connection)).

Save the response. The interesting parts:

> **`case spec --output json` returns PascalCase keys.** The `.Data.*` read paths below reflect that (`.Data.CaseShape.Context`, not `.Data.caseShape.context`). A camelCase jq path returns `null`. The spliced subtree's keys are repaired on the way to disk — see [§ Normalize key casing](#normalize-key-casing-pascalcase--camelcase).

| Variable | Source |
|---|---|
| `spec.identity` | `.Data.Identity` — connectorKey, connectorName, objectName, full TypeCache entry |
| `spec.connection.id` | `.Data.Connection.Id` — connection UUID (matches `--connection-id`) |
| `spec.connection.folderKey` | `.Data.Connection.FolderKey` — needed for the FolderKey binding (may be `null`) |
| `spec.caseShape.inputs[]` | `.Data.CaseShape.Inputs` — single `body` entry. Body holds `parameters` (from eventParameters) and/or `filters.expression` (compiled JMESPath) when authored |
| `spec.caseShape.outputs[]` | `.Data.CaseShape.Outputs` — `response` (with displayName like "Email Received") + `Error` |
| `spec.outputs.responseFields[]` | `.Data.Outputs.ResponseFields` — connector-contract field names as dotted leaf paths, held in `Name` VALUES (which the serializer leaves intact). The authority for the payload output's `body.properties` keys, which the serializer damages |
| `spec.inputs.*[]` | `.Data.Inputs.EventParameters` / `.BodyFields` / `.QueryParameters` / `.PathParameters` — same shape, the authority for `inputs[].body` keys. See [§ Normalize key casing](#normalize-key-casing-pascalcase--camelcase) for both |
| `spec.caseShape.context[]` | `.Data.CaseShape.Context` — FE-canonical context array. Carries `{{CONN_BINDING_ID}}` / `{{FOLDER_BINDING_ID}}` placeholders, plus a `metadata.body.bindings[Property]` entry with `{{TRIGGER_REGISTRATION_KEY}}` placeholder when the trigger has event parameters |
| `spec.diagnostics.fallbacks[]` | `.Data.Diagnostics.Fallbacks` — surface to `build-issues.md` when non-empty |

### Step 3 — Mint binding IDs and (when applicable) trigger registration key

Mint two prefixed IDs for the connection + folder bindings:

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

The **entire** `caseShape.context[]` array, and every nested subtree under it, is CLI-authoritative. The ONLY permitted modifications are the placeholder substitutions in the table above and the key repair in [§ Normalize key casing](#normalize-key-casing-pascalcase--camelcase). **Every other key — current or future, top-level or nested — must be copied from the spec output, regardless of what those keys are or how many there are.** The doc cannot enumerate them all; the CLI's emitted shape is the contract. Composing or reconstructing any subtree of `caseShape.context` from agent memory is FORBIDDEN.

> **Mechanical contract — ordered passes, never combined.** At gather time, persist the full `case spec` response to `tasks/spec-cache.<elementId>.json` (one file per task / rule / trigger node). Pass 1: Read that file and splice `Data.CaseShape.Context` **verbatim — PascalCase keys intact** — into the target shape (the two placeholders are unique literal strings; substitute inline or via a later Edit). After the write, repair keys per [§ Normalize key casing](#normalize-key-casing-pascalcase--camelcase) (Pass 2 lowers structural keys, Pass 3 restores contract keys). The skill is a substituter, not a composer. Repairing WHILE transcribing forces re-composition from memory — that is where subtrees get dropped. **Never retype `context` content from agent reasoning.**

#### Normalize key casing (PascalCase → camelCase)

Applies to the **whole** spliced spec subtree — `context` / `inputs` / `outputs` and their nested `body` — after it is written, i.e. after [§ Step 5](#step-5--mint-var--id--elementid-on-inputs-and-outputs) has minted `var` / `id`. Nothing touches the subtree afterwards.

`case spec --output json` PascalCases every key it serializes. That is a naming **policy**, not a reversible casing toggle, so the correct on-disk form depends on what a key IS. Values are never touched.

| Class | Keys | Correct form |
|---|---|---|
| **Structural** — disk-schema keywords. Closed set | `Name` `Type` `Value` `Target` `Body` `DisplayName` `Source` `DataType` `Required` `Reference` `Properties` `Definitions` `Title` `Items` `ActivityPropertyConfiguration` `ActivityMetadata` `InputMetadata` `TelemetryData` `UiPathActivityTypeId` `Configuration` `ErrorState` `Multipart` `MultipartParameters` `BodyFieldName` | camelCase — lower first char, preserve rest (Pass 2) |
| **Contract** — connector field names. Data, so any casing is legitimate | keys inside `inputs[].body`, and inside the payload output's `body.properties` / `body.definitions` | byte-exact from its authority (Pass 3). Lowering round-trips camelCase only: `ConversationId`→`conversationId` ✓, `RequestBody`→`requestBody` ✗ (contract says `request_body`) |

**Keys only — never values.** `"name": "Subject"`, `"source": "=response.Subject"` and the `=jsonString:` / `=js:` blobs are case-sensitive identifiers; re-casing one breaks byte-for-byte runtime matching ([global-vars/impl-json.md § Name matching](plugins/variables/global-vars/impl-json.md)). Blob-internal JSON is already camelCase — leave it.

**Scope: the spliced subtree.** The skill-authored envelope is already camelCase. One exception: the root `variables[].inputOutputs[].body` companion is a copy of this schema, so copy the repaired body, not the cached one.

**Pass 1 — write verbatim**, per the mechanical contract above.

**Pass 2 — lower structural keys.** One `Edit` per structural key present, `replace_all: true`, old/new carrying BOTH quotes AND the trailing colon: `"Name":` → `"name":`. That anchor makes it keys-only by construction — a value has no trailing colon, a blob-internal key is escaped (`\"Name\":`). Drive it from the closed set above, never from "every capital-first key you see": a contract field is legitimately `Fields` or `Id`, and lowering it here is safe only because Pass 3 overwrites it next.

**Pass 3 — restore contract keys.** Runtime matches these byte-for-byte; `validate` never checks them. Each authority `Name` is a dotted **leaf path**, not a top-level key:

| Repair | Authority |
|---|---|
| payload output `body.properties` | `.Data.Outputs.ResponseFields[].Name` |
| `inputs[].body` | `.Data.Inputs.BodyFields` / `.QueryParameters` / `.PathParameters` / `.EventParameters`, `[].Name` |
| a `body.definitions` key | the `$ref` value targeting it — `"#/definitions/response_metadata"` → `response_metadata` |

Split each `Name` on `.` and walk the segments through `properties` / `items` / `$ref`; each segment is the byte-exact key at its level. Top-level set = de-duplicated first segments. Match by comparing with case and underscores ignored, confirmed by `DisplayName` ↔ `title`. **Never by index** — the collections differ in shape and length: Jira returns `Fields, Id, Key` against `fields.issuetype.name, id, key`, so index pairing writes a literal `"fields.issuetype.name":` key, while segment-walking gives `fields`/`issuetype`/`name`.

**Payload output only.** The `Error` output carries the fixed envelope `Code, Message, Detail, Category, Status, Element`, which `ResponseFields` never describes — skip it. Pass 2's camelCase is correct there, and renaming it breaks every `=Error.Message` binding.

**Cannot complete** → log to `build-issues.md` and surface; never invent a name or guess a casing. Three cases: a written key with no matching segment (or the reverse); a `$ref` with no matching `definitions` key; the authority missing because the cache kept only `CaseShape` — re-read the persisted response, re-run `case spec` only if genuinely absent, and persist the WHOLE response (`Outputs.ResponseFields` / `Inputs.*` sit outside `CaseShape`).

**Verify.** `validate` passes a Pascal `multipartParameters` and a merely plausible field name alike, so this is the only build-time gate. (1) Repaired key sets equal their authority segments byte-for-byte — a capital-first scan cannot substitute, since the defect is lowercase-first (`requestBody` for `request_body`). (2) No capital-first key remains outside the repaired regions; each is a missed Pass 2 `Edit`. No observed connector field name is capital-first, so `"Id":` under `properties` is damage, not contract.


### Step 5 — Mint `var` / `id` / `elementId` on inputs and outputs

Per-plugin: each plugin's `impl-json.md` mints these onto `caseShape.inputs[]` / `caseShape.outputs[]` and writes them to its target shape (task vs trigger node).

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
2. Run `case spec --type trigger --input-details` ([§ Phase 3 Implementation](#phase-3-implementation--single-cli-call)) to mint the populated `caseShape`.
3. Substitute `{{CONN_BINDING_ID}}` / `{{FOLDER_BINDING_ID}}` in `caseShape.context` ([§ Step 4](#step-4--substitute-placeholders-in-caseshapecontext)). If the caseShape carries a `{{TRIGGER_REGISTRATION_KEY}}` entry (event-parameter connectors only), substitute it exactly as the task does ([§ Step 3](#step-3--mint-binding-ids-and-when-applicable-trigger-registration-key)) — there is no rule-specific variant.
4. Mint `var` / `id` / `elementId` on `caseShape.inputs[]` / `outputs[]` ([§ Step 5](#step-5--mint-var--id--elementid-on-inputs-and-outputs)), with `elementId = <ownerNodeId>-<ruleId>`. Apply the output dedup rule.
5. Replace the existing stub's `uipath` with the populated block below, then repair its spliced keys per [§ Normalize key casing](#normalize-key-casing-pascalcase--camelcase) — Pass 2 and Pass 3 apply to `rule.uipath` exactly as they do to `task.data`, in **every** condition scope. The full shape is shown for context; do not rewrite the enclosing rule or condition:

```json
{
  "id": "<ruleId>",
  "rule": "wait-for-connector",
  "uipath": {
    "serviceType": "Intsvc.WaitForEvent",
    "context": "<caseShape.context — placeholders substituted>",
    "inputs":  "<caseShape.inputs  — var/id/elementId minted, keys repaired>",
    "outputs": "<caseShape.outputs — var/id/elementId minted, dedup applied, keys repaired>",
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

---

## Root-level bindings

Read [bindings/impl-json.md § Full binding shape — connector tasks](plugins/variables/bindings/impl-json.md) for the canonical 7-field shape on each entry (all required — omitting any causes Studio Web render failure). Per-trigger value sources:

- `<connection-id>` (drives `resourceKey` on both bindings + ConnectionBinding `default`): from this trigger's `tasks.md` entry
- `<connectorKey>` (drives ConnectionBinding templated `name`): from `tasks.md`
- `<folderKey>` (FolderKey binding `default`): from `spec.connection.folderKey` in Step 2 response. **Omit the FolderKey binding entirely when this value is null** (matches `binding-builder.ts:73-83`).

Dedup per [§ Deduplication](plugins/variables/bindings/impl-json.md). Source-of-truth code: `binding-builder.ts` in `uipcli-case-validate/packages/case-tool/src/utils/`.

After writing root bindings, populate IS connection cache per [bindings-v2-sync.md § Populate IS connection cache](bindings-v2-sync.md). Skip if `case spec` failed.

> **`bindings_v2.json` regeneration is deferred and batched.** Runs at three points, not per-target: end of Phase 2 Step 9 (non-connector tasks), end of Phase 3 Step 9.7 (connector tasks + triggers), and end of Phase 3 **Step 10.5** (upgraded connector condition rules across all 4 scopes). See [bindings-v2-sync.md § When to Run](bindings-v2-sync.md#when-to-run).

---

## What NOT to Do (shared)

- **Do NOT call legacy `uip maestro case tasks describe --type connector-trigger` or `uip is triggers describe`.** `case spec --type trigger` replaces both. The legacy commands still work but produce a different shape that doesn't include `caseShape` or placeholders.
- **Do NOT reconstruct `caseShape.context` (or any nested subtree) from agent memory.** Printing the keys of `context` and later re-emitting from memory drops any subtree not fully expanded in context. Persist the full `case spec` response to `tasks/spec-cache.<elementId>.json` at gather time; at Write time, Read it and splice `Data.caseShape.context` verbatim. See Step 4.
- **Do NOT leave spec PascalCase structural keys in the finished node — and do NOT repair by retyping.** The write is PascalCase-verbatim (Pass 1); the repair is per-key `Edit` with `replace_all` (`"Name":` → `"name":`, Pass 2) plus the contract-key restore (Pass 3). Retyping the subtree to change keys is the memory-reconstruction failure above wearing a different hat. See [§ Normalize key casing](#normalize-key-casing-pascalcase--camelcase).
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
