# Connector Integration Reference

Resolve `connector-activity`, `connector-trigger`, and `event` plugin tasks against UiPath Integration Service.

## When to Use

Consult for:
- `connector-activity` — [`plugins/tasks/connector-activity/impl-json.md`](plugins/tasks/connector-activity/impl-json.md)
- `connector-trigger` — [`plugins/tasks/connector-trigger/impl-json.md`](plugins/tasks/connector-trigger/impl-json.md)
- `event` case-level trigger — [`plugins/triggers/event/impl-json.md`](plugins/triggers/event/impl-json.md)

## Prerequisites

<!--skill-flavor:connector-login-prerequisite:start-->
1. Run `uip login` — tenant-scoped connectors require authentication.
<!--skill-flavor:connector-login-prerequisite:end-->
2. Run `uip maestro case registry pull` to populate `typecache-activities-index.json` and `typecache-triggers-index.json` at `~/.uip/case-resources/`.
3. Ensure a healthy Integration Service connection. If `Connections` is empty after `get-connection`, offer creation (Step 2), not failure; see [§ Creating a Connection](#creating-a-connection).

For `--refresh`, ping verification, BYOA, and connection creation, see [/uipath:uipath-platform — connections.md](../../uipath-platform/references/integration-service/connections.md).

## Catalog unavailable (TypeCache 5xx)

Studio Web TypeCache supplies the catalog. A ring without connector packages may return `500`; `registry pull` may exit 0 with `Result: Success`, put failed `typecache-*` types in `Data.Errors[]`, and omit indexes. After every pull, read `Data.Errors`; `Warning: N of M resource types failed to pull` is the cue.

Detect any of:
- A `registry pull` `Data.Errors[]` row whose `Type` starts with `typecache-` and has a 5xx. Newer CLIs include `HttpStatus: 5xx`, `ErrorCode: "server_error"`, and `Retry: "RetryLater"`; older CLIs show `Error: "catalog search failed: 5xx …"`. Other statuses, including `401` (`authentication_required`) and `403` (`permission_denied`), are login/permission failures: use Rule 3's pull-failure path, surface the error, and stop Phase 1; never use this section.
- `registry get-connection`, `registry get-connector`, or `case spec` fails with `Connector catalog unavailable: the last pull of <index> failed with HTTP <status> from Studio Web TypeCache …` and `ErrorCode: "server_error"` (`Retry: "RetryLater"`). For another `ErrorCode`, follow the envelope's `Instructions` (such as `uip login` or Studio Web access) and stop as for any pull failure.
- On an older CLI, `No resource index found` or `No TypeCache entry found` immediately follows a pull whose `Data.Errors` listed that `typecache-*` type; the index is missing because the pull failed.

Scope by failed index, not every connector. Activities, triggers, and packages for one project type share a request; external types may fail independently. Synced `Data.ResourceTypes[]` resolve normally.

| Failed index | Placeholder elements |
|---|---|
| `typecache-activities` | `execute-connector-activity` tasks |
| `typecache-triggers` | event triggers, `wait-for-connector` tasks, connector-bound condition rules |
| `typecache-external-agent-activities` | `external-agent` tasks |
| `typecache-external-automation-activities` | `external-workflow` tasks |
| any `typecache-*-packages` | none; names only the connector category |

For every element served by a failed index:
1. Do not run the pull again or retry a 5xx. Rule 18's `Force pull and re-resolve` gate does not apply: this is not an empty lookup, so ask nothing.
2. Skip the Resolution Pipeline: no Step 1 index read, `get-connection`, or `case spec`.
3. In `tasks/registry-resolved.json`, set `type-id` and `connector-key` to `<UNRESOLVED: connector catalog unavailable (TypeCache <status>)>`, omit `input-values`, and preserve SDD inputs in `wiringNotes`.
4. At execution use the existing placeholder shape: connector task `data: {}` ([placeholder-tasks.md](placeholder-tasks.md)); event trigger placeholder node ([event/impl-json.md § Placeholder fallback](plugins/triggers/event/impl-json.md#placeholder-fallback-unresolved-connector--connection)); condition-rule stub ([connector-trigger-impl.md § Placeholder fallback](connector-trigger-impl.md#placeholder-fallback)). Never retain flat `{name, value}` inputs emitted by `sdd convert` for a connector task: `validate` rejects them with `CASE_MGMT_CONNECTOR_INPUT_FLATTENED`. If convert emitted `data`, replace it with `{}`.
5. Immediately say in one business-language line that the catalog is unavailable and continue. In the completion report call it an **environment gap**, including status, endpoint `studio_/typecache/api/Search/Catalog`, and time—not a build defect; see [placeholder-tasks.md § Completion-Report Shape](placeholder-tasks.md#completion-report-shape).

End the build with placeholders; `validate` passes except expected condition-rule stub errors ([connector-trigger-impl.md § What validate reports for a stub](connector-trigger-impl.md#what-validate-reports-for-a-stub)). When recovered, upgrade with `uip maestro case registry pull --force`, then [placeholder-tasks.md § Upgrade Procedure](placeholder-tasks.md#upgrade-procedure--placeholder--full-task).

## Resolution Pipeline

For each connector task or event trigger, run metadata fetches in order; each feeds the next. Write populated `caseShape` from `case spec` directly to `caseplan.case` per the plugin's `impl-json.md`; do not use a `tasks add-connector` mutation. Empty `Connections[]` is not terminal: Step 2 offers `uip is connections create` before `<UNRESOLVED>`.

### Step 1 — Find the activity-type-id

Read the TypeCache index or search with `uip maestro case registry search` (see [registry-discovery.md](registry-discovery.md)).

| Target | Cache file | Identifier |
|---|---|---|
| Connector activity | `typecache-activities-index.json` | `uiPathActivityTypeId` |
| Connector trigger | `typecache-triggers-index.json` | `uiPathActivityTypeId` |

Match the SDD's `displayName`; skip entries without `uiPathActivityTypeId` because non-connector activities are unsupported case tasks.

### Step 2 — Resolve the connection

```bash
uip maestro case registry get-connection --type <typecache-activities|typecache-triggers> \
  --activity-type-id "<uiPathActivityTypeId>" --output json
```

Output `{ Entry, Config, Connections }`: `Entry` is the raw TypeCache entry (`displayName`, `configuration`); `Config.connectorKey` is the Integration Service identifier; `Config.objectName` is the operation; `Connections[]` contains PascalCase `{ Id, Name }` objects.

Select in order:
1. If the SDD names a connection, match by `name` and use its `id`.
2. If silent, always use AskUserQuestion—never auto-select, even with one connection. With non-empty `Connections`, list each `name` and **Create a new connection**. With empty `Connections`, offer **Create a new connection** / **Skip (defer)**.
3. If creation is chosen, create it and continue to Step 3 with returned `ConnectionId`; see [§ Creating a Connection](#creating-a-connection).
4. If skipped, declined, failed, or non-interactive, set `<UNRESOLVED: no IS connection for <connectorKey>>` in `tasks/registry-resolved.json`, omit `input-values`, emit a placeholder connector task with `type` + `displayName` + `data: {}` and no `data.typeId` / `data.connectionId`, and report it. A failed `is connections create` MUST follow this path after surfacing its error (§ Creating a Connection step 4); planning continues and never stalls. See [placeholder-tasks.md](placeholder-tasks.md).

### Creating a Connection

When requested or no usable connection exists, run:

```bash
uip is connections create "<connector-key>" --output json
# → Data: { ConnectionId, ConnectionName, Connector, State, Owner, Folder, FolderKey }
```

Use `Config.connectorKey` as positional `<connector-key>`, including when `Connections` is empty. The command opens OAuth and blocks until authorization finishes.

1. Run it in the background so human-paced OAuth survives foreground timeouts; read the result when it exits.
2. Capture `Data.ConnectionId` and pass it directly as `--connection-id` to Step 3. Do **NOT** re-run `get-connection`; its cache may be stale and create output is authoritative.
3. Optionally verify with `uip is connections ping "<ConnectionId>" --output json`.
4. On non-zero exit, JSON `Result: "Failure"`, or missing `Data.ConnectionId` (OAuth denial/failure, closed browser, or misconfiguration), surface `Message` and any `Instructions` verbatim, then AskUserQuestion: **Retry create** (re-run `is connections create`) / **Skip (defer)**. On Skip or repeated failure, use Selection rule 4, emit the placeholder, and finish writing `registry-resolved.json`. Auth failure exits (verified: exit 1); it does not hang.

**Headless/no-browser fallback** (CI, remote sandbox, no display): ask the user to run `! uip is connections create "<connector-key>" --output json` in their terminal and return `ConnectionId`, or run with `--no-wait`, surface the pending authorization URL, and poll until `State: Enabled`.

If rediscovery via `is connections list` is necessary, pass `--refresh`; capturing create output is preferred.

### Step 3 — Discover the operation contract via `case spec`

Run one of these calls:

```bash
# Planning phase — lean response (no caseShape payload)
uip maestro case spec --type <activity|trigger> \
  --activity-type-id "<uiPathActivityTypeId>" \
  --connection-id "<connection-id>" \
  --skip-case-shape --output json

# Phase 3 (implementation) — populated caseShape from --input-details
uip maestro case spec --type <activity|trigger> \
  --activity-type-id "<uiPathActivityTypeId>" \
  --connection-id "<connection-id>" \
  --input-details "<json>" --output json
```

The contract contains:
- `inputs.bodyFields[]`: `name` (dotted), `dataType`, `required`, `description`, `defaultValue`, `enum`, `reference`.
- `inputs.{path,query}Parameters[]`: URL-template/query fields with the same shape.
- `inputs.eventParameters[]`: trigger-only design-time scoping fields.
- `inputs.multipart`: `null`, or `{ bodyFieldName, parameters[] }`.
- `outputs.responseFields[]`: response shape; `[?responseCurated]` are FE-broken-out outputs and `[?primaryKey]` id fields.
- `outputs.pagination`: `null`, or `{ maxPageSize: N }` for list operations.
- `filter`: structured FilterBuilder contract (`ceql` activity, `jmes` trigger); `undefined` means no structured authoring. Plain filter fields remain native-syntax query/body inputs.
- `references[]`: cross-references with runnable `discoverCommand` strings.
- `caseShape`: FE-canonical `inputs[]` / `outputs[]` / `context[]`, ready for `caseplan.case` after binding-id substitution; absent with `--skip-case-shape`.
- `diagnostics`: per-endpoint `fetched` / `fallbacks`.

See [`case-spec-input-details.md`](case-spec-input-details.md) for the complete `--input-details` JSON contract.

For `Config.activityType === "Generic"`, TypeCache has an empty/templated `objectName` because one definition covers all connector objects. Discover objects with `uip is resources list <connector-key>` and `uip is resources describe <connector-key> <object-name>`, choose one, and pass it as `--object-name` on the Phase 3 call; `case spec --type activity` fails without it.

### Step 4 — Resolve reference fields

For each `inputs.*` entry with `reference`, run its `discoverCommand` exactly as given, match the SDD value to `lookupNames[0]`, and put `lookupValue` (the id) in `input-values`.

> **Reference IDs are connection-scoped.** Resolve every reference freshly against the current `--connection-id`, immediately before writing `registry-resolved.json` / minting the spec. Never reuse an ID from another connection. See [/uipath:uipath-platform — reference-resolution.md § Reference IDs Are Connection-Scoped (CRITICAL)](../../uipath-platform/references/integration-service/reference-resolution.md#reference-ids-are-connection-scoped-critical).

> **Paginate when looking up by name.** `run list` returns one page (up to 1000 items). Check `Data.Pagination.HasMore` and `Data.Pagination.NextPageToken`; rerun with `--query "nextPage=<NextPageToken>"` until found or `HasMore` is `"false"`; stop on the first match.

If unresolved, use AskUserQuestion with candidates (dropdown when finite, plus **Something else**).

## Applying Results to caseplan.case

In Phase 3, drop populated `caseShape` from `case spec --input-details` into task `data` after binding-id substitution. Per-class wiring is in each plugin's `impl-json.md`.

| Resolved value | Connector activity/trigger field |
|---|---|
| `uiPathActivityTypeId` | `data.context[name="metadata"].body.activityPropertyConfiguration.uiPathActivityTypeId` (set by spec) |
| Selected `connection.id` | `data.context[name="resourceKey"].value` and connection-root binding `default` (set by spec) |
| SDD connector inputs | `data.inputs[].body`, populated by `--input-details.{bodyParameters, queryParameters, pathParameters, eventParameters}` and `nestDottedKeys` |
| Activity filter (CEQL) | `data.context[name="metadata"].body.activityPropertyConfiguration.configuration` → `essentialConfiguration.savedFilterTrees.<filterParamName>` (tree); `data.inputs[name="queryParameters"].body.<filterParamName>` (compiled CEQL) |
| Trigger filter (JMESPath) | `data.context[name="metadata"].body.activityPropertyConfiguration.{configuration → essentialConfiguration.filter, filterExpression}` and `data.inputs[name="body"].body.filters.expression` |

For connector tasks, `uip maestro case splice` resolves `{{CONN_BINDING_ID}}` and `{{FOLDER_BINDING_ID}}`. For event-trigger nodes and connector-bound rules, substitute them in `caseShape.context[*].value` with minted binding ids before writing.

## Filter Authoring

Author filters for activities (CEQL) and triggers (JMESPath) as structured FilterTree JSON. The CLI compiles the tree, preserving both tree (Studio Web round-tripping) and compiled expression (runtime). See tree shape, operators, anti-patterns, construction guide, and examples at [/uipath:uipath-platform — Filter Trees (CEQL)](../../uipath-platform/references/integration-service/activities.md#filter-trees-ceql); triggers use the same shape with different compiler output.

> **Do NOT pass a raw filter string** under `--input-details.queryParameters.where` or the connector-specific filter parameter. The CLI rejects it; otherwise Studio Web would reopen with the filter widget as `undefined`.

## Output Contract to `registry-resolved.json`

Alongside Rule 10 keys (`stage`, `task`, `taskType`, `cacheFile`, `searchQuery`, `matches`, `selected`, `rationale`), record `type-id`, `connection-id`, `connector-key`, `object-name`, `input-values`, and `filter`; also record the selected connection, connector metadata, and any surfaced `spec.diagnostics.fallbacks[]`.

`input-values` and `filter` are JSON objects, not strings; Phase 2 reads them verbatim into `--input-details` ([connector-activity/impl-json.md § Step 1](plugins/tasks/connector-activity/impl-json.md)).

<!-- END: connector-integration.md -->