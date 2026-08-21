# HTTP Request

`UiPath.Web.Activities.Http.NetHttpRequest`

Configures and sends an HTTP request with customizable options for headers, authentication, cookies, retries, SSL, and request body formats. Supports Basic, OAuth bearer token, Windows/negotiated, AWS SigV4, and Integration Service **connector** authentication. Includes flexible retry mechanisms and graceful handling of errors, with optional continuation on failure.

> This activity has extensive runtime logic. For full understanding of defaults, side-effects, retry mechanics, and edge cases, read the [Observable Behavior](#nethttprequest--observable-behavior) section at the bottom of this document.

**Package:** `UiPath.WebAPI.Activities`
**Category:** Web
**Platform:** Cross-platform

> **XAML references.** This activity's class is `UiPath.Web.Activities.Http.NetHttpRequest`. Its assembly **and** namespace root are `UiPath.Web.Activities` (the `Web.Activities` form, without "API"). The `UiPath.WebAPI.Activities` package name belongs only in `project.json` — never in `assembly=`/`clr-namespace:`. In XAML, declare:
> ```xml
> xmlns:uwah="clr-namespace:UiPath.Web.Activities.Http;assembly=UiPath.Web.Activities"
> ```
> and reference the activity as `<uwah:NetHttpRequest .../>`. See [overview.md](../overview.md#identity--references-read-this-first) for the full prefix table.

## When to use

Use for HTTP calls that require retries, authentication, file downloads, or rich response inspection. For calls against an Integration Service connection, use `Connector` authentication so the base URL, auth headers, and API-key query parameters are injected automatically from the connector.

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `RequestUrl` | Request URL | InArgument | `string` | Yes* | | The URL to send the HTTP request to. *When `AuthenticationType = Connector`, this acts as the **operation path** appended to the connector base URL and is optional (see [URL Handling](#url-handling)). |
| `Method` | Request method | Property | `HttpMethod` | No | `GET` | | The HTTP method to use. |
| `RequestBodyType` | Request body type | Property | `HttpRequestBodyType` | No | `None` | | The type of request body to send. |

### Authentication (conditional)

Properties in this group appear based on the value of `AuthenticationType`.

| Name | Display Name | Kind | Type | Visible When | Default | Description |
|------|-------------|------|------|------------|---------|-------------|
| `AuthenticationType` | Authentication | Property | `AuthenticationType` | Always | `None` | The authentication method to use. |
| `BasicAuthUsername` | Username | InArgument | `string` | `AuthenticationType = BasicUsernamePassword` | | The username for basic authentication. |
| `BasicAuthPassword` | Password | InArgument | `string` | `AuthenticationType = BasicUsernamePassword` AND not using secure password | | The password for basic authentication. |
| `BasicAuthSecurePassword` | Secure password | InArgument | `SecureString` | `AuthenticationType = BasicUsernamePassword` AND using secure password | | The password for basic authentication, stored as a secure string. |
| `OAuthToken` | Bearer token | InArgument | `string` | `AuthenticationType = OAuthToken` | | The OAuth2 bearer token. |
| `AwsAccessKeyId` | AWS access key ID | InArgument | `string` | `AuthenticationType = AwsSigV4` | | The AWS access key ID for SigV4 signing. |
| `AwsSecretAccessKey` | AWS secret access key | InArgument | `string` | `AuthenticationType = AwsSigV4` AND not using secure secret | | The AWS secret access key for SigV4 signing, stored as a plain string. Must be kept secure. |
| `AwsSecretAccessKeySecureString` | AWS secret access key (secure) | InArgument | `SecureString` | `AuthenticationType = AwsSigV4` AND using secure secret | | The AWS secret access key for SigV4 signing, stored as a secure string. This is the default mode; use the property's context menu to switch between the plain-string and secure-string fields. |
| `AwsRegion` | AWS region | InArgument | `string` | `AuthenticationType = AwsSigV4` | | The AWS region (e.g., us-east-1, eu-west-1) for SigV4 signing. |
| `AwsService` | AWS service name | InArgument | `string` | `AuthenticationType = AwsSigV4` | | The AWS service name (e.g., s3, dynamodb, lambda) for SigV4 signing. |
| `ConnectionId` | Connection | InArgument | `string` | `AuthenticationType = Connector` | | The Integration Service connection to authenticate with. The connector's base URL, auth headers, and query parameters are resolved from this connection at runtime. |
| `ConnectorKey` | Connector | InArgument | `string` | `AuthenticationType = Connector` | | The key of the selected connector. Used only to retrieve connector metadata when the activity is deserialized; it is not used in request logic. |
| `UseOsNegotiatedAuthCredentials` | Use operating system credentials | InArgument | `bool` | `AuthenticationType = NegotiatedAuthentication` | `True` | Whether to use operating system credentials for negotiated authentication. |
| `CustomNegotiatedAuthCredentials` | Custom credentials | InArgument | `NetworkCredential` | `AuthenticationType = NegotiatedAuthentication` AND not using OS credentials | | Custom network credentials for negotiated authentication. |

### Request Body (conditional)

Properties in this group appear based on the value of `RequestBodyType`.

| Name | Display Name | Kind | Type | Visible When | Default | Description |
|------|-------------|------|------|------------|---------|-------------|
| `TextPayload` | JSON payload | InArgument | `string` | `RequestBodyType = Text` | | The text or JSON body content. |
| `TextPayloadContentType` | Text content type | InArgument | `string` | `RequestBodyType = Text` | `"application/json"` | The content type header for text payloads. |
| `TextPayloadEncoding` | Text encoding | InArgument | `string` | `RequestBodyType = Text` | `"UTF-8"` | The encoding for text payloads. |
| `BinaryPayload` | Binary payload | InArgument | `byte[]` | `RequestBodyType = Binary` | | The binary content to send. |
| `FilePath` | Local file | InArgument | `string` | `RequestBodyType = Stream` AND using local file | | Path to a local file to stream as the request body. |
| `PathResource` | Resource file | InArgument | `IResource` | `RequestBodyType = Stream` AND not using local file | | Resource file to stream as the request body. |
| `FormData` | Url-encoded form data | InArgument | `Dictionary<string, string>` | `RequestBodyType = FormUrlEncoded` | | Form URL-encoded key-value data. |
| `FormDataParts` | Form data parts | InArgument | `IEnumerable<FormDataPart>` | `RequestBodyType = MultipartFormData` | | Multipart form data parts. |
| `LocalFiles` | Local files | InArgument | `IEnumerable<string>` | `RequestBodyType = MultipartFormData` | | Local file paths for multipart upload. |
| `ResourceFiles` | Resource files | InArgument | `IEnumerable<IResource>` | `RequestBodyType = MultipartFormData` | | Resource files for multipart upload. |

> **`FormDataPart` types — read if you hit `BC30002: type FormDataPart is not defined`.** `FormDataParts` holds items of `FormDataPart` and its subtypes `TextFormDataPart`, `FileFormDataPart`, and `BinaryFormDataPart`, all in `UiPath.Web.Activities.Http.Models` (assembly `UiPath.Web.Activities`) — **not** the activity's own namespace. In coded workflows add `using UiPath.Web.Activities.Http.Models;`; in XAML use the `uwahm:` prefix (see [overview.md](../overview.md#model--result-types-variable-types-multipart-parts)).

### Retry Policy (conditional)

Properties in this group appear based on the value of `RetryPolicyType`.

| Name | Display Name | Kind | Type | Visible When | Default | Description |
|------|-------------|------|------|------------|---------|-------------|
| `RetryPolicyType` | Retry policy type | Property | `RetryPolicyType` | Always | `Basic` | The retry strategy to use. |
| `RetryCount` | Retry count | InArgument | `int` | `RetryPolicyType = Basic` or `ExponentialBackoff` | `3` | Number of retry attempts. |
| `InitialDelay` | Initial delay | InArgument | `int` | `RetryPolicyType = Basic` or `ExponentialBackoff` | `500` | Initial delay in milliseconds before the first retry. |
| `PreferRetryAfterValue` | Use Retry-After header | InArgument | `bool` | `RetryPolicyType = Basic` or `ExponentialBackoff` | `True` | Whether to respect the server's Retry-After header value. |
| `MaxRetryAfterDelay` | Delay limit | InArgument | `int` | `RetryPolicyType = Basic` or `ExponentialBackoff` | `30000` | Maximum delay in milliseconds when using the Retry-After header. |
| `RetryStatusCodes` | Retry status codes | InArgument | `IEnumerable<HttpStatusCode>` | `RetryPolicyType = Basic` or `ExponentialBackoff` | | HTTP status codes that should trigger a retry. |
| `Multiplier` | Multiplier | InArgument | `double` | `RetryPolicyType = ExponentialBackoff` | `2` | Exponential backoff multiplier applied to the delay between retries. |
| `UseJitter` | Use jitter | InArgument | `bool` | `RetryPolicyType = ExponentialBackoff` | `True` | Whether to add randomization to the delay between retries. |

### Request Options

| Name | Display Name | Kind | Type | Default | Placeholder | Description |
|------|-------------|------|------|---------|-------------|-------------|
| `FollowRedirects` | Follow redirects | InArgument | `bool` | `True` | | Whether to automatically follow HTTP redirects. |
| `MaxRedirects` | Max redirects | InArgument | `int` | `3` | | Maximum number of redirects to follow. Only visible when `FollowRedirects` is `True`. |
| `TimeoutInMiliseconds` | Request timeout | InArgument | `int?` | `10000` | | Request timeout in milliseconds. |
| `Headers` | Headers | InArgument | `Dictionary<string, string>` | | Click to open | Custom HTTP headers to include in the request. |
| `Parameters` | Parameters | InArgument | `Dictionary<string, string>` | | Click to open | URL query parameters to append to the request URL. |
| `Cookies` | Additional cookies | InArgument | `Dictionary<string, string>` | | | Extra cookies to send with the request. |

### Client Options

| Name | Display Name | Kind | Type | Default | Description |
|------|-------------|------|------|---------|-------------|
| `DisableSslVerification` | Disable SSL verification | InArgument | `bool` | `False` | Whether to skip SSL certificate validation. |
| `TlsProtocol` | TLS protocol | InArgument | `SupportedTlsProtocols` | `Automatic` | The TLS protocol version to use. |
| `EnableCookies` | Enable cookies | InArgument | `bool` | `True` | Whether to enable cookie handling. |
| `ClientCertPath` | Client certificate | InArgument | `string` | | Path to a client certificate file. |
| `ClientCertPassword` | Client certificate password | InArgument | `string` | | Plain-string password for the client certificate (available via menu action). |
| `ClientCertSecurePassword` | Client certificate secure password | InArgument | `SecureString` | | Secure password for the client certificate. |
| `ProxySetting` | Proxy settings | Property | `ProxySettingType` | `None` | Proxy usage configuration. |
| `ProxyConfiguration` | Proxy configuration | InArgument | `WebProxyConfiguration` | | Custom proxy configuration. Only visible when `ProxySetting = Custom`. |

### Response Options

| Name | Display Name | Kind | Type | Default | Placeholder | Description |
|------|-------------|------|------|---------|-------------|-------------|
| `SaveResponseAsFile` | Always save response as file | InArgument | `bool` | `False` | | Whether to save the response body to a file. |
| `OutputFileTargetFolder` | Output file target folder | InArgument | `string` | | Current project folder | Target folder path for the saved response file. |
| `OutputFileName` | Output file name | InArgument | `string` | | Content-Disposition file name | Custom filename for the saved response file. |
| `FileOverwrite` | If the file already exists | Property | `FileOverwriteOption` | `AutoRename` | | Behavior when the output file already exists. |
| `SaveRawRequestResponse` | Enable debugging info | InArgument | `bool` | `False` | | Whether to save raw request and response data for debugging. Credential-bearing headers and URL query parameters are redacted in the output (see [Debug Output](#debug-output)). |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Result` | Result | OutArgument | `HttpResponseSummary` | The full HTTP response summary. |

**`HttpResponseSummary` properties:**

| Property | Type | Description |
|----------|------|-------------|
| `StatusCode` | `HttpStatusCode` | The HTTP status code of the response. |
| `TextContent` | `string` | The response body as text. |
| `BinaryContent` | `byte[]` | The response body as a byte array. |
| `File` | `ILocalResource` | The downloaded file resource, if the response was saved to a file. |
| `Headers` | `IEnumerable<KeyValuePair<string, string>>` | The response headers. |
| `ContentHeaders` | `IEnumerable<KeyValuePair<string, string>>` | Content-specific response headers. |
| `RawRequestDebuggingInfo` | `string` | Raw request debug information, available when `SaveRawRequestResponse` is enabled. Sensitive values (auth headers, cookies, API keys, presigned-URL query parameters) are redacted — see [Debug Output](#debug-output). |

> **Type location — read if you hit "unknown type `HttpResponseSummary`".** `HttpResponseSummary` is **not** in the same namespace as this activity. It lives in `UiPath.Web.Activities.Http.Models`, assembly `UiPath.Web.Activities`. In XAML, a variable of this type needs `xmlns:uwahm="clr-namespace:UiPath.Web.Activities.Http.Models;assembly=UiPath.Web.Activities"` and is referenced as `x:TypeArguments="uwahm:HttpResponseSummary"`. In coded workflows, add `using UiPath.Web.Activities.Http.Models;`. The same namespace holds the activity's enums and the `FormDataPart` types (see [Request Body](#request-body-conditional)).

### Common

| Name | Display Name | Kind | Type | Default | Description |
|------|-------------|------|------|---------|-------------|
| `ContinueOnError` | Continue on error | InArgument | `bool` | `True` | Whether to continue workflow execution when an HTTP error occurs. |

## Valid Configurations

The activity uses conditional property groups where certain properties only appear based on the value of a controlling property.

### Request Body modes (`RequestBodyType`)

- **None** -- No request body is sent.
- **Text** -- Shows `TextPayload`, `TextPayloadContentType`, and `TextPayloadEncoding`.
- **FormUrlEncoded** -- Shows `FormData` for URL-encoded key-value pairs.
- **MultipartFormData** -- Shows `FormDataParts`, `LocalFiles`, and `ResourceFiles` for multipart uploads.
- **Binary** -- Shows `BinaryPayload` for raw binary content.
- **Stream** -- Shows either `FilePath` (local file) or `PathResource` (resource file) to stream.

### Authentication modes (`AuthenticationType`)

- **None** -- No authentication is applied.
- **BasicUsernamePassword** -- Shows `BasicAuthUsername` and either `BasicAuthPassword` or `BasicAuthSecurePassword`.
- **Client certificate password mode** -- For certificate auth, the password can be entered as either `ClientCertPassword` or `ClientCertSecurePassword` (menu toggle in the designer).
- **OAuthToken** -- Shows `OAuthToken` for a bearer token.
- **NegotiatedAuthentication** -- Shows `UseOsNegotiatedAuthCredentials` and optionally `CustomNegotiatedAuthCredentials`.
- **AwsSigV4** -- Shows `AwsAccessKeyId`, `AwsSecretAccessKey`, `AwsRegion`, and `AwsService` for AWS Signature Version 4 signing.
- **Connector** -- Shows `ConnectionId` (and stores `ConnectorKey`). The base URL, auth headers, and query parameters come from the selected Integration Service connection; `RequestUrl` becomes the operation path.

### Retry Policy modes (`RetryPolicyType`)

- **None** -- No retries are performed.
- **Basic** -- Shows `RetryCount`, `InitialDelay`, `PreferRetryAfterValue`, `MaxRetryAfterDelay`, and `RetryStatusCodes`.
- **ExponentialBackoff** -- Shows the same properties as Basic plus `Multiplier` and `UseJitter`.

### Proxy modes (`ProxySetting`)

- **None** -- No proxy is used.
- **SystemDefault** -- Uses the system default proxy.
- **Custom** -- Shows `ProxyConfiguration` for a custom proxy setup.

### Redirect handling

- When `FollowRedirects` is `True`, the `MaxRedirects` property becomes visible.

## Enum Reference

| Enum | Values |
|------|--------|
| `HttpMethod` | `GET`, `POST`, `PUT`, `DELETE`, `HEAD`, `OPTIONS`, `PATCH`, `TRACE` |
| `HttpRequestBodyType` | `None`, `Text`, `FormUrlEncoded`, `MultipartFormData`, `Binary`, `Stream` |
| `AuthenticationType` | `None`, `BasicUsernamePassword`, `OAuthToken`, `NegotiatedAuthentication`, `Connector`, `AwsSigV4` |
| `RetryPolicyType` | `None`, `Basic`, `ExponentialBackoff` |
| `FileOverwriteOption` | `AutoRename`, `Replace`, `Discard` |
| `ProxySettingType` | `None`, `SystemDefault`, `Custom` |
| `SupportedTlsProtocols` | `Automatic`, `Tls12`, `Tls13` |

## XAML Examples

> The snippets below use the prefix `uwah:` for `clr-namespace:UiPath.Web.Activities.Http;assembly=UiPath.Web.Activities`. The first example shows the full `<Activity>` wrapper with every `xmlns` it needs; later snippets show only the activity element.
>
> **These examples use VB-expression syntax** (the `[ … ]` bracket shorthand). In a **C# expression project** (root has `ExpressionActivityEditor="C#"`) the bracket form fails validation — bind values with `CSharpValue`/`CSharpReference` child elements instead. See [Expression language: VB vs C#](../overview.md#expression-language-xaml-vb-vs-c) for both forms; a C# version of the example below follows it.
>
> **Escape `&` as `&amp;` inside attribute values.** A literal `&` in a `RequestUrl`, header, or expression (e.g. a URL with multiple query parameters `a=1&b=2`) makes the XAML parser fail with `An error occurred while parsing EntityName`. Write the URL as `…?a=1&amp;b=2`.

### Complete workflow — GET then Deserialize JSON (VB expression)

A full, loadable `Main.xaml` that calls an API and parses the response. Note the `uwah:` (NetHttpRequest), `web:` (Deserialize JSON), and `jn:` (`JObject` type argument) namespaces. This is the **VB-expression** form (bracket shorthand).

```xml
<Activity mc:Ignorable="sap sap2010" x:Class="Main"
    xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities"
    xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"
    xmlns:sap2010="http://schemas.microsoft.com/netfx/2010/xaml/activities/presentation"
    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
    xmlns:uwah="clr-namespace:UiPath.Web.Activities.Http;assembly=UiPath.Web.Activities"
    xmlns:uwahm="clr-namespace:UiPath.Web.Activities.Http.Models;assembly=UiPath.Web.Activities"
    xmlns:web="clr-namespace:UiPath.Web.Activities;assembly=UiPath.Web.Activities"
    xmlns:jn="clr-namespace:Newtonsoft.Json.Linq;assembly=Newtonsoft.Json">
  <Sequence DisplayName="Main">
    <Sequence.Variables>
      <Variable x:TypeArguments="uwahm:HttpResponseSummary" Name="httpResponse" />
      <Variable x:TypeArguments="jn:JObject" Name="jsonResult" />
    </Sequence.Variables>
    <uwah:NetHttpRequest DisplayName="GET API Data"
      RequestUrl="[&quot;https://jsonplaceholder.typicode.com/todos/1&quot;]"
      Method="GET"
      Result="[httpResponse]" />
    <web:DeserializeJson x:TypeArguments="jn:JObject"
      DisplayName="Deserialize JSON"
      JsonString="[httpResponse.TextContent]"
      JsonObject="[jsonResult]" />
  </Sequence>
</Activity>
```

### Same workflow — C# expression project

In a C# project, set `ExpressionActivityEditor="C#"` on the root and bind non-literal values with `CSharpValue` (in-arguments) and `CSharpReference` (out-arguments) child elements. The `xmlns` declarations are identical; literal scalars like `Method` stay plain attributes.

```xml
<Activity mc:Ignorable="sap sap2010" x:Class="Main"
    sap2010:ExpressionActivityEditor.ExpressionActivityEditor="C#"
    xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities"
    xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"
    xmlns:sap2010="http://schemas.microsoft.com/netfx/2010/xaml/activities/presentation"
    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
    xmlns:uwah="clr-namespace:UiPath.Web.Activities.Http;assembly=UiPath.Web.Activities"
    xmlns:uwahm="clr-namespace:UiPath.Web.Activities.Http.Models;assembly=UiPath.Web.Activities"
    xmlns:web="clr-namespace:UiPath.Web.Activities;assembly=UiPath.Web.Activities"
    xmlns:jn="clr-namespace:Newtonsoft.Json.Linq;assembly=Newtonsoft.Json">
  <Sequence DisplayName="Main">
    <Sequence.Variables>
      <Variable x:TypeArguments="uwahm:HttpResponseSummary" Name="httpResponse" />
      <Variable x:TypeArguments="jn:JObject" Name="jsonResult" />
    </Sequence.Variables>
    <uwah:NetHttpRequest DisplayName="GET API Data" Method="GET">
      <uwah:NetHttpRequest.RequestUrl>
        <InArgument x:TypeArguments="x:String">
          <CSharpValue x:TypeArguments="x:String">"https://jsonplaceholder.typicode.com/todos/1"</CSharpValue>
        </InArgument>
      </uwah:NetHttpRequest.RequestUrl>
      <uwah:NetHttpRequest.Result>
        <OutArgument x:TypeArguments="uwahm:HttpResponseSummary">
          <CSharpReference x:TypeArguments="uwahm:HttpResponseSummary">httpResponse</CSharpReference>
        </OutArgument>
      </uwah:NetHttpRequest.Result>
    </uwah:NetHttpRequest>
    <web:DeserializeJson x:TypeArguments="jn:JObject" DisplayName="Deserialize JSON">
      <web:DeserializeJson.JsonString>
        <InArgument x:TypeArguments="x:String">
          <CSharpValue x:TypeArguments="x:String">httpResponse.TextContent</CSharpValue>
        </InArgument>
      </web:DeserializeJson.JsonString>
      <web:DeserializeJson.JsonObject>
        <OutArgument x:TypeArguments="jn:JObject">
          <CSharpReference x:TypeArguments="jn:JObject">jsonResult</CSharpReference>
        </OutArgument>
      </web:DeserializeJson.JsonObject>
    </web:DeserializeJson>
  </Sequence>
</Activity>
```

> `CSharpValue` and `CSharpReference` resolve through the default activities namespace, so no extra `xmlns` is required — the sample above is the form Studio emits for C# projects and loads as-is (verified against validated C#-expression workflows). A fully-qualified `mca:CSharpValue` (where `mca` is `clr-namespace:Microsoft.CSharp.Activities;assembly=System.Activities`) is equivalent; the `assembly=` token is `System.Activities`, not the `UiPath.Workflow` DLL name.

### GET request with basic authentication and retry

```xml
<uwah:NetHttpRequest
  DisplayName="GET API Data"
  RequestUrl="[&quot;https://api.example.com/data&quot;]"
  Method="GET"
  RequestBodyType="None"
  AuthenticationType="BasicUsernamePassword"
  BasicAuthUsername="[apiUser]"
  BasicAuthPassword="[apiPassword]"
  RetryPolicyType="Basic"
  RetryCount="[3]"
  TimeoutInMiliseconds="[10000]"
  Result="[httpResponse]" />
```

### POST request with JSON body and OAuth token

When sending a JSON body, set `RequestBodyType="Text"` **and** `TextPayloadContentType="application/json"` explicitly. Although `application/json` is the default, setting it makes the request self-documenting and guarantees the correct `Content-Type` header.

```xml
<uwah:NetHttpRequest
  DisplayName="POST JSON Data"
  RequestUrl="[&quot;https://api.example.com/items&quot;]"
  Method="POST"
  RequestBodyType="Text"
  TextPayload="[jsonPayload]"
  TextPayloadContentType="[&quot;application/json&quot;]"
  AuthenticationType="OAuthToken"
  OAuthToken="[bearerToken]"
  Result="[httpResponse]" />
```

### GET request using an Integration Service connector

With connector authentication, `RequestUrl` is the operation path appended to the connector base URL; auth headers and query parameters come from the connection.

```xml
<uwah:NetHttpRequest
  DisplayName="GET via Connector"
  RequestUrl="[&quot;/customers&quot;]"
  Method="GET"
  RequestBodyType="None"
  AuthenticationType="Connector"
  ConnectionId="[connectionId]"
  ConnectorKey="[&quot;uipath-myconnector&quot;]"
  Result="[httpResponse]" />
```

### POST request signed with AWS SigV4

```xml
<uwah:NetHttpRequest
  DisplayName="POST to S3"
  RequestUrl="[&quot;https://s3.eu-west-1.amazonaws.com/my-bucket/key&quot;]"
  Method="PUT"
  RequestBodyType="Binary"
  BinaryPayload="[payloadBytes]"
  AuthenticationType="AwsSigV4"
  AwsAccessKeyId="[awsAccessKeyId]"
  AwsSecretAccessKey="[awsSecretAccessKey]"
  AwsRegion="[&quot;eu-west-1&quot;]"
  AwsService="[&quot;s3&quot;]"
  Result="[httpResponse]" />
```

## Notes

- Cookies can persist across activity calls within the same workflow execution.
- Only one of `TextContent`, `BinaryContent`, or `File` is meaningfully populated per response.
- With `Connector` authentication, `RequestUrl` is the operation path relative to the connector base URL; leave it empty to call the base URL itself.

## Use with other activities

### Preparing inputs

- Use **Serialize JSON** to convert a .NET object to a JSON string before assigning it to `TextPayload` (when `RequestBodyType = Text`).
- Use **Serialize JSON** with custom `JsonSerializationSettings` for non-default serialization (date format, null handling, etc.) before sending.

### Processing outputs

- Use `StatusCode` to guard downstream parsing (for example, only deserialize on success codes you expect).
- When `TextContent` contains JSON, use **Deserialize JSON** or **Deserialize JSON Array** to parse it before further processing.
- When `TextContent` contains XML, use **Deserialize XML** followed by **Execute XPath**, **Get XML Nodes**, or **Get XML Node Attributes**.
- When `File` is populated, treat it as the response payload for downstream file-based activities instead of using `TextContent` or `BinaryContent`.
- Use `Headers` and `ContentHeaders` to capture server metadata needed for follow-up requests.

---

# NetHttpRequest — Observable Behavior

This section describes **what it does**. Focus: side-effects, shared state, defaults, edge cases, and the output contract.

## Runtime execution flow (high level)

At runtime, request processing follows this sequence:

1. Validate input values (including endpoint constraints).
2. Preprocess connector input (only when `AuthenticationType = Connector`): resolve the connection, prepend the connector base URL to the operation path, and merge connector headers and query parameters.
3. Normalize URL (adds `http://` when scheme is missing).
4. Append query parameters to the URL.
5. Create `HttpClient` using transport config, late-bound config, and timeout.
6. Create `HttpRequestMessage` with method + final URL.
7. Apply activity metadata.
8. Apply cookies through the shared cookie manager.
9. Resolve text encoding.
10. Build request body from the selected body type.
11. Add request headers (applied after body build, so explicit headers can override defaults such as `Content-Type`).
12. Send request with `ResponseHeadersRead` and cancellation token.
13. Build `HttpResponseSummary` using response options.

Important implications:
- Connector preprocessing runs before URL normalization, so the resolved absolute URL is what gets validated and sent.
- URL normalization and parameter appending happen before length validation and send.
- Header application happens after body construction.
- Cancellation token is propagated through body preparation, send, and response processing.

## Defaults

See [Parameter Configuration Guide](#parameter-configuration-guide) for full details on how each property interacts with others and when to set it.

| Property | Default | Notes |
| --- | --- | --- |
| Method | `GET` | |
| EnableCookies | `true` | Cookies persist across calls (see below) |
| TimeoutInMiliseconds | 10 000 ms | |
| ContinueOnError | `true` | Network errors become 503 responses |
| FollowRedirects | `true` | |
| MaxRedirects | 3 | Only used when `FollowRedirects = true` |
| RetryPolicyType | `Basic` | Constant-delay retries enabled by default |
| RetryCount | 3 | Total attempts, not additional retries |
| InitialDelay | 500 ms | |
| Multiplier | 2.0 | Only used with `ExponentialBackoff` policy |
| UseJitter | `true` | Adds 0–99 ms random noise per retry |
| PreferRetryAfterValue | `true` | Honors server `Retry-After` header |
| MaxRetryAfterDelay | 30 000 ms | Cap on server-suggested delay |
| TextPayloadEncoding | UTF-8 | |
| TextPayloadContentType | application/json | |
| FileOverwrite | AutoRename | |
| SaveResponseAsFile | `false` | |
| SaveRawRequestResponse | `false` | |
| URL scheme when omitted | `http://` | **Not** https |

## Side-Effects and Shared State

### Cookie Persistence (Workflow-Scoped)

A **single cookie jar** is shared across every NetHttpRequest call in the same workflow execution.

Observable effects:
- Server-set cookies (`Set-Cookie` headers) from one call are automatically sent on subsequent calls to the same domain.
- User-supplied cookies (`Cookies` property) are added to the same jar and accumulate — they are **never cleared**.
- Even if a later call sets `EnableCookies = false`, the jar still holds cookies from earlier calls. The `false` flag only prevents the jar from being *read* for that specific request.

When this matters:
- Login flows: a first call authenticates, subsequent calls automatically carry the session cookie.
- Browser-like cookie reuse: cookies set for `api.example.com` are sent on future calls to the same host, even from different parts of the workflow.

### Connection Pooling (Automatic, Transparent)

Requests with **identical transport settings** (SSL config, proxy, cookies, redirects, client cert, negotiated auth) share the same connection pool.

Observable effects:
- Subsequent requests to the same host reuse TCP connections (faster).
- Idle connections close after ~30 seconds.
- Connections recycle after ~5 minutes (picks up DNS changes).
- Max 100 concurrent connections per server.

When this matters:
- High-throughput loops benefit automatically — no configuration needed.
- Changing any transport setting (e.g., toggling `DisableSslVerification`) creates a separate pool; connections are not shared across pools.

### File System Writes

When a response is saved to disk (either `SaveResponseAsFile = true` or the response is detected as a file-type like image/pdf/etc.):

- Files are written atomically: content streams to a temp file first, then moved to the final path. No partial files on failure.
- `FileOverwrite` modes:
  - **AutoRename** — appends ` 1`, ` 2`, etc. if the file already exists.
  - **Replace** — deletes existing file, then writes.
  - **Discard** — throws `IOException` immediately if file exists (before downloading the body).
- Default target folder: `Environment.CurrentDirectory` if none specified.
- Filename resolution order: user-supplied `OutputFileName` → server `Content-Disposition` header → auto-generated `downloaded_file_<GUID>`.

### Automatic Decompression

gzip, deflate, and brotli responses are **always** transparently decompressed. `TextContent` and `BinaryContent` contain the decompressed data. The `Content-Length` header in `ContentHeaders` may still reflect the compressed size.

## Retry Behavior

Retries are **enabled by default** (`Basic` policy, 3 attempts, 500 ms delay).

### What triggers a retry

- **Network failure** (`HttpRequestException`) — connection refused, DNS failure, etc.
- **Retryable status code** — by default: `408`, `429`, `500`, `502`, `503`, `504`. Customizable via `RetryStatusCodes`.
- Any other status code (e.g., `400`, `401`, `404`) does **not** trigger a retry — the response is returned immediately.

### Retry policies

| Policy | Delay pattern |
| --- | --- |
| `None` | No retries |
| `Basic` | Same delay every time (`InitialDelay`) |
| `ExponentialBackoff` | `delay = delay × Multiplier` each attempt, plus optional jitter (0–99 ms) |

### Retry-After header

When `PreferRetryAfterValue = true` (default) and the server sends a `Retry-After` header:
- The server's suggested delay is used instead of the policy delay.
- It is capped at `MaxRetryAfterDelay` (default 30 s).
- For `ExponentialBackoff`: the server delay replaces the *wait* but the internal multiplier still progresses — so the next fallback delay is still doubled from where it was, not reset.

### Exhausted retries

If all attempts fail:
- With `ContinueOnError = true` → a synthetic **503** response is returned.
- With `ContinueOnError = false` → the last `HttpRequestException` propagates.

## ContinueOnError Behavior

When `ContinueOnError = true` (the default):

| Error type | Caught? | Result |
| --- | --- | --- |
| Network failure (`HttpRequestException`) | Yes (on every attempt) | Each attempt is converted to a synthetic 503 response; the exception message is placed in `TextContent`. Retry handlers then decide whether to retry based on the 503 status code. |
| Timeout (`TaskCanceledException`) | **No** | Exception propagates to the caller |
| Validation error (null URL, etc.) | **No** | Exception propagates to the caller |
| Response body read failure | **No** | Exception propagates to the caller |

**Key gotcha:** Timeouts are **not** caught. A request that times out will throw even with `ContinueOnError = true`.

Interaction with retries:
- **With `ContinueOnError = true`**: `HttpRequestException` is caught by the `ContinueOnError` handler on **each** attempt and converted into a synthetic 503. The retry handlers see the 503 responses and retry based on status code (503 is retryable by default). After all retries are exhausted, the final 503 response is returned to the workflow.
- **With `ContinueOnError = false`**: `HttpRequestException` is not converted to 503. It flows directly into the retry handlers, which may retry based on the exception according to the retry policy. If all retries are exhausted, the last `HttpRequestException` is propagated to the workflow.

## Authentication

| `AuthenticationType` | What happens |
| --- | --- |
| `None` | No auth header set. |
| `BasicUsernamePassword` | `Authorization: Basic <base64(user:pass)>` added to every request. Use `BasicAuthUsername` with either `BasicAuthPassword` (string) or `BasicAuthSecurePassword` (secure string). Throws if username or password is empty. |
| `OAuthToken` | `Authorization: Bearer <token>` added. Throws if token is empty. |
| `NegotiatedAuthentication` | Windows/Kerberos negotiation at the connection level. Set `UseOsNegotiatedAuthCredentials = true` to use current Windows credentials. If `false`, provide `CustomNegotiatedAuthCredentials` (a `NetworkCredential` instance). |
| `AwsSigV4` | The request is signed with AWS Signature Version 4 just before it is sent. The handler adds `X-Amz-Date`, `X-Amz-Content-SHA256`, and an `Authorization: AWS4-HMAC-SHA256 ...` header (plus `X-Amz-Security-Token` when temporary credentials are used). Requires `AwsAccessKeyId`, `AwsSecretAccessKey`, `AwsRegion`, and `AwsService`. |
| `Connector` | Authentication is delegated to an Integration Service connection identified by `ConnectionId`. The connector's base URL, auth headers, and any API-key query parameters are resolved and injected at runtime. See [Connector Authentication](#connector-authentication) for the full behavior. |

Auth headers are set **per request** — they are not cached or shared.

## URL Handling

- If the URL has no scheme (`example.com/api`), `http://` is prepended — **not** `https://`.
- Query parameters from the `Parameters` dictionary are URI-escaped and appended.
- Existing query strings in the URL are preserved; parameters are appended with `&`.
- Final URL must be ≤ 2000 characters.

### Connector authentication URL composition

When `AuthenticationType = Connector`, `RequestUrl` is treated as the **operation path** appended to the connector's base URL rather than a standalone URL:

- Empty path -> the connector base URL is used as-is.
- Path starting with `/` or `?` -> concatenated directly to the base URL (no extra slash).
- Any other path -> joined to the base URL with a single `/`.
- A user-supplied **absolute** URL does **not** override the connector base URL; the base URL is always prepended. This is a deliberate fail-closed measure so connector-injected credentials (auth headers, API-key query parameters) cannot be sent to an arbitrary host.
- If the connector base URL cannot be resolved, or the composed URL is not a valid absolute `http`/`https` URL, the activity throws instead of sending the request.

## Connector Authentication

When `AuthenticationType = Connector`, the activity resolves an Integration Service connection (`ConnectionId`) and augments the request from the connector's configuration. The connector's authentication style is detected automatically and mapped to a request header or query parameter:

| Connector auth style | What is injected |
| --- | --- |
| Custom API key | The configured key/value pair, added either as a header or as a query parameter depending on the connector's "add to" setting (header is the default). |
| Personal access token | `Authorization: <prefix> <token>` (prefix defaults to `Bearer`). |
| OAuth 2.0 / OAuth / OAuth user token | `Authorization: <tokenType> <token>` (token type defaults to `Bearer`). |
| Basic | `Authorization: Basic <base64(user:pass)>`. |
| OAuth basic header | `Authorization: Basic <base64(apiKey:apiSecret)>` when the connector enables the basic-header option. |

Additional behaviors:

- **Header resolution from configuration** — connector configuration entries that name a header (e.g. `header.X-Custom`) are also merged into the request.
- **Access-token fallback** — for token-based connector auth where no `Authorization` header was produced directly, the activity requests an access token from Integration Service and applies it as `Authorization: <tokenType> <token>`.
- **Explicit override** — if the connector configuration carries an explicit `Authorization` / `AuthHeader` value, it takes precedence over the inferred header.
- **Precedence** — connector-supplied headers and query parameters **override** values already present on the request with the same key. User-supplied headers that the connector does not set are preserved.
- **401 refresh-and-retry** — if a connector-authenticated request returns `401 Unauthorized`, the activity asks Integration Service for a fresh token and replays the request **once** with the new `Authorization` header. If the refresh yields no token, throws, or the retry still returns `401`, the original `401` response is returned. The request is replayed as-is, so a forward-only `Stream` body replays empty on the second attempt (same limitation as the retry handlers).
- **Availability** — connector authentication requires the Integration Service access provider to be present in the runtime. When it is unavailable, the activity throws rather than sending an unauthenticated request.

## Request Body

| `RequestBodyType` | What's sent | Content-Type set to |
| --- | --- | --- |
| `None` | No body | — |
| `Text` | `StringContent` with the specified encoding | `TextPayloadContentType` (default `application/json`) |
| `FormUrlEncoded` | Key-value pairs from `FormData` dictionary | `application/x-www-form-urlencoded` |
| `MultipartFormData` | Files (`LocalFiles`, `ResourceFiles`) + fields (`FormData`, `FormDataParts`) | `multipart/form-data` (boundary auto-generated) |
| `Binary` | Raw bytes from `BinaryPayload` | `application/octet-stream` |
| `Stream` | File streamed from `FilePath` or `PathResource` | Auto-detected from file (see below) |

A user-supplied `Content-Type` header in `Headers` overrides the auto-generated one when a body is present.

### Which properties are used per body type

| `RequestBodyType` | Required properties | Ignored properties |
| --- | --- | --- |
| `Text` | `TextPayload`, `TextPayloadContentType`, `TextPayloadEncoding` | `FormData`, `BinaryPayload`, `LocalFiles`, `ResourceFiles`, `FilePath`, `PathResource`, `FormDataParts` |
| `FormUrlEncoded` | `FormData` | `TextPayload`, `BinaryPayload`, `LocalFiles`, `ResourceFiles`, `FilePath`, `PathResource`, `FormDataParts` |
| `MultipartFormData` | At least one of: `FormData`, `LocalFiles`, `ResourceFiles`, `FormDataParts` | `TextPayload`, `BinaryPayload`, `FilePath`, `PathResource` |
| `Binary` | `BinaryPayload` | Everything else |
| `Stream` | `FilePath` **or** `PathResource` (not both) | Everything else |

## Response Body Classification

The activity decides how to populate the output based on the response:

| Server response | Output field populated |
| --- | --- |
| Text content type (JSON, XML, text/*) | `TextContent` |
| File-like (image/*, video/*, audio/*, attachment, most application/*) | `File` (saved to disk) |
| Other binary | `BinaryContent` |
| HEAD request or empty body | All empty, `StatusCode` reflects the actual status |
| Null/no response (network error with ContinueOnError) | `StatusCode = 503`, error message in `TextContent` |

Setting `SaveResponseAsFile = true` forces any response to be saved as a file regardless of content type.

## Validation (Pre-Flight)

These checks run before any network call:

- `RequestUrl` must not be null or whitespace. **Exception:** when `AuthenticationType = Connector`, `RequestUrl` is optional — an empty operation path resolves to the connector base URL. In that mode `ConnectionId` is required instead.
- `MaxRedirects` ≥ 0.
- `RetryCount` ≥ 0.
- `InitialDelay` ≥ 0.
- `MaxRetryAfterDelay` ≥ 0.
- `Timeout` ≥ 0 (if set).

Failures throw `ArgumentException` / `ArgumentOutOfRangeException` immediately.

## Redirects

- `FollowRedirects = true` (default): the activity follows up to `MaxRedirects` (default 3) HTTP redirects automatically.
- `FollowRedirects = false`: redirect responses (3xx) are returned as-is.
- Redirects are handled at the transport level — the `Authorization` header may be stripped by the underlying handler on cross-origin redirects (standard .NET behavior).

## Debug Output

When `SaveRawRequestResponse = true`, `RawRequestDebuggingInfo` contains a structured text dump designed for **machine consumption**. An agent can parse this output to understand what happened at runtime and make quick adjustments to request parameters (change headers, fix auth, tune retry, adjust timeout) without re-running a full test cycle.

The dump is **redaction-safe**: credentials are stripped from both headers and URLs before the text is built, so it can be pasted into tickets or shared with support without leaking secrets. The specific fields that are redacted are called out in the section list below.

Sections in the output:

- **Timing** — start UTC, end UTC, elapsed ms.
- **Redirect** — whether a redirect occurred, initial vs. final URI. Credential-bearing query parameters are **redacted** in every printed URI: `X-Amz-Signature`, `X-Amz-Credential`, `X-Amz-Security-Token`, `Signature`, `sig`, `AWSAccessKeyId`, `access_token`, `token`, `api_key`, and `apikey` (covers AWS SigV4 presigned URLs, Azure SAS, and generic api-key/token links). Redaction is applied to the display string only; redirect detection still compares the raw URIs, so a redirect that changes only a sensitive parameter is still reported.
- **Transport** — SSL protocol, cookie mode, redirect config, proxy settings, client certificate path, auth type.
- **Retry history** — for each attempt: status code, delay waited, whether `Retry-After` was honored (and the raw vs. clamped value), exception if any, start/end timestamps.
- **Request headers** — all headers sent. Sensitive headers are **redacted**: `Authorization` and `Proxy-Authorization` show the scheme with the value replaced by `***redacted***`; `X-Amz-Security-Token`, `X-Amzn-Authorization`, `Cookie`, `X-Api-Key`, and `Api-Key` are fully replaced with `***redacted***`.
- **Request body preview** — content type, size, and text preview truncated at 2000 characters. Multipart requests list each part with its name, type, and size.
- **Response headers** — all response + content headers. The same sensitive-header set is redacted as on the request; in practice `Set-Cookie` is the one that appears.
- **Response options** — file save settings, actual saved path and file size.
- **Response body preview** — text truncated at 2000 chars; binary shows length only; file responses are not previewed.

Use this output to:
- Confirm which `Authorization` scheme was sent (even though the value is redacted, the scheme — `Basic`, `Bearer`, `Negotiate` — is visible).
- See exact retry timing and whether the server's `Retry-After` was used.
- Detect redirect chains and verify the final URL.
- Inspect the actual `Content-Type` sent and received.
- Verify file save path and size for download responses.

If the debug assembly itself fails, the field contains an error message rather than crashing the activity.

## Content Type and File Extension Detection

### On requests (outbound)

When the body type is `Stream` or `MultipartFormData`, the activity auto-detects the `Content-Type` for each file:

1. **`IResource` files** (from `PathResource` or `ResourceFiles`) — the resource's own `MimeType` property is used if present. If `null`, falls back to step 2.
2. **Local files** (from `FilePath` or `LocalFiles`) — the file extension is looked up in a built-in map. Recognized extensions include: `.jpg`, `.png`, `.gif`, `.pdf`, `.json`, `.xml`, `.csv`, `.zip`, `.mp4`, `.docx`, `.xlsx`, `.pptx`, and ~30 more. Unknown extensions default to `application/octet-stream`.
3. **User override** — a `Content-Type` header in `Headers` overrides the auto-detected value for the main body (but not individual multipart parts).

### On responses (inbound)

The response `Content-Type` header drives two decisions:

**Body classification** — determines which output field is populated:
- **Text** if: `text/*`, `application/json`, `application/xml`, or any `application/*+json` / `application/*+xml` pattern, plus additional types like `application/javascript`, `application/yaml`, `application/sql`, `application/graphql`, `application/toml`, `application/markdown`.
- **File** if: `Content-Disposition` has a filename or is `attachment`/`inline`, or content type is `image/*`, `video/*`, `audio/*`, or an `application/*` type that is not JSON/XML/form-urlencoded/octet-stream.
- **Bytes** — everything else (including `application/octet-stream` without a filename).

**Auto-generated file extension** — when saving to disk and no filename is available from the server:
- Text responses get a mapped extension (e.g., `application/json` → `.json`, `text/html` → `.html`). Unknown text types get `.tmp`.
- File/stream responses get a reverse-mapped extension from the content type (e.g., `image/png` → `.png`). Unknown types get `.tmp`.
- Binary responses always get `.bin`.

## Parameter Configuration Guide

This section explains how to correctly configure each group of properties. Properties interact with each other — setting one may require or invalidate others. See [Defaults](#defaults) for the default value of each property.

### Basic Input

| Property | Type | How to use |
| --- | --- | --- |
| `Method` | Enum | `GET`, `POST`, `PUT`, `DELETE`, `HEAD`, `OPTIONS`, `PATCH`, `TRACE` |
| `RequestUrl` | String | **Required** (except with `Connector` auth). Full URL or just host+path (scheme defaults to `http://`). Always set `https://` explicitly for secure APIs. With `Connector` auth this is the operation path appended to the connector base URL and may be left empty. |
| `Parameters` | Dictionary | Query string key-value pairs. URI-escaped automatically. Appended to existing query strings. Connector-supplied parameters override same-key entries. |
| `Headers` | Dictionary | Request headers. Empty keys/values are silently skipped. `Content-Type` has special handling — see Request Body. Connector-supplied headers override same-key entries. |

### Request Body

Set `RequestBodyType` first — it determines which other properties are used.

| If `RequestBodyType` is… | Then set… | And leave empty… |
| --- | --- | --- |
| `None` | Nothing else | All body properties |
| `Text` | `TextPayload` (required), `TextPayloadContentType`, `TextPayloadEncoding` | `FormData`, `BinaryPayload`, file properties |
| `FormUrlEncoded` | `FormData` (required) | `TextPayload`, `BinaryPayload`, file properties |
| `MultipartFormData` | Any combination of: `FormData` (string fields), `LocalFiles` / `ResourceFiles` (file uploads), `FormDataParts` (typed parts with per-part content types and encoding) | `TextPayload`, `BinaryPayload`, `FilePath`, `PathResource` |
| `Binary` | `BinaryPayload` (required) | Everything else |
| `Stream` | `FilePath` **or** `PathResource` (one required, not both) | Everything else |

Notes:
- `TextPayloadContentType` defaults to `application/json`, but **set it explicitly** whenever you send a body — `application/json` for JSON, `application/xml` for XML, `text/plain` for plain text. Relying on the default leaves the request's intent implicit and is a common review/validation red flag; an explicit value guarantees the right `Content-Type` header.
- `TextPayloadEncoding` defaults to `UTF-8`. Override for legacy encodings.
- `FormDataParts` allows typed parts (`TextFormDataPart`, `BinaryFormDataPart`, `FileFormDataPart`) with per-part content types and encoding. Parts marked `IsExample = true` are skipped at runtime.
- For `Stream`, the `Content-Type` is auto-detected from the file extension (or `IResource.MimeType`). Override with a `Content-Type` header if needed.

### Client Options (Transport)

These affect the **connection pool** — changing any of these creates a separate pool (different connections than requests with different settings).

| Property | How to use |
| --- | --- |
| `DisableSslVerification` | Set `true` only for testing against self-signed certs. **Never in production.** |
| `TlsProtocol` | Leave as `Automatic` unless the server requires a specific version. `Tls13` requires server support. |
| `EnableCookies` | `true` = cookies persist in shared jar. `false` = cookies sent via manual header only. |
| `ProxySetting` | `None` = direct connection. `SystemDefault` = OS proxy. `Custom` = requires `ProxyConfiguration`. |
| `ProxyConfiguration` | Only used when `ProxySetting = Custom`. Set `Address`, optionally `BypassOnLocal`, `BypassList`, `ProxyCredentials`. When switching away from `Custom`, clear this. |
| `ClientCertPath` | Path to `.pfx`/`.p12` file, or a certificate subject name to find in the Windows Root store. |
| `ClientCertPassword` / `ClientCertSecurePassword` | Password for the client certificate. Use one or the other, not both. Prefer `SecureString`. |

### Proxy Configuration

Use `ProxySetting` to choose how the request resolves proxy settings:

- `SystemDefault`: Uses the operating system proxy configuration (WinINET). This matches browser behavior, including PAC scripts and system-level bypass lists.
- `None`: Bypasses proxies entirely.
- `Custom`: Uses the provided `ProxyConfiguration` object. Set the proxy `Address`, optional `BypassOnLocal`/`BypassList`, and `ProxyCredentials` when required.

Switching proxy modes changes the underlying connection pool. If you move from `Custom` to `SystemDefault` or `None`, clear `ProxyConfiguration` to avoid confusion.