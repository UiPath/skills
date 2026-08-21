# Service Discovery

An agent skill for progressively exploring an unknown service URL and producing a working coded workflow.

## Important instruction for agents

Read this file **completely** before generating any code. The workflow is sequential — each phase depends on the output of the previous one. Do **not** skip phases or assume the service type up front.

### Hard rules — always enforced

**RULE 1 — Never use bash, curl, or any shell tool for API exploration.**
All HTTP probing must be done by writing a UiPath coded workflow using `http.SendRequestAsync` with `SaveRawRequestResponse = true`. Read `RawRequestDebuggingInfo` from the logs — it captures exact headers sent/received, redirect chains, retry history, timing, and body previews that external tools cannot replicate. Probe pattern:
```csharp
var options = HttpRequestOptions.ForGet(url);
options.ContinueOnError = true;
options.ResponseOptions.SaveRawRequestResponse = true;
var response = http.SendRequestAsync(options).GetAwaiter().GetResult();
Log(response.RawRequestDebuggingInfo);
Log($"Status: {response.GetStatusCodeNumber()}  Media-Type: {response.GetMediaType()}");
Log(response.TextContent);
```

**RULE 2 — Always add `using UiPath.Web.Activities.API` in every coded workflow.**
`HttpResponseSummaryExtensions` — which provides `IsSuccessStatusCode()`, `IsServerError()`, `IsClientError()`, `IsRedirect()`, `HasTextContent()`, `HasFile()`, `GetStatusCodeNumber()`, `GetHeader()`, `GetMediaType()`, `GetContentType()`, `GetCharset()`, `GetWwwAuthenticate()`, `GetRedirectLocation()` — lives in `UiPath.Web.Activities.API` namespace, assembly `UiPath.Web.Activities.API.dll`. This is a separate assembly from `UiPath.Web.Activities.dll` where `HttpResponseSummary` itself lives. Omitting it causes all extension method calls to fail to compile. Required usings:
```csharp
using UiPath.Web.Activities.API;         // HttpResponseSummaryExtensions
using UiPath.Web.Activities.API.Models;  // HttpRequestOptions, RetryPolicyOptions, etc.
using UiPath.Web.Activities.Http.Models; // HttpResponseSummary, FormDataPart, etc.
```

**RULE 3 — Follow every phase in this skill in order. No shortcuts.**
Do not skip phases, do not assume the service type up front, do not write the final workflow before completing the probe and spec-parse phases. Each phase gate must be passed before proceeding to the next.

**RULE 4 — Use the full `HttpResponseSummaryExtensions` set on every response.**
Prefer extension methods over raw property access: `GetStatusCodeNumber()` not `(int)response.StatusCode`, `IsSuccessStatusCode()` not manual status comparison, `HasTextContent()` before any JSON parsing, `GetMediaType()` for content-type checks. Always log `RawRequestDebuggingInfo` on every non-success path.

## When to use

The user provides a URL (or a base URL + a vague goal) and expects you to:

1. Figure out whether it is a REST or SOAP service.
2. Download and parse its interface definition (OpenAPI / Swagger / WSDL).
3. Optionally map a user goal to a specific operation.
4. Generate a coded workflow that calls the operation and reaches a **200 OK**.

The user may have **zero knowledge** of the service. Treat every assumption as unverified until a response confirms it.

## Prerequisites

- The URL must be reachable from the runtime environment.
- Authentication credentials, if required, must be supplied by the user (prompt when a 401/403 is received).
- The coded workflow project must reference `UiPath.Web.Activities.API` (provides `IHttpService` and `ISoapService`).
- `Newtonsoft.Json` is available in coded workflows for JSON serialization/deserialization.

---

## Phase 1 — Determine service type

### Goal

Classify the URL as **REST**, **SOAP**, or **Unknown** by probing for well-known interface documents.

### Strategy

