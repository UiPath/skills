# connector-activity task — Planning

A connector activity task inside a stage. Calls an external service (Jira, Slack, Salesforce, Gmail, etc.) via UiPath Integration Service.

This plugin is **schema-data-driven** — one plugin covers every connector. Connector-specific input shapes are discovered via IS CLI commands, not baked into this plugin.

## When to Use

Pick this plugin when the sdd.md describes a task as `CONNECTOR_ACTIVITY` or names a specific external service action (e.g., "send a Slack message", "create a Jira issue", "update Salesforce opportunity").

For **connector-based triggers** inside a stage (wait for an external event), use [connector-trigger](../connector-trigger/planning.md).

For **case-level event triggers** (outside any stage), use [`plugins/triggers/event/`](../../triggers/event/planning.md).

## Resolution Pipeline

Run these steps during planning. Each step feeds into the `tasks.md` entry.

### 1. Find the connector in TypeCache

Read `~/.uip/case-resources/typecache-activities-index.json` directly. Match on `displayName` or `connectorKey` + operation description from sdd.md. Record `uiPathActivityTypeId`.

### 2. Resolve the connection

```bash
uip case registry get-connection \
  --type typecache-activities \
  --activity-type-id "<uiPathActivityTypeId>" --output json
```

Returns `Entry`, `Config`, and `Connections`.

- **Single connection** → use it.
- **Multiple connections** → **AskUserQuestion** with connection names + "Something else".
- **Empty `Connections`** → mark `<UNRESOLVED: no IS connection for <connectorKey>>` and omit `input-values:`. Execution creates a skeleton task — see [skeleton-tasks.md](../../../skeleton-tasks.md).

Record `connection-id`, `connector-key`, `object-name` from the response.

### 3. Describe the resource — discover fields and references

```bash
uip is resources describe "<connector-key>" "<object-name>" \
  --connection-id "<connection-id>" --operation Create --output json
```

> **Operation mapping for `--operation`:** Use `Create` for POST, `Retrieve` for GET, `Update` for PATCH/PUT, `Delete` for DELETE. If unsure, omit `--operation`.

Returns:
- **`requestFields`** — body fields with `type`, `required`, `description`, and `reference` objects
- **`parameters`** — query and path parameters (may include required params not in `requestFields`)

**This step is mandatory** — not optional. Without it, the agent cannot:
- Know which fields are required (causes runtime errors if missing)
- Discover reference fields that need ID resolution (display names fail at runtime)
- Build correct `input-values` for the tasks.md entry

### 4. Resolve reference fields

Check `requestFields` for fields with a `reference` object. For each, resolve display names from sdd.md to IDs:

```bash
uip is resources execute list "<connector-key>" "<reference.objectName>" \
  --connection-id "<connection-id>" --output json
```

Match the sdd.md value to `displayName` in the results. Use the resolved `id` in `input-values`.

> **Paginate when looking up by name.** If `Pagination.HasMore` is `true`, re-run with `--query "nextPage=<NextPageToken>"` until found.

If a reference cannot be resolved, **AskUserQuestion** with the available options. Do not guess.

### 5. Validate required fields

For each `requestFields` and `parameters` entry with `required: true`:
1. Check if sdd.md provides a value (literal, variable reference, or cross-task output)
2. If missing and no `defaultValue`, **AskUserQuestion** — list the missing field with its `displayName` and description
3. Only after all required fields have values, proceed to writing the tasks.md entry

### 6. Map SDD inputs to connector fields

SDD input names don't match connector field names. Match each SDD input to a `requestFields` or `parameters` entry by comparing the SDD field name against the `displayName` (or `name`) from Step 3.

For each **required** field in `requestFields`/`parameters`, there must be a matching SDD input. If a required field has no match in the SDD, **AskUserQuestion** — do not leave required fields unmapped.

Values can be:
- **Static literals** — `"Payment__c"`, `"Text"`
- **Resolved reference IDs** — from Step 4
- **Case variable references** — `=vars.X` for runtime values
- **Expressions** — `=js:()` only when operators are needed

### 7. Build input-values

Using the mapped fields from Step 6, build the `input-values` JSON with dot-path field names from `requestFields`:

```json
{"body":{"message":{"toRecipients":"=vars.managerEmail","subject":"=vars.caseId","body":{"content":"=vars.description","contentType":"Text"}}}}
```

`queryParameters` and `pathParameters` go as separate top-level keys if the connector uses them.

## tasks.md Entry Format

```markdown
## T<n>: Add connector-activity task "<display-name>" to "<stage>"
- type-id: <uiPathActivityTypeId>
- connection-id: <connection-uuid>
- connector-key: <connectorKey>
- object-name: <objectName>
- input-values: {"body":{"field":"value"},"queryParameters":{"key":"val"}}
- isRequired: true
- runOnlyOnce: false
- order: after T<m>
- lane: <n>
- verify: Confirm task created with correct inputs
```

## Unresolved Fallback

If the connector or connection cannot be resolved:
- Mark `type-id` or `connection-id` with `<UNRESOLVED: reason>`
- Omit `input-values:` entirely — no schema to wire against
- Execution creates a skeleton task (display-name + type only) per [skeleton-tasks.md](../../../skeleton-tasks.md)
