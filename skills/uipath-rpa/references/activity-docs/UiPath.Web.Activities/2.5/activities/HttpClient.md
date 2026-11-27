# HTTP Request (legacy)

`UiPath.Web.Activities.HttpClient`

> **Legacy activity** — Retained for existing workflow compatibility only. For new workflows, use **HTTP Request** (`NetHttpRequest`) instead.

Composes a request to an endpoint URL, executes it and returns the response in a string format, saving the resource if specified. It has authentication capabilities allowing communication with secured endpoints. This is the legacy HTTP request activity; prefer the newer "HTTP Request" (`NetHttpRequest`) for new workflows.

**Package:** `UiPath.WebAPI.Activities`
**Category:** Web
**Platform:** Cross-platform

## When to use

Use only to understand or maintain existing workflows that already depend on this activity. For new workflows or migrations, use the modern **HTTP Request** (`NetHttpRequest`) activity.

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `EndPoint` | Request URL | InArgument | `string` | Yes | | | The URL endpoint to send the request to. |
| `Method` | Request method | Property | `Method` | | | | HTTP method (GET, POST, PUT, DELETE, HEAD, OPTIONS, PATCH, MERGE). |
| `AcceptFormat` | Accept Format | Property | `AcceptHeaderType` | | | | The Accept header format for the response. |
| `Body` | Body | InArgument | `string` | | | | The request body content. |

### Authentication (conditional on AuthenticationType)

| Name | Display Name | Kind | Type | Visible When | Description |
|------|-------------|------|------|------------|-------------|
| `AuthenticationType` | Authentication Type | Property | `AuthType` | Always | The authentication method to use. |
| `Username` | Username | InArgument | `string` | AuthenticationType = SimpleHttp | Username for basic authentication. OverloadGroup: SimpleAuthentication. |
| `Password` | Password | InArgument | `string` | AuthenticationType = SimpleHttp AND NOT using secure | Password for basic authentication. OverloadGroup: SimpleAuthentication. |
| `SecurePassword` | Secure password | InArgument | `SecureString` | AuthenticationType = SimpleHttp AND using secure | Secure password for basic authentication. OverloadGroup: SimpleAuthentication. |
| `ConsumerKey` | ConsumerKey | InArgument | `string` | AuthenticationType = OAuth1 | OAuth1 consumer key. OverloadGroup: OAuth1. |
| `ConsumerSecret` | ConsumerSecret | InArgument | `string` | AuthenticationType = OAuth1 | OAuth1 consumer secret. OverloadGroup: OAuth1. |
| `OAuth1Token` | OAuth1Token | InArgument | `string` | AuthenticationType = OAuth1 | OAuth1 token. OverloadGroup: OAuth1. |
| `OAuth1TokenSecret` | OAuth1TokenSecret | InArgument | `string` | AuthenticationType = OAuth1 | OAuth1 token secret. OverloadGroup: OAuth1. |
| `OAuth2Token` | OAuth2Token | InArgument | `string` | AuthenticationType = OAuth2 | OAuth2 bearer token. OverloadGroup: OAuth2. |
| `ClientCertificate` | ClientCertificate | InArgument | `string` | AuthenticationType = ClientCertificate | Path to the client certificate file. |
| `ClientCertificatePassword` | ClientCertificatePassword | InArgument | `string` | AuthenticationType = ClientCertificate AND NOT using secure | Password for the client certificate. |
| `SecureClientCertificatePassword` | SecureClientCertificatePassword | InArgument | `SecureString` | AuthenticationType = ClientCertificate AND using secure | Secure password for the client certificate. |

### Options

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `BodyFormat` | Body Format | Property | `string` | The content type of the request body (e.g., `application/json`). |
| `ResourcePath` | Filename for response attachment | InArgument | `string` | Path to save the response body as a file. |
| `EnableSSLVerification` | Enable SSL certificate verification | InArgument | `bool` | Default: `True`. When enabled, validates the server SSL certificate. |
| `Headers` | Headers | Property | `Dictionary<string, InArgument<string>>` | Custom HTTP headers to include in the request. |
| `Parameters` | Parameters | Property | `Dictionary<string, InArgument<string>>` | URL query parameters to append to the request URL. |
| `Cookies` | Cookies | Property | `Dictionary<string, InArgument<string>>` | Cookies to include in the request. |
| `Attachments` | Attachments | Property | `Dictionary<string, InArgument<string>>` | File attachments to include in the request. |
| `FileAttachments` | File Attachments | InArgument | `ICollection<ILocalResource>` | File resources to attach to the request. |
| `UrlSegments` | URL Segments | Property | `Dictionary<string, InArgument<string>>` | URL segment replacements for parameterized URLs. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Result` | Response content | OutArgument | `string` | The response body returned as a string. |
| `StatusCode` | Response status | OutArgument | `int` | The HTTP status code of the response. |
| `ResponseHeaders` | Headers | OutArgument | `Dictionary<string, string>` | The response headers returned by the server. |
| `ResponseAttachment` | Response attachment | OutArgument | `ILocalResource` | The saved response file attachment when `ResourcePath` is specified. |

### Common

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `ContinueOnError` | Continue on error | InArgument | `bool` | When set to `True`, the workflow continues executing even if the activity throws an error. |
| `TimeoutMS` | Timeout (milliseconds) | InArgument | `int` | The maximum time (in milliseconds) to wait for the request to complete. |

## Valid Configurations

The activity supports five authentication modes controlled by the `AuthenticationType` property:

1. **None** -- No authentication is applied to the request.
2. **SimpleHttp** -- Basic HTTP authentication using a username and password (or secure password). `Password` and `SecurePassword` are mutually exclusive.
3. **OAuth1** -- OAuth 1.0 authentication requiring a consumer key, consumer secret, token, and token secret.
4. **OAuth2** -- OAuth 2.0 bearer token authentication.
5. **ClientCertificate** -- Client certificate authentication with an optional certificate password. `ClientCertificatePassword` and `SecureClientCertificatePassword` are mutually exclusive.

## Enum Reference

**`Method`**: `GET`, `POST`, `PUT`, `DELETE`, `HEAD`, `OPTIONS`, `PATCH`, `MERGE`

**`AcceptHeaderType`**: `ANY`, `JSON`, `XML`, `CUSTOM`

**`AuthType`**: `None`, `SimpleHttp`, `OAuth1`, `OAuth2`, `ClientCertificate`

## XAML Examples

A simple GET request:

```xml
<web:HttpClient
  DisplayName="GET API Data"
  EndPoint="[&quot;https://api.example.com/data&quot;]"
  Method="GET"
  AcceptFormat="JSON"
  Result="[responseContent]"
  StatusCode="[responseStatus]" />
```

A POST request with basic authentication:

```xml
<web:HttpClient
  DisplayName="POST with Basic Auth"
  EndPoint="[&quot;https://api.example.com/items&quot;]"
  Method="POST"
  AcceptFormat="JSON"
  Body="[jsonBody]"
  BodyFormat="application/json"
  AuthenticationType="SimpleHttp"
  Username="[apiUser]"
  Password="[apiPassword]"
  Result="[responseContent]"
  StatusCode="[responseStatus]" />
```

## Notes

This is the legacy HTTP Request activity that uses RestSharp internally. For new workflows, prefer the newer **HTTP Request** (`NetHttpRequest`) activity.
