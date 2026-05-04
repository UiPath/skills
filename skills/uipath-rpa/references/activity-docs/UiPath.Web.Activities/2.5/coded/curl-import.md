# cURL Import � Converting cURL Commands to `HttpRequestOptions`

An agent skill for converting raw cURL commands into a ready-to-use `HttpRequestOptions` object using the deterministic `ICurlImportService` parser.

## Important instruction for agents

**Do not parse cURL commands yourself.** The `ICurlImportService` (accessed as `curl` in coded workflows) is a deterministic parser that handles method, URL, headers, authentication, body types, proxy, TLS, cookies, retries, file output, and more. It automatically detects and correctly parses both **bash-style** and **cmd-style** cURL commands � there is no need to normalize shell syntax before importing.

Manually parsing cURL is error-prone and unnecessary � the parser covers the vast majority of cURL flags and produces an `HttpRequestOptions` object that feeds directly into `http.SendRequestAsync()`.

Read this file completely before generating code. The workflow is: **import ? act on warnings ? hand off `HttpRequestOptions`**.

### Scope of this skill

This skill is concerned **only** with producing a correct `HttpRequestOptions` from a cURL command. Once the object is ready, hand it off to `http.SendRequestAsync()`. Diagnosing HTTP responses, iterating on failures, and processing response content are handled by [NetHttpRequest.md](../../UiPath.Web.Activities.Package.Design/docs/activities/NetHttpRequest.md) and [service-discovery.md](service-discovery.md).

## When to use

The user provides a cURL command and expects a coded workflow that reproduces the same HTTP request. Indicators:

- The user message contains `curl ` followed by a URL or flags.
- The user says "convert this cURL", "run this cURL", "make a workflow from this cURL", or similar.
- The user pastes a command copied from browser DevTools, API documentation, or Postman.

## Prerequisites

- The coded workflow project must reference `UiPath.Web.Activities.API` (provides `ICurlImportService` and `IHttpService`).
- The `curl` and `http` services are auto-imported via `WebRegistry` � no `using` statements needed for `UiPath.Web.Activities.API`, `UiPath.Web.Activities.API.Models`, or `UiPath.Web.Activities.Http.Models`.

---

## Phase 1 � Import the cURL command

### Goal

Use `curl.Import()` to parse the raw cURL string into structured `HttpRequestOptions`.

### How it works

`curl.Import(rawCurl)` returns a `CurlImportResult` with three fields:

| Field | Type | Description |
| --- | --- | --- |
| `Options` | `HttpRequestOptions` | The parsed HTTP request options. `null` if the import failed (errors in `Warnings`). |
| `Warnings` | `IReadOnlyList<CurlImportWarning>` | Warnings and errors from the parser. Each has `Code` (string), `Severity` (Info/Warning/Error), and `Args` (object[]). |
| `Raw` | `string` | The original cURL string passed to the parser. |

