# UiPath.Web.Activities - Coded Workflow API

`UiPath.WebAPI.Activities`

HTTP automation APIs for coded workflows, including request execution, convenience verb methods, payload helpers, multipart upload, and file transfer support.

**Service accessor:** `http` (type `IHttpService`)  
**Service accessor:** `soap` (type `ISoapService`)  
**Service accessor:** `curl` (type `ICurlImportService`)  
**Required package:** `"UiPath.WebAPI.Activities": "[2.5.0,)"` in project.json dependencies

## Auto-Imported Namespaces

These namespaces are automatically available in coded workflows when this package is installed:

```csharp
System
System.Collections.Generic
System.Net
UiPath.Web.Activities.API
UiPath.Web.Activities.API.Models
UiPath.Web.Activities.Http.Models
```

## Agent Capabilities

This package exposes three core services for HTTP/SOAP automation in coded workflows. Agents can invoke workflows based on the following scenario:

### **Core Services**

| Service | Type | Access | Capability |
|---------|------|--------|-----------|
| `http` | `IHttpService` | `http` service accessor | Send HTTP requests (GET/POST/PUT/DELETE/PATCH/etc.) with advanced options: authentication, retries, file upload/download, multipart forms, timeout, redirects. Returns `HttpResponseSummary` with response inspection helpers. |
| `soap` | `ISoapService` | `soap` service accessor | Invoke SOAP operations via WSDL metadata. Requires endpoint, contract, method, and parameters. Returns `HttpResponseSummary` with XML content in `TextContent`. |
| `curl` | `ICurlImportService` | `curl` service accessor | Parse raw cURL commands into structured `HttpRequestOptions`. Handles bash/cmd styles, auto-detects shell escaping, produces actionable warnings. |

### **Agent Workflow Triggers**

| User Intent | Agent Workflow | Entry Point |
|---|---|---|
| "Convert this cURL command" | cURL import + optional reconfiguration | [curl-import.md](curl-import.md) skill — parse cURL, handle warnings, execute with `http.SendRequestAsync()` |
| "Call this URL but I don't know what it is" | Service discovery + auto-detection | [service-discovery.md](service-discovery.md) skill — probe for REST/SOAP, parse interface docs (OpenAPI/WSDL), map user goal, generate DTOs, iterate to success |
| "Migrate from the old HTTP activity" | Legacy activity translation + verification | [http-request-upgrade.md](http-request-upgrade.md) skill — 5-phase capture→translate→compare workflow with safety gates |
| "Send an HTTP GET/POST/etc. with auth, retry, file handling" | Direct API usage | Use `http.SendRequestAsync(HttpRequestOptions)` or convenience verb methods (`GetAsync`, `PostJsonAsync`, `PostMultipartAsync`, `DownloadFileAsync`, `UploadFileAsync`) |
| "Parse/deserialize JSON response" | Native .NET methods | `Newtonsoft.Json.JsonConvert.DeserializeObject<T>(response.TextContent)` or `JsonConvert.DeserializeObject` + JArray.Parse for arrays |
| "Parse/evaluate XML response or XPath" | Native .NET LINQ to XML | `System.Xml.Linq.XDocument.Parse(response.TextContent)` + `XElement`, `XPathEvaluate`, `Descendants`, etc. |

### **Common Patterns**

- **Request inspection:** Use `response.GetStatusCodeNumber()`, `response.IsSuccessStatusCode()`, `response.GetHeader(name)`, `response.GetMediaType()` to inspect responses without manual header parsing.
- **Error handling:** Set `ContinueOnError = true` in options to get synthetic 503 responses instead of exceptions; inspect `response.TextContent` for error details.
- **File operations:** Use `DownloadFileAsync(url, targetFolder, fileName)` or `UploadFileAsync(url, filePath)` for file transfer; `PostMultipartAsync(url, parts)` for multipart form uploads.
- **Retries & timeout:** Configure `RetryPolicy` (Basic, ExponentialBackoff, None) and `TimeoutMilliseconds` in `HttpRequestOptions`.
- **Authentication:** Use `.WithBasicAuth(user, pass)`, `.WithBearerToken(token)`, or set custom `Headers["Authorization"]` for other schemes.

---

## Skills & Related Workflows

