# Scenario: web-deserialize-xml-root-missing

Replays staging job `4fa9cfe0-3a24-4502-a498-cf8672b1f3d8` (`OrderStatusSync`). Fault: `System.Xml.XmlException: Root element is missing.` in Deserialize XML (DeserializeXml). Maps to `web-activities/playbooks/deserialize-xml-malformed.md` (branch B - empty input).

Fixtures are fresh, unfiltered `uip` responses for the real staging faulted job, scrubbed (user email -> original_email@test.com, user name -> user1, host -> MOCK-HOST). `process/OrderStatusSync/` holds the failing workflow source. Grading: `skill_triggered` + `llm_judge` vs `RESOLUTION.md` (final response only).
