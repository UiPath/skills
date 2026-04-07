# Integration Service — Coded Workflow Reference

Use `IntegrationConnectorService` to call any Integration Service connector (Jira, Salesforce, ServiceNow, Slack, etc.) directly from a coded workflow — no drag-and-drop activities required.

## Contents

- [How It Works](#how-it-works)
- [Required Package](#required-package)
- [Step-by-Step Workflow](#step-by-step-workflow)
- [ExecuteAsync Reference](#executeasync-reference)
- [ConnectorResponse Reference](#connectorresponse-reference)
- [ActivityType Values](#activitytype-values)
- [ConnectorOperation Values](#connectoroperation-values)
- [Error Handling](#error-handling)
- [Full Example — Jira](#full-example--jira)

---

## How It Works

The skill resolves all metadata up-front using the `uipath-development` skill's Integration Service workflow (connector → connection → describe → execute). The coded workflow then receives the pre-resolved values and passes them to `IntegrationConnectorService.ExecuteAsync` — **no metadata lookup happens at runtime**.

---

## Required Package

Add to `project.json` `dependencies`:

```json
"UiPath.IntegrationService.Activities": "[1.24.0]"
```

Add to the workflow file:

```csharp
using UiPath.IntegrationService.Activities.Runtime.CodedWorkflows;
using UiPath.IntegrationService.Activities.Runtime.Models;
```

---

## Step-by-Step Workflow

### Step 1 — Resolve metadata using the uipath-development skill

Before writing the coded workflow, resolve the connector metadata using the `uipath-development` skill. The full CLI commands and output interpretation are covered in those reference files:

- **Find connector key and list connections:** [`uipath-development/references/integration-service/connectors.md`](../../uipath-development/references/integration-service/connectors.md) and [`connections.md`](../../uipath-development/references/integration-service/connections.md)
- **Discover activities/resources and run describe:** [`activities.md`](../../uipath-development/references/integration-service/activities.md) and [`resources.md`](../../uipath-development/references/integration-service/resources.md)

The describe response tells you:

- `Path` → the `path` argument (e.g. `/curated_get_issue/{issueId}`)
- `MethodName` → the `httpMethod` argument (e.g. `GET`)
- `requiredFields[].type` / `optionalFields[].type` → which bucket each field belongs to (`path`, `query`, or `body`)
- `referenceFields` → fields that need a lookup value resolved first

> **Gap — query/path params not shown by describe:** The describe output only surfaces `requestFields` (body-level fields) as `requiredFields`/`optionalFields`. It does **not** surface the `parameters` array from the raw metadata file, which contains query- and path-level parameters (e.g. `send_as` for Slack). After running describe, also read the raw metadata file directly:
>
> ```bash
> # The metadataFile path is returned in the describe response, e.g.:
> ~/.uipath/cache/integrationservice/<connector>/<connection-id>/<object>.<Operation>.json
> ```
>
> In that file, look for the top-level `parameters` array. Any entry with `"required": true` **must** be passed in `queryParameters` or `pathParameters` (based on its `"in"` field: `"query"` or `"path"`). These will not appear in `requiredFields` and will silently be missing if you rely on describe alone.

### Step 1b — Check for multipart parameters (CRITICAL for Create/Update)

After running `describe`, check whether the endpoint requires `multipart/form-data` by reading the raw metadata file returned in the describe response:

```bash
# metadataFile path is returned in the describe response, e.g.:
# ~/.uipath/cache/integrationservice/<connector>/<connection-id>/<object>.<Operation>.json

cat ~/.uipath/cache/integrationservice/<connector>/<connection-id>/<object>.Create.json \
  | python3 -c "
import json, sys
d = json.load(sys.stdin)
mp = [p for p in d.get('parameters', []) if p.get('type') == 'multipart' or p.get('in') == 'multipart']
print('MULTIPART PARAMS:', mp if mp else 'None — safe to use ExecuteAsync without multipartParameters')
"
```

**If multipart parameters are found:**
- Pass `multipartParameters: new Dictionary<string, object?>()` to `ExecuteAsync` — this signals multipart encoding.
- For file attachments, add `IResource` values to `multipartParameters` (keyed by the form-data field name).
- `bodyParameters` is still serialized as JSON and attached as the `body` part of the form.

**If no multipart parameters are found:** proceed normally to Step 2.

### Step 2 — Resolve reference fields (if any)

If the describe output has `referenceFields`, resolve each one before calling `ExecuteAsync`:

```bash
uipcli is resources execute list "<connector-key>" "<referenced-object>" \
  --connection-id "<id>" --output json
# Pick the correct id from the results
```

### Step 3 — Write the coded workflow

Once you have all values from the describe output, pass them directly to `ExecuteAsync`. No runtime metadata call is made.

```csharp
var service = IntegrationConnectorService.Create(services.Container);

var response = await service.ExecuteAsync(
    connectionId:    "<connection-id>",
    connectorKey:    "<connector-key>",
    objectName:      "<object-name>",
    operation:       ConnectorOperation.Get,
    httpMethod:      "GET",                          // from describe MethodName
    path:            "/<object>/{pathVar}",          // from describe Path
    activityType:    ActivityType.Curated,           // Curated = activity, Generic = resource
    pathParameters:  new() { ["pathVar"] = value },  // fields with type: path
    queryParameters: new() { ["key"] = value },      // fields with type: query
    bodyParameters:  new() { ["key"] = value });     // fields with type: body
```

---

## ExecuteAsync Reference

```csharp
Task<ConnectorResponse> ExecuteAsync(
    string connectionId,                        // Integration Service connection ID
    string connectorKey,                        // e.g. "uipath-atlassian-jira"
    string objectName,                          // e.g. "curated_get_issue" or "issue"
    ConnectorOperation operation,               // List / Get / Create / Update / Delete
    string httpMethod,                          // "GET" | "POST" | "PATCH" | "PUT" | "DELETE"
    string path,                                // e.g. "/curated_get_issue/{issueId}"
    ActivityType activityType = ActivityType.Curated,
    Dictionary<string, string>?  pathParameters       = null,  // fills {variable} in path
    Dictionary<string, string>?  queryParameters      = null,  // appended as ?key=value
    Dictionary<string, object?>? bodyParameters       = null,  // sent as JSON body (or as JSON part in multipart)
    Dictionary<string, object?>? multipartParameters  = null,  // non-null → multipart/form-data; IResource values = file parts
    int maxRecords = -1,                        // List only: -1 = all records
    CancellationToken cancellationToken = default)
```

### Choosing the right parameter bucket


| Field `type` in describe output | Pass in...                                                                                         |
| ------------------------------- | -------------------------------------------------------------------------------------------------- |
| `path`                          | `pathParameters` — key must match `{variable}` name in path template                               |
| `query`                         | `queryParameters`                                                                                  |
| `body`                          | `bodyParameters` — supports nested `Dictionary<string, object>` for complex payloads               |
| `multipart`                     | Pass `multipartParameters: new()` to force multipart encoding; add `IResource` values for file uploads |


> **Important:** `pathParameters` keys must exactly match the placeholder name inside `{...}` in the path template. E.g. path `/issue/{issueId}` requires `pathParameters: new() { ["issueId"] = "APD-1" }`.

> **Connector-specific body shapes:** Some connectors wrap all body fields under a top-level key. For example, Jira's curated activities require all fields nested under `"fields"`, and reference fields (project, issuetype, reporter) must be nested objects with a single identifying key (`"key"` or `"id"`). Always verify the body shape by running the `uipcli is resources describe` command and comparing against what the design-time activity sends.

### ActivityType


| Value                  | When to use                                       |
| ---------------------- | ------------------------------------------------- |
| `ActivityType.Curated` | Object discovered via `uipcli is activities list` |
| `ActivityType.Generic` | Object discovered via `uipcli is resources list`  |


---

## ConnectorResponse Reference

```csharp
public class ConnectorResponse
{
    // Populated for List operations — each item is a flat or nested dictionary
    IReadOnlyList<IReadOnlyDictionary<string, object?>> Items { get; }

    // Populated for Get / Create / Update / Delete
    IReadOnlyDictionary<string, object?> Output { get; }

    // Populated when the operation returns a file (e.g. download)
    IFileResource? FileResource { get; }
}
```

```csharp
// List
foreach (var record in response.Items)
    Log(record["Name"]?.ToString());

// Get / Create / Update
var id = response.Output["id"]?.ToString();

// Nested value
if (response.Output["address"] is IReadOnlyDictionary<string, object?> addr)
    Log(addr["city"]?.ToString());
```

## ActivityType Values

Defined in `UiPath.IntegrationService.Activities.Runtime.Models.ActivityType`:


| Value                         | Description                                                  |
| ----------------------------- | ------------------------------------------------------------ |
| `ActivityType.Curated`        | Pre-built named activity from `uipcli is activities list`    |
| `ActivityType.Generic`        | Raw CRUD resource from `uipcli is resources list`            |
| `ActivityType.CuratedTrigger` | *(reserved — triggers not yet supported in coded workflows)* |
| `ActivityType.GenericTrigger` | *(reserved — triggers not yet supported in coded workflows)* |


---

## ConnectorOperation Values


| Value                       | Maps to                   | Typical HTTP method |
| --------------------------- | ------------------------- | ------------------- |
| `ConnectorOperation.List`   | List all records          | `GET`               |
| `ConnectorOperation.Get`    | Retrieve one record by ID | `GET`               |
| `ConnectorOperation.Create` | Create a new record       | `POST`              |
| `ConnectorOperation.Update` | Partially update a record | `PATCH` or `PUT`    |
| `ConnectorOperation.Delete` | Delete a record           | `DELETE`            |


---

## Error Handling

```csharp
try
{
    var response = await service.ExecuteAsync(...);
}
catch (UiPath.IntegrationService.Activities.Runtime.Exceptions.RuntimeException ex)
{
    // ex.Message contains the error from the connector (e.g. "Missing path variables")
    Log($"Connector error: {ex.Message}", LogLevel.Error);
    throw;
}
```

Common errors and fixes:


| Error                                           | Cause                                                                   | Fix                                                                                |
| ----------------------------------------------- | ----------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| `Missing path variables in URL '.../{varName}'` | `pathParameters` key doesn't match `{varName}` in path template                                               | Use exact placeholder name from the path string                                                                            |
| `404 Not Found` on metadata call                | Leading `/` in path used as relative URI                                                                      | Ensure path is passed without manual URI construction — `ExecuteAsync` handles it                                          |
| `A suitable constructor could not be located`   | DI registration issue                                                                                         | Ensure `IntegrationConnectorService.Create(services.Container)` is used, not `new`                                        |
| `Operation 'X' is not supported`                | `ConnectorOperation` value has no matching method in connector metadata                                       | Check `uipcli is resources describe` for supported operations                                                              |
| `Unable to parse multipart body` / `415 Unsupported Media Type` | Endpoint requires `multipart/form-data` but `bodyParameters` was sent as `application/json` | Pass `multipartParameters: new Dictionary<string, object?>()` — see Step 1b; check metadata with `grep '"type": "multipart"'` |


---

## Full Example — Jira

All values below come from running the uipath-development skill describe commands first.

```csharp
using UiPath.CodedWorkflows;
using UiPath.IntegrationService.Activities.Runtime.CodedWorkflows;
using UiPath.IntegrationService.Activities.Runtime.Models;

namespace MyProject
{
    public class JiraIssuesWorkflow : CodedWorkflow
    {
        [Workflow]
        public async Task Execute(string connectionId)
        {
            var service = IntegrationConnectorService.Create(services.Container);

            // CREATE — curated activity, fields wrapped under "fields" key.
            // Resolved from: uipcli is activities list "uipath-atlassian-jira"
            //   → object: curated_create_issue, MethodName: POST, Path: /curated_create_issue
            // Reference fields (project, issuetype, reporter) are nested objects.
            // Resolve their ids/keys via:
            //   uipcli is resources execute list "uipath-atlassian-jira" "project" --connection-id <id>
            //   uipcli is resources execute list "uipath-atlassian-jira" "issuetype" --connection-id <id>
            var createResponse = await service.ExecuteAsync(
                connectionId:   connectionId,
                connectorKey:   "uipath-atlassian-jira",
                objectName:     "curated_create_issue",
                operation:      ConnectorOperation.Create,
                httpMethod:     "POST",
                path:           "/curated_create_issue",
                activityType:   ActivityType.Curated,
                bodyParameters: new()
                {
                    ["fields"] = new Dictionary<string, object?>
                    {
                        ["summary"]   = "Bug found in production",
                        ["project"]   = new Dictionary<string, object?> { ["key"] = "APD" },
                        ["issuetype"] = new Dictionary<string, object?> { ["id"]  = "10304" },
                        ["reporter"]  = new Dictionary<string, object?> { ["id"]  = "712020:89f83693-a619-42a5-a23f-0ea40c216456" }
                    }
                });

            var issueId = createResponse.Output["key"]?.ToString();
            Log($"Created: {issueId}");

            // GET — curated activity, issueId is path param, project/issuetype are query params
            // Resolved from: uipcli is resources describe "uipath-atlassian-jira" "curated_get_issue"
            //   --operation Retrieve
            //   → Path: /curated_get_issue/{issueId}
            //   → issueId: type=path, project: type=query, issuetype: type=query
            var getResponse = await service.ExecuteAsync(
                connectionId:    connectionId,
                connectorKey:    "uipath-atlassian-jira",
                objectName:      "curated_get_issue",
                operation:       ConnectorOperation.Get,
                httpMethod:      "GET",
                path:            "/curated_get_issue/{issueId}",
                activityType:    ActivityType.Curated,
                pathParameters:  new() { ["issueId"]   = issueId },
                queryParameters: new() { ["project"]   = "APD", ["issuetype"] = "10306" });

            // Jira wraps all issue fields under "fields" in the response
            var fields = getResponse.Output["fields"] as IReadOnlyDictionary<string, object?>;
            Log($"Summary: {fields?["summary"]}");

            // LIST — generic resource, JQL filter as query param
            // Resolved from: uipcli is resources list "uipath-atlassian-jira"
            //   --operation List
            //   → object: issue, MethodName: GET, Path: /issue
            var listResponse = await service.ExecuteAsync(
                connectionId:    connectionId,
                connectorKey:    "uipath-atlassian-jira",
                objectName:      "issue",
                operation:       ConnectorOperation.List,
                httpMethod:      "GET",
                path:            "/issue",
                activityType:    ActivityType.Generic,
                queryParameters: new() { ["jql"] = "project = APD AND status = Open" },
                maxRecords:      20);

            foreach (var issue in listResponse.Items)
                Log($"{issue["key"]} — {issue["summary"]}");
        }
    }
}
```