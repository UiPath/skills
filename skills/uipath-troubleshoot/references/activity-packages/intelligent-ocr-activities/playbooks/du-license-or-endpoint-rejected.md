---
confidence: medium
---

# Document Understanding — License or endpoint rejected the call

## Context

A DU activity (`Digitize Document`, `Data Extraction Scope`, `Classify Document Scope`) faults when its HTTP call to the Document Understanding server / endpoint is rejected. The exception is `UiPath.SmartData.Utils.DocumentUnderstandingClient.DUApiException`, which carries the HTTP status, the server response content, `CF-RAY`, and `AppId`. The HTTP status is the discriminator.

What this looks like — `DUApiException` with one of these verbatim messages:

- `Your license could not be validated. Please make sure that the API key parameter is correctly configured.` (HTTP **401**) — the API key / license parameter is missing, wrong, or not valid for this endpoint.
- `Failed to consume the requested number of pages. Please check that your license key is valid and has enough units available.` (HTTP **403**) — the license is valid but out of page units / not entitled for the volume.
- `You have exceeded the request size limitations of the currently used plan.` (HTTP **413**) — the document/request is larger than the plan allows.
- `The service has rejected the request. Please make sure you are using the correct endpoint for the activity and that the API key parameter is correctly configured.` (HTTP **400**) — wrong endpoint for the activity, or a malformed/misconfigured API key.
- `Response signature is invalid. Endpoint is not supported.` — the endpoint responded but isn't a supported DU endpoint.
- `DocumentUnderstanding server returned <code> (<reason>). Additional details: <content>. CF-RAY: <cfray>. AppId: <appId>` — generic; any other non-success status (incl. 5xx — server-side / transient).
- `Failed to parse response.` — the server response couldn't be parsed (often downstream of one of the above).

What can cause it:
- **API key / license misconfigured** (401/400) — the key parameter is empty/wrong, or doesn't match the endpoint.
- **Out of units / not entitled** (403) — the license ran out of page units or lacks entitlement.
- **Request too large** (413) — document exceeds the plan's size limit.
- **Wrong / unsupported endpoint** (400 / signature-invalid) — the activity points at the wrong endpoint for its operation.
- **Server-side / transient** (5xx generic) — the DU service had a temporary failure.

What to look for:
- The exception **type is `DUApiException`** — the connection to the DU service succeeded enough to get an HTTP response; the **HTTP status + message** name the cause. Capture `CF-RAY` and `AppId` for escalation.

> **Different cause — do not apply this playbook:**
> - `Failed to fetch Document Understanding projects list...` / `Couldn't retrieve a tenant key.` → DU not enabled / tenant setup, before an endpoint call → use [du-not-enabled-or-tenant-key.md](./du-not-enabled-or-tenant-key.md).
> - `No such bucket ...` / `Could not load the ... from storage bucket ...` → storage/taxonomy access → use [du-storage-or-taxonomy-missing.md](./du-storage-or-taxonomy-missing.md).

## Investigation

1. **Confirm the exception is `DUApiException`** and read the HTTP status + message; capture `CF-RAY`, `AppId`, and `HttpResponseContent`.
2. **Map the status to its cause** (401 license/key, 403 units, 413 size, 400 endpoint/key, signature-invalid, 5xx server).
3. **For 401/400**, capture which endpoint and API-key parameter the activity is configured with (don't expose the key value).
4. **For 5xx / generic**, check the failure window for a transient DU-service outage.

## Resolution

- **If 401 `Your license could not be validated...`:** correct the API key / license parameter for this endpoint (re-enter the key; confirm it's valid for the targeted DU endpoint).
- **If 403 `Failed to consume the requested number of pages...`:** top up / fix the license units, or confirm the tenant is entitled for the volume.
- **If 413 `You have exceeded the request size limitations...`:** reduce the document/request size (split the document, lower DPI/page count) or move to a plan that allows it.
- **If 400 `The service has rejected the request...` / `Response signature is invalid. Endpoint is not supported.`:** point the activity at the correct DU endpoint for its operation and verify the API key.
- **If generic 5xx `DocumentUnderstanding server returned ...`:** retry transient failures; if persistent, escalate to the DU service with the `CF-RAY` and `AppId`.
