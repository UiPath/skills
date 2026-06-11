# Execute Non Query Failure — Stored-Proc Output Parameter Size=0 (ODBC)

This scenario reproduces a runtime `Execute Non Query` failure caused by
a **stored-procedure output parameter whose `Size` is left at `0`**,
invoked over an **ODBC** provider. The ODBC driver cannot size the value
the procedure returns, so it throws
`The Size property has an invalid size of 0` before the command runs.

## What this scenario uncovers

**Root Cause:** The `Execute Non Query` activity calls the stored
procedure `usp_FinalizeOrder` with `CommandType=StoredProcedure` over
`ProviderName="System.Data.Odbc"`. Its `Parameters` collection has an
`Output` parameter (`@ResultStatus`, `Direction=Output`) with
`Size="0"`. Over ODBC, output parameters need an explicit buffer size;
`Size=0` is rejected at parameter-binding time.

This maps to:
`references/activity-packages/database-activities/playbooks/execute-non-query-failures.md`
— **Branch 1** ("Stored-procedure output parameter with `Size = 0`
(ODBC)").

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | synthesized UiPath project — Execute Non Query stored proc over ODBC with an Output parameter `Size=0` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the documented Branch 1 signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its fixture |

The decisive evidence:

1. The job error (`or jobs get`): `The Size property has an invalid size of 0` with inner `System.Data.Odbc.OdbcParameter` exception.
2. The job logs show the `Execute Non Query - usp_FinalizeOrder` step running `usp_FinalizeOrder` (`CommandType=StoredProcedure`) over `System.Data.Odbc`.
3. The workflow source (`Main.xaml`) shows `CommandType=StoredProcedure`, `ProviderName="System.Data.Odbc"`, and the `@ResultStatus` parameter with `Direction=Output` and `Size="0"`.
4. `project.json` declares `UiPath.Database.Activities` `[1.3.2]`, predating the historical `1.4.0` ODBC-sizing fix.

## How this differs from sibling Execute Non Query branches

| Dimension | Branch 1 (this) | Branch 2 (SQL/params) | Branch 3 (empty Sql) | Branch 4 (driver load) |
|---|---|---|---|---|
| Error anchor | `The Size property has an invalid size of 0` | `A database error occurred` + syntax/type error | `CommandText property has not been initialized` | `Failed to load library (ErrorCode: 126)` / `DllNotFoundException` |
| CommandType | StoredProcedure | Text (usually) | any | any |
| Provider | ODBC | any | any | driver missing/wrong bitness |
| Output param Size=0? | **yes** | n/a | n/a | n/a |
| Fix | set param `Size` / upgrade package | parameterize SQL / fix type | populate `Sql` | install driver at right bitness |

The failing layer here is the **ODBC output-parameter buffer size** —
not the SQL text, not the connection, not a missing driver, not the
activity choice. The agent must recommend setting the parameter `Size`
(or upgrading `UiPath.Database.Activities`), not rewriting the SQL or
touching the connection.

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched the execute-non-query-failures playbook Branch 1 AND reached the same root cause as `RESOLUTION.md`
- Conclusion must (a) name the `Size=0` output parameter as the cause, (b) tie it to the `StoredProcedure` CommandType over the ODBC provider, and (c) recommend setting the parameter `Size` (or upgrading `UiPath.Database.Activities`)

## Regenerating from a real session

```bash
python tests/tasks/uipath-troubleshoot/_shared/scripts/generate_scenario.py \
    --investigation <path-to-.local/investigations> \
    --project <path-to-failing-project> \
    --transcript <path-to-session-jsonl> \
    --scenario-name execute-non-query-out-param-size --apply
```
