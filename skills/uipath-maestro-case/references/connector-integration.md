# Connector Integration Reference

Procedure for resolving connector activity and connector trigger tasks against UiPath Integration Service. Shared between the `connector-activity` and `connector-trigger` task plugins and the `event` trigger plugin.

## When to Use

Consult this reference when planning or implementing any of:

- `connector-activity` task (added via `uip maestro case tasks add-connector --type activity`)
- `connector-trigger` task (added via `uip maestro case tasks add-connector --type trigger`)
- `event` case-level trigger (added via `uip maestro case triggers add-event`)

## Prerequisites

1. `uip login` — tenant-scoped connectors are only visible after authentication.
2. `uip maestro case registry pull` — populates `typecache-activities-index.json` and `typecache-triggers-index.json` at `~/.uipcli/case-resources/`.
3. A healthy Integration Service connection must exist for the connector. If `Connections` is empty after `get-connection`, the user must create one in IS before proceeding.

## Three-Step Resolution Pipeline

For every connector task or event trigger, run these three CLI calls in order. Each call feeds required inputs into the next.

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
4. If `Connections` is empty, mark the task `<UNRESOLVED: no IS connection for <connectorKey>>` in `tasks.md` and omit `input-values:`. Execution creates a skeleton connector task (bare `tasks add-connector --type <activity|trigger> --display-name …`). Tell the user in the completion report to create the connection in the IS portal before the task can run. See [skeleton-tasks.md](skeleton-tasks.md).

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

## Applying Results to CLI Commands

### Connector activity task

```bash
uip maestro case tasks add-connector <file> <stage-id> \
  --type activity \
  --type-id "<uiPathActivityTypeId>" \
  --connection-id "<connection-id>" \
  --input-values '{"body":{"field":"value"},"queryParameters":{"key":"val"}}'
```

`--input-values` is a JSON object. Keys come from the `describe` response (Step 4). Use `body`, `queryParameters`, `pathParameters` as top-level keys depending on what the operation expects.

### Connector trigger task (inside a stage)

```bash
uip maestro case tasks add-connector <file> <stage-id> \
  --type trigger \
  --type-id "<uiPathActivityTypeId>" \
  --connection-id "<connection-id>" \
  --input-values '{"body":{"project":"PROJ"}}' \
  --filter '((fields.status=`Open`))'
```

### Event trigger (case-level, outside any stage)

```bash
uip maestro case triggers add-event <file> \
  --type-id "<uiPathActivityTypeId>" \
  --connection-id "<connection-id>" \
  --event-params '{"project":"PROJ"}' \
  --filter '((fields.status=`Open`))'
```

---

## Filter Expression Syntax

Trigger `--filter` expressions use the connector's filter DSL. Common patterns:

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
- type-id: 718fdc36-73a8-3607-8604-ddef95bb9967
- connection-id: 7622a703-5d85-4b55-849b-6c02315b9e6e
- connector-key: uipath-atlassian-jira
- object-name: issue
- input-values: {"body":{"fields.project.key":"PROJ","fields.issuetype.id":"10004"}}
```

Also record in `registry-resolved.json`: search query, matched entry, selected connection, connector metadata.
