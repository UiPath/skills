# Scenario: web-deserialize-jsonarray-malformed

Replays staging job `1150d469-f4dc-44fc-b39e-c89aaa5db3f9` (`ParseList`). Fault: `Newtonsoft.Json.JsonReaderException: Unexpected character encountered while parsing value: n. Path '', line 0, position 0.` in Deserialize JSON Array (DeserializeJsonArray). Maps to `web-activities/playbooks/deserialize-malformed-input.md`.

Fixtures captured from a real staging faulted job, scrubbed (host → MOCK-HOST, account → UIPATH\AUTOMATION1). `process/WebApiClient/` holds the failing workflow source. Grading: `skill_triggered` + `llm_judge` vs `RESOLUTION.md` (final response only).

## Fixture isolation

`data/uip-fixture.json` is a finite command/response map mounted only into coder-eval's UID/GID-isolated mock service. The evaluated agent receives a bounded `uip` client and cannot read the fixture or mock implementation.