This API reference covers direct programmatic use of `IHttpService`, `ISoapService`, and `ICurlImportService`. For common workflows, refer to these companion agent skills:

| Skill | Use case | Key workflow |
|-------|----------|--------------|
| [curl-import.md](curl-import.md) | Convert raw cURL commands to `HttpRequestOptions` | **Deterministic parsing + warning-driven reconfiguration.** Import a cURL, inspect warnings, adjust if needed, execute. Best for cURL → coded workflow conversion. |
| [service-discovery.md](service-discovery.md) | Discover unknown service endpoints (REST/SOAP) and generate working requests | **Progressive probing + spec parsing + iterative execution.** Given a URL, auto-detect service type, parse interface docs (OpenAPI/WSDL), map user intent to operations, generate DTOs, and iterate until success. Best for green-field integration. |
| [http-request-upgrade.md](http-request-upgrade.md) | Migrate from legacy `HttpClient` activity to modern `NetHttpRequest` in coded workflows | **High-risk 5-phase refactor with checkpoint gates.** Capture legacy baseline, translate inputs, compare outputs in test environment, verify downstream logic. One activity at a time with learnings carryover. |

---

## Service Overview

The `http` service follows a direct-method API pattern. You can either:
- Call convenience methods like `GetAsync`, `PostJsonAsync`, and `PostMultipartAsync`
- Use `SendRequestAsync` with a fully configured `HttpRequestOptions` object for advanced control

All methods return `Task<HttpResponseSummary>`, which contains status information, response content metadata, and diagnostic context for the request.

The same package also exposes:
- `soap` (`ISoapService`) for SOAP requests through `CallAsync(SoapRequestOptions options, CancellationToken cancellationToken = default)`
- `curl` (`ICurlImportService`) for cURL-to-options conversion through `Import(string rawCurl, CurlImportOptions options = null)`

## Response Extensions Quick Reference

Use `HttpResponseSummaryExtensions` to inspect common response characteristics and metadata.

| Extension method | Purpose |
|------------------|---------|
| `IsSuccessStatusCode()` | Returns `true` for 2xx responses. |
| `IsClientError()` | Returns `true` for 4xx responses. |
| `IsServerError()` | Returns `true` for 5xx responses. |
| `IsRedirect()` | Returns `true` for 3xx responses. |
| `GetStatusCodeNumber()` | Returns the numeric status code (for example, `200`, `404`). |
| `GetHeader(string name)` | Returns the first matching response or content header value (case-insensitive). |
| `GetContentType()` | Returns the full `Content-Type` value, if present. |
| `GetMediaType()` | Returns the media type portion of `Content-Type` (for example, `application/json`). |
| `GetCharset()` | Returns the charset from `Content-Type` when available. |

For detailed runtime behavior, defaults, and cross-property interactions, see the NetHttpRequest activity reference documentation.

## Core

### `SendRequestAsync(HttpRequestOptions options, CancellationToken cancellationToken = default)`

Sends an HTTP request with the specified options.

**Parameters:**
- `options` (`HttpRequestOptions`) - The HTTP request options.
- `cancellationToken` (`CancellationToken`) - Token to cancel the asynchronous operation. (default: `default`)

**Returns:** `Task<HttpResponseSummary>` - Asynchronous result that contains the HTTP response summary for the executed request.

## Basic Verbs (No Body)

### `GetAsync(string url, CancellationToken cancellationToken = default)`

Sends an HTTP GET request to the specified URL.

**Parameters:**
- `url` (`string`) - The request URL.
- `cancellationToken` (`CancellationToken`) - Token to cancel the asynchronous operation. (default: `default`)

**Returns:** `Task<HttpResponseSummary>` - Asynchronous result containing the response summary for the GET operation.

### `HeadAsync(string url, CancellationToken cancellationToken = default)`

Sends an HTTP HEAD request to the specified URL to check resource availability without downloading the body.

**Parameters:**
- `url` (`string`) - The request URL.
- `cancellationToken` (`CancellationToken`) - Token to cancel the asynchronous operation. (default: `default`)

**Returns:** `Task<HttpResponseSummary>` - Asynchronous result containing headers and status summary for the HEAD operation.

### `DeleteAsync(string url, CancellationToken cancellationToken = default)`

Sends an HTTP DELETE request to the specified URL.

