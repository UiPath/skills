# Orchestrator HTTP Request

`UiPath.Core.Activities.OrchestratorHttpRequest`

Performs HTTP requests to the Orchestrator API by authenticating under the robot it is executed on.

**Package:** `UiPath.System.Activities`
**Category:** API

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `JSONPayload` | Relative Endpoint | InArgument | `string` | Conditional | — | The JSON request body. Required when `Method` is POST, PUT, or PATCH. Can also be configured as a project setting under `OrchestratorHTTPRequest / RelativeEndpoint`. |
| `RelativeEndpoint` | Relative Endpoint | InArgument | `string` | No | — | The relative URL path of the Orchestrator API endpoint to call (e.g. `/odata/Queues`). |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `Method` | Method | `OrchestratorAPIHttpMethods` | — | The HTTP method to use for the request. |
| `ResponseHeaders` | Headers | `OutArgument<Dictionary<string, string>>` | — | Output property. See Output section. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Result` | Result | OutArgument | `string` | The raw response body returned by the Orchestrator API as a JSON string. |
| `StatusCode` | StatusCode | OutArgument | `int` | The HTTP status code of the response (e.g. 200, 201, 400, 404). |
| `ResponseHeaders` | Headers | OutArgument | `Dictionary<string, string>` | The HTTP response headers returned by the Orchestrator API. |

## Valid Configurations

- `JSONPayload` is required when `Method` is `POST`, `PUT`, or `PATCH` (any method that requires a request body). The designer enforces this via an `InitializeRules` validation.
- `RelativeEndpoint` is the path relative to the Orchestrator base URL (e.g. `/odata/Jobs`, `/odata/Queues(1234)/UiPathODataSvc.GetQueueItemById`).
- `JSONPayload` can be saved as a project-level setting under the `OrchestratorHTTPRequest` section with key `RelativeEndpoint`.

### Enum Reference

**OrchestratorAPIHttpMethods**

| Value | Description |
|-------|-------------|
| `GET` | Retrieve a resource or collection. No request body required. |
| `POST` | Create a new resource. Requires a JSON body. |
| `PUT` | Replace an existing resource. Requires a JSON body. |
| `PATCH` | Partially update an existing resource. Requires a JSON body. |
| `DELETE` | Delete a resource. No request body required. |

## XAML Example

```xml
<!-- GET: retrieve queue definitions -->
<ui:OrchestratorHttpRequest
    RelativeEndpoint="&quot;/odata/QueueDefinitions&quot;"
    Method="GET"
    Result="[responseJson]"
    StatusCode="[statusCode]"
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities" />

<!-- POST: add a queue item directly via API -->
<ui:OrchestratorHttpRequest
    RelativeEndpoint="&quot;/odata/Queues/UiPathODataSvc.AddQueueItem&quot;"
    Method="POST"
    JSONPayload="[jsonBody]"
    Result="[responseJson]"
    StatusCode="[statusCode]"
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities" />
```

## Notes

- Requires an active Orchestrator connection. The robot must be connected to Orchestrator at runtime. Authentication is handled automatically using the robot's credentials — no API key or token is required in the workflow.
- The base URL of the Orchestrator instance is resolved from the robot's connection context. Only the relative path needs to be specified.
- `Result` contains the raw JSON response body as a string. Deserialize it (e.g. using `Newtonsoft.Json.JObject.Parse`) to work with the response data.
- `FolderPath` is an advanced/hidden property inherited from the base activity that can override the Orchestrator folder context.
