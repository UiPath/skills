# GSuite Invalid / Null Input Troubleshooting — Faithful Replay

This scenario replays a real `uipath-troubleshoot` investigation of a Faulted
Orchestrator job whose UiPath.GSuite **Write Range** activity threw a
**client-side** null/empty `range` validation error — before any Google
Sheets API call.

## What the original session uncovered

The user asked only *"why did my last job from folder Shared fail?"*. The agent:

1. Listed folders → resolved **Shared** to key `1965a46b-db4e-469e-aaaa-7e0b379cb34d`.
2. Listed Faulted jobs in Shared → newest is **SheetExportRunner**,
   job `c123367e-8e5e-4ec0-9903-fd75d5ef9ad7`.
3. Read the job's `Info` → a `UiPath.GSuite.Exceptions.GSuiteException`
   wrapping `GSuiteInternalException` / `System.ArgumentNullException` on the
   `range` parameter, thrown from `WriteRangeConnections`.

Conclusion: a **client-side input-validation** failure — the `range` input was
null/empty, so the activity threw `Value cannot be null. (Parameter 'range')`
*before* any request reached Google Sheets (no HTTP status, no API round-trip).
*Not* a Google API, 404, connection, auth, scope, throttling, outage, or
transient fault. (Listing connections confirms both GSuite connections serving
Shared are Enabled and valid — a defensive fixture reinforces that the
connection is fine.)

## Client-side null-range signature

```
UiPath.GSuite.Exceptions.GSuiteException: Value cannot be null. (Parameter 'range')
 ---> UiPath.GSuite.Exceptions.GSuiteInternalException:  is not a valid Spreadsheet range. (Parameter 'range')
 ---> System.ArgumentNullException:  is not a valid Spreadsheet range. (Parameter 'range')
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

`skills/uipath-troubleshoot/references/activity-packages/gsuite-activities/playbooks/invalid-or-null-input.md`
