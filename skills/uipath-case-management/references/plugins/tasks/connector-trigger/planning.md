# connector-trigger task — Planning

A connector-based trigger **inside a stage** — waits for an external event (e.g., "issue created in Jira", "email received in Outlook") before continuing.

This plugin is **schema-data-driven** — one plugin covers every connector trigger. Per-connector event parameters and filter fields are discovered via IS CLI commands.

## When to Use

Pick this plugin when the sdd.md describes a task that **suspends the stage until an external event fires**. Typical patterns:

- "Wait until a new row appears in Salesforce"
- "Continue when a Slack reaction is added"
- "Suspend until an email arrives in Inbox"

Distinguish from:

- **Case-level event triggers** (start the case from outside) → [`plugins/triggers/event/`](../../triggers/event/planning.md)
- **Connector activity** (call out, don't wait) → [connector-activity](../connector-activity/planning.md)
- **Timer wait** (not connector-driven) → [wait-for-timer](../wait-for-timer/planning.md)

## Resolution Pipeline

Run these steps during planning. Each step feeds into the `tasks.md` entry.

### 1. Find the trigger in TypeCache

Read `~/.uip/case-resources/typecache-triggers-index.json` directly. Match on `displayName`, `connectorKey`, or `eventOperation` from sdd.md. Record `uiPathActivityTypeId`.

### 2. Resolve the connection

```bash
uip case registry get-connection \
  --type typecache-triggers \
  --activity-type-id "<uiPathActivityTypeId>" --output json
```

Returns `Entry`, `Config`, and `Connections`.

- **Single connection** → use it.
- **Multiple connections** → **AskUserQuestion** with connection names + "Something else".
- **Empty `Connections`** → mark `<UNRESOLVED: no IS connection for <connectorKey>>`. Execution creates a skeleton task.

Record `connection-id`, `connector-key`, `object-name`, `eventOperation`, `eventMode` from the response.

### 3. Describe the trigger — discover event parameters and filter fields

```bash
uip is triggers describe "<connector-key>" "<eventOperation>" "<object-name>" \
  --connection-id "<connection-id>" --output json
```

Returns:
- **`eventParameters`** — fields that configure *what* the trigger watches (e.g., which email folder, which Jira project). May be `required: true` and may have `reference` objects.
- **`filterFields`** — fields used to narrow *which* events fire the trigger (e.g., only emails from a specific sender). These are optional filter criteria.
- **`eventMode`** — `"polling"` or `"webhooks"`.

**This step is mandatory** — not optional. Without it, the agent cannot:
- Know which event parameters are required (e.g., `parentFolderId` for Email Received)
- Discover reference fields that need ID resolution
- Know which fields are available for filtering

### 4. Resolve reference fields in event parameters

Check `eventParameters` for fields with a `reference` object. For each, resolve display names from sdd.md to IDs:

```bash
uip is resources execute list "<connector-key>" "<reference.objectName>" \
  --connection-id "<connection-id>" --output json
```

Example — resolve folder "Inbox" to its ID:
```bash
uip is resources execute list "uipath-microsoft-outlook365" "MailFolder" \
  --connection-id "<connection-id>" --output json
# → items: [{ "id": "AAMkADNm...", "displayName": "Inbox" }, ...]
```

Match the sdd.md value to `displayName`. Use the resolved `id` in `input-values`.

> **Paginate when looking up by name.** If `Pagination.HasMore` is `true`, re-run with `--query "nextPage=<NextPageToken>"` until found.

If a reference cannot be resolved, **AskUserQuestion** with the available options. Do not guess.

### 5. Validate required event parameters

For each `eventParameters` entry with `required: true`:
1. Check if sdd.md provides a value
2. If missing, **AskUserQuestion** — list the missing parameter with its `displayName` and description
3. Only after all required event parameters have values, proceed

### 6. Map SDD inputs to event parameters vs filter fields

SDD input fields don't map 1:1 to the connector's schema. Cross-reference each SDD input against `eventParameters` and `filterFields` from Step 3 to decide where it goes:

- **eventParameters** → configure *what* the trigger monitors. Values must be **static** — resolved to IDs at planning time. Go into `input-values`.
- **filterFields** → narrow *which* events fire the trigger. Values can be **static** literals or **dynamic** `=vars.X` references resolved at runtime. Go into `filter`.

If an SDD input matches an `eventParameters` field name, it's an event parameter. If it matches a `filterFields` field name, it's a filter. If it matches neither, **AskUserQuestion** — the SDD may use different naming than the connector.

### 7. Build input-values and filter

**input-values** — resolved event parameter values (static IDs only):
```json
{"parentFolderId": "AAMkADNm..."}
```

**filter** — translate SDD filter criteria using `filterFields` from Step 3. Use JMESPath syntax. Supports `=vars.X` for runtime case variable references:

| Pattern | JMESPath |
|---|---|
| Exact match (static) | `(fieldName == 'value')` |
| Exact match (dynamic variable) | `(fieldName == '=vars.variableName')` |
| Substring match | `(contains(fieldName, 'value'))` |
| Multiple conditions | `(fieldA == 'x' && fieldB == 'y')` |

Only use field names that appear in `filterFields`. If a filter cannot be translated unambiguously, **AskUserQuestion**.

## tasks.md Entry Format

```markdown
## T<n>: Add connector-trigger task "<display-name>" to "<stage>"
- type-id: <uiPathActivityTypeId>
- connection-id: <connection-uuid>
- connector-key: <connectorKey>
- object-name: <objectName>
- event-operation: <eventOperation>
- event-mode: <polling|webhooks>
- input-values: {"parentFolderId": "AAMkADNm..."}
- filter: "(contains(subject, 'urgent'))"
- isRequired: true
- runOnlyOnce: false
- order: after T<m>
- lane: <n>
- verify: Confirm task created with correct event parameters
```

## Unresolved Fallback

If the connector or connection cannot be resolved:
- Mark `type-id` or `connection-id` with `<UNRESOLVED: reason>`
- Omit `input-values:` and `filter:` — no schema to wire against
- Execution creates a skeleton task (display-name + type only) per [skeleton-tasks.md](../../../skeleton-tasks.md)
