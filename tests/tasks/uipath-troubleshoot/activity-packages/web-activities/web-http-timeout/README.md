# Scenario: web-http-timeout

Replays staging job `3bdb5a85-b6ae-4e1f-b5a5-2488ca74de12` (`FetchReport`). Fault: `System.Net.WebException: The operation has timed out.` in HTTP Request (HttpClient). Maps to `web-activities/playbooks/http-request-timeout.md`.

Fixtures captured from a real staging faulted job, scrubbed (host → MOCK-HOST, account → UIPATH\AUTOMATION1). `process/WebApiClient/` holds the failing workflow source. Grading: `skill_triggered` + `llm_judge` vs `RESOLUTION.md` (final response only).