**Parameters:**
- `url` (`string`) - The request URL.
- `cancellationToken` (`CancellationToken`) - Token to cancel the asynchronous operation. (default: `default`)

**Returns:** `Task<HttpResponseSummary>` - Asynchronous result containing the response summary for the DELETE operation.

### `OptionsAsync(string url, CancellationToken cancellationToken = default)`

Sends an HTTP OPTIONS request to the specified URL to retrieve communication options.

**Parameters:**
- `url` (`string`) - The request URL.
- `cancellationToken` (`CancellationToken`) - Token to cancel the asynchronous operation. (default: `default`)

**Returns:** `Task<HttpResponseSummary>` - Asynchronous result containing allowed methods and response summary for the OPTIONS operation.

### `TraceAsync(string url, CancellationToken cancellationToken = default)`

Sends an HTTP TRACE request to the specified URL for diagnostic purposes.

**Parameters:**
- `url` (`string`) - The request URL.
- `cancellationToken` (`CancellationToken`) - Token to cancel the asynchronous operation. (default: `default`)

**Returns:** `Task<HttpResponseSummary>` - Asynchronous result containing diagnostic trace response information.

## JSON Operations

### `PostJsonAsync(string url, string jsonContent, CancellationToken cancellationToken = default)`

Sends an HTTP POST request with a JSON body to the specified URL.

**Parameters:**
- `url` (`string`) - The request URL.
- `jsonContent` (`string`) - The JSON string to send as the request body.
- `cancellationToken` (`CancellationToken`) - Token to cancel the asynchronous operation. (default: `default`)

**Returns:** `Task<HttpResponseSummary>` - Asynchronous result containing the response summary for the JSON POST operation.

### `PutJsonAsync(string url, string jsonContent, CancellationToken cancellationToken = default)`

Sends an HTTP PUT request with a JSON body to the specified URL.

**Parameters:**
- `url` (`string`) - The request URL.
- `jsonContent` (`string`) - The JSON string to send as the request body.
- `cancellationToken` (`CancellationToken`) - Token to cancel the asynchronous operation. (default: `default`)

**Returns:** `Task<HttpResponseSummary>` - Asynchronous result containing the response summary for the JSON PUT operation.

### `PatchJsonAsync(string url, string jsonContent, CancellationToken cancellationToken = default)`

Sends an HTTP PATCH request with a JSON body to the specified URL.

**Parameters:**
- `url` (`string`) - The request URL.
- `jsonContent` (`string`) - The JSON string to send as the request body.
- `cancellationToken` (`CancellationToken`) - Token to cancel the asynchronous operation. (default: `default`)

**Returns:** `Task<HttpResponseSummary>` - Asynchronous result containing the response summary for the JSON PATCH operation.

## Form Operations

### `PostFormAsync(string url, Dictionary<string, string> formData, CancellationToken cancellationToken = default)`

Sends an HTTP POST request with form-urlencoded data to the specified URL.

**Parameters:**
- `url` (`string`) - The request URL.
- `formData` (`Dictionary<string, string>`) - The form data key-value pairs to send.
- `cancellationToken` (`CancellationToken`) - Token to cancel the asynchronous operation. (default: `default`)

**Returns:** `Task<HttpResponseSummary>` - Asynchronous result containing the response summary for the form POST operation.

### `PutFormAsync(string url, Dictionary<string, string> formData, CancellationToken cancellationToken = default)`

Sends an HTTP PUT request with form-urlencoded data to the specified URL.

**Parameters:**
- `url` (`string`) - The request URL.
- `formData` (`Dictionary<string, string>`) - The form data key-value pairs to send.
- `cancellationToken` (`CancellationToken`) - Token to cancel the asynchronous operation. (default: `default`)

**Returns:** `Task<HttpResponseSummary>` - Asynchronous result containing the response summary for the form PUT operation.

### `PatchFormAsync(string url, Dictionary<string, string> formData, CancellationToken cancellationToken = default)`

Sends an HTTP PATCH request with form-urlencoded data to the specified URL.

**Parameters:**
- `url` (`string`) - The request URL.
- `formData` (`Dictionary<string, string>`) - The form data key-value pairs to send.
- `cancellationToken` (`CancellationToken`) - Token to cancel the asynchronous operation. (default: `default`)

**Returns:** `Task<HttpResponseSummary>` - Asynchronous result containing the response summary for the form PATCH operation.

