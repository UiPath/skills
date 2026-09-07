<!--skill-flavor:ct-configure-command:start-->
```bash
uip maestro flow node configure /solution/<FlowProject>/new.flow <triggerId> --output json --detail '{
  "connectionId": "<CONNECTION_ID>",
  "folderKey": "<FOLDER_KEY>",
  "eventMode": "<EVENT_MODE>",
  "objectName": "<OBJECT_NAME>",
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
<!--skill-flavor:ct-configure-command:end-->

<!--skill-flavor:ct-event-node-add:start-->
```bash
uip maestro flow node add /solution/<FlowProject>/new.flow uipath.connector.event.<key>.<event> \
  --label "<LABEL>" --position 400,144 --output json
```
<!--skill-flavor:ct-event-node-add:end-->

<!--skill-flavor:ct-bindings:start-->
Trigger nodes require more binding resources than activity nodes: `Connection` + `EventTrigger` + `Property` resources. **`node configure` and the host handle all of these automatically:**

- **Connection bindings** — created in the `.flow` file by `node configure` (Step 6)
- **EventTrigger + Property bindings** — `node configure` writes `bindings_v2.json` in the project directory (`/solution/<FlowProject>/bindings_v2.json`); the host debug reads the saved project directly

You do **not** need to manually create or edit `bindings_v2.json` for trigger nodes.
<!--skill-flavor:ct-bindings:end-->

<!--skill-flavor:ct-cli-commands:start-->
```bash
# Discovery
uip maestro flow registry search trigger --output json               # find trigger node types
uip maestro flow registry pull --force                                # refresh registry (auth is host-provided)

# Enriched trigger metadata (--connection-id REQUIRED)
uip maestro flow registry get <trigger-node-type> --connection-id <connection-id> --output json

# Node lifecycle
uip maestro flow node remove /solution/<FlowProject>/new.flow start --output json       # remove manual trigger
uip maestro flow node add /solution/<FlowProject>/new.flow <trigger-node-type> --label "<LABEL>" --position 200,144 --output json
uip maestro flow node configure /solution/<FlowProject>/new.flow <nodeId> --detail '<TRIGGER_DETAIL_JSON>' --output json

# Trigger object metadata (MANDATORY — Steps 1b and 1b-2)
uip is triggers objects "<connector-key>" "<operation>" --connection-id "<id>" --output json   # Step 1b: objects + parameters[]
uip is triggers describe "<connector-key>" "<operation>" "<objectName>" --connection-id "<id>" --output json  # Step 1b-2: fields

# Connections — see /uipath:uipath-platform — connections.md for selection rules (Native, BYOA, --refresh)
uip is connections list "<connector-key>" --all-folders --output json         # discover connections (--all-folders is mandatory)
uip is connections list "<connector-key>" --byoa --all-folders --output json  # BYOA only (Step 1c)
uip is connections ping "<connection-id>" --output json               # verify health

# Reference resolution (same as IS activity)
uip is resources run list "<connector-key>" "<resource>" \
  --connection-id "<id>" --output json

# Webhook URL retrieval — see /uipath:uipath-platform — triggers.md (Step 6b, webhooks only)
uip is webhooks config "<connector-key>" \
  --connection-id "<connection-guid>" \
  --element-instance-id <number> --output json
