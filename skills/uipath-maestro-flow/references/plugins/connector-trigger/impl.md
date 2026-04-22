# Connector Trigger Nodes — Implementation

How to configure connector trigger nodes: connection binding, enriched metadata, event parameter resolution, and trigger-specific `node configure` fields. This replaces the IS activity workflow (Steps 1-6 in [connector/impl.md](../connector/impl.md)) — trigger nodes have different metadata and configuration.

## Configuration Workflow

Follow these steps for every IS trigger node.

### Step 1 — Fetch and bind a connection

Same as IS activity nodes. Extract the connector key from the node type (`uipath.connector.trigger.<connector-key>.<trigger-name>`) and fetch a connection.

```bash
# 1. List available connections
uip is connections list "<connector-key>" --output json

# 2. Pick the default enabled connection (IsDefault: Yes, State: Enabled)

# 3. Verify the connection is healthy
uip is connections ping "<connection-id>" --output json
```

**If `connections list` returns empty**, check other folders with `uip or folders list` + `--folder-key <key>` (Shared is the common case). If still not found, the connection doesn't exist — tell the user, and have them create one via the IS portal or `uip is connections create "<connector-key>"`.

### Step 2 — Get enriched trigger metadata

`--connection-id` is **required** for trigger nodes. Without it, the command fails.

```bash
uip maestro flow registry get <triggerNodeType> --connection-id <connection-id> --output json
```

The response contains three trigger-specific sections:

**`eventParameters`** — fields that configure *what* the trigger watches (e.g., which email folder, which Jira project). These are the trigger's required setup fields.

```json
{
  "eventParameters": {
    "fields": [
      {
        "name": "parentFolderId",
        "displayName": "Email folder",
        "type": "string",
        "required": true,
        "reference": {
          "objectName": "MailFolder",
          "lookupValue": "id",
          "lookupNames": ["displayName"],
          "path": "/MailFolders"
        }
      }
    ]
  }
}
```

**`filterFields`** — fields used to narrow *which* events fire the trigger (e.g., only emails from a specific sender). These are optional filter criteria.

```json
{
  "filterFields": {
    "fields": [
      {
        "name": "fromAddress",
        "displayName": "From address",
        "type": "string",
        "required": false
      }
    ]
  }
}
```

**`outputResponseDefinition`** — the event payload schema (all fields the trigger outputs when it fires). **Save this** — you need it in Step 4b to know the exact field paths for downstream `$vars` expressions (e.g., `$vars.{nodeId}.output.text`, `$vars.{nodeId}.output.channel`). Do not guess output field names.

**`eventMode`** — `"webhooks"` or `"polling"`.

The response also includes `model.context` with:
- `connectorKey` — the connector identifier
- `operation` — the event operation name (e.g., `"EMAIL_RECEIVED"`, `"ISSUE_CREATED"`)
- `objectName` — the IS object (e.g., `"Message"`, `"Issue"`)

### Step 3 — Resolve reference fields in event parameters

Check `eventParameters.fields` for fields with a `reference` object — these require ID lookup, same as IS activity nodes.

```bash
# Example: resolve Outlook mail folder "Inbox" to its ID
uip is resources execute list "<connector-key>" "<reference.objectName>" \
  --connection-id "<id>" --output json
```

Use the resolved IDs in the trigger's event parameter configuration.

> **Paginate when looking up by name.** `execute list` returns one page (up to 1000 items) and surfaces `Data.Pagination.HasMore` + `Data.Pagination.NextPageToken`. If the target isn't on the first page, re-run with `--query "nextPage=<NextPageToken>"` until found or `HasMore` is `"false"`. Short-circuit as soon as the target name matches — don't pull every page.

**Read [/uipath:uipath-platform — Integration Service — resources.md](../../../../uipath-platform/references/integration-service/resources.md) for the full reference resolution workflow**, including pagination, describe failures, and fallback strategies.

### Step 4 — Validate required event parameters

Check every field in `eventParameters.fields` where `required: true`. All required event parameters must have values before building the flow.

