# `case spec --input-details` — JSON shape reference

> **Vendored from the CLI repo.** Canonical source: `packages/case-tool/docs/spec-input-details.md` in the `UiPath/cli` repo. Re-sync when the CLI's `--input-details` contract changes (the validators in `packages/case-tool/src/services/case-spec-input-validator.ts` are the source of truth).

`uip maestro case spec` accepts an optional `--input-details <json>` flag that pre-fills the generated `caseShape` with values the consumer already has on hand. Without the flag, `caseShape.inputs[*].body` are empty containers (default behavior); with it, they're populated and the filter (if any) is compiled and spliced into the FE-canonical sinks.

This document is the skill's reference for constructing `--input-details` JSON.

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

Object keyed by field name. Dotted keys (`message.body.contentType`) get nested into structured objects via `nestDottedKeys`. Array values are leaves — pass arrays as their final shape, not via index syntax (`x[0]` is NOT supported).

**Example input:**
```json
{
    "bodyParameters": {
        "message.subject": "Quarterly Review",
        "message.body.contentType": "Text",
        "message.body.content": "Please review the attached report.",
        "message.toRecipients": [
            { "emailAddress": { "address": "alice@example.com" } }
        ],
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
        "toRecipients": [
            { "emailAddress": { "address": "alice@example.com" } }
        ],
        "importance": "high"
    }
}
```

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

Object keyed by trigger event-parameter name. Lands at `caseShape.inputs[name="body"].body.parameters`.

```json
{
    "eventParameters": {
        "parentFolderId": "Inbox"
    }
}
```

For Outlook 365 `EMAIL_RECEIVED`, `parentFolderId` is required. The connector contract is in `caseShape.inputs.eventParameters[?required]` — consult that array to know which event params your trigger needs.

### `filter` (activity OR trigger)

Structured `FilterTree`. Tree shape, `FilterOperator` enum (28 operators), `WorkflowValue` shape, anti-patterns, and worked examples (single / multi-AND / OR-with-nested-AND): [/uipath:uipath-platform — Filter Trees (CEQL)](../../uipath-platform/references/integration-service/activities.md#filter-trees-ceql). Tree shape is identical for triggers — only the compiler output differs (CEQL for activities, JMESPath for triggers).

The CLI compiles the tree at the authoring boundary:
- **Activity** → CEQL string. Connector-specific filter param name (often `where`, sometimes `q`) is resolved via the IS metadata's `FilterBuilder` design component.
- **Trigger** → JMESPath string.

**Case-specific quirk — `groupOperator` accepts string OR numeric.** The IS SDK's `FilterGroupOperator` is a numeric enum (`And=0`, `Or=1`); the case-tool input layer normalizes string `"And"` / `"Or"` to numeric before threading the tree to the SDK compilers, so JSON authors can use either form. `null` and numeric values pass through unchanged. Lowercase `"and"` / `"or"` is NOT normalized — the SDK then fails to produce the expected joiner. (The platform examples use string form.)

**Note:** the CLI is the authoring side. You CANNOT pass `ceqlExpression` (activity) or `filterExpression` (trigger) directly — those are derived from the tree. Studio Web cannot reverse a string into a tree, so passing only the string would silently drop the filter on first SW open.

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
| `eventParameters` | `caseShape.inputs[name="body"].body.parameters` |
| `filter` — tree | `essentialConfiguration.filter` inside `caseShape.context[name="metadata"].body.activityPropertyConfiguration.configuration` |
| `filter` — compiled JMESPath (sink 1, FE projection) | `caseShape.context[name="metadata"].body.activityPropertyConfiguration.filterExpression` |
| `filter` — compiled JMESPath (sink 2, runtime) | `caseShape.inputs[name="body"].body.filters.expression` |

The trigger filter expression is duplicated in two non-config sinks because both have load-bearing roles: SW reads `activityPropertyConfiguration.filterExpression` for the design-time summary; the runtime reads `body.filters.expression` to evaluate against incoming events. Mirroring flow's `configureTrigger` write semantics.

---

## Validation rules (`InvalidInputDetailsError` on violation)

All errors include the offending field path and a remediation hint, formatted as a single multi-line string.

| Rule | Error |
|---|---|
| Unknown top-level key | `Unknown keys: <names>. Valid keys for <activity\|trigger>: <whitelist>` |
| `ceqlExpression` passed directly (activity) | `ceqlExpression is derived from the filter tree and cannot be provided directly` |
| `filterExpression` passed directly (trigger) | `filterExpression is derived from the filter tree and cannot be provided directly. Pass a structured "filter" (FilterTree) instead.` |
| `filter` + `queryParameters.where` together (activity) | `queryParameters.where is derived from "filter" and cannot be set alongside it. Drop one of the two — prefer "filter" so Studio Web can re-render the filter widget.` |
| `bodyParameters` not an object | `bodyParameters must be a JSON object` |
| `filter` not an object | `filter must be a JSON object (FilterTree)` |
| Activity has no FilterBuilder param but `filter` was provided | `Activity "<type>" does not declare a FilterBuilder parameter — server-side filtering is not supported by this operation. Drop "filter" from --input-details.` |
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
      "message.toRecipients": [
        { "emailAddress": { "address": "alice@example.com" } }
      ]
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
