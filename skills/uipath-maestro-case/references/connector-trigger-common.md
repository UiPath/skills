# Connector Trigger — Shared Pipeline

Shared planning and implementation logic for connector-based triggers. Used by both:
- [connector-trigger task](plugins/tasks/connector-trigger/planning.md) — in-stage `wait-for-connector`
- [event trigger](plugins/triggers/event/planning.md) — case-level `Intsvc.EventTrigger`

Both use the same TypeCache (`typecache-triggers-index.json`), same single-call `case spec` discovery, same FE-canonical `caseShape` consumption. Only the target (task vs trigger node), `serviceType`, and a few node-shape details differ — see each plugin's own docs for those specifics.

> Mirrors the [connector-activity](plugins/tasks/connector-activity/planning.md) flow. Same CLI surface (`uip maestro case spec` with `--sections` + `--input-details`); `--type trigger` swaps in trigger-shaped inputs/outputs and the trigger-specific `metadata.body.bindings[Property]` registration entry.

---

## Planning Pipeline

### 1. Find the trigger in TypeCache

Read `~/.uip/case-resources/typecache-triggers-index.json` directly. Match on `displayName`, `connectorKey`, or `eventOperation` from sdd.md. Record `uiPathActivityTypeId`.

### 2. Resolve the connection

```bash
uip maestro case registry get-connection \
  --type typecache-triggers \
  --activity-type-id "<uiPathActivityTypeId>" --output json
```

Returns `Entry`, `Config`, and `Connections`.

- **Single connection** → use it.
- **Multiple connections** → **AskUserQuestion** with connection names + "Something else".
- **Empty `Connections`** → mark `<UNRESOLVED>`. Both plugins emit skeletons at execution time (different shapes per plugin) — see [skeleton-tasks.md](skeleton-tasks.md) for connector-task skeletons and [`plugins/triggers/event/impl-json.md` § Skeleton fallback](plugins/triggers/event/impl-json.md) for event-trigger skeletons.

Record `connection-id`, `connector-key`, `object-name`, `eventOperation` from the response.

Connection selection rules (default-preference, `--refresh` retry, multi-connection disambiguation, ping verification, BYOA workflow): see [/uipath:uipath-platform — connections.md](../../uipath-platform/references/integration-service/connections.md).

> **Entity-typed Curated triggers** (e.g. UiPath Data Service `Record Created (Preview)`) carry a placeholder `objectName` in the typecache (`{tenantEntityName|folderEntityName}`). Pick a real entity via `uip is triggers objects <connector-key> <eventOperation>` and pass it as `--object-name` on the `case spec` call in Step 3.

### 3. Discover the trigger contract via `case spec`

One CLI call replaces the legacy `case tasks describe` + `is triggers describe` dance:

```bash
uip maestro case spec --type trigger \
  --activity-type-id "<uiPathActivityTypeId>" \
  --connection-id "<connection-id>" \
  --sections identity,operation,connection,inputs,outputs,filter,webhook,references \
  --output json
```

The `--sections` value above is the **PLANNING_SECTIONS** bundle — drops `caseShape`, `essentialConfiguration`, and `diagnostics` for a leaner response sized for planning. Phase 3 runs the same command with the **IMPLEMENTATION_SECTIONS** bundle (`identity,connection,caseShape`) plus `--input-details` to mint the populated `caseShape`. See [`case-spec-input-details.md`](case-spec-input-details.md) for the full `--input-details` JSON contract.

> **Diagnostics opt-in.** Append `,diagnostics` to `--sections` when you need the per-endpoint `fetched` / `fallbacks` audit trail (e.g. surfacing fallbacks to the user). Omitted from PLANNING_SECTIONS by default to keep the payload small.

> **Entity-typed Curated triggers.** Add `--object-name "<picked entity>"` when the typecache `object-name` is a placeholder (Step 2).

The response carries everything the planning phase needs:

| Spec output | What it tells you |
|---|---|
| `inputs.eventParameters[]` | Trigger event params with `name`, `dataType`, `required`, `description`, optional `defaultValue` / `enum` / `reference` |
| `outputs.responseFields[]` | Response shape (incoming event payload). `[?responseCurated]` are FE-broken-out outputs, `[?primaryKey]` are id fields |
| `operation.eventMode` | `"polling"` or `"webhooks"` — authoritative source for `event-mode` in `tasks.md` |
| `webhook` | Present (with `url` etc.) when the trigger has a visible webhook URL after configuration; absent otherwise. Surface for webhook-mode triggers when applicable |
| `filter` | `undefined` when the trigger does NOT support server-side filtering. Present when it does, with `builder: "jmes"` and `fields[]` listing every searchable field |
| `references[]` | Cross-references for any event params with lookups. Each entry carries a pre-built `discoverCommand` runnable string |
| `diagnostics.fetched` / `fallbacks` | Surface fallbacks to the user when meaningful (only when you appended `,diagnostics` to `--sections`) |

