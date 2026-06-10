# Connector Integration Reference

Procedure for resolving connector activity and connector trigger tasks against UiPath Integration Service. Shared between the `connector-activity` and `connector-trigger` task plugins and the `event` trigger plugin.

## When to Use

Consult this reference when planning or implementing any of:

- `connector-activity` task — see [`plugins/tasks/connector-activity/impl-json.md`](plugins/tasks/connector-activity/impl-json.md)
- `connector-trigger` task — see [`plugins/tasks/connector-trigger/impl-json.md`](plugins/tasks/connector-trigger/impl-json.md)
- `event` case-level trigger — see [`plugins/triggers/event/impl-json.md`](plugins/triggers/event/impl-json.md)

## Prerequisites

1. `uip login` — tenant-scoped connectors are only visible after authentication.
2. `uip maestro case registry pull` — populates `typecache-activities-index.json` and `typecache-triggers-index.json` at `~/.uip/case-resources/`.
3. A healthy Integration Service connection for the connector. If `Connections` is empty after `get-connection`, offer to create one (Step 2) rather than failing — see [§ Creating a Connection](#creating-a-connection).

Connection selection mechanics (`--refresh` retry, ping verification, BYOA workflow, connection creation): see [/uipath:uipath-platform — connections.md](../../uipath-platform/references/integration-service/connections.md).

## Resolution Pipeline

For every connector task or event trigger, run these CLI metadata fetches in order. Each call feeds the next; the populated `caseShape` from `case spec` is written directly into `caseplan.json` per the plugin's `impl-json.md` — there is no `tasks add-connector` mutation step.

> **Empty `Connections[]` is not terminal.** When `get-connection` returns no connections, Step 2 offers to create one (`uip is connections create`) before falling back to `<UNRESOLVED>` — see [§ Creating a Connection](#creating-a-connection).

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
2. If the sdd.md is silent, **always present the choice via AskUserQuestion — do not auto-select**, even when exactly one connection exists:
   - **`Connections` non-empty** → list connections by `name` **plus a "Create a new connection" option** (an existing connection may not fit the intent).
   - **`Connections` empty** → offer **Create a new connection** / **Skip (defer)**.
3. **Create chosen** → create the connection, then continue to Step 3 with the returned `ConnectionId`. Procedure — background `is connections create`, capture `ConnectionId`, headless fallback: [§ Creating a Connection](#creating-a-connection).
4. **Skip / create declined or failed / non-interactive run** → mark the task `<UNRESOLVED: no IS connection for <connectorKey>>` in `tasks.md` and omit `input-values:`. Execution writes a placeholder connector task — `type` + `displayName` + `data: {}`, no `data.typeId` / `data.connectionId` keys. Note it in the completion report. See [placeholder-tasks.md](placeholder-tasks.md). A failed `is connections create` MUST route here after surfacing the error (§ Creating a Connection step 4) — **planning continues to a placeholder, it never stalls.**

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
   3. On **Skip**, or after a repeated failure, fall to Selection rule 4 — mark `<UNRESOLVED>`, emit the placeholder, and **finish writing `tasks.md`** so planning completes.

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
| `filter` | `undefined` when server-side filtering is not supported. Present when supported, with `builder: "ceql"` (activity) / `"jmes"` (trigger) and `fields[]` listing every searchable field |
| `references[]` | Cross-references with pre-built `discoverCommand` runnable strings |
| `caseShape` | FE-canonical `inputs[]` / `outputs[]` / `context[]` ready to drop into `caseplan.json` (after binding-id substitution); only present when `--skip-case-shape` is NOT set |
| `diagnostics` | Per-endpoint `fetched` / `fallbacks` |

Full input-details contract (the `--input-details` JSON shape): [`case-spec-input-details.md`](case-spec-input-details.md).

> **Generic-typed activities** (`Config.activityType === "Generic"`) carry an empty/templated `objectName` in the typecache because one definition is shared across every object the connector exposes (e.g. Salesforce `InsertRecord`). The CLI fails fast on `case spec --type activity` without `--object-name`. Discover the available objects via `uip is resources list --connector-key <connector-key>` and `uip is resources describe --connector-key <connector-key> --object-name <name>`, then pass the picked name as `--object-name` on the Phase 3 call.

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