Send lightweight GET requests using `IHttpService` with `ContinueOnError = true` and `SaveRawRequestResponse = true` so that failures return a synthetic 503 instead of throwing, and debug info is captured.

Probe the following suffixes **in order** (stop as soon as one succeeds):

#### REST / OpenAPI probes

| Probe URL | Indicates |
| --- | --- |
| `{base}/swagger/v1/swagger.json` | ASP.NET default Swagger |
| `{base}/swagger.json` | Common alternative |
| `{base}/openapi.json` | OpenAPI 3.x convention |
| `{base}/api-docs` | Swagger UI / SpringFox |
| `{base}/v2/api-docs` | SpringFox v2 |
| `{base}/v3/api-docs` | SpringDoc v3 |

#### SOAP / WSDL probes

| Probe URL | Indicates |
| --- | --- |
| `{base}?wsdl` | Standard WSDL query |
| `{base}?WSDL` | Case-variant WSDL query |
| `{base}?singleWsdl` | WCF single-file WSDL |

#### Fallback: inspect the base URL

If no suffix matches, GET the base URL itself and inspect:
- `Content-Type` header via `response.GetMediaType()`:
  - `application/json` or `text/html` → likely REST.
  - `text/xml` or `application/xml` → likely SOAP (look for `<wsdl:` or `<soap:` in body).
- Response body content for clues (HTML page with links, JSON payload, XML envelope).

### Decision

| Evidence | Classification |
| --- | --- |
| A probe returned valid JSON with `"openapi"` or `"swagger"` key | **REST** — proceed to Phase 2A |
| A probe returned valid XML with `<wsdl:definitions>` or `<definitions>` root | **SOAP** — proceed to Phase 2B |
| Base URL returned JSON or HTML but no interface doc found | **REST (no spec)** — proceed to Phase 2C |
| Nothing useful returned (all 4xx/5xx or connection errors) | **Unknown** — report to user, ask for guidance |

### Coded workflow example — probing

```csharp
var baseUrl = "https://example.com/api";

// Try OpenAPI/Swagger first
var probes = new[]
{
    $"{baseUrl}/swagger/v1/swagger.json",
    $"{baseUrl}/swagger.json",
    $"{baseUrl}/openapi.json",
    $"{baseUrl}/api-docs",
    $"{baseUrl}/v2/api-docs",
    $"{baseUrl}/v3/api-docs",
};

HttpResponseSummary specResponse = null;
string specUrl = null;

foreach (var probe in probes)
{
    var options = HttpRequestOptions.ForGet(probe)
        .WithTimeout(15_000);
    options.ContinueOnError = true;
    options.ResponseOptions.SaveRawRequestResponse = true;

    var response = await http.SendRequestAsync(options);

    if (response.IsSuccessStatusCode() && response.HasTextContent())
    {
        var mediaType = response.GetMediaType();
        if (mediaType != null && mediaType.Contains("json"))
        {
            specResponse = response;
            specUrl = probe;
            break;
        }
    }
}

// If no REST spec found, try WSDL
if (specResponse == null)
{
    var wsdlProbes = new[]
    {
        $"{baseUrl}?wsdl",
        $"{baseUrl}?WSDL",
        $"{baseUrl}?singleWsdl",
    };

    foreach (var probe in wsdlProbes)
    {
        var options = HttpRequestOptions.ForGet(probe)
            .WithTimeout(15_000);
        options.ContinueOnError = true;
        options.ResponseOptions.SaveRawRequestResponse = true;

        var response = await http.SendRequestAsync(options);

        if (response.IsSuccessStatusCode() && response.HasTextContent())
        {
            var body = response.TextContent;
            if (body.Contains("<wsdl:definitions") || body.Contains("<definitions"))
            {
                specResponse = response;
                specUrl = probe;
                break; // SOAP detected
            }
        }
    }
}
```

---

## Phase 2A — Parse REST interface (OpenAPI / Swagger)

### Goal

