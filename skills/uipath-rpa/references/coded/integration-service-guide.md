# Integration Service — Coded Workflow Reference

Use `ConnectorConnection.ExecuteAsync` to call any Integration Service connector (Jira, Salesforce, ServiceNow, Slack, etc.) directly from a coded workflow — no drag-and-drop activities required.

> **Two IS connection patterns exist in coded workflows.** This file covers raw IS connectors (Jira, Salesforce, custom) via `CodedConnectorConfiguration` + `ISConnections.cs`. For first-party package connections (Office365, GSuite) that use the auto-generated `ConnectionsManager.cs` / `ConnectionsFactory.cs`, see [codedworkflow-reference.md § Integration Service Connections](codedworkflow-reference.md#integration-service-connections).

## Contents

- [How It Works](#how-it-works)
- [Required Package](#required-package)
- [Key Types](#key-types)
- [Step-by-Step Workflow](#step-by-step-workflow)
- [Pagination on List Operations](#pagination-on-list-operations)
- [ExecuteAsync Reference](#executeasync-reference)
- [ConnectorResponse Reference](#connectorresponse-reference)
- [Operation Values](#operation-values)
- [Error Handling](#error-handling)
- [Anti-patterns](#anti-patterns)
- [Full Example — Jira](#full-example--jira)

---

## How It Works

The skill resolves all metadata up-front using the `uipath-platform` skill's Integration Service workflow (connector → connection → describe → execute). The coded workflow then receives the pre-resolved values and passes them to `ConnectorConnection.ExecuteAsync` — **no metadata lookup happens at runtime**.

---

## Required Package

**Always include `UiPath.IntegrationService.Activities` with version >= 1.25.0** in `project.json` `dependencies`:

```json
"UiPath.IntegrationService.Activities": "[1.25.0,)"
```

Add to the workflow file:

```csharp
using UiPath.IntegrationService.Activities.Runtime.CodedWorkflows;
using UiPath.IntegrationService.Activities.Runtime.Models;
using UiPath.IntegrationService.Activities.Runtime.Models.ConnectorMetadata;
```

---

## Key Types

### `CodedConnectorConfiguration`

Groups connection identity (sourced from a `ConnectorConnection`) with the routing metadata for a single operation. Construct one per call.

```csharp
public sealed class CodedConnectorConfiguration(
    ConnectorConnection connection,    // typed handle from ISConnections.cs
    string objectName,                 // object/activity name from uip is activities/resources list
    Operation operation,               // Operation.List / Retrieve / Create / Update / Delete
    string httpMethod,                 // HTTP verb from describe response MethodName field
    string path,                       // URL path template from describe response Path field
    ActivityType activityType = ActivityType.Curated); // see Determining ActivityType below
```

### `ConnectorRequest`

Groups the runtime execution parameters for a single call.

| Property | Type | What it controls | Default |
| -------- | ---- | ---------------- | ------- |
| `PathParameters` | `Dictionary<string, string>` | Values substituted into `{placeholders}` in the path template | `{}` |
| `QueryParameters` | `Dictionary<string, string>` | Key/value pairs appended as `?key=value` to the URL | `{}` |
| `BodyParameters` | `Dictionary<string, object?>` | Fields sent as JSON body; supports nested `Dictionary<string, object?>` | `{}` |
| `MultipartParameters` | `Dictionary<string, object?>?` | Non-null → request sent as `multipart/form-data`; empty dict = no file attachments; `IResource` values = file upload fields | `null` |
| `MaxRecords` | `int` | Client-side cap on total results across all pages (`-1` = all). Does **not** control vendor page size — set `QueryParameters["pageSize"]` separately. See [Pagination on List Operations](#pagination-on-list-operations). | `-1` |

```csharp
var request = new ConnectorRequest
{
    PathParameters  = new() { ["varName"] = "<value>" },
    QueryParameters = new() { ["key"]     = "<value>" },
    BodyParameters  = new() { ["field"]   = "<value>" },
};
```

### `ConnectorConnection`

Typed handle to a specific IS connector + connection. Constructed by the auto-generated `ISConnections.cs`. Carries `ConnectionId` and `ConnectorKey`; exposes `ExecuteAsync`.

---

## Step-by-Step Workflow

**Before you start — check these three things:**

1. Does `.project/ISBindingMetadata.json` exist? → **Merge** new entries into it; do not overwrite the file.
2. Does `.codedworkflows/ISConnections.cs` exist? → Update only the relevant connector class; do not regenerate the whole file.
3. Is the connection UUID already known? → If not, resolve it now before proceeding:
   ```bash
   uip is connections list "<CONNECTOR_KEY>" --output json
   # → copy the "Id" field of the target connection
   ```

### Step 1 — Resolve metadata using the uipath-platform skill

Before writing the coded workflow, resolve the connector metadata using the `uipath-platform` skill. The full CLI commands and output interpretation are covered in those reference files:

- **Find connector key and list connections:** [connectors.md](../../../uipath-platform/references/integration-service/connectors.md) and [connections.md](../../../uipath-platform/references/integration-service/connections.md)
- **Discover activities/resources and run describe:** [activities.md](../../../uipath-platform/references/integration-service/activities.md) and [resources.md](../../../uipath-platform/references/integration-service/resources.md)

The describe response tells you:

- `Path` → the `path` argument to `CodedConnectorConfiguration` (e.g. `/curated_get_issue/{issueId}`)
- `MethodName` → the `httpMethod` argument (e.g. `GET`)
- `requiredFields[].type` / `optionalFields[].type` → which bucket each field belongs to (`path`, `query`, or `body`) — maps to the corresponding `ConnectorRequest` property
- `referenceFields` → fields that need a lookup value resolved first

> **Gap — query/path params not shown by describe:** The describe output only surfaces `requestFields` (body-level fields) as `requiredFields`/`optionalFields`. It does **not** surface the `parameters` array from the raw metadata file, which contains query- and path-level parameters (e.g. `send_as` for Slack). After running describe, also read the raw metadata file directly:
>
> ```bash
> # The metadataFile path is returned in the describe response, e.g.:
> ~/.uipath/cache/integrationservice/<CONNECTOR_KEY>/<CONNECTION_ID>/<OBJECT_NAME>.<OPERATION>.json
> ```
>
> In that file, look for the top-level `parameters` array. Any entry with `"required": true` **must** be passed in `ConnectorRequest.QueryParameters` or `ConnectorRequest.PathParameters` (based on its `"in"` field: `"query"` or `"path"`). These will not appear in `requiredFields` and will silently be missing if you rely on describe alone.

### Step 2 — Detect multipart requirement (required for Create/Update operations)

Skip this step for `List`, `Retrieve`, and `Delete` operations — multipart encoding only applies to `Create` and `Update`. Otherwise, run this before writing the workflow. Read the raw metadata file returned in the describe response and check for `multipart` parameters. If found, use `MultipartParameters`; if none, proceed normally to Step 3.

```bash
# METADATA_FILE_PATH is returned in the describe response, e.g.:
# ~/.uipath/cache/integrationservice/<CONNECTOR_KEY>/<CONNECTION_ID>/<OBJECT_NAME>.<OPERATION>.json
cat "<METADATA_FILE_PATH>" | python3 -c "import json,sys; d=json.load(sys.stdin); print([p for p in d.get('parameters',[]) if p.get('type')=='multipart' or p.get('in')=='multipart'])"
```

**If multipart parameters are found:**
- Set `ConnectorRequest.MultipartParameters = new Dictionary<string, object?>()` — this signals multipart encoding.
- For file attachments, add `IResource` values to `MultipartParameters` (keyed by the form-data field name).
- `BodyParameters` is still serialized as JSON and attached as the `body` part of the form.

**If no multipart parameters are found:** proceed normally to Step 3.

### Step 3 — Resolve reference fields (if any)

If the describe output has `referenceFields`, resolve each one before calling `ExecuteAsync`:

```bash
uip is resources execute list "<CONNECTOR_KEY>" "<REFERENCED_OBJECT>" \
  --connection-id "<CONNECTION_ID>" --output json
# Pick the correct id from the results
```

### Step 4 — Generate `ISConnections.cs`

Create (or update) `.codedworkflows/ISConnections.cs`. One class per connector, one property per connection:

```csharp
// .codedworkflows/ISConnections.cs — managed by coding agent — regenerate via uipath-rpa skill when connections change.
using UiPath.CodedWorkflows;
using UiPath.IntegrationService.Activities.Runtime.CodedWorkflows;

// Determine the namespace from other .cs files in the project root:
//   grep -m1 "^namespace" *.cs
namespace <ProjectNamespace>
{
    public class ISConnections
    {
        private readonly ICodedWorkflowsServiceContainer _container;
        public ISConnections(ICodedWorkflowsServiceContainer container) => _container = container;

        // One property per connector. Class name = last hyphen-segment of connector key, title-cased + "ISConnections".
        // e.g. "uipath-atlassian-jira" → last segment "jira" → JiraISConnections, property name → Jira
        public JiraISConnections Jira => new(_container);
    }

    public class JiraISConnections
    {
        private readonly ICodedWorkflowsServiceContainer _container;
        public JiraISConnections(ICodedWorkflowsServiceContainer container) => _container = container;

        // UUID resolved by coding agent via: uip is connections list "<CONNECTOR_KEY>" --output json
        // At runtime, ConnectionBase resolves it via the service container binding.
        public ConnectorConnection MyJiraConnection =>
            new("02a02e3a-9b22-4802-87f2-c343bc38dde4", "uipath-atlassian-jira", _container);
    }
}
```

**Naming rules:** take the last hyphen-separated segment of the connector key, title-case it, append `ISConnections`. e.g. `uipath-atlassian-jira` → last segment `jira` → `JiraISConnections`; property on `ISConnections` → `Jira`. First constructor arg = Orchestrator **connection UUID** — allows environment overrides at deploy time.

### Step 5 — Create or update `ISBindingMetadata.json`

Create `.project/ISBindingMetadata.json` in the project root (alongside `CodedBindingsMetadata.json`). Add one entry per IS connection. Studio's `PackageBindingsGeneratorService` reads this file at publish time and includes all entries in `PackageBindings.json` — no code-pattern scan is needed.

**Unlike `CodedBindingsMetadata.json`, this file is never regenerated by Studio on project open or package install, so coding-agent edits are always preserved.**

The format matches the existing `CodedBindingsMetadata.json` connection entry shape exactly. The dictionary key is `"<ConnectorDisplayName>.<ConnectionDisplayName>"`. `UseConnectionService: "true"` in `Metadata` is what signals to Orchestrator that this is an Integration Service connection.

```json
{
  "Jira.MyJiraConnection": {
    "ActivityDisplayName": null,  // leave null — set by Studio for drag-and-drop activities only
    "ActivityId": null,           // leave null — set by Studio for drag-and-drop activities only
    "Resource": "Connection",
    "Key": "02a02e3a-9b22-4802-87f2-c343bc38dde4",
    "Id": "02a02e3a-9b22-4802-87f2-c343bc38dde4",
    "Description": null,
    "Value": {
      "ConnectionId": {
        "DefaultValue": "02a02e3a-9b22-4802-87f2-c343bc38dde4",
        "IsExpression": false,
        "DisplayName": "Connection",
        "Description": "The connection to be used"
      }
    },
    "Metadata": {
      "UseConnectionService": "true",
      "Connector": "uipath-atlassian-jira",
      "BindingsVersion": "2.2"
    }
  }
}
```

The UUID in `Key`, `Id`, `Value.ConnectionId.DefaultValue`, and in `ISConnections.cs` must all be the **same connection UUID** — use the one resolved in the Before you start checklist (item 3).

If the file already exists, **merge** the new entry into it — do not overwrite the entire file.

### Step 6 — Write the coded workflow

Once you have all values from the describe output and `ISConnections.cs` is generated, build a `CodedConnectorConfiguration` and `ConnectorRequest`, then call `ExecuteAsync` on the `ConnectorConnection`:

```csharp
var conn = new ISConnections(services.Container).<CONNECTOR>.<CONNECTION_NAME>;
//                                               ^^^^^^^^^^^  ^^^^^^^^^^^^^^^^
//                                               Replace with actual property names from ISConnections.cs
//                                               e.g. .Jira.MyJiraConnection

var config = new CodedConnectorConfiguration(
    connection:   conn,
    objectName:   "<OBJECT_NAME>",   // from uip is activities/resources list
    operation:    Operation.Create,  // replace with actual: List/Retrieve/Create/Update/Delete
    httpMethod:   "POST",            // from describe response MethodName field
    path:         "/<OBJECT_PATH>"); // from describe response Path field

var request = new ConnectorRequest
{
    BodyParameters  = new() { ["field"]   = "<value>" },   // body fields from describe requiredFields
    // PathParameters  = new() { ["<VAR>"] = "<value>" },  // if path contains {placeholders}
    // QueryParameters = new() { ["key"]   = "<value>" },  // if query params needed
};

var response = await conn.ExecuteAsync(config, request);
```

### Step 7 — Validate

Run `uip rpa get-errors` on the written workflow file until 0 errors. Cap at 5 fix attempts.

```bash
uip rpa get-errors --file-path "<WORKFLOW_FILE>" --project-dir "<PROJECT_DIR>" --output json```

---

## Pagination on List Operations

**Why this matters:** The drag-and-drop activity framework silently injects `pageSize=maxPageSize` into every List call. Coded workflows do not — `ConnectorConnection.ExecuteAsync` passes only what you put into `ConnectorRequest`. Omitting `pageSize` falls back to the connector's `defaultPageSize` (commonly 20), causing many small HTTP calls instead of one.

### MaxRecords vs pageSize — Two Different Things

| Property | Scope | What it controls |
| -------- | ----- | ---------------- |
| `ConnectorRequest.MaxRecords` | Client-side | Total records returned across all pages. `-1` = all. |
| `QueryParameters["pageSize"]` | Vendor-side | Records per HTTP call. Should match the connector's `maxPageSize`. |

Setting `MaxRecords = 10` with no `pageSize` means the runtime still makes multiple 20-record calls under the hood and discards extras — you pay for the extra HTTP traffic. **Always set both.**

### How to Find a Connector's maxPageSize

Known `maxPageSize` values (verify per connector version):

| Connector key | maxPageSize | defaultPageSize |
| ------------- | ----------- | --------------- |
| `uipath-atlassian-jira` | 1000 | 20 |
| `uipath-salesforce` | Varies by object | Varies |

**When in doubt, use `1000`** — connectors clamp the value to their actual max, so overspecifying is safe.

### Rule: Always Set pageSize on List Operations

For every `Operation.List` call in a coded workflow, always explicitly set `pageSize` in `QueryParameters`:

```csharp
var request = new ConnectorRequest
{
    QueryParameters = new() { ["pageSize"] = "1000" },  // vendor-side: records per HTTP call
    MaxRecords      = 50,                                // client-side: total results cap
};
```

If a connector uses a different pagination parameter name (`maxResults`, `limit`, etc.), check the raw metadata file for that object:

```bash
# METADATA_FILE_PATH is returned in the describe response:
# ~/.uipath/cache/integrationservice/<CONNECTOR_KEY>/<CONNECTION_ID>/<OBJECT_NAME>.List.json
cat "<METADATA_FILE_PATH>" | python3 -c "import json,sys; [print(p) for p in json.load(sys.stdin).get('parameters',[]) if any(k in p.get('name','').lower() for k in ['page','size','limit','max'])]"
```

Use whatever name that parameter has as the key in `QueryParameters`.

---

## ExecuteAsync Reference

`ConnectorConnection.ExecuteAsync` signature:

```csharp
Task<ConnectorResponse> ExecuteAsync(
    CodedConnectorConfiguration configuration,   // routing: object, operation, method, path, activityType
    ConnectorRequest            request,          // params: path/query/body/multipart + maxRecords
    CancellationToken           cancellationToken = default)
```

### Choosing the right parameter bucket

| Field `type` in describe output | `ConnectorRequest` property |
| ------------------------------- | --------------------------- |
| `path`                          | `PathParameters` — key must match `{variable}` name in path template |
| `query`                         | `QueryParameters` |
| `body`                          | `BodyParameters` — supports nested `Dictionary<string, object?>` |
| `multipart`                     | Set `MultipartParameters = new()` to force multipart; add `IResource` values for file uploads |

> **Important:** `PathParameters` keys must exactly match the placeholder name inside `{...}` in the path template. E.g. path `/issue/{issueId}` requires `PathParameters = new() { ["issueId"] = "APD-1" }`.

> **Connector-specific body shapes:** Some connectors wrap all body fields under a top-level key. For example, Jira's curated activities require all fields nested under `"fields"`, and reference fields (project, issuetype, reporter) must be nested objects with a single identifying key (`"key"` or `"id"`). Always verify the body shape by running the `uip is resources describe` command.

### Determining ActivityType

Do not guess. Run this check against the cached `activities.json` for the connector:

```bash
grep -A3 '"<OBJECT_NAME>"' \
  ~/.uipath/cache/integrationservice/<CONNECTOR_KEY>/activities.json
```

| Result | `ActivityType` to use |
| ------ | --------------------- |
| Object found with `"isCurated": true` | `ActivityType.Curated` |
| Object found with `"isCurated": false` | `ActivityType.Generic` |
| Object **not** in `activities.json` | `ActivityType.Generic` |

> **Example:** The Jira `users` object exists in the connection cache (`users.List.json`) but is absent from `activities.json` — it must use `ActivityType.Generic` even though it can be discovered via `uip is resources list`.

---

## ConnectorResponse Reference

```csharp
public class ConnectorResponse
{
    // Populated for List operations — each item is a flat or nested dictionary
    IReadOnlyList<IReadOnlyDictionary<string, object?>> Items { get; }

    // Populated for Retrieve / Create / Update / Delete
    IReadOnlyDictionary<string, object?> Output { get; }

    // Populated when the operation returns a file (e.g. download)
    ILocalResource? FileResource { get; }
}
```

---

## Operation Values

Defined in `UiPath.IntegrationService.Activities.Runtime.Models.ConnectorMetadata`:

| Value                | Description               | Typical HTTP method |
| -------------------- | ------------------------- | ------------------- |
| `Operation.List`     | List all records          | `GET`               |
| `Operation.Retrieve` | Retrieve one record by ID | `GET`               |
| `Operation.Create`   | Create a new record       | `POST`              |
| `Operation.Update`   | Partially update a record | `PATCH` or `PUT`    |
| `Operation.Delete`   | Delete a record           | `DELETE`            |

> `Operation.Download`, `Operation.Upload`, `Operation.Replace`, and `Operation.Unsupported` are **not supported** in `ExecuteAsync` and will throw `ArgumentOutOfRangeException`.

---

## Error Handling

```csharp
try
{
    var response = await conn.ExecuteAsync(config, request);
}
catch (UiPath.IntegrationService.Activities.Runtime.Exceptions.RuntimeException ex)
{
    // ex.Message contains the error from the connector (e.g. "Missing path variables")
    Log($"Connector error: {ex.Message}", LogLevel.Error);
    throw;
}
```

Common errors and fixes:

| Error | Cause | Fix |
| ----- | ----- | --- |
| `Missing path variables in URL '.../{varName}'` | `PathParameters` key doesn't match `{varName}` in path template | Use exact placeholder name from the path string |
| `404 Not Found` on metadata call | Leading `/` in path used as relative URI | Ensure path is passed without manual URI construction — `ExecuteAsync` handles it |
| `Operation 'X' is not supported` | Unsupported `Operation` value (Download/Upload/Replace/Unsupported) | Use only: `List`, `Retrieve`, `Create`, `Update`, `Delete` |
| `Unable to parse multipart body` / `415 Unsupported Media Type` | Endpoint requires `multipart/form-data` but request was sent as `application/json` | Set `ConnectorRequest.MultipartParameters = new Dictionary<string, object?>()` — see Step 2 |
| Too many HTTP calls for a List operation (observed via network trace) | `pageSize` not set — connector falls back to `defaultPageSize` (e.g. 20) | Set `QueryParameters["pageSize"] = "1000"` in `ConnectorRequest`. See [Pagination on List Operations](#pagination-on-list-operations). |

---

## Anti-patterns

1. **Do not use unsupported Operation values.** `Operation.Download`, `Operation.Upload`, `Operation.Replace`, and `Operation.Unsupported` are not supported — see [Operation Values](#operation-values).

2. **Do not omit `ISBindingMetadata.json`.** Without it, Orchestrator cannot bind the connection at publish time. The coded workflow will compile but fail at runtime when deployed. Always create or merge this file in Step 5.

3. **Do not overwrite `ISConnections.cs` when adding a new connector.** The file may already contain classes for other connectors. Always read the existing file and merge — add a new class, or add a new property to an existing class.

4. **Do not omit `pageSize` on `Operation.List` calls.** Coded workflows do not auto-inject it. See [Pagination on List Operations](#pagination-on-list-operations).

5. **Do not use `ActivityType.Generic` for curated activities or vice versa.** Curated activities come from `uip is activities list` → use `ActivityType.Curated`. Generic resources come from `uip is resources list` → use `ActivityType.Generic`. Mixing them causes routing errors at runtime.

6. **Do not set `MultipartParameters` unless the metadata file contains multipart parameters.** Setting it on a non-multipart endpoint sends `multipart/form-data` where the connector expects `application/json`, causing `415 Unsupported Media Type`.

---

## Full Example — Jira

```csharp
using UiPath.CodedWorkflows;
using UiPath.IntegrationService.Activities.Runtime.CodedWorkflows;
using UiPath.IntegrationService.Activities.Runtime.Models;
using UiPath.IntegrationService.Activities.Runtime.Models.ConnectorMetadata;

namespace MyProject
{
    public class JiraIssuesWorkflow : CodedWorkflow
    {
        [Workflow]
        public async Task Execute()
        {
            var jiraConn = new ISConnections(services.Container).Jira.MyJiraConnection;

            // CREATE — curated activity, fields wrapped under "fields" key.
            // Resolved from: uip is activities list "uipath-atlassian-jira"
            //   → object: curated_create_issue, MethodName: POST, Path: /curated_create_issue
            // Reference fields (project, issuetype, reporter) are nested objects.
            // Resolve their ids/keys via:
            //   uip is resources execute list "uipath-atlassian-jira" "project" --connection-id <id>
            //   uip is resources execute list "uipath-atlassian-jira" "issuetype" --connection-id <id>
            var createConfig = new CodedConnectorConfiguration(
                connection:   jiraConn,
                objectName:   "curated_create_issue",
                operation:    Operation.Create,
                httpMethod:   "POST",
                path:         "/curated_create_issue");

            var createRequest = new ConnectorRequest
            {
                BodyParameters = new()
                {
                    ["fields"] = new Dictionary<string, object?>
                    {
                        ["summary"]   = "Bug found in production",
                        ["project"]   = new Dictionary<string, object?> { ["key"] = "APD" },
                        ["issuetype"] = new Dictionary<string, object?> { ["id"]  = "10304" },
                        ["reporter"]  = new Dictionary<string, object?> { ["id"]  = "712020:89f83693-a619-42a5-a23f-0ea40c216456" }
                    }
                }
            };

            var createResponse = await jiraConn.ExecuteAsync(createConfig, createRequest);
            Log($"Created: {createResponse.Output["key"]}");

            // LIST — generic resource, JQL filter as query param
            // Resolved from: uip is resources list "uipath-atlassian-jira"
            //   --operation List
            //   → object: issue, MethodName: GET, Path: /issue
            var listConfig = new CodedConnectorConfiguration(
                connection:   jiraConn,
                objectName:   "issue",
                operation:    Operation.List,
                httpMethod:   "GET",
                path:         "/issue",
                activityType: ActivityType.Generic);

            var listRequest = new ConnectorRequest
            {
                // pageSize = vendor maxPageSize (1000 for Jira) — must be set explicitly in coded
                // workflows. The activity framework auto-injects this; coded workflows do not.
                // Without it, Jira defaults to pageSize=20, causing many small HTTP calls.
                QueryParameters = new() { ["jql"] = "project = APD AND status = Open", ["pageSize"] = "1000" },
                MaxRecords      = 20,   // client-side cap — trim to 20 total across all pages
            };

            var listResponse = await jiraConn.ExecuteAsync(listConfig, listRequest);

            foreach (var issue in listResponse.Items)
                Log($"{issue["key"]} — {issue["summary"]}");
        }
    }
}
```
