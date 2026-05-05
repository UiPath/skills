# connector-activity task — Planning

A connector activity task inside a stage. Calls an external service (Jira, Slack, Salesforce, Gmail, etc.) via UiPath Integration Service.

This plugin is **schema-data-driven** — one plugin covers every connector. Connector-specific input shapes are discovered from the `case spec` CLI's normalized output, not baked into this plugin.

## When to Use

Pick this plugin when the sdd.md describes a task as `CONNECTOR_ACTIVITY` or names a specific external service action (e.g., "send a Slack message", "create a Jira issue", "update Salesforce opportunity").

For **connector-based triggers** inside a stage (wait for an external event), use [connector-trigger](../connector-trigger/planning.md).

For **case-level event triggers** (outside any stage), use [`plugins/triggers/event/`](../../triggers/event/planning.md).

## Resolution Pipeline

Run these steps during planning. Each step feeds into the `tasks.md` entry.

### 1. Find the connector in TypeCache

If `~/.uip/case-resources/typecache-activities-index.json` does not exist, run `uip maestro case registry pull` first (missing file is a precondition failure, not a 0-match — Rule 17 gate does not apply). If still missing after pull, the tenant has no connector activities — emit skeleton per § Unresolved Fallback below.

Read `~/.uip/case-resources/typecache-activities-index.json` directly. Match on `displayName` or `connectorKey` + operation description from sdd.md. Record `uiPathActivityTypeId`.

### 2. Resolve the connection

```bash
uip maestro case registry get-connection \
  --type typecache-activities \
  --activity-type-id "<uiPathActivityTypeId>" --output json
```

Returns `Entry`, `Config`, and `Connections`.

- **Single connection** → use it.
- **Multiple connections** → **AskUserQuestion** with connection names + "Something else".
- **Empty `Connections`** → mark `<UNRESOLVED: no IS connection for <connectorKey>>` and omit `input-values:`. Execution creates a skeleton task — see [skeleton-tasks.md](../../../skeleton-tasks.md).

Record `connection-id`, `connector-key`, `object-name` from the response.

Connection selection rules (default-preference, `--refresh` retry, multi-connection disambiguation, ping verification, BYOA workflow): see [/uipath:uipath-platform — connections.md](../../../../../uipath-platform/references/integration-service/connections.md).

### 3. Discover the operation contract via `case spec`

One CLI call replaces the legacy `case tasks describe` + `is resources describe` dance:

```bash
uip maestro case spec --type activity \
  --activity-type-id "<uiPathActivityTypeId>" \
  --connection-id "<connection-id>" \
  --skip-case-shape \
  --output json
```

`--skip-case-shape` returns a leaner response (no `caseShape`) — the right size for planning. Phase 3 re-runs the same command without the flag, plus `--input-details`, to mint the populated `caseShape`. See [`case-spec-input-details.md`](../../../case-spec-input-details.md) for the full `--input-details` JSON contract.

> **Synthetic HTTP request branch.** When `spec.identity.objectName` is `"httpRequest"` or `"http-request"`, the activity is the synthetic generic-HTTP path — `bodyParameters` is rejected (no curated body schema). Pass HTTP body via `queryParameters` instead, or omit. Spec output reflects this in `inputs.bodyFields = []`.

The response carries everything the planning phase needs:

| Spec output | What it tells you |
|---|---|
| `inputs.bodyFields[]` | Body request fields with `name` (dotted), `dataType`, `required`, `description`, optional `defaultValue` / `enum` / `reference` |
| `inputs.pathParameters[]`, `inputs.queryParameters[]` | URL-template substitutions and query-string params with the same per-field shape |
| `inputs.multipart` | `null` for non-multipart; otherwise `{ bodyFieldName, parameters[] }` — multipart upload contract |
| `outputs.responseFields[]` | Response shape; `[?responseCurated]` are FE-broken-out outputs, `[?primaryKey]` are id fields |
| `outputs.pagination` | `null` for non-list, `{ maxPageSize: N }` for list operations |
| `filter` | `undefined` when the activity does NOT support server-side filtering. Present when it does, with `builder: "ceql"` and `fields[]` listing every searchable field |
| `references[]` | Cross-references (lookups). Each entry includes a pre-built `discoverCommand` runnable string |
| `diagnostics.fetched` / `fallbacks` | What endpoints succeeded / fell back; surface `fallbacks` to the user when meaningful |

### 4. Resolve reference fields

Check `inputs.{bodyFields, pathParameters, queryParameters}` for entries with a `reference` object. Each carries a pre-built `discoverCommand`:

```jsonc
"reference": {
    "objectName": "MailFolder",
    "lookupValue": "id",
    "lookupNames": ["displayName"],
    "discoverCommand": "uip is resources execute list uipath-microsoft-outlook365 MailFolder --connection-id <id>"
}
```

Run the `discoverCommand` exactly as given. Match the sdd.md value to `lookupNames[0]` in the results. Use the resolved `lookupValue` (the id) in `input-values`.

