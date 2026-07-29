# GSuite Sheets Invalid-Range Troubleshooting — Faithful Replay

This scenario replays a real `uipath-troubleshoot` investigation of a Faulted
Orchestrator job whose UiPath.GSuite **Write Range** activity sent a malformed
A1 range and hit a Google Sheets **HTTP 400**.

## What the original session uncovered

The user asked only *"why did my last job from folder Shared fail?"*. The agent:

1. Listed folders → resolved **Shared** to key `1965a46b-db4e-469e-aaaa-7e0b379cb34d`.
2. Listed Faulted jobs in Shared → newest is **SheetRangeWriter**,
   job `d5e0e6b0-55b8-4256-8494-c601cb986dab`.
3. Read the job's `Info` → a `UiPath.GSuite.Exceptions.GSuiteException`
   wrapping `Google.GoogleApiException` with **HttpStatusCode BadRequest** and
   `Unable to parse range: Sheet1!A0` thrown from `WriteRangeConnections`.

Conclusion: a Google Sheets **400 / unparseable-A1-range** failure — row 0 is
invalid because Sheets is 1-indexed. The range is present but malformed; this
is *not* a 404, connection, auth, null-input, throttling, or transient fault.
The error is server-side, raised after the spreadsheet resolved and the
connection authenticated. (Listing connections confirms both GSuite connections
serving Shared are Enabled and valid — a defensive fixture reinforces that the
connection is fine.)

## 400 signature

```
Google.GoogleApiException: The service sheets has thrown an exception.
HttpStatusCode is BadRequest. Unable to parse range: Sheet1!A0
```

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` (manifest-driven dispatcher) |
| `fixtures/mocks/responses/*.json` | verbatim, scrubbed stdout from the real session's `.local/investigations/raw/` |
| `fixtures/mocks/responses/manifest.json` | first-match-wins dispatch table; `docsai ask` is passthrough |

CLI-driven — no `process/` snapshot; the root cause is fully contained in the
`or jobs get` `Info` field.

## Playbook validated

`skills/uipath-troubleshoot/references/activity-packages/gsuite-activities/playbooks/sheets-invalid-range.md`
