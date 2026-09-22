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

Pass `--activity-version 4.0.0` only when the activity's `configuration` JSON reports `"version":"4.0.0"`. Otherwise do not pass the flag at all. Any value other than `1.0.0` (the default) or `4.0.0` fails with `Invalid --activity-version value`. `4.0.0` responses cache under a separate key (`<object-name>.v4.schema.json`), so switching never serves the other version's metadata.

The resource argument follows the same rule: `4.0.0` activities are addressed by **object name** — pass the `objectName` from the `configuration` JSON.

```bash
uip is resources describe <connector-key> <object-name> --output json
uip is resources describe <connector-key> <object-name> --activity-version 4.0.0 --operation <METHOD> --output json
```

Pass `--operation` with the HTTP verb for `4.0.0` describes — without it the response is an operation summary with no `requestFields`. `4.0.0` reference fields carry `reference.scriptRef` instead of `objectName`; resolve them with `uip is resources run script --script-ref`, not `run list` — see [reference-resolution.md — 4.0.0 Activities — Script References](reference-resolution.md#400-activities--script-references-scriptref).

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

### `run script` — run a published connector script

`uip is resources run script` runs a connector's published script with the connection's credential. Use it to resolve `4.0.0` reference fields (`reference.scriptRef`):

```bash
uip is resources run script --connection-id "<CONNECTION_ID>" \
  --connector-key "<CONNECTOR_KEY>" --script-ref "<SCRIPT_REF>" --output json
```

Exactly one of `--script-ref` or `--inline-script` is accepted; `--connector-key` is required with `--script-ref`. `Data.Body` is the vendor's response (parsed JSON), and a vendor `4xx`/`5xx` still returns `Result: "Success"` — check `Data.Status`. Parsing rules and the full lookup workflow: [reference-resolution.md — 4.0.0 Activities — Script References](reference-resolution.md#400-activities--script-references-scriptref).

### Filtering Results with `--output-filter`

Use the global `--output-filter` flag with a JMESPath expression to extract specific fields from large responses if possible via JMESPath.

Expressions are evaluated against `Data`, so they start at `Data` and never carry a `Data.` prefix; a `Data`-prefixed path resolves to null. `run list` returns `Data` as an object (`items`, `Pagination`), while `resources list` returns a flat array. Probe once with `--output-filter "type(@)"`, then `"keys(@)"` on an object, before writing a projection.

```bash
# Extract only id, name, and email from a user list
uip is resources run list "<CONNECTOR_KEY>" "<OBJECT_NAME>" \
  --connection-id "<CONNECTION_ID>" \
  --output json \
  --output-filter "items[].{id: id, name: name, email: profile.email}"
```

Common JMESPath patterns for `run list`; drop the `items` prefix where `Data` is already an array:

| Pattern | Effect |
|---|---|
| `items[]` | Return every record on this page |
| `items[].name` | Return just the `name` field from each record |
| `items[].{id: id, name: name}` | Return selected fields as objects |
| `items[?status=='active']` | Filter records by field value |
| `items[0]` | Return only the first record |

> **A filter sees one page.** The filter runs after a page is fetched, so a predicate matching nothing yields `Data: []`, which means "not on this page" and never "not in the collection". Project `Pagination` alongside the predicate (`"{hit: items[?<match-field>=='<target>'], next: Pagination}"`) so one call answers both questions.

---

## Pagination

`uip is resources run list` may not return all results in a single call. **Always check for pagination** when searching for a specific item or listing all items.

### Narrow before you page

A tenant directory (Slack channels, Teams users, Drive files) runs to thousands of rows, many pages deep. Work down this ladder and stop at the first rung that applies; only the last one walks the collection.

1. **A by-key resource, when you already hold the exact key.** Connectors often expose a dedicated lookup beside the collection — Slack `users_lookupByEmail` next to `users`, Teams `user-by-email/{email}`. `uip is resources list "<key>"` shows them, and the naming (`*_lookupBy*`, `*-by-*`) is the tell. One call, no walk:

   ```bash
   uip is resources run list "uipath-salesforce-slack" "users_lookupByEmail" \
     --connection-id "<id>" --query "email=<address>" --output json --output-filter "items.id"
   ```

   Its `Data.items` is a single object rather than an array, so project `items.<field>`, not `items[?…]`. A miss arrives as a vendor 4xx instead of an empty list (Slack returns `400` with `"message":"users_not_found"` in `Instructions`), so read `Instructions` per [Execute Error Handling](#execute-error-handling) to tell a genuine miss from a broken call before reporting either.

2. **`reference.filterPattern`**, if the field declares one. Substitute the search term and pass the whole string as `--query`. This narrows server-side but does not promise a single page — a `startswith(...)` pattern can still match more rows than fit — so keep honouring `Pagination`. See [reference-resolution.md — Search References](reference-resolution.md#search-references-filterpattern).

3. **The operation's own query parameters.** `uip is resources describe "<key>" "<resource>" --operation List`, against the *referenced* resource rather than the activity you are configuring, lists every accepted `--query` key under `parameters`. Most are not a `filterPattern` and so are easy to miss: Slack `conversations` takes `exclude_archived`, `types` and `team_id`. Keys the operation does not declare (`searchTerm=`, `where=`, `filter=`) are silently ignored.

4. **Then page**, carrying every narrowing key from rungs 2 and 3 on each request alongside `nextPage`. The page token encodes position only, so dropping them widens page 2 back to the whole collection.

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

**Chain the pages into one call, rather than a turn per page.** Put the successive `run list` calls in a single shell invocation, and project the predicate and `Pagination` together so each page answers "is it here" and "is there more" at once. `--output-filter` expresses this whole projection, so it needs no external parser.

Build the predicate from the reference, not from the shape of the first row you see. Match against **every** entry in `lookupNames`, one clause per entry (`items[?<f1>=='<target>' || <f2>=='<target>']`), take the value you write from `lookupValue`, and resolve dotted entries as paths (`profile.email`). A predicate on the wrong field matches nothing on every page, which reads as absence for a row that is there. Escape an apostrophe in the target as `\'`, or the filter is a lexer error.

**Stop on the first hit only when the field is unique.** A by-key resource or an exact `lookupValue` is. A display name is not: `run list` can return a global row and a project-scoped row carrying the same name, on different pages, and taking the first silently picks a scope ([Scope Filtering](reference-resolution.md#scope-filtering-critical)). For a name match, collect every hit before deciding, paging until `HasMore: "false"` or a page stops adding rows you have not seen — otherwise "one match" is only ever "the first match I happened to see".

How the walk ends decides what you do next, and only the first ending below is a resolved value:

| Ending | What to do |
|---|---|
| exactly one match, walk complete | write its `lookupValue` |
| several matches | ask the user with the candidates; never take the first |
| `HasMore: "false"` and no match | re-check the predicate against `lookupNames`, then re-run against this connector's other Enabled connections, then ask |
| a page adds no rows you have not already seen, or `HasMore` never reaches `"false"` | first re-check the page param: it is `nextPage`, and an undeclared name like `pageToken` is silently ignored, so every call re-serves page one. If the name is right, the collection is exhausted and the connector is re-serving it: keep the distinct rows and stop. Do not wait for `HasMore` or for a repeated page token — some resources advance the token forever (Slack `curated_users`: 5984 users exhausted by page 6, `HasMore` still `"true"` at page 12) |
| you bounded the walk yourself and stopped before `HasMore: "false"` | not a not-found; narrow the query and walk again |
| the call errored | stop and report per [When the Lookup Call Fails](reference-resolution.md#when-the-lookup-call-fails-critical) |

Never collapse the last three into "not found". Writing a display name or a remembered id after any of them passes `flow validate` and faults at runtime. These endings read `Data.Pagination`; resources that page by `offset`/`limit` have their own section below.

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
