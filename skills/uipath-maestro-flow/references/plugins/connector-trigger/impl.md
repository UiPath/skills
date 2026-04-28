# Connector Trigger Nodes — Implementation

How to configure connector trigger nodes: connection binding, enriched metadata, event parameter resolution, and trigger-specific `node configure` fields. This replaces the IS activity workflow (Steps 1-6 in [connector/impl.md](../connector/impl.md)) — trigger nodes have different metadata and configuration.

## Configuration Workflow

Follow these steps for every IS trigger node.

### Step 1 — Fetch a preliminary connection and query trigger objects

Extract the connector key from the node type (`uipath.connector.trigger.<connector-key>.<trigger-name>`) and the operation name from the `registry get` response (`model.context[].operation`).

**1a. Get any enabled connection** — needed as `--connection-id` for `triggers objects` below. Pick any enabled one (prefer `IsDefault: Yes`):

```bash
uip is connections list "<connector-key>" --output json
```

If empty, follow the recovery in [/uipath:uipath-platform — connections.md — For Native Connectors](../../../../uipath-platform/references/integration-service/connections.md#for-native-connectors) (`--refresh` retry, then create-or-prompt).

**1b. Query trigger objects** — **mandatory** for every trigger node. Do NOT skip:

```bash
uip is triggers objects "<connector-key>" "<OPERATION>" \
  --connection-id "<id>" --output json
```

Save the response. It carries two flags per event object that drive later steps:

| Flag | Drives | Meaning |
|------|--------|---------|
| `byoaConnection` | Step 1c | If `true`, only BYOA connections are valid for this event |
| `isWebhookUrlVisible` | Step 6b | If `true`, retrieve and present the webhook URL |

It may also include `design.textBlocks` with connector-specific user-facing instructions (e.g., "Add this URL to your Slack app's Event Subscriptions"). Surface that text verbatim when applicable — do not invent service-specific guidance.

> Both flags are per event object, not per connector. Some connectors require BYOA for some events but not others.

### Step 1c — Select the final connection

**If `byoaConnection: true`** — the Step 1a connection is not usable. Follow the BYOA selection workflow in [/uipath:uipath-platform — connections.md — For BYOA Connections](../../../../uipath-platform/references/integration-service/connections.md#for-byoa-connections-webhook-triggers) (filter with `--byoa`, `--refresh` retry, stop-and-ask if none exist).

**If `byoaConnection: false`** — use the Step 1a connection. Verify health:

```bash
uip is connections ping "<connection-id>" --output json
```

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

**`filterFields`** — fields used to narrow *which* events fire the trigger (e.g., only emails from a specific sender). These are optional filter criteria and are passed as a structured tree in `--detail.filter` (see [Filter Trees](#filter-trees)).

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

> **Resolve every reference field freshly, against the current `--connection-id`, immediately before `node configure` (Step 6)** — even if you think you already know the ID from a previous flow. Reference IDs are connection-scoped and reused values fault silently at runtime. See [Reference IDs Are Connection-Scoped (CRITICAL)](../../../../uipath-platform/references/integration-service/reference-resolution.md#reference-ids-are-connection-scoped-critical) for the full mechanism and failure mode, and the top-level Anti-Patterns in [SKILL.md](../../../SKILL.md).

```bash
# Example: resolve Outlook mail folder "Inbox" to its ID
uip is resources execute list "<connector-key>" "<reference.objectName>" \
  --connection-id "<id>" --output json
```

The `<id>` in `--connection-id "<id>"` MUST be the connection bound to **this** flow (the final connection from Step 1c), not any other connection you've used in another flow. Use the resolved IDs — from this very `execute list` call — in the trigger's event parameter configuration.

> **Anti-pattern: do not pass the display name as the ID.** Reference fields take the GUID returned by `execute list` (e.g. the `id` field of an item — typically `"AAMkAD..."` for an Outlook MailFolder), **not** the human-readable folder name like `"Inbox"`. Passing the display name validates fine and may even round-trip through `flow validate`, but the trigger faults silently at runtime because the connector cannot resolve a non-GUID against the live connection. After running `execute list`, parse the response and extract the `id` value from the matching item — never substitute the user-typed name.

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

**Read the `--detail` field table below before calling `node configure`.** The fields and types are strict — unknown keys or wrong types cause validation errors. Do not guess field names from other node types (e.g., activity nodes use `method`/`endpoint`/`bodyParameters`; triggers use `eventMode`/`eventParameters`/`filter`).

Use `node configure` with trigger-specific `--detail` fields:

```bash
uip maestro flow node configure <PROJECT>.flow <triggerId> --output json --detail '{
  "connectionId": "<CONNECTION_ID>",
  "folderKey": "<FOLDER_KEY>",
  "eventMode": "<EVENT_MODE>",
  "eventParameters": { "<paramName>": "<RESOLVED_VALUE>" },
  "filter": {
    "groupOperator": 0,
    "index": 0,
    "filters": [
      {
        "id": "subject",
        "operator": "Contains",
        "value": { "value": "urgent", "rawString": "\"urgent\"", "isLiteral": true }
      }
    ]
  }
}'
```

**`--detail` fields for triggers:**

| Field | Required | Description |
|---|---|---|
| `connectionId` | Yes | Connection UUID from Step 1c (the final connection — BYOA if required) |
| `folderKey` | Yes | Orchestrator folder key for the connection |
| `eventMode` | Yes | `"webhooks"` or `"polling"` — from `registry get` response |
| `eventParameters` | No | JSON object of resolved event parameter values from Steps 3-4 |
| `filter` | No | Structured filter tree — see [Filter Trees](#filter-trees) below. Omit to trigger on all events |

The CLI derives the runtime JMESPath `filterExpression` from `filter` automatically and persists both into the workflow so Studio Web can re-open the trigger without losing the filter configuration (MST-8802). **Do not pass `filterExpression` directly — the validator rejects it.**

The command populates `inputs.detail` (including the internal `configuration` blob with the `filter` tree and derived `filterExpression`) and creates workflow-level connection bindings.

> **Shell quoting tip:** For complex `--detail` JSON, write it to a temp file: `uip maestro flow node configure <file> <nodeId> --detail "$(cat /tmp/detail.json)" --output json`

### Step 6b — Retrieve and display webhook URL (webhooks only)

Applies when `eventMode` is `"webhooks"`, regardless of `byoaConnection`.

> **Guard:** If the trigger object's `isWebhookUrlVisible` is `false` (from Step 1b), skip this step — the connector manages webhook registration automatically and does not expose a URL. If you do not have `triggers objects` output, you skipped Step 1b — go back.

Follow [/uipath:uipath-platform — triggers.md — Webhook URL Retrieval](../../../../uipath-platform/references/integration-service/triggers.md#webhook-url-retrieval) for the exact commands (`uip is connections list` → `ElementInstanceId` → `uip is webhooks config`).

**Presenting the URL:** If the Step 1b `triggers objects` response included `design.textBlocks`, use that text verbatim (substituting `{webhookUrl}`) — it carries connector-specific registration instructions. Otherwise, use a generic message instructing the user to register the URL in their external service's app settings (e.g., Slack Event Subscriptions, Salesforce Outbound Messages). The trigger will not fire until the URL is registered and verified.

**On failure:** if `ElementInstanceId` is empty, the connection is the wrong type — verify the `byoaConnection` flag from Step 1b and switch to a BYOA connection if required. If `webhooks config` itself fails, ping the connection (`uip is connections ping`) and re-authenticate via `uip is connections edit` if unhealthy.

---

## Filter Trees

Filters are authored as a **structured tree**, not a string expression. The CLI compiles the tree into a JMESPath `filterExpression` using the same logic Studio Web does, and writes both forms into the flow so the trigger round-trips cleanly when re-opened in SW.

### Tree shape

```jsonc
{
  "groupOperator": 0,             // 0 = And, 1 = Or — combines sibling filters/groups
  "index": 0,                     // ordering index within parent (root is 0)
  "filters": [                    // leaf conditions at this level
    {
      "id": "<fieldName>",        // from filterFields.fields[].name
      "operator": "<Operator>",   // see operator table below
      "value": {
        "value": <typed value>,   // string / number / boolean / ISO-8601 date-time
        "rawString": "\"...\"",   // verbatim user-entered text (with quotes for strings)
        "isLiteral": true         // literals only — expression values are not supported
      }
    }
  ],
  "groups": []                    // optional: nested subgroups (same shape as root)
}
```

A no-op filter — used when the user wants all events to fire the trigger — is `null` or `{"groupOperator": null, "index": 0, "filters": []}`. Prefer **omitting** the `filter` field entirely.

### Supported operators

| Operator | Meaning | Typical field types |
|---|---|---|
| `Equals` / `NotEquals` | Exact (in)equality | string, number, boolean |
| `LessThan` / `LessThanOrEqual` / `GreaterThan` / `GreaterThanOrEqual` | Numeric comparison | number, integer |
| `Contains` / `NotContains` | Substring match | string |
| `StartsWith` / `NotStartsWith` / `EndsWith` / `NotEndsWith` | Prefix / suffix match | string |
| `IsEmpty` / `IsNotEmpty` | Value is / is not empty string | string (no `value` needed) |
| `Is` / `IsNot` | Boolean is true / false | boolean (no `value` needed) |
| `In` / `NotIn` / `IsOneOf` / `IsNotOneOf` | Membership — pass comma-separated values in `value.value` | string, number |
| `Before` / `BeforeOrEqual` / `After` / `AfterOrEqual` / `DateTimeEquals` / `DateTimeNotEqual` | Date-time comparison (ISO-8601 strings) | date-time |

### Examples

**Emails containing "urgent" in the subject:**

```json
{
  "groupOperator": 0,
  "index": 0,
  "filters": [
    { "id": "subject", "operator": "Contains",
      "value": { "value": "urgent", "rawString": "\"urgent\"", "isLiteral": true } }
  ]
}
```

**Emails from a specific sender AND subject contains "good day":**

```json
{
  "groupOperator": 0,
  "index": 0,
  "filters": [
    { "id": "from", "operator": "Equals",
      "value": { "value": "boss@example.com", "rawString": "\"boss@example.com\"", "isLiteral": true } },
    { "id": "subject", "operator": "Contains",
      "value": { "value": "good day", "rawString": "\"good day\"", "isLiteral": true } }
  ]
}
```

**Multiple senders (OR) nested inside an outer AND with a subject match:**

```json
{
  "groupOperator": 0,
  "index": 0,
  "filters": [
    { "id": "subject", "operator": "Contains",
      "value": { "value": "urgent", "rawString": "\"urgent\"", "isLiteral": true } }
  ],
  "groups": [
    {
      "groupOperator": 1,
      "index": 1,
      "filters": [
        { "id": "from", "operator": "Equals",
          "value": { "value": "a@ex.com", "rawString": "\"a@ex.com\"", "isLiteral": true } },
        { "id": "from", "operator": "Equals",
          "value": { "value": "b@ex.com", "rawString": "\"b@ex.com\"", "isLiteral": true } }
      ]
    }
  ]
}
```

### How to build a filter tree from `filterFields`

1. Run `registry get` with `--connection-id` (Step 2) and read the `filterFields.fields` array.
2. For each user-intent condition, pick a matching field `name` from that array — using an unknown field name will be rejected by the CLI at configure time.
3. Choose an operator based on the user's intent and the field type (see operator table).
4. Build one leaf per condition; place multiple conditions under the same `groupOperator` (0 for AND, 1 for OR).
5. If you need mixed AND/OR logic, use nested `groups`.
6. **Wrap string values in a `value` object** with `value`, `rawString`, `isLiteral: true` — passing a bare string will fail validation.
7. If `filterFields` is empty or absent, the trigger does not support filtering — omit `filter` entirely.

### What NOT to generate

| Invalid input | Why it fails | Valid replacement |
|---|---|---|
| `"filterExpression": "(contains(subject, 'x'))"` | Legacy format — the CLI now rejects `filterExpression` as an input field (see MST-8802). It is *only* an output in the generated `.flow`. | Build a `filter` tree with a `Contains` leaf. |
| `"filter": "(subject == 'x')"` | `filter` must be an object, not a string. | Structured tree with `filters: [...]`. |
| `{ "id": "fields.subject", ... }` | `fields.` prefix — use the bare field name from `filterFields.fields[].name`. | `{ "id": "subject", ... }` |
| `{ "id": "subject", "operator": "contains", ... }` | Operator is case-sensitive — use PascalCase. | `"operator": "Contains"` |
| `{ "value": "urgent" }` on a leaf | Bare string — must be wrapped in the `WorkflowValue` object. | `{ "value": { "value": "urgent", "rawString": "\"urgent\"", "isLiteral": true } }` |
| `{ "isLiteral": false, "value": "${var}" }` | Expression values are not yet supported by the CLI port. | Resolve the value first, then pass it as a literal. |
| `{ "id": "tags[*].name", ... }` | Array-field filters are not yet supported. | File a follow-up; use a scheduled poll + in-flow filter for now. |

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

# Trigger object metadata (MANDATORY — Step 1b)
uip is triggers objects "<connector-key>" "<operation>" --connection-id "<id>" --output json
uip is triggers describe "<connector-key>" "<operation>" "<objectName>" --connection-id "<id>" --output json

# Connections — see /uipath:uipath-platform — connections.md for selection rules (Native, BYOA, --refresh)
uip is connections list "<connector-key>" --output json               # list connections
uip is connections list "<connector-key>" --byoa --output json        # BYOA only (Step 1c)
uip is connections ping "<connection-id>" --output json               # verify health

# Reference resolution (same as IS activity)
uip is resources execute list "<connector-key>" "<resource>" \
  --connection-id "<id>" --output json

# Webhook URL retrieval — see /uipath:uipath-platform — triggers.md (Step 6b, webhooks only)
uip is webhooks config "<connector-key>" \
  --connection-id "<connection-guid>" \
  --element-instance-id <number> --output json
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
| `filterExpression is derived from the filter tree and cannot be provided directly` | Passed `filterExpression` string instead of a `filter` tree | Build a structured `filter` tree — see [Filter Trees](#filter-trees) |
| `Filter references field '<name>' which is not present in trigger metadata` | Leaf `id` does not match any `filterFields.fields[].name` | Re-run `registry get` and use a valid field name |
| Trigger not firing | Event parameters point to wrong resource (e.g., wrong folder ID) | Re-resolve reference fields with `uip is resources execute list` |
| Trigger faults immediately with no visible error after a clean build | Event parameter uses a reference ID scoped to a **different** connection (common when copying from a prior flow in the same session — e.g., a `parentFolderId` for mailbox A pasted into a trigger bound to mailbox B's connection) | Re-run `uip is resources execute list "<connector-key>" "<objectName>" --connection-id <CURRENT_CONNECTION_ID>`, extract the fresh ID, update `eventParameters` in `--detail`, re-run `node configure`, re-debug. See Step 3 and the top-level Anti-Pattern on reference-ID reuse in [SKILL.md](../../../SKILL.md). |
| `model.context` missing operation | Node added without context entries | Delete and re-add the node — `node add` populates `model.context` from the registry definition |
| Trigger faults at runtime with webhook-related error | Standard (non-BYOA) connection used for a trigger that requires `byoaConnection: true` | Run `uip is triggers objects` (Step 1b) to check `byoaConnection` flag, then switch to a BYOA connection with `uip is connections list "<connector-key>" --byoa --output json`. If no BYOA connections exist, user must create one. |
| `connections list` returns empty but connections exist in the IS portal | CLI is using cached connection data that is stale | Retry with `--refresh` flag: `uip is connections list "<connector-key>" --refresh --output json` |
| `ElementInstanceId` is empty on the selected connection | Connection is not a BYOA connection, or connector does not support webhooks on this connection type | Verify the trigger requires BYOA (Step 1b `byoaConnection` flag). If `true`, switch to a BYOA connection. |

### Debug Tips

1. **Always verify the connection is healthy** before debugging trigger issues — run `uip is connections ping "<id>"`
2. **`flow validate` does NOT catch trigger-specific issues** — missing event parameters, wrong reference IDs, and expired connections are caught only at runtime
3. **Event parameters with `reference` objects** need resolved IDs, not display names — same as IS activity fields
4. **Filters are optional** — omit `filter` from `--detail` if the user wants all events to trigger the flow. Do not invent an "empty" expression.
5. **Bindings are auto-managed** — `node configure` creates flow-level bindings; `flow debug`/packaging generates `bindings_v2.json` from them
6. **Use `uip maestro flow node delete` to remove the manual trigger** — do NOT manually edit the JSON to delete the start node. The CLI automatically removes associated edges, orphaned definitions, and regenerates `variables.nodes`. Direct JSON editing skips these cleanup steps and can leave orphaned references.
7. **Check `outputResponseDefinition` before writing downstream expressions** — trigger output field names vary by connector. Do not assume field names like `.text` or `.subject` — verify from the enriched `registry get` response (Step 2)
8. **Validate filter field names against `filterFields`** — only field names returned in `filterFields.fields[].name` are valid leaf `id`s in the filter tree. The CLI rejects trees that reference unknown fields at configure time, so guessing will surface as an `InvalidDetailError` rather than a silent runtime no-match.
