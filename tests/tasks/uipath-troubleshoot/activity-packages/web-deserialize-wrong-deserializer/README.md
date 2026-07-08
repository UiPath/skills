# Scenario: web-deserialize-wrong-deserializer

Job `1150d469-f4dc-44fc-b39e-c89aaa5db3f9` (`ParseList`). Fault: `Newtonsoft.Json.JsonReaderException: Error reading JArray from JsonReader. Current JsonReader item is not an array: StartObject. Path '', line 1, position 1.` in Deserialize JSON Array (DeserializeJsonArray). Maps to the **wrong-deserializer** branch of `web-activities/playbooks/deserialize-malformed-input.md`.

The input is **valid JSON but a JSON object (`{...}`)** fed to Deserialize JSON Array, which requires an array (`[...]`). Distinct from the malformed-literal scenario (`web-deserialize-malformed-input`) — the payload parses fine; only the deserializer choice is wrong. Correct fix: use Deserialize JSON (`DeserializeJson` → `JObject`), or fix the producer to emit an array.

Fixtures scrubbed (host → MOCK-HOST, account → UIPATH\AUTOMATION1). `process/WebApiClient/` holds the failing workflow source. Grading: `skill_triggered` + `llm_judge` vs `RESOLUTION.md` (final response only).
