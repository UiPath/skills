# connector-activity task — Planning

A connector activity task inside a stage. Calls an external service (Jira, Slack, Salesforce, Gmail, etc.) via UiPath Integration Service.

This file is the planning owner for activity TypeCache discovery, connection selection, required/reference input mapping, and the activity T-entry. One schema-driven procedure covers every connector activity.

## When to Use

Pick this plugin when the sdd.md describes a task as `CONNECTOR_ACTIVITY` or names a specific external service action (e.g., "send a Slack message", "create a Jira issue", "update Salesforce opportunity").

Connector event targets use the shared trigger owner instead; do not load their target files while planning an activity.

## Resolution Pipeline

Run these steps during planning. Each step feeds into the `tasks.md` entry.

### 1. Find the connector in TypeCache

Consume Rule 3 and Rule 17 without redefining them. Before a successful current-session pull, a missing `~/.uip/case-resources/typecache-activities-index.json` is a failed precondition; complete the normal login + pull gate once. After success, a still-missing index or empty exact-name match is a genuine zero-match item in the one Rule 17 batch. Label it `placeholder only`; run `registry pull --force` only from the user's Force-pull branch.

Read `~/.uip/case-resources/typecache-activities-index.json` directly. Match on `displayName` or `connectorKey` + operation description from sdd.md. Record `uiPathActivityTypeId`.

**No match (Scenario A — connector not found).** Add it to the canonical Rule 17 lookup batch. Only when that batch assigns the non-creatable connector to fallback (`Use placeholders for all`, or the mixed Create branch) mark `type-id` `<UNRESOLVED: no typecache activity for <query>>`, skip §2, and use § Unresolved Fallback. Continue planning.

### 2. Resolve the connection

```bash
uip maestro case registry get-connection \
  --type typecache-activities \
  --activity-type-id "<uiPathActivityTypeId>" --output json
```

Returns `Entry`, `Config`, and `Connections`. If the sdd.md names a connection, match it by `name` and use it directly. Otherwise **always present the choice via AskUserQuestion — do not auto-select**, even when one connection exists:

