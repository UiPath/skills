# Intelligent OCR / Document Understanding Investigation Guide

## Data Correlation

Before using any fetched data, verify it matches the user's reported problem:

- **Activity** — the faulted activity is a classic DU activity (`UiPath.IntelligentOCR.Activities.DigitizeDocument`, `...ClassifyDocumentScope`, `...DataExtractionScope`, `...PresentValidationStation`, `...ExportExtractionResults`). Modern DU / IXP is a different surface.
- **Tenant / DU endpoint** — the tenant and DU endpoint/API key in evidence are the ones the user is asking about. A different tenant = different DU entitlement and a different storage layout.
- **Storage bucket / folder** — the bucket, blob path, and Orchestrator folder named in the error are the ones the workflow targets.
- **Document** — the document being processed is the one the user reports (matters for size-limit and validation-rejection cases).
- **Workflow file** — the error originates from the workflow the user references.
- **Timestamp** — the failure occurred in the reported window (load-bearing for a transient DU-server outage vs. a config problem).

If the data doesn't match: discard it.

## Domain-Specific Data Gathering

1. **Classify by exception type and message.**
   - `DUApiException` → the **DU server / endpoint** rejected the HTTP call. Read the HTTP status and message: 401 license/API key, 403 page-units, 413 request size, 400 wrong endpoint/API key, signature-invalid, or the generic `DocumentUnderstanding server returned <code> ...`.
   - `Failed to fetch Document Understanding projects list...` / `Couldn't retrieve a tenant key.` / `Information about tenant <id> couldn't be retrieved.` → **tenant not enabled / setup**: DU isn't enabled/licensed on the tenant, or tenant context couldn't be resolved.
   - `No such bucket ...` / `Couldn't find path ...` / `Could not load the ... from storage bucket ...` / `The local directory path ... could not be found.` / `Could not find Orchestrator Folder ...` → **storage / taxonomy / folder** missing.
   - `DocumentRejectedByUserException` → a **human rejected** the document at Validation Station (a business outcome, not a system fault).
2. **For a `DUApiException`, the HTTP status is the discriminator.** The message text is fixed per status — match it (e.g. 401 → `Your license could not be validated...`). Capture `CF-RAY` and `AppId` from the exception for escalation; the `HttpResponseContent` carries the server's detail.
3. **Separate license from connectivity.** 401/403 are entitlement/units; a generic `DocumentUnderstanding server returned 5xx ...` is a server-side/transient failure — check the window.
4. **For storage errors, confirm what's missing and where.** The message names the bucket / blob path / folder — confirm it exists in the tenant/folder the robot runs in and that the robot account can read it.

## Testing Prerequisites

> The invalid-API-key failure occurs on the OCR call itself; tenant-not-enabled / storage / document-rejected failures depend on the DU project / endpoint / storage / HITL setup. Diagnosis is evidence-based from the faulted job.

1. **Activity identity** — which DU activity and its display name.
2. **Exception type + message** — `DUApiException` (with HTTP status / `CF-RAY` / `AppId`) vs. tenant resource string vs. storage resource string vs. `DocumentRejectedByUserException`, verbatim.
3. **DU endpoint / API key** — which endpoint the activity targets and whether the API key/license parameter is configured (do not expose the key).
4. **Tenant entitlement** — whether Document Understanding is enabled/licensed on the tenant and has page units available.
5. **Storage** — the bucket, blob path, and Orchestrator folder the workflow reads/writes, and whether they exist and are accessible to the robot account.
6. **Package version** — `UiPath.IntelligentOCR.Activities` version.
