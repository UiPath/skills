# HTTP Request

`UiPath.Web.Activities.Http.NetHttpRequest`

Configures and sends an HTTP request with customizable options for headers, authentication, cookies, retries, SSL, and request body formats. Includes flexible retry mechanisms and graceful handling of errors, with optional continuation on failure.

> This activity has extensive runtime logic. For full understanding of defaults, side-effects, retry mechanics, and edge cases, read the [Observable Behavior](#nethttprequest--observable-behavior) section at the bottom of this document.

**Package:** `UiPath.WebAPI.Activities`
**Category:** Web
**Platform:** Cross-platform

## When to use

Use for HTTP calls that require retries, authentication, file downloads, or rich response inspection.

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `RequestUrl` | Request URL | InArgument | `string` | Yes | | | The URL to send the HTTP request to. |
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
| `SaveRawRequestResponse` | Enable debugging info | InArgument | `bool` | `False` | | Whether to save raw request and response data for debugging. |

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
| `RawRequestDebuggingInfo` | `string` | Raw request debug information, available when `SaveRawRequestResponse` is enabled. |

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
| `AuthenticationType` | `None`, `BasicUsernamePassword`, `OAuthToken`, `NegotiatedAuthentication` |
| `RetryPolicyType` | `None`, `Basic`, `ExponentialBackoff` |
| `FileOverwriteOption` | `AutoRename`, `Replace`, `Discard` |
| `ProxySettingType` | `None`, `SystemDefault`, `Custom` |
| `SupportedTlsProtocols` | `Automatic`, `Tls12`, `Tls13` |

## XAML Examples

### GET request with basic authentication and retry

```xml
<nhr:NetHttpRequest
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

```xml
<nhr:NetHttpRequest
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

## Notes

- Cookies can persist across activity calls within the same workflow execution.
- Only one of `TextContent`, `BinaryContent`, or `File` is meaningfully populated per response.

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
2. Normalize URL (adds `http://` when scheme is missing).
3. Append query parameters to the URL.
4. Create `HttpClient` using transport config, late-bound config, and timeout.
5. Create `HttpRequestMessage` with method + final URL.
6. Apply activity metadata.
7. Apply cookies through the shared cookie manager.
8. Resolve text encoding.
9. Build request body from the selected body type.
10. Add request headers (applied after body build, so explicit headers can override defaults such as `Content-Type`).
11. Send request with `ResponseHeadersRead` and cancellation token.
12. Build `HttpResponseSummary` using response options.

Important implications:
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

Auth headers are set **per request** — they are not cached or shared.

## URL Handling

- If the URL has no scheme (`example.com/api`), `http://` is prepended — **not** `https://`.
- Query parameters from the `Parameters` dictionary are URI-escaped and appended.
- Existing query strings in the URL are preserved; parameters are appended with `&`.
- Final URL must be ≤ 2000 characters.

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

- `RequestUrl` must not be null or whitespace.
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

Sections in the output:

- **Timing** — start UTC, end UTC, elapsed ms.
- **Redirect** — whether a redirect occurred, initial vs. final URI.
- **Transport** — SSL protocol, cookie mode, redirect config, proxy settings, client certificate path, auth type.
- **Retry history** — for each attempt: status code, delay waited, whether `Retry-After` was honored (and the raw vs. clamped value), exception if any, start/end timestamps.
- **Request headers** — all headers sent. `Authorization` and `Proxy-Authorization` values are **redacted** (scheme shown, value replaced with `***redacted***`).
- **Request body preview** — content type, size, and text preview truncated at 2000 characters. Multipart requests list each part with its name, type, and size.
- **Response headers** — all response + content headers.
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
| `RequestUrl` | String | **Required.** Full URL or just host+path (scheme defaults to `http://`). Always set `https://` explicitly for secure APIs. |
| `Parameters` | Dictionary | Query string key-value pairs. URI-escaped automatically. Appended to existing query strings. |
| `Headers` | Dictionary | Request headers. Empty keys/values are silently skipped. `Content-Type` has special handling — see Request Body. |

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
- `TextPayloadContentType` defaults to `application/json`. Change it for XML (`application/xml`), plain text (`text/plain`), etc.
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