## Binary Operations

### `PostBinaryAsync(string url, byte[] binaryContent, string contentType = null, CancellationToken cancellationToken = default)`

Sends an HTTP POST request with binary content to the specified URL.

**Parameters:**
- `url` (`string`) - The request URL.
- `binaryContent` (`byte[]`) - The binary data to send as the request body.
- `contentType` (`string`) - The media type of the binary content. (default: `null`)
- `cancellationToken` (`CancellationToken`) - Token to cancel the asynchronous operation. (default: `default`)

**Returns:** `Task<HttpResponseSummary>` - Asynchronous result containing the response summary for the binary POST operation.

### `PutBinaryAsync(string url, byte[] binaryContent, string contentType = null, CancellationToken cancellationToken = default)`

Sends an HTTP PUT request with binary content to the specified URL.

**Parameters:**
- `url` (`string`) - The request URL.
- `binaryContent` (`byte[]`) - The binary data to send as the request body.
- `contentType` (`string`) - The media type of the binary content. (default: `null`)
- `cancellationToken` (`CancellationToken`) - Token to cancel the asynchronous operation. (default: `default`)

**Returns:** `Task<HttpResponseSummary>` - Asynchronous result containing the response summary for the binary PUT operation.

### `PatchBinaryAsync(string url, byte[] binaryContent, string contentType = null, CancellationToken cancellationToken = default)`

Sends an HTTP PATCH request with binary content to the specified URL.

**Parameters:**
- `url` (`string`) - The request URL.
- `binaryContent` (`byte[]`) - The binary data to send as the request body.
- `contentType` (`string`) - The media type of the binary content. (default: `null`)
- `cancellationToken` (`CancellationToken`) - Token to cancel the asynchronous operation. (default: `default`)

**Returns:** `Task<HttpResponseSummary>` - Asynchronous result containing the response summary for the binary PATCH operation.

## File Operations

### `DownloadFileAsync(string url, string targetFolder, string fileName = null, CancellationToken cancellationToken = default)`

Sends an HTTP GET request and saves the response to a file.

**Parameters:**
- `url` (`string`) - The request URL.
- `targetFolder` (`string`) - The folder where the file will be saved.
- `fileName` (`string`) - The output file name; if omitted, it is derived from the response. (default: `null`)
- `cancellationToken` (`CancellationToken`) - Token to cancel the asynchronous operation. (default: `default`)

**Returns:** `Task<HttpResponseSummary>` - Asynchronous result containing file transfer and response summary information.

### `UploadFileAsync(string url, string filePath, CancellationToken cancellationToken = default)`

Sends an HTTP POST request with a file streamed as the request body to the specified URL. For multipart/form-data uploads, use `PostMultipartAsync`.

**Parameters:**
- `url` (`string`) - The request URL.
- `filePath` (`string`) - The local path of the file to upload.
- `cancellationToken` (`CancellationToken`) - Token to cancel the asynchronous operation. (default: `default`)

**Returns:** `Task<HttpResponseSummary>` - Asynchronous result containing the response summary for streamed file upload.

### `PostMultipartAsync(string url, IEnumerable<FormDataPart> parts, CancellationToken cancellationToken = default)`

Sends an HTTP POST request with multipart/form-data content to the specified URL. Supports mixed content including text fields, binary data, and file uploads in a single request.

**Parameters:**
- `url` (`string`) - The request URL.
- `parts` (`IEnumerable<FormDataPart>`) - Multipart form-data parts (text, file, and/or binary parts).
- `cancellationToken` (`CancellationToken`) - Token to cancel the asynchronous operation. (default: `default`)

**Returns:** `Task<HttpResponseSummary>` - Asynchronous result containing the response summary for multipart uploads.

## SOAP Service API

### `CallAsync(SoapRequestOptions options, CancellationToken cancellationToken = default)`

Invokes a SOAP operation using WSDL metadata and request options. The service resolves endpoint metadata, builds the SOAP envelope, and executes the request.

**Parameters:**
- `options` (`SoapRequestOptions`) - SOAP invocation configuration, including endpoint, contract, method, and parameter values.
- `cancellationToken` (`CancellationToken`) - Token to cancel the asynchronous operation. (default: `default`)

**Returns:** `Task<HttpResponseSummary>` - Asynchronous result containing status, headers, and SOAP response details.