- **`Connections` non-empty** → list connections by `name` **plus a "Create a new connection" option**.
- **`Connections` empty** → offer **Create a new connection** / **Skip (defer)**.
- **Create chosen** → run `uip is connections create "<Config.connectorKey>" --output json` in the background and use `Data.ConnectionId` directly. Non-zero exit, `Result: Failure`, or missing ID is failure: surface `Message`/`Instructions`, offer Retry / Skip, and fall back only after Skip or repeated failure.
- **Skip / create fails** → mark `<UNRESOLVED: no IS connection for <connectorKey>>` and omit `input-values:` ([§ Unresolved Fallback](#unresolved-fallback)).

Record `connection-id`, `connector-key`, and `object-name` from the response (or from the create output).

When `Config.activityType === "Generic"`, the TypeCache entry is shared across objects and its object name is not sufficient. Discover candidates and verify the selected object against this connection:

```bash
uip is resources list "<Config.connectorKey>" \
  --connection-id "<connection-id>" --output json
uip is resources describe "<Config.connectorKey>" "<selected-object>" \
  --connection-id "<connection-id>" --output json
```

Use an exact SDD object match; otherwise ask from the returned candidates. Persist the selection as `object-name`. If no object can be selected, mark both `type-id` and `object-name` `<UNRESOLVED: no selectable Generic object>` so Phase 2 takes this activity's placeholder. A Generic activity must pass the selected `object-name` to both `case spec` calls.

An empty `Connections` list is not a Rule 17 zero: the connector type exists, so offer creation first and use this activity's placeholder only after decline/failure.

### 3. Discover the operation contract via `case spec`

One CLI call replaces the legacy `case tasks describe` + `is resources describe` dance:

```bash
uip maestro case spec --type activity \
  --activity-type-id "<uiPathActivityTypeId>" \
  --connection-id "<connection-id>" \
  --object-name "<object-name when present; required for Generic>" \
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

If `inputs.multipart` is non-null, load only [complex inputs § Multipart planning](complex-inputs-guide.md#multipart-planning) for that branch. Otherwise do not load the guide for multipart handling.

### 4. Resolve reference fields

Check `inputs.{bodyFields, pathParameters, queryParameters}` for entries with a `reference` object. Each carries a pre-built `discoverCommand`:

```jsonc
"reference": {
    "objectName": "MailFolder",
    "lookupValue": "id",
    "lookupNames": ["displayName"],
    "discoverCommand": "uip is resources run list uipath-microsoft-outlook365 MailFolder --connection-id <id> --output json"
}
```

Run the `discoverCommand` exactly as given. Match the sdd.md value to `lookupNames[0]` in the results. Use the resolved `lookupValue` (the id) in `input-values`.

> **Reference IDs are connection-scoped.** Resolve every reference field freshly against the current `--connection-id`, immediately before writing tasks.md. Never reuse an ID resolved against a different connection.

> **Paginate when looking up by name.** `run list` returns one page (up to 1000 items); check `Data.Pagination.HasMore` + `Data.Pagination.NextPageToken`. Re-run with `--query "nextPage=<NextPageToken>"` until found or `HasMore` is `"false"`. Short-circuit on first match.

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

An SDD input that matches `spec.inputs.*` remains a normal Step 6 input even when its name is literally `filter`: include it in `input-values`; Step 7 applies only when the SDD separately requests a structured filter tree and `spec.filter` supports one.

For each required field in spec.inputs.*, there must be a matching SDD input. If a required field has no match, **AskUserQuestion** — never leave required fields unmapped.

Values can be:
- **Static literals** — `"Payment__c"`, `"Text"`, `42`
- **Resolved reference IDs** — from Step 4
- **Case variable references** — `=vars.X` (impl wraps as `=js:(vars.X)` for the connector body sink before passing to the CLI)
- **Metadata references** — `=metadata.X` (impl wraps as `=js:(metadata.X)`)
- **Pre-wrapped operator expressions** — `=js:(vars.amount > 5000)` (already canonical — pass-through)
- **Cross-task refs** — `<- "Stage"."Task".output` (impl resolves through the common [output-reference-ID algorithm](../../variables/io-binding/impl-json.md#output-reference-id-authoritative) to `=vars.<outputReferenceId>`, then wraps)

> **tasks.md carries SDD-natural form.** The implementation step (Step 9.7 of connector-activity impl) rewrites every reference to its canonical sink form when constructing `--input-details`. Connector body sinks use `=js:(<expr>)`. Full rule: [bindings-and-expressions.md § Canonical form per sink](../../../bindings-and-expressions.md#canonical-form-per-sink).

### 7. Optional — author a server-side filter

When the SDD requests a server-side filter and `spec.filter` is present, load [complex inputs § Server-side FilterTree](complex-inputs-guide.md#server-side-filtertree). If either condition is false, do not load the guide; omit `filter:` and filter downstream when needed.

### 8. Build input-values

Using the mapped fields from Step 6, build the `input-values` JSON with dot-path field names from `inputs.bodyFields[].name`:

```json
{
    "bodyParameters": {"message.toRecipients": "=vars.managerEmail", "message.subject": "=vars.caseId", "message.body.content": "=vars.description", "message.body.contentType": "Text"},
    "queryParameters": {"limit": 50},
    "pathParameters":  {"id": "AAMkAGI..."}
}
```

Dotted keys (`message.body.content`) get nested into structured objects via `nestDottedKeys` at Phase 3 mint time — the planner just records the dotted form.

#### Array-of-object body fields — SDD authors business shape; planner translates to wire shape

If any resolved `inputs.bodyFields[].name` contains `[*]`, load [complex inputs § Array-of-object body fields](complex-inputs-guide.md#array-of-object-body-fields) before emitting `bodyParameters`. Otherwise do not load the guide for array translation.

## tasks.md Entry Format

Populate `outputs:` using the shared [I/O-binding output-list contract](../../variables/io-binding/planning.md#canonical-tasksmd-output-list).

```markdown
## T<n>: Add connector-activity task "<display-name>" to "<stage>"
- type-id: <uiPathActivityTypeId>
- connection-id: <connection-uuid>
- connector-key: <connectorKey>
- object-name: <objectName>
- input-values: {"bodyParameters":{...},"queryParameters":{...},"pathParameters":{...}}
- file-inputs: {"<multipart parameter name>":"=vars.<file Case-variable id>"}   # multipart only; omit otherwise; authored by the conditional guide
- filter: {"groupOperator":"And","index":0,"uuId":null,"filters":[{"id":"Status","operator":"Equals","value":{"isLiteral":true,"rawString":"\"Active\"","value":"Active"},"uiId":null}]}
- outputs:                            # optional; omit only when the SDD declares none
  - <SDD output row, copied verbatim>
- isRequired: true
- runOnlyOnce: false
- activation-mode: <sequential|parallel|parallel-after-predecessor|event-triggered|adhoc|fan-in|conditional-gate>   # required
- entry-rule: <copy the matching supplied/approved SDD task-entry rule>   # required; legality: ../../conditions/task-entry-conditions/planning.md#phase-1-plan-presentation-contract
- rationale: "<copy the supplied/approved SDD rationale>"   # required
- order: after T<m>
- lane: <n>
- verify: tasks.md `input-values` covers every `inputs.*[?required]` from the lean spec across `bodyFields`, `queryParameters`, `pathParameters` — see Step 5 above.
```

`filter:` is optional and present only when the operation supports CEQL (i.e. `spec.filter` was non-null in step 7).

## Unresolved Fallback

Two entry paths: **Scenario A** — a TypeCache zero assigned to placeholder by the canonical Rule 17 batch; **Scenario B** — the connector exists but its connection creation offer is declined or fails. An empty `Connections` list takes Scenario B only after that offer; it is never a TypeCache zero.

If the connector, connection, or required Generic object cannot be resolved:
- Mark the blocking `type-id`, `connection-id`, or `object-name` with `<UNRESOLVED: reason>`; an unresolved required object also marks `type-id` so placeholder dispatch is unambiguous
- Omit `input-values:` entirely — no schema to wire against
- Execution creates a placeholder task (display-name + type only) per [placeholder-tasks.md](../../../placeholder-tasks.md)

<!-- END: planning.md -->
