# `case spec --input-details` — JSON shape reference

> **Vendored from the CLI repo.** Canonical source: `packages/case-tool/docs/spec-input-details.md` in the `UiPath/cli` repo. Re-sync when the CLI's `--input-details` contract changes (the validators in `packages/case-tool/src/services/case-spec-input-validator.ts` are the source of truth).

`uip maestro case spec` accepts an optional `--input-details <json>` flag that pre-fills the generated `caseShape` with values the consumer already has on hand. Without the flag, `caseShape.inputs[*].body` are empty containers (default behavior); with it, they're populated and the filter (if any) is compiled and spliced into the FE-canonical sinks.

This document is the canonical reference for skills/agents that construct `--input-details` JSON.

---

## When to use it

- You're calling `case spec` to generate a connector task, AND you already know the values for body / query / path / event parameters AND/OR the filter the user wants to apply.
- The compiled `caseShape` will be ready to drop into the case JSON without an additional configure step.

If you don't yet have values, omit the flag — the default empty `caseShape` is the right shape for downstream substitution.

---

## Top-level shape per task type

### `--type activity`

```jsonc
{
    "bodyParameters":  {},   // optional — body request fields (dotted keys allowed)
    "queryParameters": {},   // optional — query string params
    "pathParameters":  {},   // optional — path-template substitutions
    "filter":          {}    // optional — FilterTree (compiles to CEQL)
}
```

### `--type trigger`

```jsonc
{
    "eventParameters": {},   // optional — design-time params scoping the trigger
    "filter":          {}    // optional — FilterTree (compiles to JMESPath)
}
```

Empty input details (`{}`) is valid and a no-op — equivalent to omitting the flag.

---

## Per-key reference

### `bodyParameters` (activity only)

Object keyed by field name. Dotted keys (`message.body.contentType`) get nested into structured objects via `nestDottedKeys` — that nesting is purely about how the CLI groups keys, NOT about the leaf value type.

> **Per-field leaf shape is connector-specific. Always read `inputs.bodyFields[].dataType` AND `description` from `case spec --skip-case-shape` before authoring a value.** Curated wrappers often expose a simplified leaf type (e.g. `string` with `description: "separated by comma(,)"`) where the underlying upstream API expects a structured object. Authoring the structured shape against a Curated wrapper produces a runtime failure even though the input JSON nests correctly through `nestDottedKeys`. The `dataType` + `description` returned by `case spec` are authoritative; the example below illustrates the dotted-key nesting mechanic only — different connectors and different operations on the same connector may type-narrow the same dotted-key path differently.

> **Array values are leaves** — pass arrays as their final shape, not via index syntax (`x[0]` is NOT supported). Whether a given field WANTS an array or a scalar is determined by `bodyFields[].dataType`, not by whether the field name suggests plurality.