### 4. Resolve reference fields in event parameters

Check `inputs.eventParameters[]` for entries with a `reference` object. Each carries a pre-built `discoverCommand`:

```jsonc
"reference": {
    "objectName": "MailFolder",
    "lookupValue": "id",
    "lookupNames": ["displayName"],
    "discoverCommand": "uip is resources execute list uipath-microsoft-outlook365 MailFolder --connection-id <id>"
}
```

Run the `discoverCommand` exactly as given. Match the sdd.md value to `lookupNames[0]` in the results. Use the resolved `lookupValue` (the id) in `input-values`.

> **Reference IDs are connection-scoped.** Resolve every reference field freshly against the current `--connection-id`, immediately before writing tasks.md. Never reuse an ID resolved against a different connection — silent runtime fault. Full mechanism: [/uipath:uipath-platform — reference-resolution.md § Reference IDs Are Connection-Scoped (CRITICAL)](../../uipath-platform/references/integration-service/reference-resolution.md#reference-ids-are-connection-scoped-critical).

> **Paginate when looking up by name.** `execute list` returns one page (up to 1000 items); check `Data.Pagination.HasMore` + `Data.Pagination.NextPageToken`. Re-run with `--query "nextPage=<NextPageToken>"` until found or `HasMore` is `"false"`. Short-circuit on first match.

If a reference cannot be resolved, **AskUserQuestion** with the candidates (dropdown when finite set, plus "Something else"). Do not guess.

### 5. Validate required event parameters (HARD GATE)

This is a hard gate — do NOT proceed to writing tasks.md until every required event parameter has a value.

1. Collect every `inputs.eventParameters[?required]` entry from the spec output.
2. For each, check whether sdd.md names a value (literal, resolved reference id, or — in `filter:` only — a `=vars.X` runtime reference).
3. If missing and no `defaultValue`, **AskUserQuestion** — list the missing parameters with their `displayName` and what kind of value is expected.
4. Free-form input is appropriate when the value space is open-ended (folder names, channel names, IDs); when a finite set of sensible values exists (e.g. an `enum`), present them via AskUserQuestion per the dropdown rule in [SKILL.md](../SKILL.md).
5. Only after all required event parameters have values, proceed.

> **Do NOT guess or skip missing required event parameters.** A missing required event parameter causes a runtime error. It is always better to ask than to assume.

### 6. Map SDD inputs to event parameters vs filter fields

SDD input fields don't map 1:1 to the connector's schema. Cross-reference each SDD input against `spec.inputs.eventParameters[]` and `spec.filter.fields[]` from Step 3 to decide where it goes:

- **eventParameters** → configure *what* the trigger monitors. Values must be **static** — resolved to IDs at planning time. Go into `input-values`.
- **filter fields** → narrow *which* events fire the trigger. Values can be **static** literals or **dynamic** `=vars.X` references resolved at runtime. Go into `filter`.

If an SDD input matches an `eventParameters` field name, it's an event parameter. If it matches a `filter.fields[].name`, it's a filter. If it matches neither, **AskUserQuestion** — the SDD may use different naming than the connector.

### 7. Build input-values and filter

**input-values** — resolved event parameter values (static IDs only):
```json
{"eventParameters": {"parentFolderId": "AAMkADNm..."}}
```

**filter** — translate SDD filter criteria using `spec.filter.fields[]` from Step 3. Build a **structured filter tree** (NOT a flat JMESPath string). The CLI compiles the tree to JMESPath at Phase 3 mint time. Tree shape, operator table, anti-patterns, worked examples (single / multi-AND / nested AND-OR): [/uipath:uipath-platform — Filter Trees (CEQL)](../../uipath-platform/references/integration-service/activities.md#filter-trees-ceql). Same shape applies to triggers — only the compiler output differs (JMESPath instead of CEQL). `spec.filter.fields[].name` (Step 3) supplies the valid `id` values.

`groupOperator` accepts both string (`"And"` / `"Or"`) and numeric (`0` / `1`) — the case-tool normalizes string→numeric before threading to the SDK. Use either form; the platform examples use string.

The filter tree goes into `tasks.md` under `filter:` as a literal JSON object — Phase 3 passes it to `case spec --input-details.filter`. The CLI compiles it into all three trigger filter sinks (see § Trigger filter sinks below).

No filter (trigger fires on all events): omit `filter` from the tasks.md entry entirely.

#### Dynamic variable limitation

The filter tree only supports `isLiteral: true` values. When a filter requires runtime case variable references (`=vars.X`), write the `body.filters.expression` JMESPath string directly post-CLI and leave `essentialConfiguration.filter` as `null`. This is a known SDK limitation shared with flow-tool. Practically: pass the literal-only filter to `case spec`, then patch the `=vars.X` reference into the relevant sink afterwards (rare path).

Only use field names that appear in `spec.filter.fields[]`. If a filter cannot be translated unambiguously, **AskUserQuestion**.

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
  --sections identity,connection,caseShape \
  --input-details "<json from Step 1>" \
  --output json
```

The `--sections` value above is the **IMPLEMENTATION_SECTIONS** bundle — emits only `identity`, `connection`, `caseShape` (plus `specVersion`). `--input-details` requires `caseShape` to be in the requested sections. Append `,diagnostics` when you need to surface fallbacks to `build-issues.md`. Add `--object-name "<picked entity>"` for entity-typed Curated triggers (Step 2).

Save the response. The interesting parts:

| Variable | Source |
|---|---|
| `spec.identity` | `.Data.identity` — connectorKey, connectorName, objectName, full TypeCache entry |
| `spec.connection.id` | `.Data.connection.id` — connection UUID (matches `--connection-id`) |
| `spec.connection.folderKey` | `.Data.connection.folderKey` — needed for the FolderKey binding (may be `null`) |
| `spec.caseShape.inputs[]` | `.Data.caseShape.inputs` — single `body` entry. Body holds `parameters` (from eventParameters) and/or `filters.expression` (compiled JMESPath) when authored |
| `spec.caseShape.outputs[]` | `.Data.caseShape.outputs` — `response` (with displayName like "Email Received") + `Error` |
| `spec.caseShape.context[]` | `.Data.caseShape.context` — FE-canonical context array. Carries `{{CONN_BINDING_ID}}` / `{{FOLDER_BINDING_ID}}` placeholders, plus a `metadata.body.bindings[Property]` entry with `{{TRIGGER_REGISTRATION_KEY}}` placeholder when the trigger has event parameters |
| `spec.diagnostics.fallbacks[]` | `.Data.diagnostics.fallbacks` — surface to `build-issues.md` when non-empty. Only present when `--sections` includes `diagnostics` (opt-in) |

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

`startNode.id` is the case's start-node id (existing in `caseplan.json`). This matches FE's `PackagingUtil.ts:227` convention.

Save them as `<connBindingId>`, `<folderBindingId>`, `<eventTriggerKey>` for Step 4.

### Step 4 — Substitute placeholders in `caseShape.context`

The CLI emits placeholders the skill resolves at write-time:

| Placeholder | Where | Replace with |
|---|---|---|
| `{{CONN_BINDING_ID}}` | `caseShape.context[name="connection"].value` (string `=bindings.{{CONN_BINDING_ID}}`) | `<connBindingId>` |
| `{{FOLDER_BINDING_ID}}` | `caseShape.context[name="folderKey"].value` (string `=bindings.{{FOLDER_BINDING_ID}}`); entry only present when `spec.connection.folderKey !== null` | `<folderBindingId>` |
| `{{TRIGGER_REGISTRATION_KEY}}` | `caseShape.context[name="metadata"].body.bindings[*].metadata.ParentResourceKey` (string `EventTrigger.{{TRIGGER_REGISTRATION_KEY}}`); entry only present when `caseShape.context[name="metadata"].body.bindings` exists (i.e. trigger has event parameters) | `<eventTriggerKey>` |

The `metadata` context entry's `body.activityPropertyConfiguration.configuration` JSON-string contains an `essentialConfiguration` blob already populated by the CLI (with `instanceParameters`, `objectName`, `eventOperation`, `eventMode`, `filter` if any). Do not modify this blob — copy verbatim.

### Step 5 — Mint `var` / `id` / `elementId` on inputs and outputs

Per-plugin: each plugin's `impl-json.md` mints these onto `caseShape.inputs[]` / `caseShape.outputs[]` and writes them to its target shape (task vs trigger node).

Conventions (shared with activity):
- `var` = `v` + 8 alphanumeric chars (unique across the case — see [global-vars/impl-json.md § Uniqueness Rule](plugins/variables/global-vars/impl-json.md#uniqueness-rule))
- `id` = same as `var`
- `elementId` = the task's elementId (for in-stage `wait-for-connector` task) or the trigger node's id (for case-level event trigger)

For **outputs** apply the dedup rule: collect existing output `var` values across every task / trigger already in `caseplan.json`; if a `var` already exists (e.g. `response`, `error` collide across multiple connector tasks/triggers), append a counter starting at 2 (`response2`, `error2`). Update `var`, `id`, `value`, `target` (when present); keep `name`, `displayName`, `source` unchanged.

> **Trigger inputs:** trigger inputs do **not** get `elementId` (different from in-stage task inputs). See each plugin's `impl-json.md` for the target-specific shape.

---

## Trigger filter sinks (FYI — populated by CLI)

When `--input-details.filter` is supplied, the CLI populates **three** trigger filter sinks. The skill consumes them by reference; no manual writes:

| Sink | Where (post-spec) |
|---|---|
| FilterTree (design-time) | `caseShape.context[name="metadata"].body.activityPropertyConfiguration.configuration` (inside the `=jsonString:` blob, at `essentialConfiguration.filter`) |
| Compiled JMESPath (FE projection) | `caseShape.context[name="metadata"].body.activityPropertyConfiguration.filterExpression` |
| Compiled JMESPath (runtime) | `caseShape.inputs[name="body"].body.filters.expression` |

The expression is duplicated in two non-config sinks because both have load-bearing roles: SW reads `activityPropertyConfiguration.filterExpression` for the design-time summary; the runtime reads `body.filters.expression` to evaluate against incoming events. This mirrors flow's `configureTrigger` write semantics.

---

## Root-level bindings

Create 2 entries in the bindings array — destination path per [bindings/impl-json.md § Schema-dependent destination](plugins/variables/bindings/impl-json.md) (v19: `root.data.uipath.bindings[]`; v20: top-level `bindings[]`):

| Binding | `id` | `propertyAttribute` | `default` |
|---|---|---|---|
| ConnectionId | `<connBindingId>` (Step 3) | `"ConnectionId"` | `connection-id` (tasks.md) |
| folderKey | `<folderBindingId>` (Step 3) | `"FolderKey"` | `spec.connection.folderKey` (Step 2) |

Both share `resourceKey` = `connection-id`. Deduplicate against existing root bindings.

After writing root bindings, populate IS connection cache per [bindings-v2-sync.md § Populate IS connection cache](bindings-v2-sync.md). Skip if `case spec` failed.

> **`bindings_v2.json` regeneration is deferred** — runs once at end of Step 9.7 (after all connector tasks/triggers), not per-task. See [bindings-v2-sync.md § When to Run](bindings-v2-sync.md).

---

## What NOT to Do (shared)

- **Do NOT call legacy `uip maestro case tasks describe --type connector-trigger` or `uip is triggers describe`.** `case spec --type trigger` replaces both. The legacy commands still work but produce a different shape that doesn't include `caseShape` or placeholders.
- **Do NOT modify `caseShape.context[name="metadata"].body.activityPropertyConfiguration.configuration`.** It's a CLI-produced `=jsonString:…` blob with `essentialConfiguration.{instanceParameters, objectName, eventOperation, eventMode, filter}` — copy verbatim.
- **Do NOT use `CuratedTrigger` or `Intsvc.Trigger` activityType.** The CLI overrides to `CuratedWaitFor` (in-stage task) or emits the trigger shape directly. Trust the CLI's `essentialConfiguration` value.
- **Do NOT hand-write JMESPath filter expressions.** Build a structured filter tree and pass it under `--input-details.filter`; the CLI compiles all three sinks.
- **Do NOT use `filterExpression` as a `--input-details` input.** The CLI rejects raw `filterExpression` strings (MST-8802). Pass the structured tree only.
- **Do NOT pass `ceqlExpression` for triggers** — that's the activity-side rejection key. Triggers compile to JMESPath via the `filter` tree.
- **Never reuse a reference ID from a prior case or session.** Reference IDs (mailbox folders, Slack channels, Jira projects) are scoped to the authenticated account behind each connection. Always resolve fresh via `uip is resources execute list` against the current `--connection-id`. See [/uipath:uipath-platform — reference-resolution.md § Reference IDs Are Connection-Scoped (CRITICAL)](../../uipath-platform/references/integration-service/reference-resolution.md#reference-ids-are-connection-scoped-critical).
- **Do NOT auto-inject `entryConditions`** (for in-stage tasks). The implementation step in [implementation.md](implementation.md) handles them.

## Known Limitation (shared)

The CLI-produced `essentialConfiguration` uses `essentialConfiguration` only (not `optionalConfiguration`). Triggers work at **runtime** but the FE editor may not render certain fields until the user re-configures the trigger in the UI. DAP repopulates these on form open. Documented in `~/Documents/knowledge/Skill_CLI/connector/case-spec-fe-discrepancies.md` (CLI-side).
