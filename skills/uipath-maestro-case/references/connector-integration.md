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
3. A healthy Integration Service connection must exist for the connector. If `Connections` is empty after `get-connection`, the user must create one in IS before proceeding.

## Resolution Pipeline

For every connector task or event trigger, run these CLI metadata fetches in order — three required (Steps 1-3) plus one optional (Step 4). Each call feeds required inputs into the next. The values they return are written directly into `caseplan.json` per the plugin's `impl-json.md` — there is no `tasks add-connector` mutation step.

### Step 1 — Find the activity-type-id

Read the relevant TypeCache index file directly (CLI `registry search` has known gaps — see [registry-discovery.md](registry-discovery.md)).

| Target | Cache file | Identifier field |
|--------|-----------|------------------|
| Connector activity | `typecache-activities-index.json` | `uiPathActivityTypeId` |
| Connector trigger | `typecache-triggers-index.json` | `uiPathActivityTypeId` |

Match on `displayName` from the sdd.md. **Skip entries without a `uiPathActivityTypeId`** — non-connector activities are not supported as case tasks.

### Step 2 — Get connector metadata

```bash
uip maestro case registry get-connector --type <typecache-activities|typecache-triggers> \
  --activity-type-id "<uiPathActivityTypeId>" --output json
```

Output: `{ Entry, Config }`.

- `Entry` — the raw TypeCache entry, including `displayName`, `configuration`.
- `Config.connectorKey` — the Integration Service connector identifier (e.g., `gmail`, `uipath-atlassian-jira`).
- `Config.objectName` — the specific operation (e.g., `message`, `issue`).

### Step 3 — Get connections and pick one

```bash
uip maestro case registry get-connection --type <typecache-activities|typecache-triggers> \
  --activity-type-id "<uiPathActivityTypeId>" --output json
```

Output: `{ Entry, Config, Connections }` where `Connections` is an array of `{ id, name }` objects.

**Selection rules (in priority order):**

1. If the sdd.md names a specific connection, match by `name`. Use that `id`.
2. If the sdd.md is silent and exactly one connection exists, use it.
3. If multiple connections exist and sdd.md is silent, use **AskUserQuestion** with a bounded list of connection names + "Something else".
4. If `Connections` is empty, mark the task `<UNRESOLVED: no IS connection for <connectorKey>>` in `tasks.md` and omit `inputValues:`. Execution writes a skeleton connector task — `type` + `displayName` + `data: {}`, no `data.typeId` / `data.connectionId` keys. Tell the user in the completion report to create the connection in the IS portal before the task can run. See [skeleton-tasks.md](skeleton-tasks.md).

### Step 4 — (Optional) Describe inputs/outputs

For connector activities or triggers where the sdd.md requires wiring inputs to specific fields, run `tasks describe` to fetch the schema:

```bash
uip maestro case tasks describe --type connector-activity --id "<uiPathActivityTypeId>" \
  --connection-id "<connection-id>" --output json
uip maestro case tasks describe --type connector-trigger --id "<uiPathActivityTypeId>" \
  --connection-id "<connection-id>" --output json
```

The `--connection-id` is required — without it, custom fields and dynamic enums are missing from the response.

---

## Applying Results to caseplan.json

The resolved values map to JSON fields under the connector task's `data` object. Per-class wiring lives in each plugin's `impl-json.md` — the table below is a quick reference.

| Resolved value | Connector activity / trigger task field | Event trigger field |
|---|---|---|
| `uiPathActivityTypeId` | `data.typeId` | `node.data.uipath.typeId` |
| Selected `connection.id` | `data.connectionId` | `node.data.uipath.connectionId` |
| Connector input values from sdd.md | `data.inputs[i].value` (one entry per discovered input name) | `node.data.uipath.eventParams` |
| Filter expression (trigger only) | `data.filter` | `node.data.uipath.filter` |

Input keys come from the `describe` response (Step 4): typically `body`, `queryParameters`, `pathParameters` are top-level groupings depending on what the operation expects.

---

## Filter Expression Syntax

> **Note:** The direct JSON write path uses structured filter trees (see [connector-trigger-common.md §7](connector-trigger-common.md#7-build-input-values-and-filter)) instead of flat filter expressions. The CLI internally converts event parameters to a structured filter tree.

Trigger `data.filter` (or `node.data.uipath.filter` for event triggers) uses the connector's filter DSL. Common patterns:

| Pattern | Example |
|---------|---------|
| Equality | `` ((fields.status=`Open`)) `` |
| Comparison | `` ((fields.priority>`3`)) `` |
| String contains | `` ((fields.summary contains `urgent`)) `` |
| Boolean AND | `` ((fields.status=`Open`) AND (fields.priority>`3`)) `` |

Backticks wrap literal values. Double parentheses are required at the outermost level.

If the sdd.md describes the filter in natural language, translate to the DSL. If unsure of the field name, consult the `describe` response (Step 4) for available fields.

---

## Output Contract to Tasks.md

Record the resolved values in `tasks.md` under the task entry:

```markdown
## T25: Add connector-activity task "Create Jira Issue" to "Triage"
- typeId: 718fdc36-73a8-3607-8604-ddef95bb9967
- connectionId: 7622a703-5d85-4b55-849b-6c02315b9e6e
- connectorKey: uipath-atlassian-jira
- objectName: issue
- inputValues: {"body":{"fields.project.key":"PROJ","fields.issuetype.id":"10004"}}
```

Also record in `registry-resolved.json`: search query, matched entry, selected connection, connector metadata.
