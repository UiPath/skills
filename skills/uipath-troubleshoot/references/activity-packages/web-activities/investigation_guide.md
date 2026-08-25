# Web Activities Investigation Guide

## Data Correlation

Before using any fetched data, verify it matches the user's reported problem:

- **Activity class** — the faulted activity is the one the user is asking about. `HttpClient` (legacy) and `NetHttpRequest` (modern) both make HTTP calls but fail differently (`WebException` / `TimeoutException` vs `AggregateException`). `DeserializeJson`, `DeserializeJsonArray`, and `DeserializeXml` share the "JSON/XML string" input display name but run different parsers. Treat them as different.
- **Exception class** — the exception type plus the faulted activity is the primary discriminator (these activities do not wrap exceptions). Read it from `JobError.Type` / the `Info` stack, not from a paraphrase.
- **Endpoint / target** — for HTTP, the request URL in evidence is the one the user reports. A failure against a different host or path is unrelated data.
- **Workflow file** — if the project has multiple workflows, the error originates from the workflow the user asks about, not another `.xaml` / `.cs` that uses the same activity.
- **Timestamp** — the failure occurred in the window the user reported. Load-bearing when an endpoint had a transient outage or the payload source changed between runs.

If the data doesn't match: **discard it.** Do not use unrelated data as a proxy. Report the mismatch and ask for clarification.

## Domain-Specific Data Gathering

1. **Job logs and stack** — `uip or jobs get <job-key> --output json` → `Info` and `JobError` carry the exception class, message, faulted activity name, and `WorkflowFilePath`. `uip or jobs logs <job-key> --level Error --output json` carries the activity-level error line.
2. **Execution traces** — `uip or jobs traces <job-key> --output json` AND `uip traces spans get --job-key <job-key> --output json`. Activity spans expose the request URL, HTTP status, and timing — they narrow whether an HTTP failure was a non-success status, a transport error, or a timeout, and whether a deserialize failure followed a prior HTTP activity in the same run.
3. **Workflow source** — open the faulted `.xaml`/`.cs` to read how the failing input is supplied (literal vs variable, and which upstream activity produced that variable).

## Testing Prerequisites

Gather and verify these before drawing conclusions:

1. **Activity identity** — class name and display name from the workflow source or stack trace (`HttpClient` vs `NetHttpRequest` vs which Deserialize).
2. **Exception class + message** — verbatim, including the first stack frame. The message body (HTTP status code, `line N, position M`, parameter name) selects the cause branch.
3. **HTTP request configuration** (HTTP activities) — `EndPoint` / `RequestUrl` value, `Method`, `TimeoutMS` / `TimeoutInMiliseconds`, `ContinueOnError`, auth type, and whether SSL verification is on. Capture from the workflow source, not a summary.
4. **Deserialize input source** (Deserialize activities) — **the single most decisive signal.** Determine whether the `JsonString` / `XMLString` input is a literal, a workflow variable, or the `Result` / body output of an upstream `HttpClient` / `NetHttpRequest`. A malformed-payload or null-payload fault whose input comes from an upstream HTTP activity is usually a **symptom** of that HTTP call returning an error page, an empty body, or a non-success response — diagnose the HTTP call, not the parser.
5. **`AggregateException` inner exceptions** (`NetHttpRequest`) — unwrap `InnerException` / `InnerExceptions`. The inner type (`HttpRequestException`, `TaskCanceledException`, `WebException`) is the real cause; the `AggregateException` itself is only the wrapper.
6. **Package version** — `UiPath.Web.Activities` version. Default timeouts, retry behavior, and `ContinueOnError` defaults differ between `HttpClient` (legacy) and `NetHttpRequest` (modern) and have shifted across versions.
