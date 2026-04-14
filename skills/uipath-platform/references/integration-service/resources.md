# Resources

Resources represent the data objects available through a connector (e.g., Salesforce Account, Contact, Opportunity). Each resource supports a set of CRUD operations.

> Full command syntax and options: [uip-commands.md — Integration Service](../uip-commands.md#integration-service-is). Domain-specific usage patterns are shown inline below.

## Contents
- Listing and Describing Resources
- Response Fields
- Describe Response
- Describe Failures
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
- **`reference`** — field value must be looked up from another resource. See [reference-resolution.md](reference-resolution.md).
- **`enum`** — field only accepts the listed values (e.g., `["low", "normal", "high"]`).

Results are cached locally. Use `--refresh` to bypass cache after re-auth or schema changes.

---

## Describe Failures

Some resources return an error on describe. This is a **server-side metadata gap** — do not retry with `--refresh`.

**Recovery:**

1. **Skip describe entirely** — do not waste calls retrying.
2. **Infer fields from user context** — use the field names and values the user provided in their request.
3. **Infer reference fields from naming** — see [reference-resolution.md — Inferring References Without Describe](reference-resolution.md#inferring-references-without-describe).
4. **Attempt execute directly** — let the server validate. If a field is rejected, read the error and adjust.

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

### Filtering Results with `--output-filter`

Use the global `--output-filter` flag with a JMESPath expression to extract specific fields from large responses if possible via JMESPath.

```bash
# Extract only id, name, and email from a user list
uip is resources execute list "<CONNECTOR_KEY>" "<OBJECT_NAME>" \
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

`uip is resources execute list` may not return all results in a single call. **Always check for pagination** when searching for a specific item or listing all items.

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
uip is resources execute list "<connector-key>" "<resource>" \
  --connection-id "<id>" --output json
# → Check Data.Pagination.HasMore and Data.Pagination.NextPageToken in the JSON response

# Subsequent pages — use nextPage as the query param name (NOT nextPageToken)
uip is resources execute list "<connector-key>" "<resource>" \
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
uip is resources execute list "<connector-key>" "<object>" \
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