1. Collect all required event parameter fields
2. For each, check if the user's prompt provides a value
3. If any required field is missing, **ask the user** — list the missing fields with their `displayName`
4. Only proceed after all required event parameters are resolved

### Step 4b — Map trigger output fields for downstream nodes

Before wiring downstream nodes, check `outputResponseDefinition` from Step 2 to know the exact field names available in `$vars.{triggerId}.output`. Do NOT guess field names — different triggers output different schemas.

Each trigger type has a different output schema — field names like `.text`, `.subject`, or `.body.content` vary by connector. Use the actual field names from `outputResponseDefinition` when writing expressions in downstream nodes.

### Step 5 — Replace the manual trigger with the connector trigger node

Follow the [CLI: Replace manual trigger with connector trigger](../../flow-editing-operations-cli.md#replace-manual-trigger-with-connector-trigger) procedure. The CLI handles edge cleanup, orphaned definition removal, and `variables.nodes` regeneration automatically. Note the generated node ID from the `node add` response — you need it for Step 6.

### Step 6 — Configure the trigger node

**Read the `--detail` field table below before calling `node configure`.** The fields and types are strict — unknown keys or wrong types cause validation errors. Do not guess field names from other node types (e.g., activity nodes use `method`/`endpoint`/`bodyParameters`; triggers use `eventMode`/`eventParameters`/`filterExpression`).

Use `node configure` with trigger-specific `--detail` fields:

```bash
uip maestro flow node configure <PROJECT>.flow <triggerId> --output json --detail '{
  "connectionId": "<CONNECTION_ID>",
  "folderKey": "<FOLDER_KEY>",
  "eventMode": "<EVENT_MODE>",
  "eventParameters": { "<paramName>": "<RESOLVED_VALUE>" },
  "filterExpression": "(contains(subject, 'urgent'))"
}'
```

**`--detail` fields for triggers:**

| Field | Required | Description |
|---|---|---|
| `connectionId` | Yes | Connection UUID from Step 1 |
| `folderKey` | Yes | Orchestrator folder key for the connection |
| `eventMode` | Yes | `"webhooks"` or `"polling"` — from `registry get` response |
| `eventParameters` | No | JSON object of resolved event parameter values from Steps 3-4 |
| `filterExpression` | No | JMESPath filter expression — see [JMESPath Filter Expressions](#jmespath-filter-expressions) below. Omit to trigger on all events |

The command populates `inputs.detail` (including the internal `configuration` blob) and creates workflow-level connection bindings.

> **Shell quoting tip:** For complex `--detail` JSON, write it to a temp file: `uip maestro flow node configure <file> <nodeId> --detail "$(cat /tmp/detail.json)" --output json`

---

## JMESPath Filter Expressions

Filter expressions use JMESPath syntax to narrow which events fire the trigger. They are passed as a string in the `filterExpression` field of `--detail` (Step 6). Field names come from `filterFields` returned by `registry get` (Step 2).

### Syntax Rules

1. Wrap the full expression in parentheses: `(expression)`
2. Field names are bare identifiers — no `fields.` prefix: `subject`, `fromAddress`, `status`
3. String values use single quotes: `'value'`
4. Use `==` / `!=` for equality/inequality comparisons
5. Use functions for substring/prefix matching: `contains(field, 'value')`, `starts_with(field, 'value')`
6. Use `&&` for AND, `||` for OR — not `and` / `or` keywords

### Supported Functions and Operators

| Syntax | Description | Example |
|---|---|---|
| `field == 'value'` | Exact match | `fromAddress == 'boss@example.com'` |
| `field != 'value'` | Not equal | `status != 'read'` |
| `contains(field, 'value')` | Field contains substring | `contains(subject, 'urgent')` |
| `starts_with(field, 'value')` | Field starts with prefix | `starts_with(subject, 'RE:')` |

### Combining Conditions

| Operator | Meaning | Example |
|---|---|---|
| `&&` | AND — both must match | `(status == 'new' && contains(subject, 'urgent'))` |
| `\|\|` | OR — either can match | `(status == 'new' \|\| status == 'updated')` |
| `()` | Grouping for precedence | `((contains(name, 'Inbox') \|\| id != '123') && type == 'mail')` |

### Examples

| Scenario | `filterExpression` value |
|---|---|
| Emails containing "urgent" in subject | `(contains(subject, 'urgent'))` |
| Emails from a specific sender | `(fromAddress == 'boss@example.com')` |
| Specific folder AND subject match | `(parentFolderId == 'AAMk...' && contains(subject, 'E2e test'))` |
| Multiple senders (OR) | `(fromAddress == 'a@ex.com' \|\| fromAddress == 'b@ex.com')` |
| Exclude read emails | `(status != 'read')` |
| Subject prefix match | `(starts_with(subject, 'RE:'))` |
| Complex: folder match OR name match | `(contains(FolderName, 'Inbox') \|\| FolderId != '12345')` |

### How to Build a Filter Expression from `filterFields`

1. Run `registry get` with `--connection-id` (Step 2) and read the `filterFields.fields` array
2. Each field object has a `name` (e.g., `fromAddress`, `subject`) — use these as the field argument
3. Choose the syntax based on the user's intent:
   - Exact match → `fieldName == 'value'`
   - Exclusion → `fieldName != 'value'`
   - Substring match → `contains(fieldName, 'value')`
   - Prefix match → `starts_with(fieldName, 'value')`
4. Combine multiple conditions with `&&` (AND) or `||` (OR)
5. Wrap the full expression in parentheses
6. If `filterFields` is empty or absent, the trigger does not support filtering — omit `filterExpression` entirely

### What NOT to Generate

| Invalid expression | Why it fails | Valid replacement |
|---|---|---|
| `((fields.subject == 'test'))` | Double parens, `fields.` prefix | `(subject == 'test')` |
| `` fields.fromAddress == `value` `` | Backtick quoting, `fields.` prefix | `(fromAddress == 'value')` |
| `{ "condition": "equals", "field": "status" }` | Transform filter syntax, not JMESPath | `(status == 'new')` |
| `subject contains 'test'` | English word order, not JMESPath function syntax | `(contains(subject, 'test'))` |
| `((fields.subject<\`test\`>))` | Legacy placeholder template — not valid JMESPath | `(contains(subject, 'test'))` |

---

## Bindings

Trigger nodes require more binding resources than activity nodes: `Connection` + `EventTrigger` + `Property` resources. **`node configure` and the packaging pipeline handle all of these automatically:**

- **Connection bindings** — created in the `.flow` file by `node configure` (Step 6)
- **EventTrigger + Property bindings** — generated into `bindings_v2.json` during `flow debug` or packaging from the trigger node's `inputs.detail`

You do **not** need to manually create or edit `bindings_v2.json` for trigger nodes.

---

## CLI Commands

```bash
# Discovery
uip maestro flow registry search trigger --output json               # find trigger node types
uip maestro flow registry pull --force                                # refresh registry (requires login)

# Enriched trigger metadata (--connection-id REQUIRED)
uip maestro flow registry get <triggerNodeType> --connection-id <connection-id> --output json

# Node lifecycle
uip maestro flow node delete <PROJECT>.flow start --output json       # remove manual trigger
uip maestro flow node add <PROJECT>.flow <triggerNodeType> --label "<LABEL>" --position 200,144 --output json
uip maestro flow node configure <PROJECT>.flow <nodeId> --detail '<TRIGGER_DETAIL_JSON>' --output json

# Trigger object metadata
uip is triggers objects "<connector-key>" "<operation>" --connection-id "<id>" --output json
uip is triggers describe "<connector-key>" "<operation>" "<objectName>" --connection-id "<id>" --output json

# Connections (same as IS activity)
uip is connections list "<connector-key>" --output json
uip is connections ping "<connection-id>" --output json

# Reference resolution (same as IS activity)
uip is resources execute list "<connector-key>" "<resource>" \
  --connection-id "<id>" --output json
```

---

## Testing Trigger Flows

`uip maestro flow debug` works with trigger-based flows. Debug does **not** wait for a live event — it **pulls the most recent matching event** from the connector's lookback window and executes immediately.

### How debug works for triggers

1. Debug calls the connector's `/events/debug` endpoint with `maxResults=5` and a `startDate` (default: 1 hour ago)
2. The connector returns up to 5 matching events from that window, sorted most-recent-first
3. The runtime uses `FilterMatches[0]` (the most recent match) as the trigger input
4. The flow executes immediately with that event data
5. If **no matching events** exist in the lookback window, debug fails with error code `3005` (TriggerNoMatches)

```bash
uip maestro flow debug . --output json
# → Fetches most recent matching event from the past ~1 hour
# → Flow executes immediately with that event data
```

### Polling vs webhook triggers in debug

| Trigger mode | Debug support | Behavior |
|---|---|---|
| `polling` | Supported | Pulls recent events via debug API, executes immediately |
| `webhooks` | **Not supported** | Webhook triggers cannot be tested in Studio debug mode — debug requires Orchestrator |

> **If the trigger uses `webhooks` event mode**, tell the user that debug is not available for webhook triggers. They must deploy to Orchestrator and test with a real webhook event.

### Key differences from manual-trigger debug

| Aspect | Manual trigger | Connector trigger (polling) |
|---|---|---|
| Execution start | Immediate with user-provided inputs | Immediate with most recent matching event |
| User action needed | Provide input values | Ensure a matching event exists in the past ~1 hour |
| Failure mode | Missing required inputs | No matching events in lookback window (error 3005) |

### Pre-debug checklist

1. **Verify the connection is healthy** — `uip is connections ping "<id>"`
2. **Confirm a matching event exists** — the user should have produced the event (e.g., sent an email, created a Jira issue) within the past hour
3. **Check event mode** — if `webhooks`, debug is not supported; inform the user

---

## Debug

### Common Errors

| Error | Cause | Fix |
|---|---|---|
| `Trigger nodes require --connection-id` | Ran `registry get` without `--connection-id` | Re-run with `--connection-id <id>` — required for all trigger nodes |
| No trigger nodes in registry | Not authenticated or registry not pulled | Run `uip login` then `uip maestro flow registry pull --force` |
| Connection not found in bindings | `node configure` not run or connection expired | Re-run `node configure` with valid `connectionId` and `folderKey` |
| Event parameter missing at runtime | Required event parameter not configured | Check `eventParameters.fields` for `required: true` fields and include them in `--detail` `eventParameters` |
| Filter expression syntax error | Wrong filter format | Use JMESPath syntax: `(field == 'value')` or `(contains(field, 'value'))` — see [JMESPath Filter Expressions](#jmespath-filter-expressions) |
| Trigger not firing | Event parameters point to wrong resource (e.g., wrong folder ID) | Re-resolve reference fields with `uip is resources execute list` |
| `model.context` missing operation | Node added without context entries | Delete and re-add the node — `node add` populates `model.context` from the registry definition |

### Debug Tips

1. **Always verify the connection is healthy** before debugging trigger issues — run `uip is connections ping "<id>"`
2. **`flow validate` does NOT catch trigger-specific issues** — missing event parameters, wrong reference IDs, and expired connections are caught only at runtime
3. **Event parameters with `reference` objects** need resolved IDs, not display names — same as IS activity fields
4. **Filter expressions are optional** — omit `filterExpression` from `--detail` if the user wants all events to trigger the flow
5. **Bindings are auto-managed** — `node configure` creates flow-level bindings; `flow debug`/packaging generates `bindings_v2.json` from them
6. **Use `uip maestro flow node delete` to remove the manual trigger** — do NOT manually edit the JSON to delete the start node. The CLI automatically removes associated edges, orphaned definitions, and regenerates `variables.nodes`. Direct JSON editing skips these cleanup steps and can leave orphaned references.
7. **Check `outputResponseDefinition` before writing downstream expressions** — trigger output field names vary by connector. Do not assume field names like `.text` or `.subject` — verify from the enriched `registry get` response (Step 2)
8. **Validate filter field names against `filterFields`** — only field names returned in `filterFields.fields[].name` are valid in filter expressions. Using a field name not in that list produces a silent no-match at runtime
