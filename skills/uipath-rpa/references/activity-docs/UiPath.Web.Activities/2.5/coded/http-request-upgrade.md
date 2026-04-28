# HTTP Request Upgrade — Legacy to Modern Migration

An agent skill for migrating workflows from the legacy HTTP Request activity (RestSharp-based) to the modern NetHttpRequest activity (.NET HttpClient-based).

## Important instruction for agents

Read this file **completely** before generating any code. The migration cannot be done with a simple property swap — the underlying HTTP clients differ (RestSharp vs .NET HttpClient), which causes behavioral divergences in header handling, encoding, redirect behavior, and body serialization. The skill uses a **capture → translate → verify** loop to ensure the migrated request produces the same result as the original.

## When to use

The user has an existing workflow (UI or coded) that uses the legacy `HttpClient` activity (class: `UiPath.Web.Activities.HttpClient`, display name: "HTTP Request") and wants to migrate it to the modern `NetHttpRequest` activity (display name: "HTTP Request").

Indicators that the user is referring to the legacy activity:
- The workflow XAML contains `<web:HttpClient` (namespace `UiPath.Web.Activities`).
- Properties include `AcceptFormat`, `BodyFormat`, `Body`, `UrlSegments`, `Attachments`, `OAuth1Token`, `OAuth1TokenSecret`, `ConsumerKey`, `ConsumerSecret`.
- The activity returns `Result` (string), `StatusCode` (int), `ResponseHeaders` (Dictionary), `ResponseAttachment` (ILocalResource).
- The user mentions "RestSharp", "old HTTP activity", or "legacy HTTP Request".

## Prerequisites

- The target endpoint must be reachable from the runtime environment.
- Authentication credentials used by the legacy activity must be available.
- The coded workflow project must reference `UiPath.Web.Activities.API` (provides `IHttpService`).
- `Newtonsoft.Json` is available for JSON serialization/deserialization.

---

## Caution and safety

This migration changes the HTTP transport layer underneath an existing workflow. A mismatch — even a subtle one like a different `Content-Type` charset or a missing `Accept` header — can cause the server to return a different response, silently break downstream logic, or modify server-side state (for POST/PUT/DELETE/PATCH). The agent must treat this as a **high-risk refactor** and follow the rules below.

### 1. Back up the project first

Before any migration work begins, **tell the user to create a backup** of the project (copy the folder, commit to a branch, or create a snapshot). If the user declines, proceed only after explicit acknowledgment that they accept the risk.

### 2. One activity at a time

Never migrate multiple HTTP Request activities in a single step. The agent must:
1. **Inventory** all legacy `HttpClient` activities in the workflow.
2. **Propose a migration plan** to the user — a numbered list showing which activity will be migrated in which order.
3. **Wait for user confirmation** before starting each activity's migration.
4. **Complete the full Phase 0–5 cycle** for one activity before moving to the next.

Prefer migrating **read-only (GET/HEAD/OPTIONS) activities first** — they don't modify server state, so comparison is safe. Save state-changing methods (POST/PUT/DELETE/PATCH) for later, after the pattern is established.

### 3. Side-effect warning for mutating methods

POST, PUT, DELETE, and PATCH requests may **create, modify, or delete data on the server**. Running the modern activity to compare against the legacy baseline means executing the request again — which may duplicate creates, double-delete, or produce different results if the server state changed.

Before executing a mutating request with the modern activity:
- **Warn the user** that re-executing the request will hit the server again.
- **Ask if a test/sandbox environment is available** and suggest using it.
- **If no safe environment exists**, ask the user whether to proceed or to accept the mapping from Phase 1 without runtime verification.

### 4. Preserve the old activity until confirmed

Do not delete or remove the legacy activity until the user confirms the modern replacement produces equivalent results. During migration:
- **Comment out** or **disable** the legacy activity in the workflow (if UI workflow, set `IsEnabled = false`).
- Keep it in place as a reference and rollback path.
- Only remove it in Phase 5 after explicit user confirmation.

### 5. Maintain a `learnings.md` file

Create a `learnings.md` file in the project directory at the start of the first migration. This file accumulates discoveries, decisions, and fixes that apply across multiple activities in the same workflow. The agent must:
- **Read `learnings.md`** at the start of each activity migration to reuse prior knowledge.
- **Append to `learnings.md`** after each successful migration with what was learned.
- **Reference specific learnings** when proposing mappings for subsequent activities.