Build an in-memory model of available endpoints, methods, parameters, and request/response shapes.

### Steps

1. Deserialize the spec JSON into a `JObject` using `Newtonsoft.Json.Linq.JObject.Parse(specResponse.TextContent)`.
2. Extract:
   - **basePath / servers** — the actual base URL for calls.
   - **paths** — each path key + HTTP methods underneath.
   - **parameters** — query, header, path, and body parameters for each operation.
   - **requestBody / schemas** — expected request shapes (JSON Schema or `$ref` to `#/components/schemas/...`).
   - **responses** — expected response status codes and shapes.
3. Build a summary list: `operationId`, `method`, `path`, `summary`, `parameters`, `requestBodySchema`, `responseSchema`.

### Presenting the model

If the user has a specific goal → proceed to **Phase 3**.
If the user has no specific goal → present a numbered list of operations with their summaries and ask the user to pick one, or offer to download the raw spec as a file:

```csharp
// Save the spec to a file for the user
var downloadOptions = HttpRequestOptions.ForGet(specUrl)
    .WithFileDownload(targetFolder: @"C:\temp", fileName: "openapi-spec.json");

var fileResponse = await http.SendRequestAsync(downloadOptions);
// fileResponse.File now contains the saved ILocalResource
```

---

## Phase 2B — Parse SOAP interface (WSDL)

### Goal

Extract available contracts, operations, and message shapes from the WSDL document.

### Steps

1. Parse the WSDL XML using `System.Xml.Linq.XDocument.Parse(specResponse.TextContent)`.
2. Extract:
   - **Service name** — `<wsdl:service name="...">`.
   - **Port types (contracts)** — `<wsdl:portType name="...">` → each contains `<wsdl:operation>` elements.
   - **Operations per contract** — name, input message, output message.
   - **Message schemas** — `<wsdl:types>` → inline XSD or imports.
   - **Bindings** — SOAP 1.1 vs 1.2, transport URL.
3. Build a summary list: `contractName`, `operationName`, `inputParameters`, `outputShape`.

### Presenting the model

Same logic as Phase 2A — if the user has a goal, proceed to Phase 3. Otherwise list operations or offer to save the WSDL:

```csharp
var downloadOptions = HttpRequestOptions.ForGet(specUrl)
    .WithFileDownload(targetFolder: @"C:\temp", fileName: "service.wsdl");

var fileResponse = await http.SendRequestAsync(downloadOptions);
```

---

## Phase 2C — No spec available (REST heuristic exploration)

### Goal

When no interface document is found, explore the service by making requests and inspecting responses.

### Steps

1. GET the base URL — inspect the response body for links, API keys, or embedded documentation.
2. Try common REST patterns: `{base}/api`, `{base}/api/v1`, `{base}/api/v2`.
3. If the response is JSON, analyze its structure to infer available resources.
4. If the response is HTML, look for `<a>` tags pointing to API endpoints or documentation.
5. Report findings to the user and ask for guidance before proceeding.

---

## Phase 3 — Map user goal to an operation

### Goal

Given the user's stated intent (e.g., "get a list of users", "create an order"), find the best-matching operation from the model built in Phase 2.

### Matching strategy

1. **Exact match** — `operationId` or operation `summary` closely matches the user's words.
2. **Semantic match** — HTTP method + path pattern implies the intent (e.g., `GET /users` for "list users", `POST /orders` for "create order").
3. **Ambiguous** — multiple candidates match → present a short list and ask the user to confirm.

Once an operation is selected, extract:
- The full request URL (base + path, with path parameter placeholders).
- Required and optional parameters (query, header, path, body).
- The request body JSON schema (if applicable).
- The expected success response shape.

---

## Phase 4 — Generate DTOs (if needed)

### Goal

When the selected operation has a structured request or response body, generate C# DTO classes in the project so the agent can use strongly-typed serialization.

### When to generate DTOs

