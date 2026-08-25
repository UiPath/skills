# Final Resolution

Investigation complete. Here are the findings.

---

# Why your `Data Export` job faulted — Resolution

## Root Cause
The **List Incidents** Integration Service connector activity (ServiceNow) ran an **unbounded list query** and the provider returned more data than Integration Service will marshal in a single response. Integration Service enforces an **8 MB limit for data in JSON format**; the response exceeded it, so the runtime threw **`UiPath.IntegrationService.Activities.Runtime.Exceptions.RuntimeException: Response content too large.`** and the job faulted.

- Domain: Integration Service (root cause)
- Fault bucket: **👤 A — Customer-resolvable** (a query/payload-sizing problem on the customer side, not an IS defect or a provider outage)
- Confidence: High

## What went wrong
- A scheduled unattended job for process **`Data Export`** in folder **`Shared/integration-sync/DataExport`** faulted on **2026-06-30T02:15:52Z** (job id 50301122).
- It ran cleanly (Pending → Running → Faulted in ~10s) and failed inside the workflow at the **List Incidents** activity (`Main.xaml` → Sequence → Main).
- The activity uses the **servicenow-prod** ServiceNow connection to run a `List` on the `incident` object. The provider call **succeeded**, but the response was too large for Integration Service to return.

## Why — the decisive evidence
- The exception message is the verbatim signature: **`Response content too large.`**, thrown by `RuntimeException` on `UiPath.IntegrationService.Activities.Runtime.Activities.ConnectorActivity` (frame `SendRequestClientAsync` — a read/list call).
- **There is NO `ProviderErrorCode` / provider HTTP status** in the error. That is the discriminator: this is **not** a `DAP-RT-1101` provider error (401/403/404/400/429/5xx) and **not** a connection or auth failure. The connection **pings Enabled** ("Connection is active and ready for operations."), so connection resolution and authentication are ruled out.
- The failing operation is a **`List`** (`/table/incident`) with **no bound on the result set** — `uip is resources describe uipath-servicenow incident --operation List` shows the operation exposes `sysparm_query` (filter), `sysparm_limit` / `maxRecords` (row cap), and `sysparm_offset` (paging), none of which were constraining the pull. An unbounded list of a large object blew past the 8 MB JSON ceiling.

## Immediate fix — bound the response under 8 MB

**Narrow the `List Incidents` query so the JSON response stays under the 8 MB limit.**

- **What:** On the List Incidents activity, set **Max records** (`sysparm_limit` / `maxRecords`) to a bounded value and add a query filter (`sysparm_query`, e.g. by `state`, `sys_updated_on` date range, or `assignment_group`) so each run returns only the rows it needs. For large backfills, **page** through the data in batches (increment `sysparm_offset`) instead of pulling everything in one call.
- **Why:** Integration Service enforces an **8 MB limit for data in JSON format**. The response exceeded it. Reducing rows/fields per call keeps every response under the ceiling. (Source: playbook `references/products/integration-service/playbooks/response-content-too-large.md`; UiPath docs — Integration Service Troubleshooting & Limitations.)
- **If the payload is large because of file/attachment bytes:** do **not** carry files inside the JSON body (Base64 fields count against the 8 MB JSON limit). Use the connector's file-handling path so file bytes are passed **outside** JSON — that raises the applicable limit to **1 GB**.
- **Where:** the `List Incidents` connector activity inputs in the `Data Export` project.
- **Who:** the automation owner (a workflow/input change + republish). No admin or provider action is required — the connection and credentials are fine.

After bounding the query, re-run `Data Export` and confirm the List Incidents activity returns within the limit.

## What this is NOT
- **Not** an authentication or credential problem (that would be a provider `401` / `DAP-RT-1101`, or a disabled connection). The connection pings **Enabled**.
- **Not** a connection-resolution failure (`DAP-GE-3000/3005`, `DAP-RT-1002`) — a connection resolved and the call reached ServiceNow.
- **Not** a provider outage or rate-limit (`429`/`5xx`) — no provider status was returned; ServiceNow answered successfully and IS rejected the size.

## Preventive fix
- **Always bound list/search connector activities.** Set Max records and a filter on any IS list/search operation against a large object; default to paging for exports.
- **Keep files out of the JSON payload.** For document/attachment transfers, use the connector's file handling (outside-JSON, 1 GB) rather than inline Base64.
- **Treat `Response content too large` as a sizing signal, not a provider/auth error** — the absence of a `ProviderErrorCode` confirms the call succeeded and only the size failed.

---

## Investigation summary

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|---|---|---|---|---|---|
| H1 | The **List Incidents** ServiceNow activity ran an unbounded `List` and the response exceeded the Integration Service **8 MB JSON limit**, so the runtime threw `RuntimeException: Response content too large` and the job faulted. | High | Confirmed | **Yes** | Verbatim `Response content too large` from `RuntimeException` on `ConnectorActivity "List Incidents"` (read/`SendRequestClientAsync` frame); **no** `ProviderErrorCode`/status; connection **pings Enabled**; `List` operation exposes `sysparm_limit`/`maxRecords`/`sysparm_query` that were not constraining the pull | Set **Max records** + query filter (or page) on the activity to keep the response under 8 MB; pass any file bytes outside JSON (1 GB limit). Re-run. |
