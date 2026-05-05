# Connector Integration Reference

Procedure for resolving connector activity and connector trigger tasks against UiPath Integration Service. Shared between the `connector-activity` and `connector-trigger` task plugins and the `event` trigger plugin.

## When to Use

Consult this reference when planning or implementing any of:

- `connector-activity` task — see [`plugins/tasks/connector-activity/impl-json.md`](plugins/tasks/connector-activity/impl-json.md)
- `connector-trigger` task — see [`plugins/tasks/connector-trigger/impl-json.md`](plugins/tasks/connector-trigger/impl-json.md)
- `event` case-level trigger — see [`plugins/triggers/event/impl-json.md`](plugins/triggers/event/impl-json.md)

## Prerequisites

1. `uip login` — tenant-scoped connectors are only visible after authentication.
2. `uip maestro case registry pull` — populates `typecache-activities-index.json` and `typecache-triggers-index.json` at `~/.uipcli/case-resources/`.
3. A healthy Integration Service connection must exist for the connector. If `Connections` is empty after `get-connection`, the user must create one in IS before proceeding.

Connection selection rules (default-preference, `--refresh` retry, multi-connection disambiguation, ping verification, BYOA workflow): see [/uipath:uipath-platform — connections.md](../../uipath-platform/references/integration-service/connections.md).

## Resolution Pipeline

For every connector task or event trigger, run these CLI metadata fetches in order. Each call feeds the next; the populated `caseShape` from `case spec` is written directly into `caseplan.json` per the plugin's `impl-json.md` — there is no `tasks add-connector` mutation step.

### Step 1 — Find the activity-type-id

Read the relevant TypeCache index file directly (CLI `registry search` has known gaps — see [registry-discovery.md](registry-discovery.md)).

| Target | Cache file | Identifier field |
|--------|-----------|------------------|
| Connector activity | `typecache-activities-index.json` | `uiPathActivityTypeId` |
| Connector trigger | `typecache-triggers-index.json` | `uiPathActivityTypeId` |

Match on `displayName` from the sdd.md. **Skip entries without a `uiPathActivityTypeId`** — non-connector activities are not supported as case tasks.

### Step 2 — Resolve the connection

```bash
uip maestro case registry get-connection --type <typecache-activities|typecache-triggers> \
  --activity-type-id "<uiPathActivityTypeId>" --output json
```

Output: `{ Entry, Config, Connections }` where:

- `Entry` — the raw TypeCache entry, including `displayName`, `configuration`.
- `Config.connectorKey` — the Integration Service connector identifier (e.g., `gmail`, `uipath-atlassian-jira`).
- `Config.objectName` — the specific operation (e.g., `message`, `issue`).
- `Connections[]` — array of `{ id, name }` objects.

**Selection rules (in priority order):**

1. If the sdd.md names a specific connection, match by `name`. Use that `id`.
2. If the sdd.md is silent and exactly one connection exists, use it.
3. If multiple connections exist and sdd.md is silent, use **AskUserQuestion** with a bounded list of connection names + "Something else".
4. If `Connections` is empty, mark the task `<UNRESOLVED: no IS connection for <connectorKey>>` in `tasks.md` and omit `input-values:`. Execution writes a skeleton connector task — `type` + `displayName` + `data: {}`, no `data.typeId` / `data.connectionId` keys. Tell the user in the completion report to create the connection in the IS portal before the task can run. See [skeleton-tasks.md](skeleton-tasks.md).

### Step 3 — Discover the operation contract via `case spec`

One CLI call replaces the legacy `case tasks describe` + `is resources describe` dance:

```bash
# Planning phase — PLANNING_SECTIONS bundle (no caseShape, no diagnostics, no essentialConfiguration)
uip maestro case spec --type <activity|trigger> \
  --activity-type-id "<uiPathActivityTypeId>" \
  --connection-id "<connection-id>" \
  --sections identity,operation,connection,inputs,outputs,filter,webhook,references \
  --output json

# Phase 3 (implementation) — IMPLEMENTATION_SECTIONS bundle, populated caseShape from --input-details
uip maestro case spec --type <activity|trigger> \
  --activity-type-id "<uiPathActivityTypeId>" \
  --connection-id "<connection-id>" \
  --sections identity,connection,caseShape \
  --input-details "<json>" --output json
```

Spec output carries the full operation contract:

| Spec output | What it tells you |
|---|---|
| `inputs.bodyFields[]` | Body request fields with `name` (dotted), `dataType`, `required`, `description`, `defaultValue`, `enum`, `reference` |
| `inputs.{path,query}Parameters[]` | URL-template substitutions and query-string params with the same per-field shape |
| `inputs.eventParameters[]` | Trigger-only design-time scoping params |
| `inputs.multipart` | `null` for non-multipart; `{ bodyFieldName, parameters[] }` otherwise |
| `outputs.responseFields[]` | Response shape; `[?responseCurated]` are FE-broken-out outputs, `[?primaryKey]` are id fields |
| `outputs.pagination` | `null` for non-list; `{ maxPageSize: N }` for list ops |
| `filter` | `undefined` when server-side filtering is not supported. Present when supported, with `builder: "ceql"` (activity) / `"jmes"` (trigger) and `fields[]` listing every searchable field |
| `references[]` | Cross-references with pre-built `discoverCommand` runnable strings |
| `caseShape` | FE-canonical `inputs[]` / `outputs[]` / `context[]` ready to drop into `caseplan.json` (after binding-id substitution); only present when `caseShape` ∈ `--sections` (or `--sections` omitted) |
| `diagnostics` | Per-endpoint `fetched` / `fallbacks`. Opt-in only — appended via `--sections ...,diagnostics` when an audit trail is needed |