> **Reference IDs are connection-scoped.** Resolve every reference field freshly against the current `--connection-id`, immediately before writing tasks.md. Never reuse an ID resolved against a different connection — silent runtime fault. Full mechanism: [/uipath:uipath-platform — reference-resolution.md § Reference IDs Are Connection-Scoped (CRITICAL)](../../../../../uipath-platform/references/integration-service/reference-resolution.md#reference-ids-are-connection-scoped-critical).

> **Paginate when looking up by name.** `execute list` returns one page (up to 1000 items); check `Data.Pagination.HasMore` + `Data.Pagination.NextPageToken`. Re-run with `--query "nextPage=<NextPageToken>"` until found or `HasMore` is `"false"`. Short-circuit on first match.

If a reference cannot be resolved, **AskUserQuestion** with the candidates (dropdown when finite set, plus "Something else"). Do not guess.

### 5. Validate required fields (HARD GATE)

This is a hard gate — do NOT proceed to writing tasks.md until every required field has a value.

1. Collect every `inputs.*[?required]` entry from the spec output (across `bodyFields`, `pathParameters`, `queryParameters`).
2. For each, check whether sdd.md names a value (literal, variable reference, or cross-task output).
3. If missing and no `defaultValue`, **AskUserQuestion** — list the missing fields with their `displayName` and what kind of value is expected.
4. Free-form input is appropriate when the value space is open-ended (channel names, message bodies, IDs); when a finite set of sensible values exists (e.g. an `enum`), present them via AskUserQuestion per the dropdown rule in [SKILL.md](../../../../SKILL.md).
5. Only after all required fields have values, proceed to step 6.

> **Do NOT guess or skip missing required fields.** A missing required field will cause a runtime error. It is always better to ask than to assume.

### 6. Map SDD inputs to connector fields

SDD input names rarely match connector field names exactly. Match each SDD input to a `bodyFields`/`pathParameters`/`queryParameters` entry by comparing the SDD field name against the `displayName` (or `name`) from Step 3.

For each required field in spec.inputs.*, there must be a matching SDD input. If a required field has no match, **AskUserQuestion** — never leave required fields unmapped.

Values can be:
- **Static literals** — `"Payment__c"`, `"Text"`, `42`
- **Resolved reference IDs** — from Step 4
- **Case variable references** — `=vars.X` for runtime values
- **Expressions** — `=js:()` only when operators are needed

### 7. Optional — author a server-side filter

If `spec.filter` is present (i.e. the operation declares a `FilterBuilder` parameter and supports CEQL), the user can author a filter tree. If `spec.filter` is `undefined`, server-side filtering is not supported on this operation — filter downstream (post-execution) instead.

Filter tree shape, operator table, anti-patterns, worked examples: [/uipath:uipath-platform — Filter Trees (CEQL)](../../../../../uipath-platform/references/integration-service/activities.md#filter-trees-ceql). Same shape applies to triggers (compiler differs — JMESPath instead of CEQL).

The filter tree goes into `tasks.md` under `filter:` as a literal JSON object — Phase 3 passes it to `case spec --input-details`. Do NOT pass a raw CEQL string under `queryParameters.where` (or whichever connector-specific name) when authoring a filter — case-tool rejects this at configure time, and the round-trip from Studio Web breaks.

### 8. Build input-values

Using the mapped fields from Step 6, build the `input-values` JSON with dot-path field names from `inputs.bodyFields[].name`:

```json
{
    "bodyParameters": {"message.toRecipients": "=vars.managerEmail", "message.subject": "=vars.caseId", "message.body.content": "=vars.description", "message.body.contentType": "Text"},
    "queryParameters": {"limit": 50},
    "pathParameters":  {"id": "AAMkAGI..."}
}
```

Dotted keys (`message.body.content`) get nested into structured objects via `nestDottedKeys` at Phase 3 mint time — the planner just records the dotted form. Array values are leaves; pass them as the final shape, not via `key[0]` syntax.

## tasks.md Entry Format

```markdown
## T<n>: Add connector-activity task "<display-name>" to "<stage>"
- type-id: <uiPathActivityTypeId>
- connection-id: <connection-uuid>
- connector-key: <connectorKey>
- object-name: <objectName>
- input-values: {"bodyParameters":{...},"queryParameters":{...},"pathParameters":{...}}
- filter: {"groupOperator":"And","index":0,"uuId":null,"filters":[{"id":"Status","operator":"Equals","value":{"isLiteral":true,"rawString":"\"Active\"","value":"Active"},"uiId":null}]}
- isRequired: true
- runOnlyOnce: false
- order: after T<m>
- lane: <n>
- verify: Confirm task created with correct inputs
```

`filter:` is optional and present only when the operation supports CEQL (i.e. `spec.filter` was non-null in step 7).

## Unresolved Fallback

> **Rule 17 exception.** Empty `Connections` from `get-connection` (the connector activity exists in typecache but no IS connection is registered) does NOT require the Rule 17 gate — proceed directly to skeleton.

If the connector or connection cannot be resolved:
- Mark `type-id` or `connection-id` with `<UNRESOLVED: reason>`
- Omit `input-values:` entirely — no schema to wire against
- Execution creates a skeleton task (display-name + type only) per [skeleton-tasks.md](../../../skeleton-tasks.md)
