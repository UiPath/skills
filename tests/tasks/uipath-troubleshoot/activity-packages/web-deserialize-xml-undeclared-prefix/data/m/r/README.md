# Scenario: web-deserialize-xml-undeclared-prefix

Replays staging job `08f043df-d089-4e8e-aa22-31cde10662b4` (`QuoteLookup`). Fault: `System.Xml.XmlException: 'soapenv' is an undeclared prefix. Line 1, position 2.` in Deserialize XML (DeserializeXml). Maps to `web-activities/playbooks/deserialize-xml-malformed.md` (branch A - namespace prefix never declared).

Fixtures are fresh, unfiltered `uip` responses for the real staging faulted job, scrubbed (user email -> original_email@test.com, user name -> user1, host -> MOCK-HOST). `process/QuoteLookup/` holds the failing workflow source. Grading: `skill_triggered` + `llm_judge` vs `RESOLUTION.md` (final response only).
