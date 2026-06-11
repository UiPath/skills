# Microsoft Office 365 Activities Investigation Guide

## Data Correlation

Before using any fetched data, verify it matches the user's reported problem:

- **Activity** — the faulted activity's namespace and class match the reported failure (e.g., `UiPath.MicrosoftOffice365.Activities.Mail.MoveEmailConnections`). Modern connections activities and legacy activities (`MoveMail`, `DownloadFile`, `CreateFolder`, `UploadFile`, `CreateWorkbook`, `AddSheet`) sometimes share display names but run different code paths — treat them as different.
- **Connection / Microsoft 365 account** — the Integration Service connection in evidence authenticates against the same Microsoft 365 user principal the user is asking about. Different connections = different mailboxes, different OneDrive scopes, different SharePoint sites = unrelated data.
- **Mailbox in scope** — for Mail activities, confirm the resolved mailbox is the one the user is asking about. The same connection can target the user's own mailbox, a shared mailbox, or a delegated mailbox via the activity argument; Outlook IDs are mailbox-scoped, so an item that resolves in one mailbox will not resolve in another.
- **Target resource** — the resource identifier in evidence matches the one the user reports: mail folder ID or path, message ID, OneDrive/SharePoint item ID or URL or drive-relative path, drive ID, SharePoint site URL plus document library, workbook file name, sheet name. Don't substitute a similarly-named resource.
- **Workflow file** — if the project contains multiple workflows, the error originates from the workflow the user is asking about, not a different `.xaml` / `.cs` that happens to use the same activity.
- **Timestamp** — the failure occurred during the time window the user reported. Load-bearing for filter-based Mail activities (only messages received at or before the run time are eligible), and for any investigation where the user may have moved, renamed, or deleted the target resource between runs.

If the data doesn't match: **discard it**. Do NOT use unrelated data as a proxy. Report the mismatch and ask for clarification.

## Domain-Specific Data Gathering

1. **Activity execution traces** — these activities emit per-call traces. Pull them when available — they expose the exact Microsoft Graph endpoint hit, request/response status, and timing. Trace evidence narrows whether the failure originated at connection resolution, OAuth token validation, the Graph call, or post-processing inside the activity.

## Cross-Cutting Error Classes

Many Microsoft Office 365 failures are **not specific to one activity** — they come from the shared authentication + Microsoft Graph layer and can surface from *any* Mail / Files / Excel activity. The user-visible text is keyed off the **Microsoft Graph error code, not the HTTP status**: some codes surface a fixed UiPath message, others surface the raw Graph message verbatim. So **match on the message text**, and when the class is cross-cutting, investigate the connection / permission / rate / configuration rather than over-focusing on the faulted activity's own arguments.

Route by message:

- Token / `AADSTS` / `not authenticated` / cancelled login / `No default connection` / `Automation Cloud cannot be reached` → [authentication-token-invalid](./playbooks/authentication-token-invalid.md) (401).
- `The caller doesn't have permission ...` / `Access restricted to the item's owner.` / raw `Insufficient privileges ...` → [insufficient-graph-scope](./playbooks/insufficient-graph-scope.md) (403). Note Graph may instead return **404** for unauthorized cross-mailbox/shared access — that path is the not-found playbooks.
- `Too many requests.` / `The app or user has been throttled.` / batched 429 → [request-throttled](./playbooks/request-throttled.md) (429).
- `The server is unable to process the current request.` / `Request time out.` / 500 / 504 / batched 5xx → [transient-service-error](./playbooks/transient-service-error.md).
- Faults **before any Graph call** (`Could not retrieve the selected asset`, `You must provide a value for ...`, `Please select an account.`, placement errors) → [application-scope-misconfigured](./playbooks/application-scope-misconfigured.md).

## Testing Prerequisites

When testing hypotheses for Microsoft Office 365 Activities issues, gather and verify these before drawing conclusions:

1. **Activity identity** — capture both the class name and the display name from the workflow source or stack trace. Distinguish modern `*Connections` activities from legacy equivalents.
2. **Target Microsoft 365 service** — identify whether the call lands on Outlook (Mail), OneDrive, SharePoint document libraries, Excel, Outlook Calendar, or SharePoint Lists. The same Microsoft Graph status code (404 / 403 / 409) surfaces with different wording and different remediation per service.
3. **Connection target** — capture the Integration Service connection name and the underlying Microsoft 365 user principal name (UPN) it authenticates as. For shared mailbox or SharePoint operations, also capture which mailbox / site / document library is in scope.
4. **Activity input properties** — capture every input property the activity uses to address its target, from the workflow source (not from a summary): filter collections, `ConflictBehavior` / `ConflictResolution`, `MailFolder` argument (ID or path), `CreateFolderIfMissing`, target identifiers (ID / URL / path / browse selection), `UseDriveCard` / `DriveId`, source local paths, attachment names. The playbook the agent is following will name the subset that matters.
5. **Mailbox / drive resolution evidence** — for Mail activities, capture the `Account` argument value and the resolved mailbox UPN. For Files activities, capture the resolved `DriveId` plus, for SharePoint, the site URL and document library name. Failures one tier above the item (drive-not-found, site-not-found, shared-item-not-found) are diagnosed differently from item-not-found.
6. **Job run timestamp** — exact time the activity executed. Required for filter-based Mail investigations (mailbox state at run time), for trigger debug/healing sample replays, and for any investigation where the target resource may have been deleted, moved, or renamed between authoring and execution.
7. **Package version** — `UiPath.MicrosoftOffice365.Activities` version. Behavior, exception messages, supported `ConflictBehavior` / `ConflictResolution` values, and the wrapping form of resource-not-found errors have shifted across versions; version-specific bugs are documented in playbooks as they're discovered.
