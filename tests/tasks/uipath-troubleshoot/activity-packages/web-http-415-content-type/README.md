# Scenario: web-http-415-content-type

Replays job `3f8d5a91-2b7c-4e60-9a1f-6c8e4d2b0a75` (`CrmContactUpload`).
Fault: `System.Net.WebException: The remote server returned an error: (415) Unsupported Media Type.` in HTTP Request (HttpClient) on a POST. Maps to `web-activities/playbooks/http-request-content-type-rejected.md`.

The request reached the CRM API and was rejected on **media type**: `Wf_CreateContact.xaml` sends a JSON body (`{"name":"Acme Corp",...}`) but advertises `BodyFormat="application/xml"`, so the server refuses the payload with `415`. The fix is to set `BodyFormat` / the `Content-Type` header to `application/json` to match the body — NOT an auth (401/403), wrong-endpoint (404), or transport fix. The decisive evidence is the workflow source: the JSON body paired with `application/xml`.

Fixtures hand-authored in the faithful-replay shape (scrubbed: host → MOCK-HOST, account → UIPATH\AUTOMATION1). `process/CrmContactUpload/` holds the failing workflow source. Grading: `skill_triggered` + `llm_judge` vs `RESOLUTION.md` (final response only).
