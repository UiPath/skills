# Scenario: Web Activities — Deserialize JSON malformed input

## What this scenario uncovers

A `ParseResponse` Orchestrator job faults in a **Deserialize JSON** activity with
`Newtonsoft.Json.JsonReaderException: Unexpected character encountered while parsing value: <. Path '', line 0, position 0.`
The leading `<` means a non-JSON / HTML body was fed into the JSON parser.

Root cause: the `DeserializeJson` activity's `JsonString` is a hardcoded non-JSON
literal (`<html>…503 Service Unavailable…</html>`) — there is no upstream
`HttpClient` / `NetHttpRequest` in the workflow. Maps to
`activity-packages/web-activities/playbooks/deserialize-malformed-input.md`
(literal-input branch). In production this signature means an upstream HTTP call
returned an error page / non-2xx / empty body that was parsed without a success check.

## How the test reproduces it

- **Mock `uip` dispatcher** (`../_shared/mock_template`) + `fixtures/mocks/responses/manifest.json`
  serve the recorded folder / job / logs evidence.
- **Process snapshot** (`process/WebApiClient/`) holds the failing workflow so the agent can
  read the Deserialize JSON input wiring (the decisive literal-vs-HTTP evidence).
- **Fixtures** are captured from a **real staging faulted job**
  (`febd892d-787b-4008-a573-4af66cf710cf`), scrubbed (host → `MOCK-HOST`,
  account → `UIPATH\AUTOMATION1`). `jobs traces` returns an empty list and
  `traces spans get` returns its real failure — both replayed faithfully.

## Expected investigation chain

`folders list` → `jobs list --state Faulted` → `jobs get <key>` →
`jobs logs --level Error` → read `Wf_ParseResponse.xaml` (input is a non-JSON literal,
no HTTP activity) → match `deserialize-malformed-input.md` → recommend valid-JSON / guard-the-parse fix.

## Grading

`skill_triggered` (uipath-troubleshoot) + `llm_judge` against `RESOLUTION.md`
(FAULT / CAUSE with a must-NOT-attribute list / RESOLUTION), final response only.