```
<!--skill-flavor:ct-cli-commands:end-->

<!--skill-flavor:ct-testing:start-->
`uip flow debug` works with trigger-based flows (two-token verb — `uip maestro flow debug` is not intercepted and fails in the browser bundle). Debug does **not** wait for a live event — it **pulls the most recent matching event** from the connector's lookback window and executes immediately.

### How debug works for triggers

1. Debug calls the connector's `/events/debug` endpoint with `maxResults=5` and a `startDate` (default: 1 hour ago)
2. The connector returns up to 5 matching events from that window, sorted most-recent-first
3. The runtime uses `FilterMatches[0]` (the most recent match) as the trigger input
4. The flow executes immediately with that event data
5. If **no matching events** exist in the lookback window, debug fails with error code `3005` (TriggerNoMatches)

```bash
uip flow debug
# → runs the saved open project (no positional needed; a project NAME selects another project in the solution)
# → fetches the most recent matching event from the past ~1 hour and executes immediately
# → plain-text output: status line, Trace ID, Run logs, Execution trace
```

If it prints `TimedOut after 300s` with `(no run logs emitted)`, ask the user to run Debug from the designer.

### Polling vs webhook triggers in debug

| Trigger mode | Debug support | Behavior |
|---|---|---|
| `polling` | Supported | Pulls recent events via debug API, executes immediately |
| `webhooks` | **Not supported** | Webhook triggers cannot be tested in debug — publish and fire a real event |

> **If the trigger uses `webhooks` event mode**, tell the user that debug is not available for webhook triggers. Publish the open solution (`uip flow publish --location "<FolderPathOrKey>"`; destination from `uip solution publish --help` PublishLocations) and test with a real webhook event.

### Key differences from manual-trigger debug

| Aspect | Manual trigger | Connector trigger (polling) |
|---|---|---|
| Execution start | Immediate with user-provided inputs | Immediate with most recent matching event |
| User action needed | Provide input values | Ensure a matching event exists in the past ~1 hour |
| Failure mode | Missing required inputs | No matching events in lookback window (error 3005) |

### Pre-debug checklist

1. **Verify the connection is healthy** — `uip is connections ping "<id>"`
2. **Confirm a matching event exists** — the user should have produced the event (e.g., sent an email, created a Jira issue) within the past hour
3. **Check event mode** — if `webhooks`, debug is not supported; inform the user and publish instead
<!--skill-flavor:ct-testing:end-->

<!--skill-flavor:ct-debug-table:start-->
| Error | Cause | Fix |
|---|---|---|
| `Trigger nodes require --connection-id` | Ran `registry get` without `--connection-id` | Re-run with `--connection-id <id>` — required for all trigger nodes |
| `Invalid --detail` saying `objectName is required for the trigger` — or, on older CLIs, an opaque `Error configuring node` / `Response returned an error code` on every `--detail` shape | The trigger is **generic** (`activityType: "GenericTrigger"`, e.g. Data Fabric `record-created`): its manifest ships the `objectName` context entry without a value, and configure needs the object to fetch trigger metadata. Older CLIs rejected `objectName` as a `--detail` key and called the metadata API with an empty object name — hence the opaque server error. | Pass the object in `--detail.objectName` (resolve it per Step 1b-2). On an older CLI that rejects the key, `Edit` the trigger **definition's** `model.context` `objectName` entry to add `"value": "<object>"`, then re-run `node configure`. Curated triggers never need this — their manifest carries the objectName. |
| No trigger nodes in registry | Registry not pulled, or the signed-in user lacks rights (401/403) | Run `uip maestro flow registry pull --force` (auth is host-provided) |
| Connection not found in bindings | `node configure` not run or connection expired | Re-run `node configure` with valid `connectionId` and `folderKey` |
| Event parameter missing at runtime | Required event parameter not configured (commonly one returned by `triggers describe` but absent from `triggers objects → parameters[]`) | Re-run **both** `uip is triggers objects` (Step 1b) **and** `uip is triggers describe` (Step 1b-2). Configure every field marked `required` in **either** `parameters[]` or `EventParameters` (resolving references) under the correct `--detail` bucket. |
| `filterExpression is derived from the filter tree and cannot be provided directly` | Passed `filterExpression` string instead of a `filter` tree | Build a structured `filter` tree — see [Filter Trees](#filter-trees) |
| Trigger fires on events the filter should exclude; `node configure` reported Success | A leaf `id` does not match any `filterFields.fields[].name` (matching is case-sensitive). The CLI drops the unmatched leaf from the compiled `filterExpression` instead of failing | Re-run `registry get --connection-id <id>`, compare every leaf `id` against `filterFields.fields[].name`, then re-run `node configure` with the exact names |
| Trigger not firing | Event parameters point to wrong resource (e.g., wrong folder ID) | Re-resolve reference fields with `uip is resources run list` |
| Trigger faults immediately with no visible error after a clean build | Event parameter uses a reference ID scoped to a **different** connection (common when copying from a prior flow in the same session — e.g., a `parentFolderId` for mailbox A pasted into a trigger bound to mailbox B's connection) | Re-run `uip is resources run list "<connector-key>" "<objectName>" --connection-id <CURRENT_CONNECTION_ID>`, extract the fresh ID, update `eventParameters` in `--detail`, re-run `node configure`, re-debug. See Step 3 and the top-level Anti-Pattern on reference-ID reuse in [SKILL.md](../../../../SKILL.md). |
| Definition's `model.context` missing operation | Definition not copied correctly, or node added before registry pull | Re-run `uip maestro flow registry pull --force`, then verify the `definitions[]` entry contains `model.context` with `connectorKey`/`operation`/`objectName` as returned by `registry get` |
| Trigger faults at runtime with webhook-related error | Standard (non-BYOA) connection used for a trigger that requires `byoaConnection: true` | Run `uip is triggers objects` (Step 1b) to check `byoaConnection` flag, then switch to a BYOA connection with `uip is connections list "<connector-key>" --byoa --output json`. If no BYOA connections exist, user must create one. |
| `connections list` returns empty but connections exist in the IS portal | CLI is using cached connection data that is stale | Retry with `--refresh` flag: `uip is connections list "<connector-key>" --refresh --output json` |
| `ElementInstanceId` is empty on the selected connection | Connection is not a BYOA connection, or connector does not support webhooks on this connection type | Verify the trigger requires BYOA (Step 1b `byoaConnection` flag). If `true`, switch to a BYOA connection. |
<!--skill-flavor:ct-debug-table:end-->

<!--skill-flavor:ct-debug-tip-bindings:start-->
5. **Bindings are auto-managed** — `node configure` creates flow-level bindings and writes `bindings_v2.json` in the project directory; the host debug reads the saved project directly
<!--skill-flavor:ct-debug-tip-bindings:end-->
