# Final Resolution

**Fault:** The `DocIntake` job (folder Shared, host MOCK-HOST) ended **Faulted**. The fault is raised by a **`UiPath.IntelligentOCR.Activities` Digitize Document** activity (via its **UiPath Document OCR** engine) and surfaces as `System.AggregateException`.

**Root cause:** The Document Understanding OCR service **rejected the call because the UiPath Document OCR API key is invalid**. The actionable signature is in the inner message: `Server response: Invalid API key specified Error:UiPathOCRInvalidApiKey` (raised from `UiPath.DocumentUnderstanding.Digitizer.Digitization.PageDigitizer.ApplyOcr`). The `ApiKey` configured on the UiPath Document OCR engine is wrong, expired, or empty.

**Fix:** Set a valid **UiPath Document OCR `ApiKey`** on the Digitize Document's OCR engine — copy the tenant's Document Understanding API key from Automation Cloud → **Licenses → Consumables → AI Units → Copy API Key**, and re-enter it (store it as a secure asset/credential). Confirm the key matches the targeted DU tenant/endpoint.

**Must NOT attribute the root cause to:**
- The **`AggregateException` wrapper** ("One or more errors occurred.") — that is not the cause; the cause is the inner `Server response: Invalid API key specified Error:UiPathOCRInvalidApiKey`. Do not stop at the wrapper.
- The **Digitizer PDF-component license** (`System.ComponentModel.LicenseException: Invalid license for the PDF component`) — a separate local Digitizer/Docotic licensing failure raised before the OCR call; this fault is a server-side invalid-API-key rejection.
- **DU not being enabled on the tenant** (`Failed to fetch Document Understanding projects list...` / `Couldn't retrieve a tenant key.`) — a tenant-enablement error, not an invalid OCR key.
- **Out of page units** (`Failed to consume the requested number of pages...`) or **request too large** — the server said the key is *invalid*, not that units/size are the problem.
- The **document content / a missing or corrupt file**, a storage-bucket/taxonomy problem, or a workflow-logic bug.

A correct answer identifies that **the UiPath Document OCR call was rejected because the API key is invalid (`Server response: Invalid API key specified Error:UiPathOCRInvalidApiKey`, wrapped in `System.AggregateException`)**, and recommends setting a valid UiPath Document OCR API key from the tenant's AI Units. It must read the inner server response rather than blaming the `AggregateException` wrapper, the Digitizer PDF-component license, tenant enablement, page units, the document, or the workflow logic.
