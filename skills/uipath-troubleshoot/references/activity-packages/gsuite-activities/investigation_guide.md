# Google Workspace Activities Investigation Guide

## Data Correlation

Before using any fetched data, verify it matches the user's reported problem:

- **Activity** — the faulted activity's namespace and class match the reported failure (e.g., `UiPath.GSuite.Activities.GetNewestEmailConnections`). Modern `*Connections` activities and legacy classic activities sometimes share display names but run different code paths — treat them as different.
- **Connection / Google account** — the Integration Service connection in evidence authenticates against the same Google account the user is asking about. Different connections = different mailboxes, different Drive scopes, different shared drives = unrelated data.
- **Target resource** — the resource identifier in evidence matches the one the user reports: Gmail mailbox label/folder, Drive file/folder ID or URL, spreadsheet ID, document ID, calendar ID. Don't substitute a similarly-named resource.
- **Workflow file** — if the project contains multiple workflows, the error originates from the workflow the user is asking about, not a different `.xaml` / `.cs` that happens to use the same activity.
- **Timestamp** — the failure occurred during the time window the user reported. Load-bearing for filter-based Gmail activities (only messages received at or before the run time are eligible) and for quota investigations (storage state may have changed since).

If the data doesn't match: **discard it**. Do NOT use unrelated data as a proxy. Report the mismatch and ask for clarification.

## Domain-Specific Data Gathering

1. **Activity execution traces** — these activities emit per-call traces. Pull them when available — they expose the exact Google REST endpoint hit, request/response status, and timing. Trace evidence narrows whether the failure originated at connection resolution, OAuth token validation, the Google API call, or post-processing inside the activity.
2. **Route by status class and exception type, not by the message sentence.** Modern `*Connections` activities wrap most failures into a `GSuiteException` whose *text* is a friendly mapping of the underlying HTTP status — different root causes share similar wording, and one generic message (`An error occurred in the activity.`) hides the real status entirely. Before matching a playbook, read the embedded HTTP status / inner exception from the trace and classify: **401** (token rejected) and **403** (authorization/quota) and auth-phase `TimeoutException` → connection/auth or storage-quota; **404** / unresolved item → resource-not-found; **400** server-side range/cell → the Sheets playbooks; **5xx / 429 / network `HttpRequestException` / per-request `A task was canceled.`** → transient-and-timeout. Note two specific traps: a per-request timeout surfaces as `TaskCanceledException` (`A task was canceled.`), **never** as `System.TimeoutException` (which only comes from authentication); and a client-side `ArgumentException`/`NullReferenceException` (invalid/null input) is thrown before any API call, so it has no HTTP status at all. One more: a raw `ConnectionHttpException` means the failure is at the **Integration Service connection layer** (connection resolution / token fetch), not at the Google API — if its message embeds a `CNS…` code, route by the exact code via the [CNS error-code reference](../../products/integration-service/cns-error-codes-reference.md) (`CNS1008` connection needs re-authentication, `CNS1006`/`CNS1049` deleted / personal-workspace, `CNS1044`/`CNS1045` scope/folder permission, `CNS2xxx` service-side); the code is more precise than the status class.

## Testing Prerequisites

When testing hypotheses for Google Workspace Activities issues, gather and verify these before drawing conclusions:

1. **Activity identity** — capture both the class name and the display name from the workflow source or stack trace. 
2. **Target Google service** — identify whether the call lands on Gmail, Drive, Sheets, Docs, Calendar, Tasks, Forms, or Apps Script. The same Google API status code (404 / 403 / 429) surfaces with different wording and different remediation per service.
3. **Connection target** — capture the Integration Service connection name and the underlying Google account email it authenticates as. For shared-drive operations, also capture which shared drive is in scope.
4. **Activity input properties** — capture every input property the activity uses to address its target, from the workflow source (not from a summary): filter collections, `ConflictResolution`, target identifiers (ID / URL / path / browse selection), `SheetName`, source local paths. The playbook the agent is following will name the subset that matters.
5. **Job run timestamp** — exact time the activity executed. Required for filter-based Gmail investigations (mailbox state at run time) and for upload quota investigations (storage state at time of failure).
6. **Package version** — `UiPath.GSuite.Activities` version. Behavior, exception messages, and supported `ConflictResolution` values have shifted across versions; version-specific bugs are documented in playbooks as they're discovered.