**Example input** (Outlook 365 Send Email — the connector's curated contract declares every recipient leaf as `dataType: string` with `description: "separated by comma(,)"`, so the values below are plain comma-strings, not arrays of email-address objects):
```json
{
    "bodyParameters": {
        "message.subject": "Quarterly Review",
        "message.body.contentType": "Text",
        "message.body.content": "Please review the attached report.",
        "message.toRecipients": "alice@example.com,bob@example.com",
        "message.importance": "high"
    }
}
```

**What lands in `caseShape.inputs[name="body"].body`:**
```json
{
    "message": {
        "subject": "Quarterly Review",
        "body": {
            "contentType": "Text",
            "content": "Please review the attached report."
        },
        "toRecipients": "alice@example.com,bob@example.com",
        "importance": "high"
    }
}
```

A different Send Email-like operation (Microsoft Graph passthrough, Gmail API, custom connector) may declare its recipients via a different **field path** AND a different **leaf shape**. For example, the Graph passthrough POST `/messages` activity exposes `toRecipients[*].emailAddress.address` at the **top level** of `bodyParameters` (NOT under `message.`) with `dataType: string` per `[*]` array element; the wire result is `bodyParameters.toRecipients = [{"emailAddress":{"address":"…"}}]`. Always inspect `inputs.bodyFields[].name` AND `dataType` before authoring — do not assume path or shape from the field name alone.

**Rejected for synthetic HTTP request activities** (`objectName === "httpRequest"` / `"http-request"`) — the synthetic activity has no curated body schema.

### `queryParameters` (activity only)

Object keyed by query-string param name. Merged into the existing query body (so `case spec` defaults are preserved unless you override them).

```json
{
    "queryParameters": {
        "limit": 50,
        "$select": "subject,from,receivedDateTime"
    }
}
```

### `pathParameters` (activity only)

Object keyed by path-template variable name. Used for endpoints like `/UpdateEvent/{id}`.

```json
{
    "pathParameters": {
        "id": "AAMkAGI2..."
    }
}
```

### `eventParameters` (trigger only)

Object keyed by trigger event-parameter name. The CLI lands the raw values at `caseShape.inputs[name="body"].body.queryParams`. **Required** event-param values (per the trigger metadata's `events[<op>].required` flag) ALSO contribute to a derived **mandatory-filter expression** that gets AND-joined with the user's compiled `filter` to produce `body.filters.expression`. Optional event params don't contribute to the filter — they ride along in `queryParams` only.

This matches flow-tool's `configureTrigger` pattern (`packages/flow-tool/src/services/connector-service.ts:1051+` post uipcli #1880). The mandatory-filter expression is computed by the SDK's `buildMandatoryFilterExpression` which handles array `[*]` projection, type-aware literal formatting, and single-quote escape.

```json
{
    "eventParameters": {
        "parentFolderId": "Inbox"
    }
}
```

Produces in `caseShape.inputs[name="body"].body`:

```json
{
    "queryParams": { "parentFolderId": "Inbox" },
    "filters": { "expression": "(parentFolderId == 'Inbox')" }
}
```

When `filter` is also provided, the mandatory clause and user filter are AND-joined:

```json
{
    "queryParams": { "parentFolderId": "Inbox" },
    "filters": { "expression": "(parentFolderId == 'Inbox') && (<userFilterExpression>)" }
}
```

The same combined expression also lands at `caseShape.context[name="metadata"].body.activityPropertyConfiguration.filterExpression` so the design-time projection and runtime body don't drift.

For Outlook 365 `EMAIL_RECEIVED`, `parentFolderId` is required. The connector contract is in `caseShape.inputs.eventParameters[?required]` — consult that array to know which event params your trigger needs.

> **Note:** `body.parameters` is not emitted for triggers. The FE reserves that key for queryParameters/pathParameters, neither of which exists in the trigger input contract.

> **What NOT to do:** don't duplicate a connector-mandated event-param value in the freeform `filter` tree. The CLI AND-joins the mandatory expression automatically; duplicating the clause would double-apply it (e.g. `(parentFolderId == 'Inbox') && (parentFolderId == 'Inbox' && ...)`). Set required event-param values via `eventParameters` ONLY.

### `filter` (activity OR trigger)

Structured `FilterTree` — see [FilterTree shape](#filtertree-shape) below.

The CLI compiles the tree:
- **Activity** → CEQL string. Connector-specific filter param name (often `where`, sometimes `q`) resolved via the IS metadata's `FilterBuilder` design component.
- **Trigger** → JMESPath string.

**Note:** the CLI is the authoring side. You CANNOT pass `ceqlExpression` (activity) or `filterExpression` (trigger) directly — those are derived from the tree. Studio Web cannot reverse a string into a tree, so passing only the string would silently drop the filter on first SW open.

---

## FilterTree shape

```jsonc
{
    "groupOperator": "And" | "Or" | 0 | 1,   // REQUIRED — emit "And" even for a single-filter tree
    "index": 0,                              // 0 for the root tree
    "uuId": null,                            // FE assigns; null is fine when authoring
    "filters": [                             // 1+ Filter objects
        {
            "id":       "<field-name>",     // matches a name in caseShape.filter.fields[]
            "operator": "<FilterOperator>", // see operator list below
            "value": {
                "isLiteral": true,
                "rawString": "<json-encoded value>",
                "value":     <unknown>
            },
            "uiId": null
        }
    ],
    "groups": []                             // optional nested groups (FilterTree[])
}
```

**`groupOperator` accepts both string and numeric.** The IS SDK's `FilterGroupOperator` is a numeric enum (`And=0`, `Or=1`); the case-tool input layer normalizes string `"And"` / `"Or"` to numeric before threading the tree to the SDK compilers, so JSON authors can use either form. Numeric values pass through unchanged. Lowercase `"and"` / `"or"` is NOT normalized — the SDK will then fail to produce the expected joiner.

**`null` / missing `groupOperator` silently drops the filter expression.** The SDK's JMES/CEQL compilers (verbatim Studio Web ports) early-return an empty expression when `groupOperator == null`. The user filter tree still round-trips into `essentialConfiguration.filter` / `savedFilterTrees`, but the compiled JMESPath / CEQL string emitted to the runtime sinks (`body.filters.expression`, `activityPropertyConfiguration.filterExpression`, `inputs[name="queryParameters"].body.<filterParamName>`) will be empty — silently widening the trigger / activity to match every event or row. **Always emit `"And"` (or `"Or"`) — including for single-filter trees.** `And of one` and `Or of one` are semantically identical, so `"And"` is the safe default.

### `FilterOperator` (string enum)

```
Equals          NotEquals          LessThan        LessThanOrEqual
GreaterThan     GreaterThanOrEqual Contains        NotContains
IsOneOf         IsNotOneOf         StartsWith      NotStartsWith
EndsWith        NotEndsWith        IsEmpty         IsNotEmpty
Is              IsNot              DateTimeEquals  DateTimeNotEqual
After           AfterOrEqual       Before          BeforeOrEqual
In              NotIn              Like            NotLike
IsNull          IsNotNull
```

### `WorkflowValue`

Each `filters[].value` is a `WorkflowValue`:

```jsonc
{
    "isLiteral": true,                      // true for literal values; false when value is an expression
    "rawString": "\"Active\"",              // JSON-stringified value (preserves type round-trip)
    "value":     "Active"                   // the actual value
}
```

For string values, `rawString` includes outer quotes (`"\"Active\""`). For numbers / booleans / arrays, no extra quoting (`"100"`, `"true"`, `"[1,2,3]"`).

`value: null` is valid for `IsNull` / `IsNotNull` operators.

### Filter examples

**Single condition (still emit `"And"` — a `null` groupOperator silently drops the compiled expression):**
```json
{
    "filter": {
        "groupOperator": "And",
        "index": 0,
        "uuId": null,
        "filters": [
            {
                "id": "Status",
                "operator": "Equals",
                "value": { "isLiteral": true, "rawString": "\"Active\"", "value": "Active" },
                "uiId": null
            }
        ]
    }
}
```

**Multiple conditions joined by AND:**
```json
{
    "filter": {
        "groupOperator": "And",
        "index": 0,
        "uuId": null,
        "filters": [
            {
                "id": "Status",
                "operator": "Equals",
                "value": { "isLiteral": true, "rawString": "\"Active\"", "value": "Active" },
                "uiId": null
            },
            {
                "id": "AnnualRevenue",
                "operator": "GreaterThan",
                "value": { "isLiteral": true, "rawString": "100000", "value": 100000 },
                "uiId": null
            }
        ]
    }
}
```

**OR group with nested AND:**
```json
{
    "filter": {
        "groupOperator": "Or",
        "index": 0,
        "uuId": null,
        "filters": [],
        "groups": [
            {
                "groupOperator": "And",
                "index": 0,
                "uuId": null,
                "filters": [
                    { "id": "Status", "operator": "Equals", "value": {...}, "uiId": null },
                    { "id": "Region", "operator": "Equals", "value": {...}, "uiId": null }
                ]
            },
            {
                "groupOperator": "And",
                "index": 1,
                "uuId": null,
                "filters": [
                    { "id": "Priority", "operator": "Equals", "value": {...}, "uiId": null }
                ]
            }
        ]
    }
}
```

---

## Where each input value ends up in `caseShape`

### Activity sinks

| Input key | Output sink |
|---|---|
| `bodyParameters` | `caseShape.inputs[name="body"].body` (dotted-keys nested) |
| `queryParameters` | `caseShape.inputs[name="queryParameters"].body` (shallow-merged) |
| `pathParameters` | `caseShape.inputs[name="pathParameters"].body` (shallow-merged) |
| `filter` — tree | `essentialConfiguration.savedFilterTrees.<filterParamName>` inside `caseShape.context[name="metadata"].body.activityPropertyConfiguration.configuration` (parsed-mutated-stringified) |
| `filter` — compiled CEQL | `caseShape.inputs[name="queryParameters"].body.<filterParamName>` |

`<filterParamName>` is connector-specific (commonly `"where"`, Salesforce uses `"q"`). Resolved from IS metadata's `FilterBuilder` design component for the operation. If no FilterBuilder param exists, the filter is rejected.

### Trigger sinks

| Input key | Output sink |
|---|---|
| `eventParameters` (raw values) | `caseShape.inputs[name="body"].body.queryParams` |
| `eventParameters` (required only, equality clauses) | AND-prefixed onto the runtime + design-time `filterExpression` sinks below via the SDK's `buildMandatoryFilterExpression` |
| `filter` — tree | `essentialConfiguration.filter` inside `caseShape.context[name="metadata"].body.activityPropertyConfiguration.configuration` |
| `filter` — combined JMESPath (sink 1, FE projection) | `caseShape.context[name="metadata"].body.activityPropertyConfiguration.filterExpression` |
| `filter` — combined JMESPath (sink 2, runtime) | `caseShape.inputs[name="body"].body.filters.expression` |

The combined expression has the form `(mandatory) && (user)` when both are present, falling back to either side alone or omitted when both are empty. Mirrors flow-tool's `combinedFilterExpression` post uipcli #1880 (`packages/flow-tool/src/services/connector-service.ts:1051+`). Both sinks carry the same combined form so the design-time projection and runtime body don't drift.

Required vs optional event params: only **required** fields (per the trigger metadata's `events[<op>].required` flag) contribute to the mandatory-filter expression. Optional event-param values are emitted at `body.queryParams` only.

`body.parameters` is intentionally not emitted for triggers. The FE reserves that key for queryParameters/pathParameters merge, and the trigger input contract has neither.

---

## Validation rules (`InvalidInputDetailsError` on violation)

All errors include the offending field path and a remediation hint, formatted as a single multi-line string.

| Rule | Error |
|---|---|
| Unknown top-level key | `Unknown keys: <names>. Valid keys for <activity\|trigger>: <whitelist>` |
| `ceqlExpression` passed directly (activity) | `ceqlExpression is derived from the filter tree and cannot be provided directly` |
| `filterExpression` passed directly (trigger) | `filterExpression is derived from the filter tree and cannot be provided directly. Pass a structured "filter" (FilterTree) instead.` |
| `filter` + `queryParameters.where` together (activity) | ``queryParameters.where is derived from `filter` and cannot be set alongside it. Drop one of the two — prefer "filter" so Studio Web can re-render the filter widget.`` |
| `bodyParameters` not an object | `bodyParameters must be a JSON object` |
| `filter` not an object | `filter must be a JSON object (FilterTree)` |
| Activity has no FilterBuilder param but `filter` was provided | `Activity "<connectorKey>/<objectName>" does not declare a FilterBuilder parameter — server-side filtering is not supported by this operation. Drop "filter" from --input-details.` |
| Synthetic HTTP request activity + `bodyParameters` | `bodyParameters is not supported for synthetic HTTP request activities. Pass body via --input-details.queryParameters or omit.` |
| `--input-details` + `--skip-case-shape` together | `--input-details has no effect when --skip-case-shape is set; remove one of the two flags.` |
| Malformed JSON in `--input-details` | `Invalid --input-details JSON: <parse error>` |

---

## Worked examples

### Activity — Outlook 365 Send Email (no filter)

```bash
uip maestro case spec \
  --type activity \
  --activity-type-id c7ce0a96-2091-3d94-b16f-706ebb1eb351 \
  --connection-id <conn-uuid> \
  --input-details '{
    "bodyParameters": {
      "message.subject": "Quarterly Review",
      "message.body.contentType": "Text",
      "message.body.content": "Please review the attached report.",
      "message.importance": "high",
      "message.toRecipients": "alice@example.com,bob@example.com"
    }
  }'
```

### Activity — list operation with CEQL filter

```bash
uip maestro case spec \
  --type activity \
  --activity-type-id <list-typeid> \
  --connection-id <conn-uuid> \
  --input-details '{
    "queryParameters": { "limit": 50 },
    "filter": {
      "groupOperator": "And",
      "index": 0,
      "uuId": null,
      "filters": [
        {
          "id": "Status",
          "operator": "Equals",
          "value": { "isLiteral": true, "rawString": "\"Active\"", "value": "Active" },
          "uiId": null
        }
      ]
    }
  }'
```

### Activity — path + query params (Get Email By ID)

```bash
uip maestro case spec \
  --type activity \
  --activity-type-id <get-email-by-id-typeid> \
  --connection-id <conn-uuid> \
  --input-details '{
    "pathParameters": { "id": "AAMkAGI2..." },
    "queryParameters": { "$select": "subject,from,receivedDateTime" }
  }'
```

### Trigger — Outlook 365 Email Received (no filter)

```bash
uip maestro case spec \
  --type trigger \
  --activity-type-id 7dc57f24-894c-5ae2-a902-66056fa40609 \
  --connection-id <conn-uuid> \
  --input-details '{
    "eventParameters": { "parentFolderId": "Inbox" }
  }'
```

### Trigger — with JMESPath filter

```bash
uip maestro case spec \
  --type trigger \
  --activity-type-id 7dc57f24-894c-5ae2-a902-66056fa40609 \
  --connection-id <conn-uuid> \
  --input-details '{
    "eventParameters": { "parentFolderId": "Inbox" },
    "filter": {
      "groupOperator": "And",
      "index": 0,
      "uuId": null,
      "filters": [
        {
          "id": "subject",
          "operator": "Contains",
          "value": { "isLiteral": true, "rawString": "\"urgent\"", "value": "urgent" },
          "uiId": null
        },
        {
          "id": "hasAttachments",
          "operator": "Equals",
          "value": { "isLiteral": true, "rawString": "true", "value": true },
          "uiId": null
        }
      ]
    }
  }'
```

---

## Discovery — what fields can a skill fill in?

Before constructing `--input-details`, run `case spec` once WITHOUT it (use `--skip-case-shape` for a leaner response that omits `caseShape`) and read:

| Looking for | Read |
|---|---|
| Required body fields | `inputs.bodyFields[?required]` |
| Required path/query params | `inputs.pathParameters[?required]`, `inputs.queryParameters[?required]` |
| Required trigger event params | `inputs.eventParameters[?required]` |
| Filter field names | `filter.fields[*].name` (also `searchableOperators[]`, `searchableNames[]`, `enum[]`) |
| Whether the activity supports filter | `filter` present in spec output → yes |

Then construct `--input-details` referencing those names.

---

## Things `--input-details` does NOT touch

- **Connection identity** (`connectionId`, `folderKey`, `connectorKey`, `objectName`, `httpMethod`, `eventType`, `eventMode`) — these come from `--connection-id` + the resolved TypeCache entry. The skill does not pass them in `--input-details`.
- **Bindings** — `caseShape.context[]` continues to emit `{{CONN_BINDING_ID}}` and `{{FOLDER_BINDING_ID}}` placeholders for the skill to substitute later when minting binding ids.
- **`caseShape.outputs[]`** — outputs are derived from the connector schema, not user input. `--input-details` only touches `inputs[]` and the filter sinks inside `context[]`.

---

## Comparison with flow-tool's `--detail`

For reference. See `packages/flow-tool/src/services/connector-service.ts:286-433` for the analogous flow validators.

| Concept | flow `--detail` | case `--input-details` |
|---|---|---|
| Connection identity | required (`connectionId`, `folderKey`) | not in input — comes from `--connection-id` |
| HTTP method / endpoint | required (`method`, `endpoint`) | not in input — comes from TypeCache |
| Event mode | required (`eventMode`) | not in input — comes from TypeCache |
| Body params | `bodyParameters` | `bodyParameters` ✓ same |
| Query params | `queryParameters` | `queryParameters` ✓ same |
| Path params | `pathParameters` | `pathParameters` ✓ same |
| Event params | `eventParameters` | `eventParameters` ✓ same |
| Filter tree | `filter` (FilterTree) | `filter` ✓ same |
| Compiled expression | rejected | rejected ✓ same |
| Filter compile | `buildCeqlFilter` / `buildFilter` | `buildCeqlFilter` / `buildFilter` ✓ same |

The case version is a strict subset — the static identity fields are removed because they're derived from the spec call's other inputs (`--type`, `--activity-type-id`, `--connection-id`).
