# Scenario: web-deserialize-null-input

Replays staging job `1dc1992a-7f84-40bf-b61d-75b50f861170` (`ReadConfig`). Fault: `System.ArgumentNullException: Value cannot be null. (Parameter 'JSON string')` in Deserialize JSON (DeserializeJson). Maps to `web-activities/playbooks/deserialize-null-input.md`.

Fixtures captured from a real staging faulted job, scrubbed (host → MOCK-HOST, account → UIPATH\AUTOMATION1). `process/WebApiClient/` holds the failing workflow source. Grading: `skill_triggered` + `llm_judge` vs `RESOLUTION.md` (final response only).
