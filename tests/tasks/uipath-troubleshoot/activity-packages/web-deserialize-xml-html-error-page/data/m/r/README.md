# Scenario: web-deserialize-xml-html-error-page

Replays staging job `bfdb5d4d-0e44-4441-b60c-3d42bbbc16c6` (`ReleaseFeedSync`). Fault: `System.Xml.XmlException: The 'hr' start tag on line 5 position 2 does not match the end tag of 'body'. Line 6, position 3.` in Deserialize XML (DeserializeXml). Maps to `web-activities/playbooks/deserialize-xml-malformed.md` (branch C - HTML page instead of XML).

Fixtures are fresh, unfiltered `uip` responses for the real staging faulted job, scrubbed (user email -> original_email@test.com, user name -> user1, host -> MOCK-HOST). `process/ReleaseFeedSync/` holds the failing workflow source. Grading: `skill_triggered` + `llm_judge` vs `RESOLUTION.md` (final response only).
