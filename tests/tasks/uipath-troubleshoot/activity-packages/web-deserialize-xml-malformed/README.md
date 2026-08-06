# Scenario: web-deserialize-xml-malformed

Replays staging job `9937b232-5a94-44ab-8aee-ce6ea52d3bb4` (`ParseDocument`). Fault: `System.Xml.XmlException: Data at the root level is invalid. Line 1, position 1.` in Deserialize XML (DeserializeXml). Maps to `web-activities/playbooks/deserialize-malformed-input.md`.

Fixtures captured from a real staging faulted job, scrubbed (host → MOCK-HOST, account → UIPATH\AUTOMATION1). `process/WebApiClient/` holds the failing workflow source. Grading: `skill_triggered` + `llm_judge` vs `RESOLUTION.md` (final response only).

## Fixture isolation

`data/uip-fixture.json` is a finite command/response map mounted only into coder-eval's UID/GID-isolated mock service. The evaluated agent receives a bounded `uip` client and cannot read the fixture or mock implementation.