**Working with the result:**
- `response.TextContent` holds the raw SOAP envelope (XML). Use `XDocument.Parse(response.TextContent)` then `Descendants(...)` or `XPathEvaluate` to extract payload fields, including namespace-qualified elements via `XNamespace`.
- A SOAP Fault can be embedded inside an HTTP 200 response. Always check for a `<Fault>` element when `IsSuccessStatusCode()` returns `true`.
- Use `HttpResponseSummaryExtensions` (`IsSuccessStatusCode()`, `IsClientError()`, `IsServerError()`, `GetHeader()`, `GetMediaType()`, `GetCharset()`) to inspect the HTTP transport layer without manual header parsing.

## cURL Import API

### `Import(string rawCurl, CurlImportOptions options = null)`

Imports a raw cURL command and converts it to structured `HttpRequestOptions` that can be executed with `http.SendRequestAsync`.

**Parameters:**
- `rawCurl` (`string`) - Raw cURL command text.
- `options` (`CurlImportOptions`) - Import behavior flags controlling mapping and normalization. (default: `null`)

**Returns:** `CurlImportResult` - Parsed request options plus warnings generated during command interpretation.

### `CurlImportResult` output model

Represents the output returned by `curl.Import`.

| Property | Type | Description |
|----------|------|-------------|
| `Options` | `HttpRequestOptions` | Parsed request options; `null` when import fails. |
| `Warnings` | `IReadOnlyList<CurlImportWarning>` | Warnings and errors from parsing/normalization. |
| `Raw` | `string` | Original cURL command text. |

---

## Options & Configuration Classes

### `HttpRequestOptions`

Options for configuring an HTTP request in coded workflows.

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `Method` | `HttpMethod` | `HttpMethod.GET` | HTTP method (GET, POST, PUT, DELETE, etc.). |
| `Url` | `string` | `null` | Request URL. |
| `Parameters` | `Dictionary<string, string>` | `null` | URL query parameters. |
| `Headers` | `Dictionary<string, string>` | `null` | HTTP headers. |
| `TimeoutMilliseconds` | `int` | `10_000` | Request timeout in milliseconds. |
| `ContinueOnError` | `bool` | `false` | Continue execution when request fails. |
| `FollowRedirects` | `bool` | `true` | Whether redirects are followed automatically. |
| `MaxRedirects` | `int` | `3` | Maximum redirects to follow. |
| `Authentication` | `AuthenticationOptions` | `null` | Authentication configuration. |
| `Body` | `RequestBodyOptions` | `null` | Request body configuration. |
| `RetryPolicy` | `RetryPolicyOptions` | `new RetryPolicyOptions()` | Retry policy configuration. |
| `Client` | `ClientOptions` | `new ClientOptions()` | HTTP client configuration options. |
| `ResponseOptions` | `ResponseOptions` | `new ResponseOptions()` | Response handling options. |
| `Cookies` | `Dictionary<string, string>` | `null` | Cookies sent with the request. |

### `SoapRequestOptions`

Options for configuring SOAP requests in coded workflows.

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `EndPoint` | `string` | `null` | WSDL endpoint URL. |
| `ContractName` | `string` | `null` | WSDL contract (port type) name. |
| `Method` | `string` | `null` | SOAP operation name to invoke. |
| `Parameters` | `Dictionary<string, object>` | `null` | SOAP operation parameter name/value pairs. |
| `Username` | `string` | `null` | Username for Basic authentication. |
| `Password` | `string` | `null` | Password for Basic authentication. |
| `SecurePassword` | `SecureString` | `null` | Secure password for Basic authentication. |
| `UseWindowsCredentials` | `bool` | `false` | Use OS-level Negotiate/NTLM credentials. |
| `ClientCertificatePath` | `string` | `null` | Path to client certificate file. |
| `ClientCertificatePassword` | `string` | `null` | Password for the client certificate. |
| `ClientCertificateSecurePassword` | `SecureString` | `null` | Secure password for the client certificate. |
| `ContinueOnError` | `bool` | `false` | Continue workflow execution on SOAP errors. |

### `CurlImportOptions`

