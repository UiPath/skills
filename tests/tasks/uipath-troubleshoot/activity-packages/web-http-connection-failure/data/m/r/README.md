# Scenario: web-http-connection-failure

Replays staging job `419a6787-6cc6-4b93-bae4-ba985bf6fe67` (`CallService`). Fault: `System.Net.WebException: No such host is known. (service-endpoint-unavailable.invalid:80)` in HTTP Request (HttpClient). Maps to `web-activities/playbooks/http-request-connection-failure.md`.

Fixtures captured from a real staging faulted job, scrubbed (host → MOCK-HOST, account → UIPATH\AUTOMATION1). `process/WebApiClient/` holds the failing workflow source. Grading: `skill_triggered` + `llm_judge` vs `RESOLUTION.md` (final response only).
