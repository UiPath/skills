# Connector Trigger — Shared Pipeline

Shared planning and implementation logic for connector-based triggers. Used by three:
- [connector-trigger task](plugins/tasks/connector-trigger/planning.md) — in-stage `wait-for-connector` task
- [event trigger](plugins/triggers/event/planning.md) — case-level `Intsvc.EventTrigger` (case start)
- **connector-bound condition rule** — a `wait-for-connector` rule in any condition scope (stage-entry / stage-exit / case-exit / task-entry). Also called "connector rule" or "connector condition rule" in shorthand; "wait-for-connector rule" when the rule-type is the salient property. All four refer to the same construct. See [§ Target: connector-bound condition rule](#target-connector-bound-condition-rule) and each condition plugin's `impl-json.md`.

All three use the same TypeCache (`typecache-triggers-index.json`), same single-call `case spec` discovery, same FE-canonical `caseShape` consumption. Only the target (task `data` / trigger node `data.uipath` / rule `uipath`), `serviceType`, and a few shape details differ — see each plugin's own docs.

> Mirrors the [connector-activity](plugins/tasks/connector-activity/planning.md) flow. Same CLI surface (`uip maestro case spec` with `--skip-case-shape` for planning, `--input-details` for Phase 3); `--type trigger` swaps in trigger-shaped inputs/outputs and, for event-parameter connectors, a `metadata.body.bindings[Property]` registration entry (Step 4).

---

## Planning Pipeline

### 1. Find the trigger in TypeCache

If `~/.uip/case-resources/typecache-triggers-index.json` does not exist, run `uip maestro case registry pull` first (missing file is a precondition failure, not a 0-match — Rule 17 gate does not apply). If still absent after pull, the tenant has no connector triggers — mark `<UNRESOLVED>` and fall through to § Placeholder fallback.

Read `~/.uip/case-resources/typecache-triggers-index.json` directly. Match on `displayName`, `connectorKey`, or `eventOperation` from sdd.md. Record `uiPathActivityTypeId`.

**No match (Scenario A — connector not found).** A 0-match inside the existing cache is gated by Rule 17 — run the [registry-discovery.md § MUST Confirm Before Placeholder Fallback](registry-discovery.md#must-confirm-before-placeholder-fallback) AskUserQuestion (`Force pull` / `Skip and use placeholders`) for the lookup batch before any fallback. Only after the user picks `Skip`: mark `type-id` **and** `connector-key` `<UNRESOLVED: no typecache trigger for <query>>` and skip § 2 entirely — with no `activity-type-id` there is nothing to pass to `get-connection`. Fall through to § Placeholder fallback (event trigger → placeholder node; connector-trigger task → `data: {}`; condition rule → stub `uipath`). Continue planning — do not halt ([planning.md § 3.4](planning.md)).

### 2. Resolve the connection

```bash
uip maestro case registry get-connection \
  --type typecache-triggers \
  --activity-type-id "<uiPathActivityTypeId>" --output json
```

Returns `Entry`, `Config`, and `Connections`. If the sdd.md names a connection, match it by `name` and use it directly. Otherwise **always present the choice via AskUserQuestion — do not auto-select**, even when one connection exists:

- **`Connections` non-empty** → list connections by `name` **plus a "Create a new connection" option**.
- **`Connections` empty** → offer **Create a new connection** / **Skip (defer)**.
- **Create chosen** → create it (background `is connections create`, capture `ConnectionId`), then continue with the new id. Procedure: [connector-integration.md § Creating a Connection](connector-integration.md#creating-a-connection).
- **Skip / create fails** → mark `<UNRESOLVED>`. Both plugins emit placeholders at execution time (different shapes per plugin) — see [placeholder-tasks.md](placeholder-tasks.md) for connector-task placeholders and [`plugins/triggers/event/impl-json.md` § Placeholder fallback](plugins/triggers/event/impl-json.md) for event-trigger placeholders.

Record `connection-id`, `connector-key`, `object-name`, `eventOperation` from the response (or from the create output).

Connection selection mechanics (`--refresh` retry, ping verification, BYOA workflow, connection creation): see [/uipath:uipath-platform — connections.md](../../uipath-platform/references/integration-service/connections.md).

> **Entity-typed Curated triggers** (e.g. UiPath Data Service `Record Created (Preview)`) carry a placeholder `objectName` in the typecache (`{tenantEntityName|folderEntityName}`). Pick a real entity via `uip is triggers objects <connector-key> <eventOperation>` and pass it as `--object-name` on the `case spec` call in Step 3.

> **Generic-typed triggers** (`Config.activityType === "Generic"`) carry an empty/templated `objectName` in the typecache because one definition is shared across every object the connector exposes (e.g. Salesforce `Record Created`). The CLI fails fast on `case spec --type trigger` without `--object-name`. Discover the available objects via `uip is resources list --connector-key <connector-key>` and `uip is resources describe --connector-key <connector-key> --object-name <name>`, then pass the picked name as `--object-name` on the Step 3 call. Same `--object-name` flag as the entity-typed Curated case above; different reason.

### 3. Discover the trigger contract via `case spec`

One CLI call replaces the legacy `case tasks describe` + `is triggers describe` dance:

```bash
uip maestro case spec --type trigger \
  --activity-type-id "<uiPathActivityTypeId>" \
  --connection-id "<connection-id>" \
  --skip-case-shape \
  --output json
```

`--skip-case-shape` returns a leaner response (no `caseShape`) — the right size for planning. Phase 3 re-runs the same command without the flag, plus `--input-details`, to mint the populated `caseShape`. See [`case-spec-input-details.md`](case-spec-input-details.md) for the full `--input-details` JSON contract.

> **Entity-typed Curated triggers.** Add `--object-name "<picked entity>"` when the typecache `object-name` is a placeholder (Step 2).

The response carries everything the planning phase needs:

| Spec output | What it tells you |
|---|---|
| `inputs.eventParameters[]` | Trigger event params with `name`, `dataType`, `required`, `description`, optional `defaultValue` / `enum` / `reference`. The `required` flag drives the [Mandatory-filter contract](#mandatory-filter-contract-required-event-params) in Step 7 |
| `outputs.responseFields[]` | Response shape (incoming event payload). `[?responseCurated]` are FE-broken-out outputs, `[?primaryKey]` are id fields |
| `operation.eventMode` | `"polling"` or `"webhooks"` — authoritative source for `event-mode` in `tasks.md` |
| `filter` | `undefined` when the trigger does NOT support server-side filtering. Present when it does, with `builder: "jmes"` and `fields[]` listing every searchable field |
| `references[]` | Cross-references for any event params with lookups. Each entry carries a pre-built `discoverCommand` runnable string |
| `diagnostics.fetched` / `fallbacks` | Surface fallbacks to the user when meaningful |

> **Webhook URL is intentionally NOT in the spec output.** Case spec doesn't snapshot it (the URL is deterministic from `connectionId` + `elementInstanceId` + `connectorKey` + `eventOperation`, all of which are on the spec — embedding would add a stale-on-rotation failure mode). When a webhook URL is genuinely needed, fetch it via `getWebhookConfig`. Most authoring flows don't need it.

### 4. Resolve reference fields in event parameters

Check `inputs.eventParameters[]` for entries with a `reference` object. Each carries a pre-built `discoverCommand`:

```jsonc
"reference": {
    "objectName": "MailFolder",
    "lookupValue": "id",
    "lookupNames": ["displayName"],
    "discoverCommand": "uip is resources run list uipath-microsoft-outlook365 MailFolder --connection-id <id>"
}
```

Run the `discoverCommand` exactly as given. Match the sdd.md value to `lookupNames[0]` in the results. Use the resolved `lookupValue` (the id) in `input-values`.

> **Reference IDs are connection-scoped.** Resolve every reference field freshly against the current `--connection-id`, immediately before writing tasks.md. Never reuse an ID resolved against a different connection — silent runtime fault. Full mechanism: [/uipath:uipath-platform — reference-resolution.md § Reference IDs Are Connection-Scoped (CRITICAL)](../../uipath-platform/references/integration-service/reference-resolution.md#reference-ids-are-connection-scoped-critical).

> **Paginate when looking up by name.** `execute list` returns one page (up to 1000 items); check `Data.Pagination.HasMore` + `Data.Pagination.NextPageToken`. Re-run with `--query "nextPage=<NextPageToken>"` until found or `HasMore` is `"false"`. Short-circuit on first match.

If a reference cannot be resolved, **AskUserQuestion** with the candidates (dropdown when finite set, plus "Something else"). Do not guess.

### 5. Validate required event parameters (HARD GATE)

This is a hard gate — do NOT proceed to writing tasks.md until every required event parameter has a value.

1. Collect every `inputs.eventParameters[?required]` entry from the spec output.
2. For each, check whether sdd.md names a value (literal, resolved reference id, or — in `filter:` only — a `=vars.X` runtime reference; impl compiles this to `` =js:`...${vars.X}...` `` template-literal form when writing `body.filters.expression`, see § Dynamic variable limitation).
3. If missing and no `defaultValue`, **AskUserQuestion** — list the missing parameters with their `displayName` and what kind of value is expected.
4. Free-form input is appropriate when the value space is open-ended (folder names, channel names, IDs); when a finite set of sensible values exists (e.g. an `enum`), present them via AskUserQuestion per the dropdown rule in [SKILL.md](../SKILL.md).
5. Only after all required event parameters have values, proceed.

> **Do NOT guess or skip missing required event parameters.** A missing required event parameter causes a runtime error. It is always better to ask than to assume.

### 6. Map SDD inputs to event parameters vs filter fields

SDD input fields don't map 1:1 to the connector's schema. Cross-reference each SDD input against `spec.inputs.eventParameters[]` and `spec.filter.fields[]` from Step 3 to decide where it goes:

- **eventParameters** → configure *what* the trigger monitors. Values must be **static** — resolved to IDs at planning time. Go into `input-values`.
- **filter fields** → narrow *which* events fire the trigger. Values can be **static** literals (filter tree `isLiteral: true`) or **dynamic** `=vars.X` references compiled into `` =js:`...${vars.X}...` `` at impl time (see § Dynamic variable limitation). Go into `filter`.

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

#### Mandatory-filter contract (REQUIRED event params)

The CLI derives a "mandatory-filter expression" from **required** event-param values (`spec.inputs.eventParameters[?required].name`) and AND-merges it with the user filter expression. Two consequences for authoring:

1. **Required event-param values automatically participate in the trigger filter.** Set them via `eventParameters` only (Step 6 mapping). The CLI emits e.g. `(parentFolderId == 'AAMkAD...')` in the filter sinks for free.
2. **Do NOT duplicate a required event-param clause in the freeform `filter` tree.** The CLI AND-joins the mandatory expression automatically; duplicating the clause double-applies it (e.g. `(parentFolderId == 'AAMkAD...') && (parentFolderId == 'AAMkAD...' && ...)`) and matches a strict subset of intended events. Optional event-param values (per `spec.inputs.eventParameters[?!required]`) do NOT contribute to the mandatory expression — they ride along in `body.queryParams` only.

Worked example. Required param `parentFolderId` + a freeform `subject` filter:

```jsonc
// tasks.md authored shape
{
    "input-values": { "eventParameters": { "parentFolderId": "AAMkAD..." } },
    "filter": {
        "groupOperator": "And",
        "filters": [
            { "id": "subject", "operator": "Contains",
              "value": { "isLiteral": true, "rawString": "\"urgent\"", "value": "urgent" } }
        ]
    }
}
```

After the Phase 3 `case spec --input-details` call, both filter sinks contain the combined form:

```
(parentFolderId == 'AAMkAD...') && (contains(subject, 'urgent'))
```

`body.queryParams` keeps the raw event-param map verbatim regardless. See `case-spec-input-details.md § eventParameters (trigger only)` for the full contract.

#### Dynamic variable limitation

The CLI's filter compiler only accepts `isLiteral: true` clauses in the FilterTree (`case-spec-input-details.md § WorkflowValue`). When a filter requires runtime case variable references, the impl step writes the canonical FE template-literal form into `body.filters.expression` (and `activityPropertyConfiguration.filterExpression`) directly post-CLI, and leaves `essentialConfiguration.filter` as `null`. This is a known SDK limitation shared with flow-tool.

**Planner-side authoring contract.** When translating an SDD filter clause to the `tasks.md` FilterTree, the planner classifies each clause by value shape:

| SDD clause value | Encoded as `WorkflowValue` |
|---|---|
| Literal (`"urgent"`, `42`, `true`) | `{ "isLiteral": true, "rawString": "\"urgent\"", "value": "urgent" }` — JSON-encoded `rawString`, unwrapped `value` |
| Variable reference (`=vars.X`, `=metadata.X`, `=bindings.X`) | `{ "isLiteral": false, "rawString": "=vars.X", "value": "=vars.X" }` — both fields carry the `=`-prefixed reference verbatim |
| Pre-wrapped expression (`=js:<expr>` on a filter clause value, e.g. `=js:vars.amount > 5000`) | `{ "isLiteral": false, "rawString": "=js:<expr>", "value": "=js:<expr>" }` — same impl treatment as plain refs (stripped from CLI payload; composed into the post-CLI template literal) |

The planner emits a single unified FilterTree containing both clause types. The impl then:

1. Strips `isLiteral: false` entries from the CLI `--input-details.filter` payload (CLI rejects them).
2. Runs `case spec --input-details` with the literal-only subset.
3. Composes the canonical `` =js:`...${vars.X}...` `` template-literal form into `body.filters.expression` post-CLI by joining the CLI-compiled literal clauses with each var-bearing clause's translated JMESPath sub-clause (using `${<ref>}` for the `=vars.X` reference). Mandatory-filter prefix from required event-params is preserved.

Example (SDD with mixed literal + var-bearing clauses):

```
filter: subject contains =vars.urgentKeyword AND from contains "VIP"
```

Planner emits to `tasks.md`:

```json
{
  "filter": {
    "groupOperator": "And",
    "filters": [
      { "id": "subject", "operator": "Contains",
        "value": { "isLiteral": false, "rawString": "=vars.urgentKeyword", "value": "=vars.urgentKeyword" } },
      { "id": "from", "operator": "Contains",
        "value": { "isLiteral": true, "rawString": "\"VIP\"", "value": "VIP" } }
    ]
  }
}
```

Impl composes (after CLI processes the literal-only subset):

```
=js:`(parentFolderId == '<inbox-id>') && (contains(subject, '${vars.urgentKeyword}')) && (contains(from, 'VIP'))`
```

**Canonical filter-expression form with variables** (matches FE `buildFiltersExpression` output at `IntsvcActivityConfigurationUtils.ts:358-371`):

```
=js:`(<JMESPath clause 1>) && (<JMESPath clause 2 with ${vars.X} interpolation>)`
```

- Outer wrap: `` =js:`...` `` — JS prefix + template-literal backticks. The template literal evaluates at runtime to a JMESPath string.
- Sub-clauses each wrapped in parens for operator-precedence grouping.
- References appear as `${vars.X}` / `${metadata.X}` / `${bindings.X}` template-literal interpolations — NOT as `=vars.X` / `=metadata.X` (plain prefix doesn't get evaluated inside the body sink). All `=js:<ref>` forms get the same transformation via FE's `wrapJsVariablesInTemplateLiteral` (`IntsvcCommonUtils.ts:251-258`).
- For each `=<prefix>.X` reference in the SDD/tasks.md filter, the impl emits `${<prefix>.X}` inside the appropriate JMESPath clause.

> **String-operand quoting (mandatory).** FE's `wrapJsVariablesInTemplateLiteral` does pure substitution — `=js:vars.X` → `${vars.X}` with NO surrounding quotes added (regex at `IntsvcCommonUtils.ts:257`; behavior confirmed by `IntsvcActivityConfigurationUtils.test.ts:986` → `:996`, which asserts the substituted output is unquoted). For JMESPath string operands (`contains(field, <string>)`, `field == '<string>'`), the impl MUST emit single quotes around the `${vars.X}` substitution. For numeric / boolean / JMESPath-literal-backtick operands, no surrounding quotes. Examples:
>
> - String operand: `contains(subject, '${vars.urgentKeyword}')` ✓
> - Numeric operand: `amount > ${vars.minAmount}` ✓
> - JMESPath array literal: `` contains(`["Open","Closed"]`, Status) `` ✓ (literal, no substitution)
>
> Forgetting quotes on a string operand evaluates at runtime to invalid JMESPath (e.g. `contains(subject, Quarterly Review)` — identifier, not string).

**Worked example.** SDD filter: `subject contains =vars.calendarTitle`. Required event-param `parentFolderId` resolved to an Outlook folder id. The impl writes:

```js
=js:`(parentFolderId == 'AAMkAD...') && (contains(subject, '${vars.calendarTitle}'))`
```

Both `body.filters.expression` and `activityPropertyConfiguration.filterExpression` carry this same combined form.

> **Mandatory-filter clauses survive the rewrite.** The CLI's mandatory-filter expression (derived from required event-param values, see § Mandatory-filter contract above) is computed at `case spec` time. When impl writes the canonical template-literal form, it preserves the mandatory prefix: `` =js:`(<mandatory>) && (<your-vars-clause>)` ``. Overwriting the whole expression strips the required event-param matching and the trigger fires on a wider event set than intended.

Only use field names that appear in `spec.filter.fields[]`. If a filter cannot be translated unambiguously, **AskUserQuestion**.

Full per-sink rule and FE source-of-truth: [bindings-and-expressions.md § Canonical form per sink](bindings-and-expressions.md#canonical-form-per-sink).

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

The Phase 3 call omits `--skip-case-shape` (incompatible with `--input-details`). The CLI returns the full `caseShape` populated with values from `--input-details`. Add `--object-name "<picked entity>"` for entity-typed Curated triggers (Step 2).

Save the response. The interesting parts:

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

The **entire** `caseShape.context[]` array, and every nested subtree under it, is CLI-authoritative. The ONLY permitted modifications are the placeholder substitutions in the table above and the key-casing normalization in [§ Normalize key casing](#normalize-key-casing-pascalcase--camelcase). **Every other key — current or future, top-level or nested — must be copied from the spec output, regardless of what those keys are or how many there are.** The doc cannot enumerate them all; the CLI's emitted shape is the contract. Composing or reconstructing any subtree of `caseShape.context` from agent memory is FORBIDDEN.

> **Mechanical contract.** At gather time, persist the full `case spec` response to `tasks/spec-cache.<elementId>.json` (one file per task / rule / trigger node). At write time, **Read that file and splice `Data.caseShape.context` verbatim** into the target shape, then re-case keys per [§ Normalize key casing](#normalize-key-casing-pascalcase--camelcase). The skill is a substituter, not a composer — the only edits between Read and Write are the placeholder substitutions above and that keys-only re-casing. **Never retype `context` content from agent reasoning.**

#### Normalize key casing (PascalCase → camelCase)

`case spec --output json` serializes its whole payload in **PascalCase** — `Data.CaseShape.Context`; context / input / output entries `{ "Name", "Type", "Value", "Target", "Body", "DisplayName", "Source" }`; nested config (`"ActivityPropertyConfiguration"`, `"ActivityMetadata"`, `"UiPathActivityTypeId"`, …); response-schema body (`"Type"`, `"Properties"`, `"Definitions"`, `"Title"`, `"Items"`). The caseplan.json disk schema requires **camelCase** (`name`, `type`, `value`, `body`, `displayName`, `source`, `context`, `properties`, …). This holds regardless of how this doc's examples are cased — the live CLI emits PascalCase; the disk schema reads camelCase.

After splicing the spec subtree (`context` / `inputs` / `outputs` and their nested `body`), lower-case the **first character of every object KEY**, preserving the rest: `Name`→`name`, `DisplayName`→`displayName`, `UiPathActivityTypeId`→`uiPathActivityTypeId`, `Properties`→`properties`.

- **Keys only — never values.** Values are case-sensitive identifiers (`"name": "Subject"`, `"source": "=response.Subject"`, the `=jsonString:` / `=js:` blobs). Re-casing a value breaks runtime variable matching — `findVariableByVariableId` compares byte-for-byte ([global-vars/impl-json.md § Name matching](plugins/variables/global-vars/impl-json.md)). The `=jsonString:` config blob is a string value; its internal JSON is already camelCase — leave it untouched.
- **Scope: the spliced spec subtree only.** The skill-authored caseplan envelope (nodes, edges, variables, bindings, task scaffolding) is already camelCase — do not re-case it.
- **Compatible with splice-verbatim (above).** Splice the full subtree first (never drop or retype content), then re-case keys. A keys-only transform is structural, not a memory reconstruction.

### Step 5 — Mint `var` / `id` / `elementId` on inputs and outputs

Per-plugin: each plugin's `impl-json.md` mints these onto `caseShape.inputs[]` / `caseShape.outputs[]` and writes them to its target shape (task vs trigger node).

Conventions (shared with activity):
- `var` = `v` + 8 alphanumeric chars (unique across the case — see [global-vars/impl-json.md § Uniqueness Rule](plugins/variables/global-vars/impl-json.md#uniqueness-rule))
- `id` = same as `var`
- `elementId` = the task's elementId (in-stage `wait-for-connector` task), the trigger node's id (case-level event trigger), or `<ownerNodeId>-<ruleId>` (connector-bound condition rule — see [§ Target: connector-bound condition rule](#target-connector-bound-condition-rule))

For **outputs** apply the dedup rule: collect existing output `var` values across every task / trigger / **connector-bound condition rule** already in `caseplan.json`; if a `var` already exists (e.g. `response`, `error` collide across multiple connector tasks / triggers / rules), append a counter starting at 2 (`response2`, `error2`). Update `var`, `id`, `value`, `target` (when present); keep `name`, `displayName`, `source` unchanged. **Rule outputs participate in the same global pool** — the dedup must walk condition `rules[][].uipath.outputs[]` across all 4 condition scopes (stage-entry / stage-exit / case-exit / task-entry, case-exit rules living under `metadata.caseExitRules`) in **both directions**: when a rule mints outputs, dedupe against tasks + triggers + rules; when a task / trigger mints outputs, dedupe against existing rule outputs. See [global-vars/impl-json.md § Uniqueness Rule](plugins/variables/global-vars/impl-json.md#uniqueness-rule) for the full enumeration.

> **Trigger-NODE inputs only:** the case-level event-**trigger node** gets no `elementId` on its inputs (different from in-stage task inputs). This does **NOT** apply to connector-bound **condition rules** — a rule's inputs AND outputs BOTH get `elementId = <ownerNodeId>-<ruleId>` (= `root-<ruleId>` for case-exit). See [§ Target: connector-bound condition rule](#target-connector-bound-condition-rule), and each plugin's `impl-json.md` for the target-specific shape.

---

## Trigger filter sinks (FYI — populated by CLI)

> **Source of truth:** [case-spec-input-details.md § Trigger sinks](case-spec-input-details.md). Re-stated below for skill plumbing convenience; keep both copies in sync.

The CLI populates **three** trigger filter sinks. The skill consumes them by reference; no manual writes:

| Sink | Where (post-spec) | Form |
|---|---|---|
| FilterTree (design-time) | `caseShape.context[name="metadata"].body.activityPropertyConfiguration.configuration` (inside the `=jsonString:` blob, at `essentialConfiguration.filter`) | User tree only — round-trips for Studio Web's filter widget |
| Compiled JMESPath (FE projection) | `caseShape.context[name="metadata"].body.activityPropertyConfiguration.filterExpression` | **Combined**: `(mandatory) && (user)` |
| Compiled JMESPath (runtime) | `caseShape.inputs[name="body"].body.filters.expression` | **Combined**: `(mandatory) && (user)` |

`mandatory` is derived from required event-param values (see § Mandatory-filter contract in Step 7). `user` is the compiled tree from `--input-details.filter`. Either side may be empty:

| Inputs supplied | Compiled expression in both sinks |
|---|---|
| Required event params + user filter | `(<mandatory>) && (<user>)` |
| Required event params only | `<mandatory>` |
| User filter only | `<user>` |
| Neither | omitted from both sinks |

The expression is duplicated in two non-config sinks because both have load-bearing roles: SW reads `activityPropertyConfiguration.filterExpression` for the design-time summary; the runtime reads `body.filters.expression` to evaluate against incoming events. Both sinks carry the same combined form so design-time and runtime don't drift. Mirrors flow's `configureTrigger` write semantics post uipcli #1880.

## Root-level bindings

Read [bindings/impl-json.md § Full binding shape — connector tasks](plugins/variables/bindings/impl-json.md) for the canonical 7-field shape on each entry (all required — omitting any causes Studio Web render failure). Per-trigger value sources:

- `<connection-id>` (drives `resourceKey` on both bindings + ConnectionBinding `default`): from this trigger's `tasks.md` entry
- `<connectorKey>` (drives ConnectionBinding templated `name`): from `tasks.md`
- `<folderKey>` (FolderKey binding `default`): from `spec.connection.folderKey` in Step 2 response. **Omit the FolderKey binding entirely when this value is null** (matches `binding-builder.ts:73-83`).

Dedup per [§ Deduplication](plugins/variables/bindings/impl-json.md). Source-of-truth code: `binding-builder.ts` in `uipcli-case-validate/packages/case-tool/src/utils/`.

After writing root bindings, populate IS connection cache per [bindings-v2-sync.md § Populate IS connection cache](bindings-v2-sync.md). Skip if `case spec` failed.

> **`bindings_v2.json` regeneration is deferred and batched.** Runs at three points, not per-target: end of Phase 2 Step 9 (non-connector tasks), end of Phase 3 Step 9.7 (connector tasks + triggers), and end of Phase 3 **Step 10** (connector condition rules across all 4 scopes). See [bindings-v2-sync.md § When to Run](bindings-v2-sync.md#when-to-run).

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

### Procedure (Phase 3)

1. Resolve the connector in planning exactly as the task does — [§ Planning Pipeline](#planning-pipeline). The condition plugin's `planning.md` records the same fields (`type-id` (activity-type-id), `connector-key`, `connection-id`, `object-name`, `event-operation`, `event-mode`, `input-values`, optional `filter`). **Event parameters and filter accept `=vars.X` / `=js:` expressions exactly like the task** — they compile into `rule.uipath.context` / filter via `case spec --type trigger --input-details` (`input-values` + filter). Only the literal request `body` input is value-less (an event sends no body).
2. Run `case spec --type trigger --input-details` ([§ Phase 3 Implementation](#phase-3-implementation--single-cli-call)) to mint the populated `caseShape`.
3. Substitute `{{CONN_BINDING_ID}}` / `{{FOLDER_BINDING_ID}}` in `caseShape.context` ([§ Step 4](#step-4--substitute-placeholders-in-caseshapecontext)). If the caseShape carries a `{{TRIGGER_REGISTRATION_KEY}}` entry (event-parameter connectors only), substitute it exactly as the task does ([§ Step 3](#step-3--mint-binding-ids-and-when-applicable-trigger-registration-key)) — there is no rule-specific variant.
4. Mint `var` / `id` / `elementId` on `caseShape.inputs[]` / `outputs[]` ([§ Step 5](#step-5--mint-var--id--elementid-on-inputs-and-outputs)), with `elementId = <ownerNodeId>-<ruleId>`. Apply the output dedup rule.
5. Write the rule:

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

6. Append root bindings (ConnectionId + FolderKey) and run the deferred `bindings_v2` sync — identical to the task ([§ Root-level bindings](#root-level-bindings)).

### tasks.md fields (planning)

A connector-bound rule's condition T-entry records these (alongside the scope's normal fields):

```markdown
- rule-type: wait-for-connector
- type-id: "<uiPathActivityTypeId>"
- connection-id: "<connection-id>"
- connector-key: "<connector-key>"
- object-name: "<object>"
- event-operation: "<EVENT_OP>"
- event-mode: "polling"               # or "webhooks"
- input-values: { "eventParameters": { ... } }   # resolved IDs; omit when none
- filter: { ... }                     # optional FilterTree; omit when none
- condition-expression: "=js:vars.X..."  # optional gate on case state — NOT the event payload
- outputs:                            # optional — bind rule outputs to case variables
  - "<schemaField> -> <caseVar>"      # extract — rule's response field to case variable
  - "<caseVar> = <expression>"        # assign — literal / =js: expression / =vars.X
```

The `outputs:` block (optional) binds the rule's `response` / `Error` to case variables — same `->` / `=` operator semantics as a connector task. Full shapes + dispatcher: [io-binding/impl-json.md § Output Binding Shapes for Connector Condition Rules](plugins/variables/io-binding/impl-json.md#output-binding-shapes-for-connector-condition-rules).

Rule `id`s are opaque to the FE (no format validation on import) — `Rule_xxxxxx` and `rxxxxxxxx` both work. Two hard requirements: (a) `elementId = <ownerNodeId>-<ruleId>` built from the exact id written; (b) **`rule.id` must be unique within the case** — the BPMN node id `ConnectorEvent_${rule.id}_${elementId}` derives from it, so a collision corrupts the case graph.

### Caveats

- **Not a case-start trigger.** A connector rule compiles to an in-flight wait (ReceiveTask / event subprocess), so it gets **no entry-points.json entry** and **no rule-specific registration key** — FE `PackagingUtil` trigger registration is gated on `Intsvc.EventTrigger` start events only, which a rule is not. If the `case spec` caseShape carries a `metadata.body.bindings[Property]` registration entry (event-parameter connectors), substitute it exactly as the task does (Step 3 / Step 4); there is nothing rule-specific.
- **Full `validate` requires `rule.uipath` + `context`** — absent → `connector activity missing`. It does NOT check the `uipath` *internals* (a wrong `serviceType` passes), so a clean validate confirms the block is *present*, not that the connector *resolves* — confirm in Studio Web. Unresolved → stub placeholder (§ Placeholder fallback). `--skeleton` (Phase 2) skips condition rules.

### Placeholder fallback

Two entry paths reach this fallback: **Scenario A** — connector not found in TypeCache (§ 1 No-match, after the Rule 17 gate); **Scenario B** — connector found but connection unresolved, only after the [§ 2 create offer](#2-resolve-the-connection) is **declined** or fails. When `Connections` is empty, offer to create one first — do not jump straight to the placeholder.

On `case spec` failure or `<UNRESOLVED>` `type-id` / `connection-id` / `connector-key`, emit the rule with a **stub `uipath`**. A *bare* rule (no `uipath`) is NOT a valid placeholder — full `validate` errors `connector activity missing` and Studio Web rejects it. The stub is the **minimum that clears `validate`**: `serviceType` plus the two `context` entries the validator checks for — named `connectorKey` + `operation`, each the literal `"placeholder"` — with empty `inputs` / `outputs` / `bindings`. Do NOT pad it with the other resolved context fields (`connection`, `objectName`, …): Studio Web flags the unresolved connector regardless of how complete the stub is, so extra placeholders buy nothing until the connector is real. The full attach checklist lives in the `tasks.md` `<UNRESOLVED>` markers and the completion report, not in the stub.

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

This stub is a **deliberate mock** — it clears `validate` only. Studio Web flags the unresolved connector, and the rule **fails at debug/run until resolved** (it cannot wait on a `"placeholder"` connector). It still skips the dependent subsystems: io-binding has no real `outputs[]` to wire, no Connection/Folder bindings, no IS-cache entry, no `bindings_v2` regen for this rule. Stamp the `tasks.md` entry with `<UNRESOLVED>` markers per Rule 8, log per [logging/impl-json.md](plugins/logging/impl-json.md), and list it in the completion report as **"replace the `placeholder` connector values before debug / publish-to-run."** Upgrade by re-running the [§ Procedure](#procedure-phase-3) once the connector resolves; same upgrade flow as `placeholder-tasks.md § Upgrade Procedure` for connector tasks.

---

## What NOT to Do (shared)

- **Do NOT call legacy `uip maestro case tasks describe --type connector-trigger` or `uip is triggers describe`.** `case spec --type trigger` replaces both. The legacy commands still work but produce a different shape that doesn't include `caseShape` or placeholders.
- **Do NOT reconstruct `caseShape.context` (or any nested subtree) from agent memory.** Printing the keys of `context` and later re-emitting from memory drops any subtree not fully expanded in context. Persist the full `case spec` response to `tasks/spec-cache.<elementId>.json` at gather time; at Write time, Read it and splice `Data.caseShape.context` verbatim. See Step 4.
- **Do NOT write the spec's PascalCase keys to disk verbatim.** `case spec` emits PascalCase (`Name`/`Type`/`Value`/`Body`/`DisplayName`/`Source`/`Properties`/…); the caseplan disk schema is camelCase. After splicing, lower-case the first character of every object key in the spec subtree — keys only, never values. See [§ Normalize key casing](#normalize-key-casing-pascalcase--camelcase).
- **Do NOT use `CuratedTrigger` or `Intsvc.Trigger` activityType.** The CLI overrides to `CuratedWaitFor` (in-stage task) or emits the trigger shape directly. Trust the CLI's `essentialConfiguration` value.
- **Do NOT hand-write JMESPath filter expressions.** Build a structured filter tree and pass it under `--input-details.filter`; the CLI compiles all three sinks.
- **Do NOT use `filterExpression` as a `--input-details` input.** The CLI rejects raw `filterExpression` strings (MST-8802). Pass the structured tree only.
- **Do NOT pass `ceqlExpression` for triggers** — that's the activity-side rejection key. Triggers compile to JMESPath via the `filter` tree.
- **Do NOT duplicate a required event-param value in the freeform `filter` tree.** The CLI AND-joins required event params into the filter expression automatically (see § 7 / Mandatory-filter contract); duplicating the clause double-applies it and narrows event matching to a strict subset of intended events. Set required event-param values via `eventParameters` ONLY.
- **Never reuse a reference ID from a prior case or session.** Reference IDs (mailbox folders, Slack channels, Jira projects) are scoped to the authenticated account behind each connection. Always resolve fresh via `uip is resources run list` against the current `--connection-id`. See [/uipath:uipath-platform — reference-resolution.md § Reference IDs Are Connection-Scoped (CRITICAL)](../../uipath-platform/references/integration-service/reference-resolution.md#reference-ids-are-connection-scoped-critical).
- **Do NOT auto-inject `entryConditions`** (for in-stage tasks). The implementation step in [implementation.md](implementation.md) handles them.

## Known Limitation (shared)

The CLI-produced `essentialConfiguration` uses `essentialConfiguration` only (not `optionalConfiguration`). Triggers work at **runtime** but the FE editor may not render certain fields until the user re-configures the trigger in the UI. DAP repopulates these on form open.
