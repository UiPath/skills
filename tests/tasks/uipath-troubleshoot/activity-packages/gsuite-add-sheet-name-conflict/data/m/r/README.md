# GSuite Add-Sheet Name-Conflict Troubleshooting — Faithful Replay

This scenario replays a real `uipath-troubleshoot` investigation of a Faulted
Orchestrator job whose UiPath.GSuite **Add Sheet** activity hit a duplicate
**sheet-name conflict**.

## What the original session uncovered

The user asked only *"why did my last job from folder Shared fail?"*. The agent:

1. Listed folders → resolved **Shared** to key `1965a46b-db4e-469e-aaaa-7e0b379cb34d`.
2. Listed Faulted jobs in Shared → newest is **SheetTabBuilder**,
   job `2fbf6ba4-b347-462f-a83e-33c6c34bbea6`.
3. Read the job's `Info` → a `UiPath.GSuite.Exceptions.GSuiteException` thrown
   from `AddSheetWithConflictResolution` in `AddSheetConnections`.

Conclusion: the target spreadsheet already had a tab matching the configured
`SheetName` and `ConflictResolution` was left at `Fail`, so Add Sheet threw a
same-name conflict — *not* a connection, auth, 404, invalid-range, throttling,
or transient fault. (Listing connections confirms both GSuite connections
serving Shared are Enabled and valid — a defensive fixture reinforces that the
connection is fine.)

## Name-conflict signature

```
UiPath.GSuite.Exceptions.GSuiteException: A sheet with the same name already exists.
   at UiPath.GSuite.Sheets.Extensions.ISheetsServiceExtensions.AddSheetWithConflictResolution(...)
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

`skills/uipath-troubleshoot/references/activity-packages/gsuite-activities/playbooks/add-sheet-name-conflict.md`
