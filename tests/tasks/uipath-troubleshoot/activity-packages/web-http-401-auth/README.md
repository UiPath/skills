# Scenario: web-http-401-auth

Replays job `9d4f2a18-3c5b-4e70-8a2f-1b6c3e5d7a90` (`InvoiceApiClient`).
Fault: `System.Net.WebException: The remote server returned an error: (401) Unauthorized.` in HTTP Request (HttpClient) on a POST. Maps to `web-activities/playbooks/http-request-auth-401-403.md`.

The request reached the API and was rejected on **authentication**: `Wf_PostInvoice.xaml` sends the **bare token** as the `Authorization` header value (`Authorization = [apiToken]`) instead of the scheme-prefixed `"Bearer " + apiToken`, so the API rejects it with `401`. The fix is to format the header with its scheme (`"Bearer " + apiToken`) — NOT a transport (DNS/TLS), proxy (`407`), wrong-endpoint (`404`), or payload/media-type (`400/415`) fix. The decisive evidence is the workflow source: the `Authorization` header built from the raw token with no `Bearer ` prefix.

Fixtures hand-authored in the faithful-replay shape (scrubbed: host → MOCK-HOST, account → UIPATH\AUTOMATION1). `process/InvoiceApiClient/` holds the failing workflow source. Grading: `skill_triggered` + `llm_judge` vs `RESOLUTION.md` (final response only).