The parser automatically detects whether the input is bash-style (with `\` line continuations and single quotes) or cmd-style (with `^` line continuations and double quotes). Pass the cURL exactly as the user provided it.

### What the parser handles

The deterministic parser extracts and maps:

| cURL concept | Mapped to `HttpRequestOptions` property |
| --- | --- |
| URL and query string | `Url`, `Parameters` |
| `-X` / `--request` (method) | `Method` |
| `-H` / `--header` | `Headers` |
| `-d` / `--data` / `--data-raw` / `--json` | `Body` (Text with JSON or other content type) |
| `--data-urlencode` | `Body` (FormUrlEncoded) |
| `-F` / `--form` | `Body` (MultipartFormData with typed `FormDataPart` entries) |
| `--data-binary` / `-T` (upload) | `Body` (Binary or Stream) |
| `-u` / `--user` (user:pass) | `Authentication` (BasicUsernamePassword) |
| `Authorization: Bearer` header | `Authentication` (OAuthToken) |
| `Authorization: Basic` header | `Authentication` (BasicUsernamePassword, decoded) |
| `--negotiate` / `--ntlm` | `Authentication` (NegotiatedAuthentication) |
| `-b` / `--cookie` | `Cookies` |
| `-L` / `--location` | `FollowRedirects` |
| `--max-redirs` | `MaxRedirects` |
| `--max-time` | `TimeoutMilliseconds` |
| `--retry`, `--retry-delay`, `--retry-max-time`, `--retry-all-errors` | `RetryPolicy` |
| `-k` / `--insecure` | `Client.DisableSslVerification` |
| `--tlsv1.2`, `--tlsv1.3` | `Client.TlsProtocol` |
| `--cert` / `--pass` | `Client.ClientCertificatePath`, `Client.ClientCertificatePassword` |
| `-x` / `--proxy`, `-U` / `--proxy-user`, `--noproxy` | `Client.ProxySetting`, `Client.ProxyConfiguration` |
| `-o` / `--output`, `-O` / `--remote-name` | `ResponseOptions` (SaveAsFile, FileName, TargetFolder) |
| `--compressed` | Transparent (handled by transport) |

### Optional import configuration

`curl.Import()` accepts an optional `CurlImportOptions` parameter:

| Option | Default | Effect |
| --- | --- | --- |
| `MapFileBodyToStream` | `true` | Maps `--data-binary @file` to a streaming body instead of loading into memory. |
| `InferJsonForTextPayload` | `true` | When `-d` payload looks like JSON, sets `ContentType` to `application/json`. |
| `StripAuthorizationHeaderOnAuthMapping` | `true` | Removes the raw `Authorization` header after mapping it to the `Authentication` property (avoids duplication). |

For most use cases, the defaults are correct. Override only when needed.

### Coded workflow � basic import

```csharp
var rawCurl = @"curl -X POST 'https://api.example.com/users' \
  -H 'Authorization: Bearer eyJhbGciOi...' \
  -H 'Content-Type: application/json' \
  -d '{""name"":""John Doe"",""email"":""john@example.com""}'";

var imported = curl.Import(rawCurl);

if (imported.Options == null)
{
    // Import failed � check Phase 2 for how to handle errors
    return;
}

// Options is ready � use with http.SendRequestAsync()
var response = await http.SendRequestAsync(imported.Options);
```

---

## Phase 2 � Act on warnings

### Goal

Inspect `CurlImportResult.Warnings` and react based on severity. The agent has two strategies for resolving issues:

1. **Fix the cURL command and re-import** � preferred when the issue is in the cURL syntax itself (e.g., malformed quoting, missing URL). Fix the cURL string and call `curl.Import()` again.
2. **Fill in the `HttpRequestOptions` directly** � when the parser produced a partial result and the warning tells the agent exactly what's missing (e.g., auth could not be decoded). Set the missing property on `imported.Options`.

### Warning severity levels

| Severity | Meaning | Agent action |
| --- | --- | --- |
| `Error` | The parser could not produce a valid `HttpRequestOptions`. `Options` is `null`. | If the fix is obvious (e.g., missing URL, broken quoting), correct the cURL and re-import. Otherwise, **ask the user** to clarify or fix the cURL. Do not guess. |
| `Warning` | The parser produced an `HttpRequestOptions` but something was ambiguous or partially mapped. | Read the warning `Code` to understand what the parser could not resolve. Either fix the cURL and re-import, or fill the gap directly on `imported.Options`. |
| `Info` | Informational � the parser made an automatic decision (e.g., stripped the `Authorization` header after mapping auth). | No action needed. Can log for transparency. |

### Known warning codes

| Code | Severity | Meaning | Agent response |
| --- | --- | --- | --- |
| `CURL_Import_DecodeBasicAuthFailed` | Warning | The Base64 payload in a `Basic` auth header could not be decoded. Auth is not mapped. | Fix the Base64 value in the cURL and re-import, **or** set `options.WithBasicAuth(username, password)` directly if the credentials are known. If neither is possible, ask the user. |
| `CURL_Import_AmbiguousAuth_BearerPreferred` | Warning | Both Bearer and Basic credentials were detected. Bearer was used. | Inform the user which auth was chosen. If Basic was intended, either remove the Bearer header from the cURL and re-import, or replace with `options.WithBasicAuth(username, password)`. |
| `CURL_Import_HeaderAuthorizationStripped` | Info | The raw `Authorization` header was removed after mapping to the `Authentication` property. | Expected when `StripAuthorizationHeaderOnAuthMapping = true` (default). No action needed. |

### Handling unrecoverable errors

If the parser returned `Options == null` and the error is not obvious to fix:

1. **Do not invent a fix.** The cURL is the user's intent � guessing what they meant risks producing a request that does something different from what they expect.
2. **Report the warnings** to the user with their codes.
3. **Ask the user** to provide a corrected cURL or clarify what they intended.
4. Once the user provides a fix, re-import.

### Rules

1. **Never re-parse the cURL yourself.** Always use `curl.Import()`.
2. **React only to what the parser reported.** If the parser mapped a property without warnings, do not override it.
3. **Prefer fixing the cURL and re-importing** over manually patching `HttpRequestOptions` � a clean re-import produces a fully consistent object.
4. **When filling `HttpRequestOptions` directly**, use the fluent builder methods (`WithBasicAuth`, `WithBearerToken`, `WithHeader`, etc.) for setting new properties.
5. **When the error is not clear, ask the user.** Do not try to over-correct a bad cURL by guessing.

### Coded workflow � warning-driven fix

```csharp
var imported = curl.Import(rawCurl);

if (imported.Options == null)
{
    // Import failed � report to user
    foreach (var w in imported.Warnings)
    {
        Log($"cURL import {w.Severity}: {w.Code}");
    }
    // Ask user to fix the cURL
    return;
}

// Act on warnings
foreach (var w in imported.Warnings.Where(w => w.Severity == WarningSeverity.Warning))
{
    Log($"cURL import warning: {w.Code}");

    if (w.Code == "CURL_Import_DecodeBasicAuthFailed")
    {
        // Parser couldn't decode Basic auth � fill in directly
        imported.Options.WithBasicAuth("username", "password");
    }
}

// Options is ready
var response = await http.SendRequestAsync(imported.Options);
```

---

## Anti-patterns

| Do not | Why | Do instead |
| --- | --- | --- |
| Parse the cURL string yourself with regex or string splitting | Error-prone; misses quoting, escaping, flag ordering, multi-line continuations, cmd vs bash differences | Use `curl.Import()` |
| Normalize bash cURL to cmd or vice versa before importing | The parser auto-detects shell style | Pass the cURL as-is |
| Ignore warnings from the import result | May miss auth gaps, decode failures, or ambiguous mappings that need resolution | Always check `imported.Warnings` and act on entries where `Severity` is `Warning` or `Error` |
| Override parser output that was mapped without warnings | The parser's mapping is tested and deterministic; overriding introduces drift | Only modify `HttpRequestOptions` when a warning tells you something is missing or ambiguous |
| Guess what a broken cURL meant and silently fix it | May produce a request that differs from the user's intent | Ask the user to clarify or correct the cURL |
| Build `HttpRequestOptions` from scratch when a cURL is available | Duplicates work the parser already does; risks transcription errors | Use `curl.Import()` and act only on warnings |

---

## See Also

- [NetHttpRequest Activity](../../UiPath.Web.Activities.Package.Design/docs/activities/NetHttpRequest.md) — modern HTTP activity behavior spec, inputs, outputs, and defaults
- [HttpClient Activity (Legacy)](../../UiPath.Web.Activities.Package.Design/docs/activities/HttpClient.md) — legacy HTTP activity reference
- [Service Discovery](service-discovery.md) — discovering unknown service endpoints and generating working requests
- [HTTP Request Upgrade](http-request-upgrade.md) — migrating from the legacy HTTP Request activity
