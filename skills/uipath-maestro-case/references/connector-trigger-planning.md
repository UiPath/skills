# Connector Trigger — Shared Planning Pipeline

Shared **planning** logic for connector-based triggers: TypeCache lookup, connection pick, `case spec` discovery, reference resolution, the required-param gate, SDD mapping, and input-values + filter authoring. It ends at `tasks.md`.

> **This file is half the contract.** Every JSON shape written to `caseplan.json` — the populated `caseShape` splice, placeholder substitution, binding-ID mint, the connector-bound condition-rule block, the placeholder stub, and root bindings — lives in the companion [connector-trigger-impl.md](connector-trigger-impl.md). Planning alone never produces a runnable connector node.

Used by three:
- [connector-trigger task](plugins/tasks/connector-trigger/planning.md) — in-stage `wait-for-connector` task
- [event trigger](plugins/triggers/event/planning.md) — case-level `Intsvc.EventTrigger` (case start)
- **connector-bound condition rule** — a `wait-for-connector` rule in any condition scope (stage-entry / stage-exit / case-exit / task-entry). Also called "connector rule" or "connector condition rule" in shorthand; "wait-for-connector rule" when the rule-type is the salient property. All four refer to the same construct. See [connector-trigger-impl.md § Target: connector-bound condition rule](connector-trigger-impl.md#target-connector-bound-condition-rule) and each condition plugin's `impl-json.md`.

All three use the same TypeCache (`typecache-triggers-index.json`), same single-call `case spec` discovery, same FE-canonical `caseShape` consumption. Only the target (task `data` / trigger node `data.inputs` / rule `uipath`), `serviceType`, and a few shape details differ — see each plugin's own docs. Connector-bound condition rules additionally use a Phase 2 stub before their Phase 3 `caseShape` upgrade.

> Mirrors the [connector-activity](plugins/tasks/connector-activity/planning.md) flow. Same CLI surface (`uip maestro case spec` with `--skip-case-shape` for planning, `--input-details` for Phase 3); `--type trigger` swaps in trigger-shaped inputs/outputs and, for event-parameter connectors, a `metadata.body.bindings[Property]` registration entry ([impl § Step 4](connector-trigger-impl.md#step-4--substitute-placeholders-in-caseshapecontext)).

---

## Planning Pipeline

### 1. Find the trigger in TypeCache

If `~/.uip/case-resources/typecache-triggers-index.json` does not exist, run `uip maestro case registry pull` first (missing file is a precondition failure, not a 0-match — Rule 17 gate does not apply). If still absent after pull, the tenant has no connector triggers — mark `<UNRESOLVED>` and fall through to [connector-trigger-impl.md § Placeholder fallback](connector-trigger-impl.md#placeholder-fallback).

Read `~/.uip/case-resources/typecache-triggers-index.json` directly. Match on `displayName`, `connectorKey`, or `eventOperation` from sdd.md. Record `uiPathActivityTypeId`.

**No match (Scenario A — connector not found).** A 0-match inside the existing cache is gated by Rule 17 — run the [registry-discovery.md § MUST Confirm Before Placeholder Fallback](registry-discovery.md#must-confirm-before-placeholder-fallback) AskUserQuestion (`Force pull` / `Use placeholders for all`) for the lookup batch before any fallback. Only after the user picks `Use placeholders for all`: mark `type-id` **and** `connector-key` `<UNRESOLVED: no typecache trigger for <query>>` and skip § 2 entirely — with no `activity-type-id` there is nothing to pass to `get-connection`. Fall through to [connector-trigger-impl.md § Placeholder fallback](connector-trigger-impl.md#placeholder-fallback) (event trigger → placeholder node; connector-trigger task → `data: {}`; condition rule → stub `uipath`). Continue planning — do not halt ([planning.md § 3.4](planning.md)).

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

Record `connection-id`, `connector-key`, `object-name`, `eventOperation` from the response (or from the create output). `Entry` and `Config` are verbatim subtrees — read them at `.Data.Config.connectorKey`, `.Data.Config.objectName`, `.Data.Entry.eventOperation`. `Connections` is not, so its entries read `.Data.Connections[].Name` / `.Id`.

Connection selection mechanics (`--refresh` retry, ping verification, BYOA workflow, connection creation): see [/uipath:uipath-platform — connections.md](../../uipath-platform/references/integration-service/connections.md).

> **Entity-typed Curated triggers** (e.g. UiPath Data Service `Record Created (Preview)`) carry a placeholder `objectName` in the typecache (`{tenantEntityName|folderEntityName}`). Pick a real entity via `uip is triggers objects <connector-key> <eventOperation>` and pass it as `--object-name` on the `case spec` call in Step 3.

> **Generic-typed triggers** (`Config.activityType === "GenericTrigger"` in `typecache-triggers-index.json` — trigger entries use `GenericTrigger` / `CuratedTrigger`, not the activity-typecache's `Generic` / `Curated`) carry an empty/templated `objectName` in the typecache because one definition is shared across every object the connector exposes (e.g. Salesforce `Record Created`). Discover the available objects via `uip is resources list --connector-key <connector-key>` and `uip is resources describe --connector-key <connector-key> --object-name <name>`, then pass the picked name as `--object-name` on the Step 3 call. Same `--object-name` flag as the entity-typed Curated case above; different reason. Omit it and `case spec --type trigger` fails at fetch time with an opaque `unknown_error` (`Error fetching connector task spec`), cause buried in `Instructions`: `objectName … null or undefined … getInstanceEventObjectMetadata()` — resolve the object and re-run with `--object-name`.

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

> **Paginate when looking up by name.** `run list` returns one page (up to 1000 items); check `Data.Pagination.HasMore` + `Data.Pagination.NextPageToken`. Re-run with `--query "nextPage=<NextPageToken>"` until found or `HasMore` is `"false"`. Short-circuit on first match.

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

---

## tasks.md fields (planning)

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

---

> **Planning is done; the write recipe is not.** Continue in [connector-trigger-impl.md](connector-trigger-impl.md) — Steps 1–5 (`case spec --input-details`, binding-ID mint, `caseShape.context` splice + placeholder substitution, `var`/`id`/`elementId` mint), the connector-bound condition-rule target, the placeholder stub, and root bindings. Stopping at this file produces a connector node with no `context` and no bindings, which `uip maestro case validate` reports as **Valid**.

<!-- END: connector-trigger-planning.md -->