Options for controlling how raw cURL commands are translated into `HttpRequestOptions`.

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `MapFileBodyToStream` | `bool` | `true` | Map file-based body content to stream/file-path form when possible. |
| `InferJsonForTextPayload` | `bool` | `true` | Infer JSON content type for text payloads when applicable. |
| `StripAuthorizationHeaderOnAuthMapping` | `bool` | `true` | Remove Authorization header if auth is mapped into typed authentication fields. |

---

## Enum Reference

The following enums from `UiPath.Web.Activities.Http.Models` are used by the coded API options classes.

### `HttpMethod`

Used by `HttpRequestOptions.Method`.

| Value | Description |
|-------|-------------|
| `GET` | HTTP GET method. |
| `POST` | HTTP POST method. |
| `PUT` | HTTP PUT method. |
| `DELETE` | HTTP DELETE method. |
| `HEAD` | HTTP HEAD method. |
| `OPTIONS` | HTTP OPTIONS method. |
| `PATCH` | HTTP PATCH method. |
| `TRACE` | HTTP TRACE method. |

### `AuthenticationType`

Used by `AuthenticationOptions.Type`.

| Value | Description |
|-------|-------------|
| `None` | No authentication. |
| `BasicUsernamePassword` | Basic authentication with username and password. |
| `OAuthToken` | OAuth bearer token authentication. |
| `NegotiatedAuthentication` | OS-level Negotiate/NTLM authentication. |

### `HttpRequestBodyType`

Used by `RequestBodyOptions.Type`.

| Value | Description |
|-------|-------------|
| `None` | No request body. |
| `Text` | Text body (JSON, XML, plain text, etc.). |
| `FormUrlEncoded` | URL-encoded form body. |
| `MultipartFormData` | Multipart form data body. |
| `Binary` | Binary body content. |
| `Stream` | Streamed body content. |

### `RetryPolicyType`

Used by `RetryPolicyOptions.Type`.

| Value | Description |
|-------|-------------|
| `None` | No retry policy. |
| `Basic` | Fixed-interval retry. |
| `ExponentialBackoff` | Exponential backoff retry. |

### `SupportedTlsProtocols`

Used by `ClientOptions.TlsProtocol`.

| Value | Description |
|-------|-------------|
| `Automatic` | Automatically negotiate the TLS protocol version. |
| `Tls12` | TLS 1.2. |
| `Tls13` | TLS 1.3. |

### `ProxySettingType`

Used by `ClientOptions.ProxySetting`.

| Value | Description |
|-------|-------------|
| `None` | No proxy. |
| `SystemDefault` | Use the system default proxy. |
| `Custom` | Use a custom proxy configuration. |

### `FileOverwriteOption`

Used by `ResponseOptions.FileOverwrite`.

| Value | Description |
|-------|-------------|
| `AutoRename` | Automatically rename the file to avoid conflicts. |
| `Replace` | Overwrite the existing file. |
| `Discard` | Discard the download if the file already exists. |

---

## Related Activity Mappings

- `Deserialize JSON` activity is not exposed as a dedicated coded API service method; use `Newtonsoft.Json.JsonConvert.DeserializeObject<T>(...)` in coded workflows.
- `HTTP Request (Legacy)` is not exposed in coded workflows; use the `http` service (`IHttpService`) with `SendRequestAsync` instead. For behavioral differences versus the legacy activity, see [docs/activities/NetHttpRequest.md](UiPath.Web.Activities.Package.Design/docs/activities/NetHttpRequest.md).
- `Deserialize JSON Array` activity is not exposed as a dedicated coded API service method; use `Newtonsoft.Json.Linq.JArray.Parse(...)` in coded workflows.
- `Serialize JSON` activity is not exposed as a dedicated coded API service method; use `Newtonsoft.Json.JsonConvert.SerializeObject(...)` in coded workflows.
- `Deserialize XML` activity is not exposed as a dedicated coded API service method; use `System.Xml.Linq.XDocument.Parse(...)` in coded workflows.
- `Execute XPath` activity is not exposed as a dedicated coded API service method; use `System.Xml.XPath.Extensions.XPathEvaluate(...)` (for example, `XDocument.XPathEvaluate(...)`) in coded workflows.
- `Get XML Node Attributes` activity is not exposed as a dedicated coded API service method; cast to `System.Xml.Linq.XElement` and call `XElement.Attributes()` in coded workflows.
- `Get XML Nodes` activity is not exposed as a dedicated coded API service method; use `System.Xml.Linq.XDocument.Nodes()` (or `XDocument.Root?.Nodes()` for element-only traversal) in coded workflows.

