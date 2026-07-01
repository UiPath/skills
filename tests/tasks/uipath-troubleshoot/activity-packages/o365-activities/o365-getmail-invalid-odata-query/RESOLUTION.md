**Root Cause:** The Get Mail activity's OData `Query` is malformed — it uses natural-language operators instead of OData syntax, so Microsoft Graph rejects the request before reading any mail.

**What went wrong:** The last job in folder Shared — process **ERN_O365_InvalidODataQuery** (job 4b4a58f8-6a7c-4af2-8700-1b6479b51028, 2026-06-10 18:37 UTC, unattended, machine MOCK-HOST) — faulted ~3 seconds in when the legacy **Get Mail** activity sent Microsoft Graph an invalid `$filter`.

**Why:** The activity composes its `$filter` by prepending a date-range clause to the configured `Query`. The configured part — `subject equals 'invoice' and unread is true` — is not valid OData: `equals` is not an OData operator (must be `eq`), and `unread is true` references a property that doesn't exist on the Graph message entity. Graph's parser failed at position 56 (the `equals` token: "`')' or operator expected`") and returned `BadRequest`, surfaced by the legacy activity as a raw `Microsoft.Graph.ServiceException`. Deterministic — fails every run regardless of mailbox content. The raw (unwrapped) ServiceException confirms the legacy (non-Connections) code path.

**Immediate fix:** Correct the `Query` to valid Graph OData — `subject eq 'invoice'` — and use the activity's built-in **Only Unread Messages** option for the unread condition. Validate the corrected filter in Graph Explorer against `/me/messages?$filter=...` before re-running. Source: `references/activity-packages/o365-activities/playbooks/mail-invalid-odata-query.md` § Resolution.

**Preventive fix:** If the query is built dynamically, guard inputs before composing the filter: escape single quotes, format dates as ISO 8601.
