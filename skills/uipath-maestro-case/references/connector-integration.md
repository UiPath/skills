# Connector Integration Reference

Procedure for resolving connector activity and connector trigger tasks against UiPath Integration Service. Shared between the `connector-activity` and `connector-trigger` task plugins and the `event` trigger plugin.

## When to Use

Consult this reference when planning or implementing any of:

- `connector-activity` task — see [`plugins/tasks/connector-activity/impl-json.md`](plugins/tasks/connector-activity/impl-json.md)
- `connector-trigger` task — see [`plugins/tasks/connector-trigger/impl-json.md`](plugins/tasks/connector-trigger/impl-json.md)
- `event` case-level trigger — see [`plugins/triggers/event/impl-json.md`](plugins/triggers/event/impl-json.md)

## Prerequisites

<!--skill-flavor:connector-login-prerequisite:start-->
1. `uip login` — tenant-scoped connectors are only visible after authentication.
<!--skill-flavor:connector-login-prerequisite:end-->
2. `uip maestro case registry pull` — populates `typecache-activities-index.json` and `typecache-triggers-index.json` at `~/.uip/case-resources/`.
3. A healthy Integration Service connection for the connector. If `Connections` is empty after `get-connection`, offer to create one (Step 2) rather than failing — see [§ Creating a Connection](#creating-a-connection).

Connection selection mechanics (`--refresh` retry, ping verification, BYOA workflow, connection creation): see [/uipath:uipath-platform — connections.md](../../uipath-platform/references/integration-service/connections.md).

## Catalog unavailable (TypeCache 5xx)

Studio Web TypeCache serves the connector catalog. When it cannot — on a ring with no connector packages it answers `500` — `registry pull` still exits 0 with `Result: Success`, lists the failed `typecache-*` types in `Data.Errors[]`, and writes no index for them. Read `Data.Errors` after every pull; a `Warning` of `N of M resource types failed to pull` is the cue.

**Detect** any one of:

- a `registry pull` `Data.Errors[]` row whose `Type` starts with `typecache-`. A newer CLI carries `ErrorCode: "server_error"`, `Retry: "RetryLater"` and `HttpStatus: 5xx` on the row; an older CLI shows only `Error: "catalog search failed: 5xx …"`.
- `registry get-connection`, `registry get-connector` or `case spec` failing with `Connector catalog unavailable: the last pull of <index> failed with HTTP <status> from Studio Web TypeCache …` (`ErrorCode: "server_error"`, `Retry: "RetryLater"`).
- on an older CLI, `No resource index found` or `No TypeCache entry found` right after a pull whose `Data.Errors` listed that `typecache-*` type. The index is missing because the pull failed, not because it never ran.

**Scope — act per failed index, not on every connector.** Studio Web answers the three slices of one project type (activities, triggers, packages) from one request, so they fail together; the external project types can fail independently of the case-management one. An index the pull synced (`Data.ResourceTypes[]`) resolves as usual.

| Index in `Data.Errors` | Elements that become placeholders |
|---|---|
| `typecache-activities` | `execute-connector-activity` tasks |
| `typecache-triggers` | event triggers, `wait-for-connector` tasks, connector-bound condition rules |
| `typecache-external-agent-activities` | `external-agent` tasks |
| `typecache-external-automation-activities` | `external-workflow` tasks |
| any `typecache-*-packages` | none of its own — it only names the connector's category |

**Then, for every element the failed index serves:**

1. **Do not run the pull again, and do not retry a 5xx.** The answer does not change within a session. Rule 18's `Force pull and re-resolve` gate does not apply — this is not an empty lookup, so ask nothing.
2. **Skip the Resolution Pipeline below** — no Step 1 index read, no `get-connection`, no `case spec`.
3. In `tasks/registry-resolved.json` mark `type-id` and `connector-key` `<UNRESOLVED: connector catalog unavailable (TypeCache <status>)>`, omit `input-values`, and keep the SDD's inputs in `wiringNotes`.
4. At execution write the existing placeholder shape: connector task `data: {}` ([placeholder-tasks.md](placeholder-tasks.md)), event trigger placeholder node ([event/impl-json.md § Placeholder fallback](plugins/triggers/event/impl-json.md#placeholder-fallback-unresolved-connector--connection)), condition-rule stub ([connector-trigger-impl.md § Placeholder fallback](connector-trigger-impl.md#placeholder-fallback)). **Never keep the flat `{name, value}` inputs `sdd convert` emits for a connector task** — `validate` rejects them with `CASE_MGMT_CONNECTOR_INPUT_FLATTENED`. If convert emitted the task with `data` anyway, replace its `data` with `{}`.
5. Say in one business-language line, as soon as it is detected, that the connector catalog is unavailable, and continue. In the completion report list it as an **environment gap** — the status, the endpoint `studio_/typecache/api/Search/Catalog` and the time — not as a build defect; see [placeholder-tasks.md § Completion-Report Shape](placeholder-tasks.md#completion-report-shape).

The build then ends with placeholders and `validate` passes. Upgrade when the service recovers: `uip maestro case registry pull --force`, then [placeholder-tasks.md § Upgrade Procedure](placeholder-tasks.md#upgrade-procedure--placeholder--full-task).

## Resolution Pipeline

For every connector task or event trigger, run these CLI metadata fetches in order. Each call feeds the next; the populated `caseShape` from `case spec` is written directly into `caseplan.case` per the plugin's `impl-json.md` — there is no `tasks add-connector` mutation step.

> **Empty `Connections[]` is not terminal.** When `get-connection` returns no connections, Step 2 offers to create one (`uip is connections create`) before falling back to `<UNRESOLVED>` — see [§ Creating a Connection](#creating-a-connection).

### Step 1 — Find the activity-type-id

Read the relevant TypeCache index file directly, or search it with `uip maestro case registry search` (see [registry-discovery.md](registry-discovery.md)).

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
- `Connections[]` — array of `{ Id, Name }` (not a verbatim subtree, so PascalCase) objects.

**Selection rules (in priority order):**

1. If the sdd.md names a specific connection, match by `name`. Use that `id`.
2. If the sdd.md is silent, **always present the choice via AskUserQuestion — do not auto-select**, even when exactly one connection exists:
   - **`Connections` non-empty** → list connections by `name` **plus a "Create a new connection" option** (an existing connection may not fit the intent).
   - **`Connections` empty** → offer **Create a new connection** / **Skip (defer)**.
3. **Create chosen** → create the connection, then continue to Step 3 with the returned `ConnectionId`. Procedure — background `is connections create`, capture `ConnectionId`, headless fallback: [§ Creating a Connection](#creating-a-connection).
4. **Skip / create declined or failed / non-interactive run** → mark the task `<UNRESOLVED: no IS connection for <connectorKey>>` in `tasks/registry-resolved.json` and omit its `input-values` key. Execution writes a placeholder connector task — `type` + `displayName` + `data: {}`, no `data.typeId` / `data.connectionId` keys. Note it in the completion report. See [placeholder-tasks.md](placeholder-tasks.md). A failed `is connections create` MUST route here after surfacing the error (§ Creating a Connection step 4) — **planning continues to a placeholder, it never stalls.**

#### Creating a Connection

Reached when the user picks "Create a new connection" or no usable connection exists. Create one via the OAuth flow:

```bash
uip is connections create "<connector-key>" --output json
# → Data: { ConnectionId, ConnectionName, Connector, State, Owner, Folder, FolderKey }
```

`<connector-key>` is a positional argument — use `Config.connectorKey` from `get-connection` (present even when `Connections` is empty). The command auto-opens the browser for OAuth and **blocks until the user finishes authorizing**, then returns the new connection.

1. **Run it in the background.** OAuth completion is human-paced and routinely exceeds a foreground command timeout — run detached so it survives across turns; read the result when it exits.
2. **Capture `Data.ConnectionId`** and use it directly as `--connection-id` for `case spec` (Step 3). **Do NOT re-run `get-connection`** to re-discover it — the IS connection cache may be stale immediately after create, and the create output already carries the authoritative id.
3. **Ping to verify** (optional): `uip is connections ping "<ConnectionId>" --output json`.
4. **On failure — surface and re-prompt, never stall.** The create failed if the command **exits non-zero**, the JSON `Result` is `"Failure"`, or no `Data.ConnectionId` is returned (e.g. OAuth denied/failed, browser closed, connector misconfigured). On auth failure the command **exits** (verified: exit 1) — it does not hang. Do NOT silently proceed and do NOT leave planning incomplete:
   1. Show the user the failure `Message` (and `Instructions` if present) verbatim — do not invent a cause. Example: `{ "Result": "Failure", "Message": "Authentication failed", "Instructions": "Check credentials and try again." }`.
   2. Re-prompt via **AskUserQuestion**: **Retry create** (re-run `is connections create`) / **Skip (defer)**.
   3. On **Skip**, or after a repeated failure, fall to Selection rule 4 — mark `<UNRESOLVED>`, emit the placeholder, and **finish writing `registry-resolved.json`** so resolution completes.

**Headless / no-browser fallback** (CI, remote sandbox, no display) — the agent cannot complete browser OAuth. Either ask the user to run `! uip is connections create "<connector-key>" --output json` in their own terminal and paste back the `ConnectionId`, or run with `--no-wait` to get the pending authorization URL, surface it, and poll until `State: Enabled`.

> If you must re-discover via `is connections list` after create, pass `--refresh` to bypass the cache — but capturing `ConnectionId` from the create output is preferred.

### Step 3 — Discover the operation contract via `case spec`

One CLI call replaces the legacy `case tasks describe` + `is resources describe` dance:

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

Spec output carries the full operation contract:

| Spec output | What it tells you |
|---|---|
| `inputs.bodyFields[]` | Body request fields with `name` (dotted), `dataType`, `required`, `description`, `defaultValue`, `enum`, `reference` |
| `inputs.{path,query}Parameters[]` | URL-template substitutions and query-string params with the same per-field shape |
| `inputs.eventParameters[]` | Trigger-only design-time scoping params |
| `inputs.multipart` | `null` for non-multipart; `{ bodyFieldName, parameters[] }` otherwise |
| `outputs.responseFields[]` | Response shape; `[?responseCurated]` are FE-broken-out outputs, `[?primaryKey]` are id fields |
| `outputs.pagination` | `null` for non-list; `{ maxPageSize: N }` for list ops |
| `filter` | Structured FilterBuilder contract (`ceql` activity / `jmes` trigger); `undefined` means no structured authoring. Plain filter fields remain native-syntax query/body inputs |
| `references[]` | Cross-references with pre-built `discoverCommand` runnable strings |
| `caseShape` | FE-canonical `inputs[]` / `outputs[]` / `context[]` ready to drop into `caseplan.case` (after binding-id substitution); only present when `--skip-case-shape` is NOT set |
| `diagnostics` | Per-endpoint `fetched` / `fallbacks` |

Full input-details contract (the `--input-details` JSON shape): [`case-spec-input-details.md`](case-spec-input-details.md).

> **Generic-typed activities** (`Config.activityType === "Generic"`) carry an empty/templated `objectName` in the typecache because one definition is shared across every object the connector exposes (e.g. Salesforce `InsertRecord`). The CLI fails fast on `case spec --type activity` without `--object-name`. Discover the available objects via `uip is resources list <connector-key>` and `uip is resources describe <connector-key> <object-name>`, then pass the picked name as `--object-name` on the Phase 3 call.

### Step 4 — Resolve reference fields

Each `inputs.*` entry with a `reference` carries a pre-built `discoverCommand`:

```jsonc
"reference": {
    "objectName": "MailFolder",
    "lookupValue": "id",
    "lookupNames": ["displayName"],
    "discoverCommand": "uip is resources run list <connector> <object> --connection-id <id>"
}
```

Run the `discoverCommand` exactly as given. Match the sdd.md value to `lookupNames[0]` in the results. Use the resolved `lookupValue` (the id) in `input-values`.

> **Reference IDs are connection-scoped.** Resolve every reference field freshly against the current `--connection-id`, immediately before writing `registry-resolved.json` / minting the spec. Never reuse an ID resolved against a different connection — silent runtime fault. Full mechanism: [/uipath:uipath-platform — reference-resolution.md § Reference IDs Are Connection-Scoped (CRITICAL)](../../uipath-platform/references/integration-service/reference-resolution.md#reference-ids-are-connection-scoped-critical).

> **Paginate when looking up by name.** `run list` returns one page (up to 1000 items); check `Data.Pagination.HasMore` + `Data.Pagination.NextPageToken`. Re-run with `--query "nextPage=<NextPageToken>"` until found or `HasMore` is `"false"`. Short-circuit on first match.

If a reference cannot be resolved, **AskUserQuestion** with the candidates (dropdown when finite set, plus "Something else").

---

## Applying Results to caseplan.case

In Phase 3, the populated `caseShape` from `case spec --input-details` is dropped into the task's `data` after binding-id substitution. Per-class wiring lives in each plugin's `impl-json.md` — the table below is a quick reference.

| Resolved value | Connector activity / trigger task field |
|---|---|
| `uiPathActivityTypeId` | `data.context[name="metadata"].body.activityPropertyConfiguration.uiPathActivityTypeId` (set by spec) |
| Selected `connection.id` | `data.context[name="resourceKey"].value` (set by spec); also the `default` of the connection root binding |
| Connector input values from sdd.md | `data.inputs[].body` (populated by `--input-details.{bodyParameters, queryParameters, pathParameters, eventParameters}` and the spec's `nestDottedKeys`) |
| Filter (activity, CEQL) | `data.context[name="metadata"].body.activityPropertyConfiguration.configuration` → `essentialConfiguration.savedFilterTrees.<filterParamName>` (tree); `data.inputs[name="queryParameters"].body.<filterParamName>` (compiled CEQL string) |
| Filter (trigger, JMESPath) | `data.context[name="metadata"].body.activityPropertyConfiguration.{configuration → essentialConfiguration.filter, filterExpression}` AND `data.inputs[name="body"].body.filters.expression` |

For connector tasks `uip maestro case splice` resolves the `{{CONN_BINDING_ID}}` and `{{FOLDER_BINDING_ID}}` placeholders; for the event-trigger node and connector-bound rules the skill substitutes them in `caseShape.context[*].value` with minted binding ids before writing.

---

## Filter Authoring

Filters for both activities (CEQL) and triggers (JMESPath) are authored as **structured FilterTree JSON**, not flat string expressions. The CLI compiles the tree to the appropriate target language and persists both the tree (for round-tripping in Studio Web) and the compiled expression (for runtime evaluation).

Tree shape, operator table, anti-patterns, "How to build" guide, worked examples: [/uipath:uipath-platform — Filter Trees (CEQL)](../../uipath-platform/references/integration-service/activities.md#filter-trees-ceql). Same shape applies to triggers — only the compiler output differs.

> **Do NOT pass a raw filter string** under `--input-details.queryParameters.where` (or the connector-specific filter param name). The CLI rejects this; even if it didn't, Studio Web would render the filter widget as `undefined` when the activity is reopened.

---

## Output Contract to `registry-resolved.json`

Record the resolved values on the task's ledger entry, alongside Rule 10's keys (`stage`, `task`, `taskType`, `cacheFile`, `searchQuery`, `matches`, `selected`, `rationale`):

```json
{
  "stage": "Triage",
  "task": "Create Jira Issue",
  "taskType": "connector-activity",
  "type-id": "718fdc36-73a8-3607-8604-ddef95bb9967",
  "connection-id": "7622a703-5d85-4b55-849b-6c02315b9e6e",
  "connector-key": "uipath-atlassian-jira",
  "object-name": "issue",
  "input-values": { "bodyParameters": { "fields.project.key": "PROJ", "fields.issuetype.id": "10004" } },
  "filter": {
    "groupOperator": "And",
    "filters": [
      { "id": "Status", "operator": "Equals", "value": { "isLiteral": true, "rawString": "\"Open\"", "value": "Open" }, "uiId": null }
    ]
  }
}
```

`input-values` and `filter` are real JSON objects, not strings — Phase 2 reads them back verbatim into `--input-details` ([connector-activity/impl-json.md § Step 1](plugins/tasks/connector-activity/impl-json.md)). Also record the selected connection, connector metadata, and (when surfaced) `spec.diagnostics.fallbacks[]`.

<!-- END: connector-integration.md -->