---

## Common Patterns

### Basic GET request

```csharp
[Workflow]
public void Execute()
{
    var response = http.GetAsync("https://httpbin.org/get").GetAwaiter().GetResult();
    Log($"Status: {response.StatusCode}");
}
```

### Advanced request with `HttpRequestOptions`

```csharp
[Workflow]
public void Execute()
{
    var options = HttpRequestOptions.ForPost("https://httpbin.org/post")
        .WithJsonBody("{\"name\":\"uipath\"}")
        .WithHeader("X-Trace-Id", Guid.NewGuid().ToString())
        .WithBearerToken("token-value")
        .WithTimeout(30_000)
        .WithRetry(3, 1_000);

    var response = http.SendRequestAsync(options).GetAwaiter().GetResult();
    Log($"Status: {response.StatusCode}");
}
```

### Multipart upload with mixed content

```csharp
[Workflow]
public void Execute()
{
    var parts = new List<FormDataPart>
    {
        new TextFormDataPart("Quarterly report", "title"),
        new FileFormDataPart(@"C:\\Temp\\report.pdf", "document"),
        new BinaryFormDataPart(new byte[] { 1, 2, 3, 4 }, "signature", "application/octet-stream")
    };

    var response = http.PostMultipartAsync("https://api.example.com/upload", parts)
        .GetAwaiter()
        .GetResult();

    Log($"Upload status: {response.StatusCode}");
}
```

### Download and save response as file

```csharp
[Workflow]
public void Execute()
{
    var response = http.DownloadFileAsync(
            "https://example.com/files/data.csv",
            @"C:\\Temp\\Downloads",
            "data.csv")
        .GetAwaiter()
        .GetResult();

    Log($"Download status: {response.StatusCode}");
}
```

### SOAP call using `SoapRequestOptions`

```csharp
[Workflow]
public void Execute()
{
    var options = new SoapRequestOptions
    {
        EndPoint = "https://www.example.com/service?wsdl",
        ContractName = "OrderService",
        Method = "GetOrder",
        Parameters = new Dictionary<string, object>
        {
            ["orderId"] = 42
        }
    };

    var response = soap.CallAsync(options).GetAwaiter().GetResult();
    Log($"SOAP status: {response.StatusCode}");
}
```

### SOAP with Basic authentication

```csharp
[Workflow]
public void Execute()
{
    var response = soap.CallAsync(new SoapRequestOptions
    {
        EndPoint = "https://secure.example.com/user-service?wsdl",
        ContractName = "UserManagementService",
        Method = "GetUserProfile",
        Parameters = new Dictionary<string, object> { { "userId", "user123" } },
        Username = "serviceaccount",
        SecurePassword = GetSecurePassword()
    }).GetAwaiter().GetResult();

    if (response.IsSuccessStatusCode())
    {
        var profileXml = System.Xml.Linq.XDocument.Parse(response.TextContent);
        Log(profileXml.ToString());
    }
}
```

### SOAP with Windows credentials

```csharp
[Workflow]
public void Execute()
{
    var response = soap.CallAsync(new SoapRequestOptions
    {
        EndPoint = "https://crm.company.local/soap?wsdl",
        ContractName = "CRMService",
        Method = "FetchCustomer",
        Parameters = new Dictionary<string, object> { { "customerId", "CUST-001" } },
        UseWindowsCredentials = true
    }).GetAwaiter().GetResult();

    Log($"SOAP status: {response.GetStatusCodeNumber()}");
}
```

### SOAP response parsing with XML namespaces

```csharp
[Workflow]
public void Execute()
{
    var response = soap.CallAsync(new SoapRequestOptions
    {
        EndPoint = "https://api.example.com/weather-soap?wsdl",
        ContractName = "WeatherService",
        Method = "GetWeather",
        Parameters = new Dictionary<string, object> { { "city", "New York" }, { "unit", "Celsius" } }
    }).GetAwaiter().GetResult();

    if (response.IsSuccessStatusCode())
    {
        var doc = System.Xml.Linq.XDocument.Parse(response.TextContent);
        var ns = System.Xml.Linq.XNamespace.Get("http://api.example.com/weather");
        var temperature = doc.Descendants(ns + "Temperature").FirstOrDefault()?.Value;
        Log($"Temperature: {temperature}");
    }
}
```

