# Resources

Resources are connector data objects, such as Salesforce Account, Contact, or Opportunity, supporting CRUD operations.

> Full command syntax and options: [uip-commands.md — Integration Service](../uip-commands.md#integration-service-is). Domain-specific patterns appear below.

For reference resolution, dependency chains, and required-field validation, see [reference-resolution.md](reference-resolution.md).

## Listing and Describing Resources

Pass `--connection-id` for connection-specific metadata, including custom objects and fields; without it, only standard objects and fields are returned.

### Response fields

| Field | Description |
|---|---|
| **`Name`** | Resource identifier used in commands |
| `DisplayName` | Human-readable name |
| `Path` | API path |
| `Type` | Resource type: standard or custom |
| `SubType` | Sub-type, such as method or entity |

Without `--operation`, describe returns only an operation summary:

- **`availableOperations`**: operations with `method` (GET/POST/PATCH/PUT/DELETE), `name` (Create/List/etc.), `description`, and `curated` (display name).
- **`hint`**: directs you to use `--operation` for field details.

With `--operation`, describe returns:

- **`operation`**: `method`, `name`, `description`, `path`, and `curated` display name.
- **`parameters`**: path and query parameters, not body fields; each has `name`, `type` (path/query), `dataType`, `required`, `defaultValue`, and `reference`.
- **`requestFields`**: fields sent in `--body`; each has `name`, `type`, `displayName`, `required`, `description`, `reference`, and `enum`.
- **`responseFields`**: returned fields with `name`, `type`, and `displayName`.

Run describe with `--operation` for field details. For `required: true`, provide the field in `--body` or `--query`. Resolve `reference` values as described in [reference-resolution.md](reference-resolution.md); when baking a static reference value, also emit `designTimeMetadata.designTimeLookups` so the edit UI renders a label; see [reference-resolution.md — Static Reference-Value Labeling](reference-resolution.md#static-reference-value-labeling). Accept only values listed by `enum`, such as `["low", "normal", "high"]`.

Results are cached locally. Pass `--refresh` after re-authentication or schema changes.

### `--activity-version`

Pass `--activity-version 4.0.0` only when the activity's `configuration` JSON reports `"version":"4.0.0"`; otherwise do not pass it. Values other than `1.0.0` (default) or `4.0.0` fail with `Invalid --activity-version value`. Version `4.0.0` uses cache key `<object-name>.v4.schema.json`, addresses the resource by object name, and requires `objectName` from the `configuration` JSON.

```bash
uip is resources describe <connector-key> <object-name> --output json
uip is resources describe <connector-key> <object-name> --activity-version 4.0.0 --output json
```

### Describe failures

Treat a describe error as a **server-side metadata gap**:

1. Skip describe entirely; do not waste calls retrying.
2. Infer fields from user context using names and values in the request.
3. Infer reference fields from naming; see [reference-resolution.md — Inferring References Without Describe](reference-resolution.md#inferring-references-without-describe).
4. Attempt execute directly and adjust rejected fields using the server error.

## Parent-Field-Driven Custom Fields (api-type ObjectActions)

For connectors whose required fields depend on parent selections (Jira `GenerateSchema` keyed by project + issue type, Salesforce SOQL `GenerateQuerySchema` keyed by query string, and Dataservice V3 `FetchObjectMetadataTenant` keyed by `tenantEntityName`), base describe returns only base fields. Preview runtime fields by passing parent values with `-f, --field` before validating required fields:

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

Require `--connection-id` and `--operation`. Bypass cache when `--field` is supplied because the response varies by parent-field combination. Get merge mode (`replace`, `append`, `prepend`, or `noop`) from `remapConfiguration.input`; Jira `GenerateSchema` uses `replace`. If no action's `rules[]` matches the supplied fields, the CLI errors with `No api-type ObjectAction matched for fields [...]`. Inspect actions in `connectorMethodInfo.design.actions[]` or, for older shapes, top-level `objectActions[]`.

| Flag | Notes |
|---|---|
| `-f, --field <name=value>` | Repeatable. Names match `apiConfiguration.url` and `apiConfiguration.body` placeholders verbatim; do not use `_sub_` encoding. Encoding applies only when caching parent values for runtime replay; see [activities.md — Custom Fields](activities.md#custom-fields-objectactionsactiontypeapi). |
| `--action <name>` | Optional; disambiguates multiple matching api-type actions. |

Run the matching api-type ObjectAction against the IS Element Service, as Studio Web's dispatcher does, and merge the response into `requestFields` according to `onSuccess.remapConfiguration`.

## Execute Operations

| Verb | Description | `--body` | `--query` |
|---|---|---|---|
| `create` | Create a record | Yes | No |
| `list` | Retrieve records | No | Optional (`limit=10&offset=0`) |
| `get` | Get one record by ID | No | Yes (`id=<RECORD_ID>`) |
| `update` | Partial update (PATCH) | Yes | Yes (`id=<RECORD_ID>`) |
| `delete` | Delete a record | No | Yes (`id=<RECORD_ID>`) |
| `replace` | Full replacement (PUT) | Yes | Yes (`id=<RECORD_ID>`) |

Use **Update** (PATCH) by default; use **Replace** (PUT) only when the user says “replace” or “overwrite”.

### Filtering with `--output-filter`

Use the global `--output-filter` flag with a JMESPath expression when possible:

```bash
# Extract only id, name, and email from a user list
uip is resources run list "<CONNECTOR_KEY>" "<OBJECT_NAME>" \
  --connection-id "<CONNECTION_ID>" \
  --output json \
  --output-filter "Data[].{id: id, name: name, email: profile.email}"
```

| Pattern | Effect |
|---|---|
| `Data[]` | Unwrap the Data envelope and return all records |
| `Data[].name` | Return `name` from each record |
| `Data[].{id: id, name: name}` | Return selected fields as objects |
| `Data[?status=='active']` | Filter by field value |
| `Data[0]` | Return the first record |

### Pagination

Always check pagination when searching or listing all items. Check `Data.Pagination`; never assume one page is complete. Continue the same pagination loop until `Data.Pagination.HasMore` is `"false"` or the item is found. Do not switch mid-loop to search endpoints, admin endpoints, or HTTP fallback. Stop early on a match and report not-found only after exhausting all pages.

Most IS connectors use the `elements-*` protocol: `Data.Pagination.HasMore` is `"true"` or `"false"`, and `Data.Pagination.NextPageToken` is passed as `--query "nextPage=<value>"`, not `nextPageToken`.

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

Do not check `Data.nextPage`; pagination is in `Data.Pagination.HasMore` and `Data.Pagination.NextPageToken`. Do not abandon pagination or conclude “not found” after one page.

Some resources use offset/limit:

```bash
uip is resources run list "<connector-key>" "<object>" \
  --connection-id "<id>" --query "limit=50&offset=0" --output json
# → next page: --query "limit=50&offset=50"
```

Stop when the result is empty or smaller than the limit. The `uipath-uipath-http` connector is an exception; use the vendor-specific pagination behavior instead of `elements-*` headers.

## Execute Error Handling

On failure, the CLI returns `Message` (HTTP status, such as `400 Bad Request`) and `Instructions` (raw vendor error response body as JSON). Read `Message` to classify the failure and `Instructions` to identify invalid fields, missing values, permission issues, or other causes. Use discovery to fix the request: run `describe` for valid fields and `list` for valid reference values. Retry with fixes, applying the correction and re-executing for a maximum of 2 retries.

For the full recovery loop, see [agent-workflow.md — Error Recovery](agent-workflow.md#error-recovery).