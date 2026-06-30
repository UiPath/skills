# Final Resolution

**Fault:** The `DocIntake` job (folder Shared, host MOCK-HOST) ended **Faulted**. The fault is raised by a **`UiPath.IntelligentOCR.Activities` Digitize Document** activity (via its **UiPath Document OCR** engine) and surfaces as `UiPath.SmartData.Utils.DocumentUnderstandingClient.DUApiException`.

**Root cause:** The Document Understanding server **rejected the digitization call with HTTP 401** because the **Document Understanding API key is invalid or misconfigured**. The actionable signature is `Your license could not be validated. Please make sure that the API key parameter is correctly configured.`, raised by `DUServerCaller` on a 401 response. The `ApiKey` configured on the UiPath Document OCR engine (or the DU API key the activity resolves) is wrong, expired, empty, or not valid for the targeted DU endpoint.

**Fix:** Set a valid Document Understanding **API key** on the UiPath Document OCR engine / Digitize Document (confirm the key matches the targeted DU endpoint and is current). Store it as a secure asset/credential and, with explicit user approval, wire it from there.

**Must NOT attribute the root cause to:**
- The **Digitizer PDF-component license** (`System.ComponentModel.LicenseException: Invalid license for the PDF component`) — that is a separate Digitizer/Docotic licensing failure raised before the DU call; this fault is a `DUApiException` HTTP 401 from the DU server about the **API key**.
- **DU not being enabled on the tenant** (`Failed to fetch Document Understanding projects list...` / `Couldn't retrieve a tenant key.`) — that is a tenant-enablement error, not a per-call 401 on the API key.
- **Out of page units** (HTTP 403, `Failed to consume the requested number of pages...`) or **request too large** (HTTP 413) — the status here is specifically 401 (license/key validation).
- The **document content / a missing or corrupt file**, a storage-bucket/taxonomy problem, or a workflow-logic bug.

A correct answer identifies that **the Document Understanding server returned 401 because the API key is invalid/misconfigured (`DUApiException: Your license could not be validated...`)**, and recommends setting a valid DU API key. It must read the 401/api-key signature rather than blaming the Digitizer PDF-component license, tenant enablement, the document, or the workflow logic.