- The request body schema defines an object with named properties.
- The response schema defines an object the user will need to inspect or transform.
- The user explicitly asks for typed models.

### Rules

- Place DTO files in the project directory, using a `Models` subfolder if one exists, or create one.
- Name the file after the schema/class (e.g., `CreateOrderRequest.cs`, `UserResponse.cs`).
- Use `Newtonsoft.Json` attributes (`[JsonProperty("...")]`) only when the JSON property name differs from the C# property name.
- Keep DTOs simple — public properties with getters and setters, no business logic.
- Use nullable types for optional fields.

### Example DTO

```csharp
// Models/CreateOrderRequest.cs
using Newtonsoft.Json;

public class CreateOrderRequest
{
    [JsonProperty("product_id")]
    public string ProductId { get; set; }

    public int Quantity { get; set; }

    [JsonProperty("shipping_address")]
    public string ShippingAddress { get; set; }
}
```

### Serialization in the workflow

```csharp
var requestBody = new CreateOrderRequest
{
    ProductId = "PROD-001",
    Quantity = 2,
    ShippingAddress = "123 Main St"
};

var json = JsonConvert.SerializeObject(requestBody);
var response = await http.PostJsonAsync("https://api.example.com/orders", json);
```

### Deserialization of the response

```csharp
if (response.IsSuccessStatusCode() && response.HasTextContent())
{
    var order = JsonConvert.DeserializeObject<OrderResponse>(response.TextContent);
}
```

---

## Phase 5 — Progressive request execution

### Goal

Build and send the actual request, then iteratively fix issues until a **200 OK** (or the expected success code) is received.

### Strategy

Always enable debug output so each attempt produces diagnostic information:

```csharp
var options = HttpRequestOptions.ForPost("https://api.example.com/orders")
    .WithJsonBody(json)
    .WithTimeout(30_000);

options.ContinueOnError = true;
options.ResponseOptions.SaveRawRequestResponse = true;
```

### Iteration loop

```
attempt = 0
while not success and attempt < MAX_ATTEMPTS:
    send request
    inspect response.StatusCode, response.TextContent, response.RawRequestDebuggingInfo
    diagnose failure
    adjust request
    attempt++
```

### Diagnosis table

| Status | Likely cause | Agent action |
| --- | --- | --- |
| **401 Unauthorized** | Missing or invalid credentials | Check `response.GetWwwAuthenticate()` for the required auth scheme. Ask the user for credentials. Apply `.WithBearerToken()` or `.WithBasicAuth()`. |
| **403 Forbidden** | Insufficient permissions | Report to user — credentials are valid but lack authorization for this operation. |
| **404 Not Found** | Wrong URL or path parameters | Re-check the base URL, path, and any path parameters. Try alternative paths from the spec. |
| **405 Method Not Allowed** | Wrong HTTP method | Check the `Allow` header via `response.GetHeader("Allow")` and switch to the correct method. |
| **400 Bad Request** | Malformed body or missing parameters | Parse `response.TextContent` for validation error messages. Fix the request body or add missing parameters. |
| **415 Unsupported Media Type** | Wrong `Content-Type` | Switch body content type (e.g., from `application/json` to `application/xml` or `application/x-www-form-urlencoded`). |
| **422 Unprocessable Entity** | Validation failure | Parse error details from `response.TextContent`. Adjust field values or add missing required fields. |
| **500 Internal Server Error** | Server-side issue | Inspect `response.TextContent` and `response.RawRequestDebuggingInfo` for clues. Report to user if the error is not actionable. |
| **503 Service Unavailable** | Synthetic error from `ContinueOnError`, or server overloaded | Check `response.RawRequestDebuggingInfo` — if it contains a network exception, the service is unreachable. Otherwise retry after a delay. |
| **3xx Redirect** | Service redirects to a different URL | Check `response.GetRedirectLocation()`. Update the base URL and retry. Consider enabling `FollowRedirects`. |

