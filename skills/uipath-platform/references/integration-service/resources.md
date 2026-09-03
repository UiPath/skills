# Resources

Resources represent the data objects available through a connector (e.g., Salesforce Account, Contact, Opportunity). Each resource supports a set of CRUD operations.

> Full command syntax and options: [uip-commands.md — Integration Service](../uip-commands.md#integration-service-is). Domain-specific usage patterns are shown inline below.

## Contents
- Listing and Describing Resources
- Response Fields
- Describe Response
- Describe Failures
- Parent-Field-Driven Custom Fields (api-type ObjectActions)
- Execute Operations
- Executing an Action Script (v4 activities)
- Pagination
- Execute Error Handling

For reference field resolution (simple refs, dependency chains, required field validation), see [reference-resolution.md](reference-resolution.md).

---

## Listing and Describing Resources

**Always pass `--connection-id`** to get connection-specific metadata including custom objects and fields. Without it, only standard objects/fields are returned.

## Response Fields

| Field | Description |
|---|---|
| **`Name`** | Resource identifier (used in commands) |
| `DisplayName` | Human-readable name |
| `Path` | API path for this resource |
| `Type` | Resource type (standard, custom) |
| `SubType` | Sub-type (e.g., method, entity) |

## Describe Response

The describe command returns metadata from the raw API. The output depends on whether `--operation` is provided.

### Without `--operation` — operation summary

Returns which operations the resource supports:

| Field | Description |
|---|---|
| **`availableOperations`** | List of operations — each with `method` (GET/POST/PATCH/PUT/DELETE), `name` (Create/List/etc.), `description`, `curated` (display name) |
| **`hint`** | Instructs to use `--operation` for field details |

### With `--operation` — per-operation field detail

Returns the full field breakdown for the specified operation:

| Field | Description |
|---|---|
| **`operation`** | Operation info — `method`, `name`, `description`, `path`, `curated` display name |
| **`parameters`** | Path and query parameters (NOT body fields) — each with `name`, `type` (path/query), `dataType`, `required`, `defaultValue`, `reference` |
| **`requestFields`** | Fields to send in `--body` — each with `name`, `type`, `displayName`, `required`, `description`, `reference`, `enum` |
| **`responseFields`** | Fields returned in the response — each with `name`, `type`, `displayName` |

> **Always use `--operation`** to get actionable field detail. Without it you only see which operations exist.

### Key field properties

- **`required: true`** — field must be provided in `--body` or `--query`. Do NOT skip.
- **`reference`** — field value must be looked up from another resource. See [reference-resolution.md](reference-resolution.md). When baking a static value for a reference field, also emit `designTimeMetadata.designTimeLookups` so the edit-UI renders a label — see [reference-resolution.md — Static Reference-Value Labeling](reference-resolution.md#static-reference-value-labeling).
- **`enum`** — field only accepts the listed values (e.g., `["low", "normal", "high"]`).

Results are cached locally. Use `--refresh` to bypass cache after re-auth or schema changes.

### `--activity-version`

Pass `--activity-version 4.0.0` only when the activity's `configuration` JSON reports `"version":"4.0.0"`. Otherwise do not pass the flag at all. Any value other than `1.0.0` (the default) or `4.0.0` fails with `Invalid --activity-version value`. `4.0.0` responses cache under a separate key (`<activity-name>.v4.schema.json`), so switching never serves the other version's metadata.

The resource argument follows the same rule: `4.0.0` activities are addressed by **activity name** — pass the `activityName` from the `configuration` JSON (`4.0.0` metadata has no `objectName`). Everything else uses the object name.

```bash
uip is resources describe <connector-key> <object-name> --output json
uip is resources describe <connector-key> <activity-name> --activity-version 4.0.0 --output json
```

---

## Describe Failures

Some resources return an error on describe. This is a **server-side metadata gap** — do not retry with `--refresh`.

**Recovery:**

1. **Skip describe entirely** — do not waste calls retrying.
2. **Infer fields from user context** — use the field names and values the user provided in their request.
3. **Infer reference fields from naming** — see [reference-resolution.md — Inferring References Without Describe](reference-resolution.md#inferring-references-without-describe).
4. **Attempt execute directly** — let the server validate. If a field is rejected, read the error and adjust.

---

## Parent-Field-Driven Custom Fields (api-type ObjectActions)

For connectors whose required fields depend on parent-field selections (Jira `GenerateSchema` keyed off project + issue type, Salesforce SOQL `GenerateQuerySchema` keyed off the query string, Dataservice V3 `FetchObjectMetadataTenant` keyed off `tenantEntityName`), the base `describe` returns only base fields. To preview the full required-field set the runtime will see, pass parent values via `-f, --field`:

```bash
# Jira: project + issue type → custom fields (GET, query-param tokens)
uip is resources describe uipath-atlassian-jira curated_create_issue \
  --connection-id "<id>" --operation Create \
  -f fields.project.key=ENGCE \
  -f fields.issuetype.id=3 \
  --output json

# Salesforce SOQL: query string → response columns (POST, body token)
uip is resources describe uipath-salesforce-sfdc query_records \
  --connection-id "<id>" --operation Create \
  -f query="SELECT Id, Name FROM Account WHERE Status = 'Active'" \
  --output json
```

What it does — runs the matching api-type ObjectAction against the IS Element Service (same path Studio Web's dispatcher uses), then merges the response into `requestFields` per the action's `onSuccess.remapConfiguration`. Use it before validating required fields to catch project- or operation-specific mandatory fields the base describe can't see.

| Flag | Notes |
|------|-------|
| `-f, --field <name=value>` | Repeatable. Token names match `apiConfiguration.url` and `apiConfiguration.body` placeholders verbatim — no `_sub_` encoding (encoding only applies when caching parent values for runtime replay; see [activities.md — Custom Fields](activities.md#custom-fields-objectactionsactiontypeapi)). |
| `--action <name>` | Optional. Disambiguates when more than one api-type action could match the field set. |

Requires `--connection-id` and `--operation`. Cache is bypassed when `--field` is supplied — the action response varies per parent-field combination. The merge mode (`replace` / `append` / `prepend` / `noop`) comes from the action's `remapConfiguration.input`; for Jira `GenerateSchema` it is `replace`.

When no api-type action's `rules[]` are satisfied by the supplied fields, the CLI errors with `No api-type ObjectAction matched for fields [...]`. List the operation's actions from the describe output's `connectorMethodInfo.design.actions[]` (or top-level `objectActions[]` for older shapes) to see which fields each action requires.

---

## Execute Operations

| Verb | Description | `--body` | `--query` |
|---|---|---|---|
| `create` | Create a new record | Yes | No |
| `list` | Retrieve multiple records | No | Optional (`limit=10&offset=0`) |
| `get` | Get a single record by ID | No | Yes (`id=<RECORD_ID>`) |
| `update` | Partial update (PATCH) | Yes | Yes (`id=<RECORD_ID>`) |
| `delete` | Delete a record | No | Yes (`id=<RECORD_ID>`) |
| `replace` | Full replacement (PUT) | Yes | Yes (`id=<RECORD_ID>`) |

> **Update** (PATCH) = change specific fields. **Replace** (PUT) = overwrite entire record. Default to **Update** unless the user says "replace" or "overwrite".

## Executing an Action Script

A v4 activity is an action script, not a CRUD object, so `run <verb>` cannot
execute it. Run it with:

```bash
uip is resources scripts execute \
  --connection-id "<id>" \
  --inline-script @<path-to-script>.js \
  --body '{"field": "value"}' --output json
```

Three modes, exactly one per call:

| flag | runs |
|---|---|
| `--inline-script <src\|@file\|->` | a local script — source directly, `@path` to read a file, `-` for stdin |
| `--script-ref <name>` | a published script; needs `--connector-key` |
| `--url <url> --method <verb>` | one direct vendor call, no script — the URL must be absolute |

`--body` differs by mode: with a script it is the script's input
(`context.request.body`); with `--url` it is the vendor's own payload. `--query`
and `--header` fill the rest of the script's inbound request — `--header` is how a
paging token is echoed back for the next page.

### Reading the result

```jsonc
{ "Result": "Success", "Code": "ScriptExecuted",
  "Data": { "Outcome": "vendor",        // `proxy_error` ⇒ never reached the vendor
            "Status": 400,              // the VENDOR's status, verbatim
            "Body": "{\"ok\":false,…}",  // a STRING — parse it yourself
            "Diagnostics": { "VendorCallCount": 1, "ScriptCpuMs": 14 } } }
```

**Read `Data.Outcome`, not the status** — a vendor 404 and an infrastructure
failure can both be 404. `Data.Body` is deliberately unparsed: a vendor may
answer with something that is not JSON, and the raw text is what diagnoses a
failure. Extract the payload with `jq -r '.Data.Body'`.

**The command exits 0 for any vendor answer, whatever the status.** A vendor 400
is a normal result, not a command failure — it exits 1 only when the request never
reached the vendor, and 3 on a bad argument. So `set -e` will not stop a loop on a
vendor rejection; branch on `Data.Status` and `Data.Body` yourself.

| `ErrorCode` when `Outcome` is `proxy_error` | means |
|---|---|
| `credential` | the connection could not mint a token — check it is Enabled |
| `guard_block` | the target is outside the connection's allowed origin |
| `script_invalid` | the script did not compile — **or** inline source is not permitted |
| `script_artifact_missing` | `--script-ref` unresolved, or `--connector-key` mismatched |
| `script_quota` | the call or egress budget was exceeded |
| `script_deadline` | CPU or wall-clock budget exceeded |

`script_invalid` has two very different causes and the message does not always
separate them. If the script compiles locally, suspect the second.

### Resolving reference fields for a script

Same discipline as [reference-resolution.md](reference-resolution.md), different
mechanism. A v4 reference is **`scriptRef`-only** — it carries no `objectName`,
`path` or `childPath` — so you do not list a referenced object, you **run a lookup
script** and filter its output:

```jsonc
"reference": { "scriptRef": "ListChannels", "lookupValue": "id",
               "lookupNames": ["name", "id"] }
```

Everything else carries over: reference IDs stay connection-scoped, you match on
`lookupNames` and pass `lookupValue`, and dependency chains still run in order.
Note there is no `filterPattern` equivalent, so a search-style reference against
an object too large to list has no v4 form — the lookup script must take a filter
as an input instead.

### Filtering Results with `--output-filter`

Use the global `--output-filter` flag with a JMESPath expression to extract specific fields from large responses if possible via JMESPath.

```bash
# Extract only id, name, and email from a user list
uip is resources run list "<CONNECTOR_KEY>" "<OBJECT_NAME>" \
  --connection-id "<CONNECTION_ID>" \
  --output json \
  --output-filter "Data[].{id: id, name: name, email: profile.email}"
```

Common JMESPath patterns:

| Pattern | Effect |
|---|---|
| `Data[]` | Return all records (unwrap the Data envelope) |
| `Data[].name` | Return just the `name` field from each record |
| `Data[].{id: id, name: name}` | Return selected fields as objects |
| `Data[?status=='active']` | Filter records by field value |
| `Data[0]` | Return only the first record |

---

## Pagination

`uip is resources run list` may not return all results in a single call. **Always check for pagination** when searching for a specific item or listing all items.

### Pagination rules

1. **Always check `Data.Pagination`** — every `list` response may contain pagination state. Never assume a single page contains all results.
2. **Complete the pagination loop** — when searching for a specific item, keep paginating until `Data.Pagination.HasMore` is `"false"` or the item is found. Do NOT abandon pagination mid-loop to try alternative APIs (e.g., search endpoints, admin endpoints, HTTP fallback).
3. **Stop early on match** — if you find the target item in the current page, stop. No need to fetch remaining pages.
4. **Report not-found only after exhausting all pages** — only conclude an item does not exist after `HasMore` is `"false"` and every page has been checked.

### Connector pagination

Most IS connectors use the `elements-*` pagination protocol. The CLI returns pagination state nested inside `Data.Pagination`:

- **`Data.Pagination.HasMore`**: `"true"` or `"false"` — indicates if more pages exist
- **`Data.Pagination.NextPageToken`**: the token value to use for the next page

**IMPORTANT:** The query parameter name is `nextPage` (NOT `nextPageToken`). Pass the value from `Data.Pagination.NextPageToken` as `--query "nextPage=<value>"`.

```bash
# First page (do not pass pageSize unless the user explicitly requests a specific page size)
uip is resources run list "<connector-key>" "<resource>" \
  --connection-id "<id>" --output json
# → Check Data.Pagination.HasMore and Data.Pagination.NextPageToken in the JSON response

# Subsequent pages — use nextPage as the query param name (NOT nextPageToken)
uip is resources run list "<connector-key>" "<resource>" \
  --connection-id "<id>" --query "nextPage=<value-from-NextPageToken>" --output json
# → Continue until Data.Pagination.HasMore is "false" or target item is found
```

Example response:
```json
{
  "Result": "Success",
  "Code": "ExecuteOperation",
  "Data": {
    "items": [ ... ],
    "Pagination": {
      "HasMore": "true",
      "NextPageToken": "eyJwYWdl..."
    }
  }
}
```

### Anti-patterns

- **Do NOT check `Data.nextPage`** — pagination lives at `Data.Pagination.HasMore` and `Data.Pagination.NextPageToken`, not at `Data.nextPage`.
- **Do NOT abandon pagination to try other APIs** — if you are paginating through `conversations` to find a channel, do not stop mid-loop to call `admin_conversations_search`, `search_all`, or `search_messages`. Complete the loop first.
- **Do NOT conclude "not found" after one page** — a single page may return only a fraction of the total results. Always check `Data.Pagination.HasMore` before concluding.

### Query-param pagination (offset/limit)

Some resources support `offset`/`limit` via `--query`:

```bash
uip is resources run list "<connector-key>" "<object>" \
  --connection-id "<id>" --query "limit=50&offset=0" --output json
# → next page: --query "limit=50&offset=50"
```

Stop when the result set is empty or smaller than the limit.

### HTTP connector exception

Connectors with key `uipath-uipath-http` do NOT use the `elements-*` pagination headers. These depend on vendor-specific pagination. Handle on a case-by-case basis.

---

## Execute Error Handling

When an execute command fails, the CLI returns:
- **`Message`**: HTTP status (e.g., `400 Bad Request`)
- **`Instructions`**: The raw vendor error response body as JSON

### How to diagnose failures

1. **Read `Message`** — the HTTP status code tells you the category (400 = bad request, 403 = forbidden, 404 = not found, etc.)
2. **Read `Instructions`** — the raw vendor error body tells you WHAT specifically failed (invalid field, missing required value, permission denied, etc.)
3. **Use discovery to fix** — run `describe` to get valid field names, run `list` to get valid values for reference fields
4. **Retry with fixes** — apply the specific correction and re-execute (max 2 retries)

For the full recovery loop, see [agent-workflow.md — Error Recovery](agent-workflow.md#error-recovery).
