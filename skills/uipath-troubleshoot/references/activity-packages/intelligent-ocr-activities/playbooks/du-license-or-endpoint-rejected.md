---
confidence: medium
---

# Document Understanding — License or endpoint rejected the call

## Context

A DU activity (`Digitize Document`, `Data Extraction Scope`, `Classify Document Scope`) faults when its call to the Document Understanding OCR / server endpoint is rejected. There are **two distinct error shapes** depending on which DU client made the call — match the one you see:

**A. `Digitize Document` via the UiPath Document OCR engine** (the common case). The fault is a `System.AggregateException` (the OCR call runs async), and the inner message carries the DU OCR server's response verbatim. Verified signature for an invalid API key:

```
System.AggregateException
Message: One or more errors occurred. (Request CorrelationId: <guid>
Request PredictionId: <id>
Server response: Invalid API key specified Error:UiPathOCRInvalidApiKey CF-RAY: <ray>. AppId: )
   at UiPath.DocumentUnderstanding.Digitizer.Digitization.PageDigitizer.ApplyOcr(...)
   at UiPath.IntelligentOCR.Activities.Digitization.DigitizeDocument.ExecuteAsync(...)
```

The `Server response:` line + `Error:UiPathOCRInvalidApiKey` is the discriminator — the configured **UiPath Document OCR `ApiKey`** is wrong/expired/empty. Related OCR-engine server errors surface the same way (`Server response: <detail> Error:<code>`).

**B. `UiPath.SmartData.Utils.DocumentUnderstandingClient.DUApiException`** (SmartData/`DUServerCaller` client path — extraction/classification/tenant calls). Carries the HTTP status, response content, `CF-RAY`, `AppId`. Verbatim messages by status:

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
- For **`Digitize Document`**, the fault is a `System.AggregateException` whose message contains `Server response: ... Error:<code>` — read that server response, not the generic `One or more errors occurred.` wrapper. `Error:UiPathOCRInvalidApiKey` = bad UiPath Document OCR `ApiKey`.
- For the **`DUApiException`** path, the connection reached the server; the **HTTP status + message** name the cause. Capture `CF-RAY` and `AppId` for escalation.

> **Different cause — do not apply this playbook:**
> - `Failed to fetch Document Understanding projects list...` / `Couldn't retrieve a tenant key.` → DU not enabled / tenant setup, before an endpoint call → use [du-not-enabled-or-tenant-key.md](./du-not-enabled-or-tenant-key.md).
> - `No such bucket ...` / `Could not load the ... from storage bucket ...` → storage/taxonomy access → use [du-storage-or-taxonomy-missing.md](./du-storage-or-taxonomy-missing.md).

## Investigation

1. **Identify the error shape.** `System.AggregateException` with `Server response: ... Error:<code>` from `PageDigitizer.ApplyOcr` → the UiPath Document OCR engine (Digitize). `DUApiException` with an HTTP status → the SmartData DU client. Read the inner `Server response:` / message, not the `AggregateException` wrapper.
2. **Map the code/status to its cause** (`UiPathOCRInvalidApiKey` = bad OCR ApiKey; 401 license/key, 403 units, 413 size, 400 endpoint/key, signature-invalid, 5xx server).
3. **For 401/400**, capture which endpoint and API-key parameter the activity is configured with (don't expose the key value).
4. **For 5xx / generic**, check the failure window for a transient DU-service outage.

## Resolution

- **If `Server response: Invalid API key specified Error:UiPathOCRInvalidApiKey` (Digitize / UiPath Document OCR):** set a valid **UiPath Document OCR `ApiKey`** (copy the tenant's Document Understanding API key from Automation Cloud → Licenses → Consumables → AI Units; re-enter it on the OCR engine). Store it as a secure asset/credential.
- **If 401 `Your license could not be validated...` (`DUApiException`):** correct the API key / license parameter for this endpoint (re-enter the key; confirm it's valid for the targeted DU endpoint).
- **If 403 `Failed to consume the requested number of pages...`:** top up / fix the license units, or confirm the tenant is entitled for the volume.
- **If 413 `You have exceeded the request size limitations...`:** reduce the document/request size (split the document, lower DPI/page count) or move to a plan that allows it.
- **If 400 `The service has rejected the request...` / `Response signature is invalid. Endpoint is not supported.`:** point the activity at the correct DU endpoint for its operation and verify the API key.
- **If generic 5xx `DocumentUnderstanding server returned ...`:** retry transient failures; if persistent, escalate to the DU service with the `CF-RAY` and `AppId`.