### Using RawRequestDebuggingInfo

The debug dump (enabled via `ResponseOptions.SaveRawRequestResponse = true`) contains the raw HTTP request and response as sent/received on the wire. Use it to:

- Verify the exact URL, headers, and body that were sent.
- Compare against the spec to find mismatches (wrong path, missing headers, malformed body).
- Identify encoding issues or unexpected content transformations.
- Present a concise diff to the user when asking for guidance.

### Example — progressive iteration


```csharp
// First attempt — minimal request
var options = HttpRequestOptions.ForGet("https://api.example.com/users")
    .WithTimeout(15_000);
options.ContinueOnError = true;
options.ResponseOptions.SaveRawRequestResponse = true;

var response = await http.SendRequestAsync(options);

if (response.IsSuccessStatusCode())
{
    // Done — parse the response
    var users = JsonConvert.DeserializeObject<List<UserResponse>>(response.TextContent);
}
else if (response.StatusCode == HttpStatusCode.Unauthorized)
{
    // Second attempt — add auth
    var authScheme = response.GetWwwAuthenticate(); // e.g., "Bearer"
    // Ask user for token, then retry:
    options = HttpRequestOptions.ForGet("https://api.example.com/users")
        .WithBearerToken(userProvidedToken)
        .WithTimeout(15_000);
    options.ContinueOnError = true;
    options.ResponseOptions.SaveRawRequestResponse = true;

    response = await http.SendRequestAsync(options);
}
else
{
    // Inspect debug info for diagnosis
    var debugInfo = response.RawRequestDebuggingInfo;
    var statusCode = response.GetStatusCodeNumber();
    var errorBody = response.TextContent;
    // Report and adjust...
}
```

---

## Phase 5B — Progressive SOAP execution

For SOAP services, use `ISoapService.CallAsync` with the contract, method, and parameters discovered in Phase 2B:

```csharp
var response = await soap.CallAsync(new SoapRequestOptions
{
    EndPoint = specUrl,  // the WSDL URL
    ContractName = "DiscoveredContractName",
    Method = "DiscoveredMethodName",
    Parameters = new Dictionary<string, object>
    {
        { "paramName", paramValue }
    },
    ContinueOnError = true
});

if (response.IsSuccessStatusCode())
{
    var xmlDoc = XDocument.Parse(response.TextContent);
    // Extract results using LINQ to XML or XPath
}
else
{
    var statusCode = response.GetStatusCodeNumber();
    var errorBody = response.TextContent;
    // Diagnose and adjust parameters
}
```

The same diagnosis table from Phase 5 applies. For SOAP-specific faults, parse the `<soap:Fault>` element from `response.TextContent` to extract `<faultcode>` and `<faultstring>`.

---

## Summary — Agent decision flow

```
User provides URL
       │
       ▼
  Phase 1: Probe for spec
       │
       ├── REST spec found ──────► Phase 2A: Parse OpenAPI
       ├── WSDL found ──────────► Phase 2B: Parse WSDL
       ├── No spec, got response ► Phase 2C: Heuristic exploration
       └── Nothing works ────────► Report to user, stop
       │
       ▼
  User has a goal?
       │
       ├── Yes ──► Phase 3: Map goal to operation
       └── No ───► List operations or download spec
       │
       ▼
  Phase 4: Generate DTOs (if operation has structured body)
       │
       ▼
  Phase 5/5B: Progressive execution until success
       │
       ▼
  Return working coded workflow to user
```

## See Also

- [NetHttpRequest Activity](../../UiPath.Web.Activities.Package.Design/docs/activities/NetHttpRequest.md) — HTTP activity behavior spec, inputs, outputs, and defaults
- [cURL Import](curl-import.md) — converting raw cURL commands to HttpRequestOptions
- [HTTP Request Upgrade](http-request-upgrade.md) — migrating from legacy HTTP Request activity
