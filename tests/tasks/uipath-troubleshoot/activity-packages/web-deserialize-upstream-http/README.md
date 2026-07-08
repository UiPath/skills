# Scenario: web-deserialize-upstream-http

Job `9937b232-5a94-44ab-8aee-ce6ea52d3bb4` (`ParseDocument`). Fault: `Newtonsoft.Json.JsonReaderException: Unexpected character encountered while parsing value: <. Path '', line 0, position 0.` in Deserialize JSON (DeserializeJson). Maps to the **upstream-HTTP** branch of `web-activities/playbooks/deserialize-malformed-input.md`.

An `HttpClient` GET returns an HTML error page (leading `<`); its `Result` is wired straight into `DeserializeJson`, and the captured `StatusCode` is never checked — so a non-2xx / HTML body reaches the parser. Distinct from the literal scenario (`web-deserialize-malformed-input`): here the bad input is a **runtime HTTP body**, so the agent must trace the input to the HTTP call and pivot (guard on `StatusCode` / investigate the endpoint), not "fix a literal."

Fixtures scrubbed (host → MOCK-HOST, account → UIPATH\AUTOMATION1). `process/WebApiClient/` holds the failing workflow source. Grading: `skill_triggered` + `llm_judge` vs `RESOLUTION.md` (final response only).
