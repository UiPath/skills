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

The describe command fetches JSON Schema from the IS API (`Accept: application/schema+json`) and returns a compact summary:

| Section | Description |
|---|---|
| **operations** | Available operations — each with method, path, description, parameters (name, type, required, description) |
| **operations[].agent** | Agent metadata (if present) — `description` (action-oriented), `fieldOrder` (resolution sequence), `knownErrors` (connector-specific error patterns and resolutions) |
| **fields** | All fields — each with name, type, required flag, enum values (if any), $ref (if any) |
| **fields[].agent** | Per-field agent hints (if present) — `description` (action-oriented, how to resolve), `resolveFirst` (boolean), `dependsOn` (field resolution dependencies) |

Use `--operation <Create|List|Retrieve|Update|Delete|Replace>` to filter to a single operation and reduce output.

Results are cached locally. Use `--refresh` to bypass cache after re-auth or schema changes.

### Agent metadata in describe

When present, agent metadata provides connector-specific guidance that goes beyond what the standard schema offers:

- **`agent.fieldOrder`** — resolve reference fields in this order (respects dependency chains)
- **`agent.knownErrors`** — connector-specific error patterns with resolutions. These contain non-obvious knowledge (e.g., "transitions are per-issue, not per-project" or "Slack returns HTTP 200 for errors")
- **`agent.description`** on fields — action-oriented descriptions (e.g., "Use channel ID not name", "Resolve accountId via user search, not email")
- **`agent.dependsOn`** on fields — explicit dependency chain (e.g., issue type depends on project key)

**Use agent metadata from describe to guide field resolution and to understand failure responses.** The `knownErrors` from describe correspond to the `AgentContext.knownErrors` returned on execute failure.

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

---

## Pagination

`uip is resources execute list` may not return all results in a single call. **Always check for pagination** when searching for a specific item or listing all items.

### Connector pagination

Most IS connectors use the `elements-*` pagination protocol. The CLI returns pagination state nested inside `Data.Pagination`:

- **`Data.Pagination.HasMore`**: `"true"` or `"false"` — indicates if more pages exist
- **`Data.Pagination.NextPageToken`**: the token value to use for the next page

**IMPORTANT:** The query parameter name is `nextPage` (NOT `nextPageToken`). Pass the value from `Data.Pagination.NextPageToken` as `--query "nextPage=<value>"`.

```bash
# First page (do not pass pageSize unless the user explicitly requests a specific page size)
uip is resources execute list "<connector-key>" "<resource>" \
  --connection-id "<id>" --format json
# → Check Data.Pagination.HasMore and Data.Pagination.NextPageToken in the JSON response

# Subsequent pages — use nextPage as the query param name (NOT nextPageToken)
uip is resources execute list "<connector-key>" "<resource>" \
  --connection-id "<id>" --query "nextPage=<value-from-NextPageToken>" --format json
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

**Stop early:** If you find the target item in the current page, no need to fetch remaining pages.

### Query-param pagination (offset/limit)

Some resources support `offset`/`limit` via `--query`:

```bash
uip is resources execute list "<connector-key>" "<object>" \
  --connection-id "<id>" --query "limit=50&offset=0" --format json
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
- **`AgentContext`** (if available): Connector-specific hints from the cached describe metadata

### AgentContext structure

When the CLI has cached describe metadata for the resource, it attaches `AgentContext` to failure responses:

```json
{
  "Result": "Failure",
  "Message": "400 Bad Request",
  "Instructions": "{\"errorMessages\":[\"Transition id 31 is not valid\"]}",
  "AgentContext": {
    "operationDescription": "Transition a Jira issue to a new status...",
    "fieldOrder": ["issueIdOrKey", "id"],
    "knownErrors": [
      {
        "match": "transition id not valid",
        "resolution": "Transitions are dynamic per issue — they depend on the CURRENT status of the specific issue. List transitions for THIS issue via /issue/{issueKey}/transitions."
      }
    ],
    "fields": [
      {
        "name": "id",
        "description": "The transition ID (not status name). List transitions for the issue to get valid IDs.",
        "resolveFirst": true,
        "dependsOn": ["issueIdOrKey"]
      }
    ]
  }
}
```

### How to use AgentContext on failure

1. **Read `Instructions`** — the raw vendor error tells you WHAT failed
2. **Read `AgentContext.knownErrors`** — match the vendor error against `match` keywords to find the connector-specific `resolution` that tells you HOW to fix it
3. **Read `AgentContext.fields`** — field-level hints with `dependsOn` chains to guide re-resolution
4. **If no `AgentContext`** — fall back to the generic self-healing loop (re-describe, discover, retry)

> **`AgentContext` is only present when cached describe metadata exists for the resource.** If the resource was never described, or describe failed, the error response only contains `Message` and `Instructions`.

For the self-healing loop (read error → diagnose → discover correct values → fix → retry), see [agent-workflow.md — Error Self-Healing](agent-workflow.md#error-self-healing).