Full input-details contract (the `--input-details` JSON shape): [`case-spec-input-details.md`](case-spec-input-details.md).

### Step 4 — Resolve reference fields

Each `inputs.*` entry with a `reference` carries a pre-built `discoverCommand`:

```jsonc
"reference": {
    "objectName": "MailFolder",
    "lookupValue": "id",
    "lookupNames": ["displayName"],
    "discoverCommand": "uip is resources execute list <connector> <object> --connection-id <id>"
}
```

Run the `discoverCommand` exactly as given. Match the sdd.md value to `lookupNames[0]` in the results. Use the resolved `lookupValue` (the id) in `input-values`.

> **Reference IDs are connection-scoped.** Resolve every reference field freshly against the current `--connection-id`, immediately before writing tasks.md / minting the spec. Never reuse an ID resolved against a different connection — silent runtime fault. Full mechanism: [/uipath:uipath-platform — reference-resolution.md § Reference IDs Are Connection-Scoped (CRITICAL)](../../uipath-platform/references/integration-service/reference-resolution.md#reference-ids-are-connection-scoped-critical).

> **Paginate when looking up by name.** `execute list` returns one page (up to 1000 items); check `Data.Pagination.HasMore` + `Data.Pagination.NextPageToken`. Re-run with `--query "nextPage=<NextPageToken>"` until found or `HasMore` is `"false"`. Short-circuit on first match.

If a reference cannot be resolved, **AskUserQuestion** with the candidates (dropdown when finite set, plus "Something else").

---

## Applying Results to caseplan.json

In Phase 3, the populated `caseShape` from `case spec --input-details` is dropped into the task's `data` after binding-id substitution. Per-class wiring lives in each plugin's `impl-json.md` — the table below is a quick reference.

| Resolved value | Connector activity / trigger task field |
|---|---|
| `uiPathActivityTypeId` | `data.context[name="metadata"].body.activityPropertyConfiguration.uiPathActivityTypeId` (set by spec) |
| Selected `connection.id` | `data.context[name="resourceKey"].value` (set by spec); also the `default` of the connection root binding |
| Connector input values from sdd.md | `data.inputs[].body` (populated by `--input-details.{bodyParameters, queryParameters, pathParameters, eventParameters}` and the spec's `nestDottedKeys`) |
| Filter (activity, CEQL) | `data.context[name="metadata"].body.activityPropertyConfiguration.configuration` → `essentialConfiguration.savedFilterTrees.<filterParamName>` (tree); `data.inputs[name="queryParameters"].body.<filterParamName>` (compiled CEQL string) |
| Filter (trigger, JMESPath) | `data.context[name="metadata"].body.activityPropertyConfiguration.{configuration → essentialConfiguration.filter, filterExpression}` AND `data.inputs[name="body"].body.filters.expression` |

The skill substitutes `{{CONN_BINDING_ID}}` and `{{FOLDER_BINDING_ID}}` placeholders in `caseShape.context[*].value` with minted binding ids before writing.

---

## Filter Authoring

Filters for both activities (CEQL) and triggers (JMESPath) are authored as **structured FilterTree JSON**, not flat string expressions. The CLI compiles the tree to the appropriate target language and persists both the tree (for round-tripping in Studio Web) and the compiled expression (for runtime evaluation).

Tree shape, operator table, anti-patterns, "How to build" guide, worked examples: [/uipath:uipath-platform — Filter Trees (CEQL)](../../uipath-platform/references/integration-service/activities.md#filter-trees-ceql). Same shape applies to triggers — only the compiler output differs.

> **Do NOT pass a raw filter string** under `--input-details.queryParameters.where` (or the connector-specific filter param name). The CLI rejects this; even if it didn't, Studio Web would render the filter widget as `undefined` when the activity is reopened.

---

## Output Contract to Tasks.md

Record the resolved values in `tasks.md` under the task entry:

```markdown
## T25: Add connector-activity task "Create Jira Issue" to "Triage"
- type-id: 718fdc36-73a8-3607-8604-ddef95bb9967
- connection-id: 7622a703-5d85-4b55-849b-6c02315b9e6e
- connector-key: uipath-atlassian-jira
- object-name: issue
- input-values: {"bodyParameters":{"fields.project.key":"PROJ","fields.issuetype.id":"10004"}}
- filter: {"groupOperator":"And","filters":[{"id":"Status","operator":"Equals","value":{"isLiteral":true,"rawString":"\"Open\"","value":"Open"},"uiId":null}]}
```

Also record in `registry-resolved.json`: search query, matched entry, selected connection, connector metadata, and (when surfaced) `spec.diagnostics.fallbacks[]`.