See [learnings.md format](#learningsmd-format) for the file structure.

### 6. User checkpoints

The agent must **stop and present results to the user** at these points — never auto-proceed:
- After proposing the migration plan (rule 2).
- After completing Phase 1 mapping — show the mapping and ask for confirmation before generating code.
- After Phase 3 comparison — show the status code, response body diff, and any diagnosis before adjusting.
- After Phase 4 output mapping — confirm the downstream variable assignments are correct.
- Before Phase 5 finalization — confirm the user is ready to remove debug settings and the old activity.

### 7. Scope lock

During migration of one activity, **do not modify any other activity, variable, argument, or workflow logic** outside the scope of that specific activity. The only exception is updating `learnings.md`.

### 8. Rollback guidance

If migration fails (the modern activity cannot reproduce the legacy behavior after reasonable attempts):
- **Re-enable the legacy activity** (uncomment or set `IsEnabled = true`).
- **Remove the modern replacement code.**
- **Record the failure reason in `learnings.md`** so future attempts can avoid the same path.
- **Inform the user** with a clear explanation of what went wrong and whether a manual fix is possible.

---

## Phase 0 — Capture the legacy baseline

### Goal

Run the legacy activity and record its outputs so we have a ground truth to compare against after migration.

### Why this matters

The legacy activity uses RestSharp internally. RestSharp and .NET HttpClient differ in:
- **Default headers** — RestSharp adds `Accept: application/json, text/json, text/x-json, text/javascript, application/xml, text/xml` by default for certain AcceptFormats; .NET HttpClient sends no Accept header by default.
- **Body content type** — The legacy activity uses `BodyFormat` (a string like `"application/xml"` or `"application/json"`) which maps to RestSharp's body serializer; the modern activity uses `RequestBodyType` enum + `TextPayloadContentType`.
- **URL segment interpolation** — The legacy activity supports `UrlSegments` (RestSharp's `{placeholder}` replacement in the URL); the modern activity does not — segments must be inlined into the URL.
- **Cookie parsing** — The legacy activity parses cookie strings in `name=value;name2=value2` format from a `Dictionary<string, InArgument<string>>`; the modern activity accepts a flat `Dictionary<string, string>`.
- **Redirect behavior** — RestSharp follows redirects by default with no limit; the modern activity follows up to 3 redirects by default.
- **Timeout** — Legacy defaults to 6000 ms; modern defaults to 10000 ms.
- **ContinueOnError** — Legacy defaults to `false`; modern defaults to `true`.
- **Error shape** — Legacy throws or returns an empty `RestResponse`; modern returns a synthetic 503 with the exception message in `TextContent`.

### What to capture

From the legacy activity's execution, record:
1. **Status code** (`StatusCode` output — an `int`).
2. **Response body** (`Result` output — a `string`).
3. **Response headers** (`ResponseHeaders` output — `Dictionary<string, string>`).
4. **Response attachment** (`ResponseAttachment` output — if present, note the file path and content type).

Also record the **inputs** that were configured:
- `EndPoint`, `Method`, `AcceptFormat`, `BodyFormat`, `Body`
- `Headers`, `Parameters`, `UrlSegments`, `Cookies`, `Attachments`, `FileAttachments`
- `Username`, `Password` / `SecurePassword`
- `ConsumerKey`, `ConsumerSecret`, `OAuth1Token`, `OAuth1TokenSecret`
- `OAuth2Token`
- `ClientCertificate`, `ClientCertificatePassword` / `SecureClientCertificatePassword`
- `TimeoutMS`, `ContinueOnError`, `EnableSSLVerification`
- `ResourcePath`

### Agent action

**Before anything else:**
1. Remind the user to **back up the project** (see [Caution and safety](#caution-and-safety)).
2. **Inventory all legacy activities** in the workflow and propose a migration plan — a numbered list showing the order of migration, with GET/HEAD/OPTIONS activities first.
3. **Wait for user confirmation** of the plan before proceeding.
4. **Read `learnings.md`** if it exists from a prior migration in this project.

Then, for the current activity:

If the legacy activity has already been run and the user can provide outputs → skip to Phase 1.

If the user wants to run it first → the legacy activity is **not available in coded workflows**. It can only run in a UI workflow. Ask the user to run the existing workflow and share the outputs, or inspect the workflow XAML to extract the configured inputs.

If the method is POST, PUT, DELETE, or PATCH → warn the user about side effects (see [Caution rule 3](#3-side-effect-warning-for-mutating-methods)) before capturing the baseline.

---

## Phase 1 — Map legacy inputs to modern inputs

### Goal

Translate every configured property of the legacy `HttpClient` activity to its equivalent on `NetHttpRequest` / `HttpRequestOptions`.

### Static mapping table

| Legacy property | Type | Modern property | Type | Notes |
| --- | --- | --- | --- | --- |
| `EndPoint` | `String` | `RequestUrl` / `Url` | `String` | Direct map. Both prepend `http://` if no scheme is present. |
| `Method` | `Enum (GET,POST,PUT,DELETE,HEAD,OPTIONS,PATCH,MERGE)` | `Method` | `Enum (GET,POST,PUT,DELETE,HEAD,OPTIONS,PATCH,TRACE)` | `MERGE` has no equivalent — see [Special cases](#merge-method). |
| `AcceptFormat` | `Enum (ANY,JSON,XML,CUSTOM)` | `Headers["Accept"]` | `String` | Map: `ANY` → omit or `*/*`, `JSON` → `application/json`, `XML` → `application/xml`, `CUSTOM` → copy from legacy `Headers["Accept"]`. |
| `BodyFormat` | `String` | `TextPayloadContentType` | `String` | Legacy sets content type as a free-form string (e.g., `"application/json"`, `"application/xml"`). Map directly to `TextPayloadContentType`. |
| `Body` | `String` | `TextPayload` | `String` | Direct map. Also set `RequestBodyType = Text`. |
| `Headers` | `Dict<string, InArgument<string>>` | `Headers` | `Dict<string, string>` | Direct map (evaluate InArguments to strings). |
| `Parameters` | `Dict<string, InArgument<string>>` | `Parameters` | `Dict<string, string>` | Direct map — both append as query string parameters. |
| `UrlSegments` | `Dict<string, InArgument<string>>` | *(inline into URL)* | — | No equivalent. Replace `{key}` placeholders in the URL with their values before setting `RequestUrl`. |
| `Cookies` | `Dict<string, InArgument<string>>` | `Cookies` | `Dict<string, string>` | Legacy parses `name=value;name2=value2` cookie strings. Modern accepts flat key-value pairs. Flatten before mapping. |
| `Attachments` | `Dict<string, InArgument<string>>` | `LocalFiles` | `IEnumerable<string>` | Legacy maps `{name: filePath}`. Modern uses file paths in `LocalFiles` with `RequestBodyType = MultipartFormData`. Field names need `FormDataParts` with `FileFormDataPart` if the name matters. |
| `FileAttachments` | `ICollection<ILocalResource>` | `ResourceFiles` | `IEnumerable<IResource>` | Direct map. Set `RequestBodyType = MultipartFormData`. |
| `ResourcePath` | `String` | `OutputFileTargetFolder` + `OutputFileName` | `String` | Legacy writes response to this path. Modern splits into folder and filename. Also set `SaveResponseAsFile = true`. |
| `Username` | `String` | `BasicAuthUsername` | `String` | Set `AuthenticationType = BasicUsernamePassword`. |
| `Password` | `String` | `BasicAuthPassword` | `String` | Set `AuthenticationType = BasicUsernamePassword`. |
| `SecurePassword` | `SecureString` | `BasicAuthSecurePassword` | `SecureString` | Set `AuthenticationType = BasicUsernamePassword`. |
| `OAuth2Token` | `String` | `OAuthToken` | `String` | Set `AuthenticationType = OAuthToken`. |
| `ConsumerKey` | `String` | — | — | **No equivalent.** OAuth 1.0 is not supported by the modern activity. See [Special cases](#oauth-10). |
| `ConsumerSecret` | `String` | — | — | **No equivalent.** |
| `OAuth1Token` | `String` | — | — | **No equivalent.** |
| `OAuth1TokenSecret` | `String` | — | — | **No equivalent.** |
| `ClientCertificate` | `String` | `ClientCertPath` | `String` | Direct map. |
| `ClientCertificatePassword` | `String` | `ClientCertPassword` | `String` | Direct map. |
| `SecureClientCertificatePassword` | `SecureString` | `ClientCertSecurePassword` | `SecureString` | Direct map. |
| `TimeoutMS` | `Int32` (default 6000) | `TimeoutInMiliseconds` | `Int32?` (default 10000) | Carry the legacy value forward. |
| `ContinueOnError` | `Boolean` (default false) | `ContinueOnError` | `Boolean` (default true) | **Carry the legacy value forward** to preserve behavior. |
| `EnableSSLVerification` | `Boolean` (default true) | `DisableSslVerification` | `Boolean` (default false) | **Inverted logic.** `EnableSSLVerification = true` → `DisableSslVerification = false`. |

### Special cases

#### MERGE method

The legacy activity supports `MERGE` (used in OData v3). The modern activity does not have a `MERGE` enum value. Options:
1. If the server accepts `PATCH` instead of `MERGE` (OData v4), switch to `PATCH`.
2. If `MERGE` is strictly required, the migration cannot proceed with the modern activity — inform the user.

#### OAuth 1.0

The modern activity does not support OAuth 1.0 (`ConsumerKey`, `ConsumerSecret`, `OAuth1Token`, `OAuth1TokenSecret`). Options:
1. If the service also accepts OAuth 2.0 Bearer tokens, migrate to `OAuthToken`.
2. If OAuth 1.0 is required, the user must construct the `Authorization` header manually (compute the OAuth 1.0 signature and set it in `Headers["Authorization"]`). Warn the user this is complex and error-prone.
3. If neither is feasible, the migration cannot proceed — inform the user.

#### Body with attachments

The legacy activity has a special path: when both `Body` and `Attachments` are set, RestSharp sends a multipart request with the body as a form field. The modern activity requires using `RequestBodyType = MultipartFormData` with `FormDataParts` to achieve the same effect:

```csharp
var parts = new List<FormDataPart>
{
    new TextFormDataPart(legacyBody, "body", legacyBodyFormat), // Body as a text part
    new FileFormDataPart(attachmentPath, attachmentName),       // Each attachment
};
var response = await http.PostMultipartAsync(url, parts);
```

#### UrlSegments

Replace placeholders in the URL string before passing to the modern activity:

```csharp
// Legacy: EndPoint = "https://api.example.com/users/{userId}/orders/{orderId}"
//         UrlSegments = { "userId": "123", "orderId": "456" }

// Modern: inline the segments
var url = "https://api.example.com/users/123/orders/456";
```

#### AcceptFormat to Header

The legacy `AcceptFormat` enum maps to an `Accept` header:

```csharp
// Legacy: AcceptFormat = JSON
// Modern: add an Accept header
var options = HttpRequestOptions.ForGet(url)
    .WithHeader("Accept", "application/json");
```

If `AcceptFormat = CUSTOM`, the user's `Headers["Accept"]` (case-insensitive) value is already in the headers dictionary and will carry over naturally.

If `AcceptFormat = ANY`, the legacy activity sends `*/*`. The modern activity sends no `Accept` header by default, which servers treat as `*/*`. Typically safe to omit, but include `*/*` explicitly if the server is sensitive to it.

---

## Phase 2 — Generate the coded workflow

### Goal

Produce a coded workflow that calls the same URL with the same method, headers, body, and authentication — using `IHttpService` and `HttpRequestOptions`.

### Strategy

Always enable `SaveRawRequestResponse` so the agent can inspect the actual wire-level request and response for debugging:

```csharp
options.ResponseOptions.SaveRawRequestResponse = true;
```

Always set `ContinueOnError = true` during migration testing so failures return diagnostic info instead of throwing:

```csharp
options.ContinueOnError = true;
```

### Template — Simple GET migration

```csharp
// Legacy: HttpClient activity with Method=GET, EndPoint="https://api.example.com/data",
//         AcceptFormat=JSON, TimeoutMS=6000

var options = HttpRequestOptions.ForGet("https://api.example.com/data")
    .WithHeader("Accept", "application/json")
    .WithTimeout(6000);
options.ContinueOnError = true;
options.ResponseOptions.SaveRawRequestResponse = true;

var response = await http.SendRequestAsync(options);
```

### Template — POST with JSON body migration

```csharp
// Legacy: Method=POST, EndPoint="https://api.example.com/items",
//         BodyFormat="application/json", Body=jsonString, AcceptFormat=JSON

var options = HttpRequestOptions.ForPost("https://api.example.com/items")
    .WithJsonBody(jsonString)
    .WithHeader("Accept", "application/json")
    .WithTimeout(6000);
options.ContinueOnError = true;
options.ResponseOptions.SaveRawRequestResponse = true;

var response = await http.SendRequestAsync(options);
```

### Template — POST with XML body migration

```csharp
// Legacy: Method=POST, BodyFormat="application/xml", Body=xmlString

var options = HttpRequestOptions.ForPost("https://api.example.com/endpoint")
    .WithTextBody(xmlString, "application/xml")
    .WithTimeout(6000);
options.ContinueOnError = true;
options.ResponseOptions.SaveRawRequestResponse = true;

var response = await http.SendRequestAsync(options);
```

### Template — Basic auth migration

```csharp
// Legacy: Username="user", Password="pass"

var options = HttpRequestOptions.ForGet("https://api.example.com/secure")
    .WithBasicAuth("user", "pass")
    .WithTimeout(6000);
options.ContinueOnError = true;
options.ResponseOptions.SaveRawRequestResponse = true;

var response = await http.SendRequestAsync(options);
```

### Template — OAuth2 Bearer token migration

```csharp
// Legacy: OAuth2Token = bearerToken

var options = HttpRequestOptions.ForGet("https://api.example.com/protected")
    .WithBearerToken(bearerToken)
    .WithTimeout(6000);
options.ContinueOnError = true;
options.ResponseOptions.SaveRawRequestResponse = true;

var response = await http.SendRequestAsync(options);
```

### Template — File download migration

```csharp
// Legacy: ResourcePath = @"C:\downloads\report.pdf"

var options = HttpRequestOptions.ForGet("https://api.example.com/reports/latest")
    .WithFileDownload(targetFolder: @"C:\downloads", fileName: "report.pdf")
    .WithTimeout(6000);
options.ContinueOnError = true;
options.ResponseOptions.SaveRawRequestResponse = true;

var response = await http.SendRequestAsync(options);
if (response.HasFile())
{
    // response.File contains the saved ILocalResource
}
```

### Template — Multipart with attachments migration

```csharp
// Legacy: Attachments = { "file1": @"C:\docs\a.pdf", "file2": @"C:\docs\b.pdf" }
//         Body = metadataJson, BodyFormat = "application/json"

var parts = new List<FormDataPart>
{
    new TextFormDataPart(metadataJson, "metadata", "application/json"),
    new FileFormDataPart(@"C:\docs\a.pdf", "file1"),
    new FileFormDataPart(@"C:\docs\b.pdf", "file2"),
};

var response = await http.PostMultipartAsync("https://api.example.com/upload", parts);
```

### Template — UrlSegments migration

```csharp
// Legacy: EndPoint = "https://api.example.com/users/{userId}/orders/{orderId}"
//         UrlSegments = { "userId": "123", "orderId": "456" }

// Inline the segments into the URL
var url = $"https://api.example.com/users/{userId}/orders/{orderId}";
var options = HttpRequestOptions.ForGet(url)
    .WithTimeout(6000);
options.ContinueOnError = true;
options.ResponseOptions.SaveRawRequestResponse = true;

var response = await http.SendRequestAsync(options);
```

---

## Phase 3 — Execute and compare

### Goal

Run the modern activity and compare its output against the legacy baseline. Use `RawRequestDebuggingInfo` to diagnose differences.

### Create or update `learnings.md`

If this is the first activity being migrated in this project, create `learnings.md` in the project directory. If it already exists, read it before proceeding — prior learnings may prevent repeated mistakes.

See [learnings.md format](#learningsmd-format) for the file structure.

### Side-effect gate

If the method is POST, PUT, DELETE, or PATCH:
- **Do not execute the request** without user confirmation.
- Remind the user that this will hit the server and may modify data.
- Suggest using a test/sandbox environment if available.
- If the user declines execution, accept the Phase 1 mapping as-is and skip to Phase 4 (mark comparison as "unverified" in `learnings.md`).

### Comparison strategy

```
execute modern request
compare status code with legacy baseline
compare response body with legacy baseline
if match → migration successful
if mismatch → diagnose using debug info → adjust → retry
```

### Comparison criteria

| Aspect | Match condition | Common mismatch causes |
| --- | --- | --- |
| **Status code** | Same numeric value | Different default headers, missing auth, different content type |
| **Response body** | Semantically equivalent (same JSON/XML structure and values) | Encoding differences, whitespace changes, header-driven content negotiation |
| **Response headers** | Key headers match (Content-Type, Set-Cookie, etc.) | Header casing differences (cosmetic, usually safe to ignore) |

### Using RawRequestDebuggingInfo for diagnosis

Enable via `options.ResponseOptions.SaveRawRequestResponse = true`, then inspect `response.RawRequestDebuggingInfo`.

The debug dump contains sections that help diagnose divergences:

1. **Request headers** — Compare the headers sent by the modern activity against what RestSharp would have sent. Look for:
   - Missing `Accept` header (legacy had `AcceptFormat` which added it automatically).
   - Different `Content-Type` (RestSharp may have added charset or boundary differently).
   - Missing `User-Agent` (RestSharp sends `RestSharp/{version}` by default; .NET HttpClient does not).

2. **Request body preview** — Verify the body content, encoding, and content type match the legacy request.

3. **Response headers** — Check for `Set-Cookie`, `Location`, `WWW-Authenticate` that indicate the server responded differently.

4. **Retry history** — The modern activity retries by default (3 attempts on 5xx/408/429). The legacy activity does **not** retry. If the server is flaky, the modern activity may succeed where legacy failed (or vice versa). Set `RetryPolicyType = None` during comparison testing to match legacy behavior:

```csharp
options.RetryPolicy = new RetryPolicyOptions { Type = RetryPolicyType.None };
```

### Diagnosis table

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| **Different status code** (e.g., legacy 200, modern 406) | Missing `Accept` header | Add `.WithHeader("Accept", "application/json")` (or the value from legacy's `AcceptFormat`) |
| **Different status code** (e.g., legacy 200, modern 415) | Wrong `Content-Type` on request body | Check `TextPayloadContentType` matches legacy `BodyFormat`. Inspect debug dump's request headers. |
| **Different status code** (e.g., legacy 200, modern 400) | Body encoding difference | RestSharp may encode form parameters differently. Check if `Parameters` in legacy were sent as query strings or form body (RestSharp puts them in the body for POST). See [Parameters as body](#parameters-as-post-body). |
| **Different status code** (e.g., legacy 200, modern 401) | Auth header format difference | Compare `Authorization` header scheme in debug dump. RestSharp's Basic auth may differ in whitespace or encoding. |
| **Same status code but different body** | Content negotiation — server returns different format based on `Accept` | Ensure `Accept` header matches exactly. |
| **Same status code but different body** | Decompression difference | Modern activity auto-decompresses gzip/deflate/brotli. Legacy may return compressed data in `Result`. The decompressed content should be semantically equivalent. |
| **Legacy returned file, modern returns text** | Response classification differs | If legacy used `ResourcePath` to force file save, set `SaveResponseAsFile = true` and configure `OutputFileTargetFolder`/`OutputFileName`. |
| **Modern retries but legacy didn't** | Modern has retries enabled by default | Set `RetryPolicyType = None` to match legacy behavior, or keep retries for improved reliability. |
| **Modern follows redirects differently** | Modern follows 3 redirects; legacy follows all | Increase `MaxRedirects` if needed, or set `FollowRedirects = false` to match legacy behavior when legacy didn't follow. |
| **Timeout difference** | Legacy defaults to 6000 ms, modern to 10000 ms | Set `TimeoutInMiliseconds` to the legacy value. |

### Parameters as POST body

**Critical behavioral difference:** RestSharp sends `Parameters` in the request **body** (as form-urlencoded) for POST/PUT/PATCH requests when no explicit body is set. The modern activity **always** sends `Parameters` as query string parameters regardless of method.

If the legacy activity uses `Parameters` with a POST method and no `Body`:
- The server likely expects form-urlencoded body content.
- Migrate `Parameters` to `FormData` with `RequestBodyType = FormUrlEncoded`:

```csharp
// Legacy: Method=POST, Parameters = { "key1": "value1", "key2": "value2" }
// (RestSharp sends these as form-urlencoded body)

// Modern: use FormData instead
var formData = new Dictionary<string, string>
{
    { "key1", "value1" },
    { "key2", "value2" }
};
var response = await http.PostFormAsync("https://api.example.com/endpoint", formData);
```

---

## Phase 4 — Handle output mapping

### Goal

Map the modern activity's `HttpResponseSummary` output back to the variables the workflow expects, matching the legacy output shape.

### Output mapping table

| Legacy output | Type | Modern equivalent | Access pattern |
| --- | --- | --- | --- |
| `Result` | `String` | `response.TextContent` | Direct. Note: legacy always returns the response body as a string regardless of content type. Modern classifies responses and may populate `BinaryContent` or `File` instead. For text responses, `TextContent` is equivalent. |
| `StatusCode` | `Int32` | `response.GetStatusCodeNumber()` | Extension method returns `int`. Or cast: `(int)response.StatusCode`. |
| `ResponseHeaders` | `Dict<string, string>` | `response.Headers` + `response.ContentHeaders` | Modern separates response headers and content headers. Merge if needed: `response.Headers.Concat(response.ContentHeaders).ToDictionary(...)`. |
| `ResponseAttachment` | `ILocalResource` | `response.File` | Available when response is classified as file or `SaveResponseAsFile = true`. |

### Code example — reproducing legacy output shape

```csharp
var response = await http.SendRequestAsync(options);

// Equivalent to legacy Result
string result = response.TextContent;

// Equivalent to legacy StatusCode
int statusCode = response.GetStatusCodeNumber();

// Equivalent to legacy ResponseHeaders (merged)
var responseHeaders = new Dictionary<string, string>();
if (response.Headers != null)
{
    foreach (var h in response.Headers)
        responseHeaders[h.Key] = h.Value;
}
if (response.ContentHeaders != null)
{
    foreach (var h in response.ContentHeaders)
        responseHeaders[h.Key] = h.Value;
}

// Equivalent to legacy ResponseAttachment
var responseAttachment = response.File;
```

---

## Phase 5 — Finalize and clean up

### Goal

Once the modern activity produces equivalent output, finalize the migration.

### Checklist

1. **Remove debug settings** — Set `SaveRawRequestResponse = false` (or remove the line) unless the user wants debug output in production.
2. **Decide on ContinueOnError** — The legacy default was `false` (throw on error). The modern default is `true` (return synthetic 503). Set to match the user's intent, not the legacy default.
3. **Decide on retries** — Legacy had no retry mechanism. Modern retries 3 times by default on 5xx/408/429. Keep retries for improved reliability, or set `RetryPolicyType = None` to match legacy behavior exactly.
4. **Decide on timeout** — If the user had a specific `TimeoutMS`, carry it forward. Otherwise, the modern default (10s) is more generous than legacy (6s).
5. **Confirm with the user** — Present the final migrated code and ask for explicit confirmation before removing the old activity.
6. **Remove the legacy activity** from the workflow — only after user confirmation. If in a UI workflow, the activity was disabled in Phase 2; now delete it.
7. **Update downstream logic** — If the workflow inspects `Result` (string), switch to `response.TextContent`. If it checks `StatusCode` (int), switch to `response.GetStatusCodeNumber()`.
8. **Update `learnings.md`** — Append an entry for this activity recording the mapping decisions, any fixes discovered during Phase 3, and whether comparison was verified or unverified.

### If migration failed

Follow [rollback guidance](#8-rollback-guidance): re-enable the legacy activity, remove the modern replacement, record the failure in `learnings.md`, and inform the user.

---

## Summary — Agent decision flow

```
User identifies legacy HTTP Request activity
       │
       ▼
  ┌─ SAFETY GATE ─────────────────────────────────────────┐
  │ 1. Remind user to back up the project                 │
  │ 2. Inventory all legacy activities                    │
  │ 3. Propose migration plan (GET first, then mutating)  │
  │ 4. Read learnings.md if it exists                     │
  │ 5. Wait for user confirmation                         │
  └───────────────────────────────────────────────────────┘
       │
       ▼
  Phase 0: Capture legacy baseline (or accept user-provided outputs)
       │  ⚠ If POST/PUT/DELETE/PATCH → warn about side effects
       │
       ▼
  Phase 1: Map inputs using static mapping table
       │
       ├── OAuth 1.0 used? ──────────────► Warn user, offer manual header or stop
       ├── MERGE method? ────────────────► Suggest PATCH or stop
       ├── UrlSegments? ─────────────────► Inline into URL
       ├── Parameters as POST body? ─────► Migrate to FormData
       └── All inputs mapped ────────────► Continue
       │
       ▼
  ┌─ USER CHECKPOINT ─┐
  │ Show mapping,      │
  │ ask to confirm     │
  └────────────────────┘
       │
       ▼
  Phase 2: Generate coded workflow with HttpRequestOptions
       │  (legacy activity disabled, not deleted)
       │
       ▼
  Phase 3: Execute with SaveRawRequestResponse = true
       │  ⚠ If mutating method → confirm with user before executing
       │  📝 Create/read learnings.md
       │
       ├── Status code matches? ──► Compare response body
       │       ├── Body matches? ──► Phase 4: Map outputs
       │       └── Body differs? ──► Diagnose with debug info → adjust → retry
       └── Status code differs? ──► Diagnose with debug info → adjust → retry
       │
       ▼
  ┌─ USER CHECKPOINT ─┐
  │ Show comparison    │
  │ results, ask to    │
  │ confirm            │
  └────────────────────┘
       │
       ▼
  Phase 4: Map outputs to legacy shape
       │
       ▼
  ┌─ USER CHECKPOINT ─┐
  │ Confirm before     │
  │ removing old       │
  │ activity           │
  └────────────────────┘
       │
       ▼
  Phase 5: Finalize (remove debug, delete old activity, update learnings.md)
       │
       ├── Success ──► Update learnings.md ──► Next activity (repeat from Phase 0)
       └── Failure ──► Rollback, record in learnings.md, inform user
```

## Known behavioral differences

This section documents differences between RestSharp (legacy) and .NET HttpClient (modern) that **cannot** be eliminated by input mapping alone. The agent should be aware of these and inform the user when they are relevant.

| Behavior | Legacy (RestSharp) | Modern (.NET HttpClient) | Impact |
| --- | --- | --- | --- |
| **Default User-Agent** | `RestSharp/{version}` | None | Some servers check User-Agent. Add `.WithHeader("User-Agent", "...")` if the server rejects requests without it. |
| **Default Accept header** | Depends on `AcceptFormat` enum; `ANY` sends a long multi-type accept string | No Accept header unless explicitly set | Servers that require `Accept` will return 406 Not Acceptable. Always map `AcceptFormat` to an explicit header. |
| **POST parameters** | Sent as form-urlencoded body | Sent as query string parameters | See [Parameters as POST body](#parameters-as-post-body). This is the most common migration-breaking difference. |
| **Cookie format** | Parses `name=value;name2=value2` from dictionary values | Flat `Dictionary<string, string>` key-value pairs | Flatten cookie strings before mapping. |
| **Redirect following** | Follows all redirects | Follows up to `MaxRedirects` (default 3) | Increase `MaxRedirects` for deeply redirecting URLs. |
| **Timeout** | Default 6000 ms | Default 10000 ms | Carry forward the legacy value to preserve timing behavior. |
| **Error handling** | `ContinueOnError` default false; throws exceptions | `ContinueOnError` default true; returns synthetic 503 | Set to match legacy behavior during migration. |
| **Retries** | None | 3 retries on 5xx/408/429 by default | Set `RetryPolicyType = None` for exact behavioral parity, or keep for reliability. |
| **SSL certificate path** | Looks up by path or subject name | Same — looks up by path or Windows Root store subject name | No change needed. |
| **Response body** | Always returned as string in `Result` | Classified: text → `TextContent`, binary → `BinaryContent`, file → `File` | For text APIs, `TextContent` is equivalent. For file downloads, use `response.File`. |
| **Decompression** | Depends on RestSharp version/config | Always decompresses gzip/deflate/brotli | Decompressed content should be equivalent. |
| **OAuth 1.0** | Supported via RestSharp authenticator | Not supported | Must construct Authorization header manually or use OAuth 2.0. |

## `learnings.md` format

The `learnings.md` file lives in the project directory and is maintained across activity migrations.

```markdown
# HTTP Request Migration Learnings

This file is auto-maintained by the migration agent. It records decisions and
discoveries from each activity migration so subsequent migrations can reuse them.

## Global learnings

<!-- Patterns that apply to all activities in this workflow -->
- (example) This server requires `Accept: application/json` header or returns 406.
- (example) Parameters on POST must be sent as form body, not query string.

## Activity migrations

### Activity 1: GET /api/users (DisplayName: "Fetch Users")
- **Status:** verified ✅
- **Date:** 2024-01-15
- **Mapping notes:** AcceptFormat=JSON → WithHeader("Accept", "application/json")
- **Fixes during comparison:** Added User-Agent header — server returned 403 without it.
- **Learnings for next activities:** Always include User-Agent for this server.

### Activity 2: POST /api/orders (DisplayName: "Create Order")
- **Status:** unverified ⚠️ (mutating method, user declined runtime comparison)
- **Date:** 2024-01-15
- **Mapping notes:** Parameters migrated to FormData (POST body). BodyFormat="application/json" → WithJsonBody().
- **Fixes during comparison:** N/A — not executed.
- **Learnings for next activities:** Same FormData pattern likely needed for other POST activities.
```

Rules:
- **Never delete entries** — append only.
- **Global learnings** accumulate patterns that apply across activities.
- **Each activity entry** records status (verified/unverified/failed), mapping decisions, fixes, and forward-looking learnings.
- The agent must **read the entire file** before starting each new activity migration.

## See Also

- [NetHttpRequest Activity](../../UiPath.Web.Activities.Package.Design/docs/activities/NetHttpRequest.md) — modern HTTP activity behavior spec, inputs, outputs, and defaults
- [HttpClient Activity (Legacy)](../../UiPath.Web.Activities.Package.Design/docs/activities/HttpClient.md) — legacy HTTP activity reference
- [cURL Import Skills](curl-import.md) — converting raw cURL commands to HttpRequestOptions
- [Service Discovery](service-discovery.md) — discovering unknown service endpoints and generating working requests