### SOAP error handling — detecting HTTP errors and SOAP Faults

```csharp
[Workflow]
public void Execute()
{
    var response = soap.CallAsync(new SoapRequestOptions
    {
        EndPoint = "https://api.example.com/validation?wsdl",
        ContractName = "ValidationService",
        Method = "ValidateData",
        Parameters = new Dictionary<string, object> { { "data", "input" } },
        ContinueOnError = true
    }).GetAwaiter().GetResult();

    if (response.IsSuccessStatusCode())
    {
        var doc = System.Xml.Linq.XDocument.Parse(response.TextContent);

        // SOAP Fault can be embedded inside an HTTP 200 response.
        var fault = doc.Descendants("Fault").FirstOrDefault();
        if (fault != null)
        {
            var code = fault.Element("faultcode")?.Value;
            var message = fault.Element("faultstring")?.Value;
            Log($"SOAP Fault [{code}]: {message}");
        }
        else
        {
            var result = doc.Descendants("Result").FirstOrDefault()?.Value;
            Log($"Result: {result}");
        }
    }
    else if (response.IsClientError())
    {
        Log($"Client error {response.GetStatusCodeNumber()}: check endpoint/credentials.");
    }
    else if (response.IsServerError())
    {
        // HTTP 5xx — server-side transport fault (not a SOAP Fault).
        Log($"Server error {response.GetStatusCodeNumber()}: {response.TextContent}");
    }
}
```

### Import cURL and execute as HTTP request

```csharp
[Workflow]
public void Execute()
{
    var rawCurl = "curl https://api.example.com/items -H \"Authorization: Bearer token\" -H \"Accept: application/json\"";

    var importResult = curl.Import(rawCurl, new CurlImportOptions
    {
        InferJsonForTextPayload = true,
        MapFileBodyToStream = true,
        StripAuthorizationHeaderOnAuthMapping = true
    });

    if (importResult.Options == null)
    {
        Log("cURL import failed. Review warnings for details.");
        return;
    }

    var response = http.SendRequestAsync(importResult.Options).GetAwaiter().GetResult();
    Log($"Imported request status: {response.StatusCode}");
}
```

### Deserialize HTTP JSON response to a typed model

```csharp
[Workflow]
public void Execute()
{
    var response = http.GetAsync("https://api.example.com/orders/42").GetAwaiter().GetResult();

    // Deserialize JSON using Newtonsoft.Json in coded workflows.
    var order = Newtonsoft.Json.JsonConvert.DeserializeObject<OrderModel>(response.TextContent);
    Log($"Order id: {order?.Id}");
}

private sealed class OrderModel
{
    public int Id { get; set; }
}
```

### Deserialize JSON array response for iteration

```csharp
[Workflow]
public void Execute()
{
    var response = http.GetAsync("https://api.example.com/orders").GetAwaiter().GetResult();

    var items = Newtonsoft.Json.Linq.JArray.Parse(response.TextContent);
    foreach (var item in items)
    {
        Log($"Item: {item["id"]}");
    }
}
```

### Serialize object to JSON request body

```csharp
[Workflow]
public void Execute()
{
    var payload = new
    {
        name = "sample",
        count = 3
    };

    var json = Newtonsoft.Json.JsonConvert.SerializeObject(payload);
    var response = http.PostJsonAsync("https://api.example.com/items", json).GetAwaiter().GetResult();
    Log($"POST status: {response.StatusCode}");
}
```

### Parse XML and evaluate XPath in coded workflows

```csharp
[Workflow]
public void Execute()
{
    var xml = "<root><order id='42' status='ok'/></root>";
    var doc = System.Xml.Linq.XDocument.Parse(xml);

    var xpathResult = System.Xml.XPath.Extensions.XPathEvaluate(doc, "string(/root/order/@status)");
    Log($"XPath status: {xpathResult}");

    var firstElement = doc.Root?.Element("order");
    if (firstElement != null)
    {
        foreach (var attribute in firstElement.Attributes())
        {
            Log($"Attr: {attribute.Name}={attribute.Value}");
        }
    }

    foreach (var node in doc.Nodes())
    {
        Log($"Node type: {node.NodeType}");
    }
}
```
