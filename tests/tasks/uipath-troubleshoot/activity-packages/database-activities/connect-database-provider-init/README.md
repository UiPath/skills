# Connect to Database Failure — Provider Init / Empty ProviderName After Windows Migration

This scenario reproduces a runtime `Connect to Database` failure caused by an
**empty `ProviderName`** on a project migrated from **Windows - Legacy** to
**Windows** (.NET). The `LedgerExportXlsx` process reads an Excel workbook as a
database through an ACE OLE DB connection string, but with no provider set the
modern runtime resolves to **SqlClient** and faults with
`System.TypeInitializationException: The type initializer for
'Microsoft.Data.SqlClient.SqlConnection' threw an exception.` — even though the
intended target is Excel.

## What this scenario uncovers

**Root Cause:** The `Connect to Database` activity (`DatabaseConnect`) has
`ProviderName=""` (empty) and a well-formed ACE OLE DB connection string
(`Provider=Microsoft.ACE.OLEDB.12.0;Data Source=C:\Finance\Ledger.xlsx;...`).
`project.json` is **Windows**, so on the modern .NET runtime the empty provider
resolves to SqlClient; the activity initializes `Microsoft.Data.SqlClient` and
the `SqlConnection` type initializer throws. The fix is to set `ProviderName`
explicitly to `System.Data.OleDb` — the source is Excel/Access, **not** SQL
Server, so switching to `Microsoft.Data.SqlClient` is the wrong fix.

This maps to:
`references/activity-packages/database-activities/playbooks/connect-to-database-failures.md`
— **branch 4 (provider init failure after migration / wrong `ProviderName`)**.

> **Package note:** `Connect to Database` lives in
> `UiPath.Database.Activities`, NOT the Excel package. Reading an Excel file
> through it is the deliberate "Excel-as-a-database" pattern.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | synthesized UiPath project — Connect to Database (empty ProviderName, ACE OLE DB string) + Execute Query over `[Ledger$]`, project type Windows |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the documented branch-4 signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its fixture |

The decisive evidence:

1. The error:
   `System.TypeInitializationException: The type initializer for
   'Microsoft.Data.SqlClient.SqlConnection' threw an exception.` pinned to the
   `Connect to Database` step (`or jobs get` / `or jobs logs`), with frames into
   `Microsoft.Data.SqlClient` and `UiPath.Database.DatabaseConnection.Connect`.
2. `Main.xaml` shows `ProviderName=""` (empty) alongside a well-formed ACE OLE
   DB connection string — ruling out the connection-string and bitness branches.
3. `project.json` `"targetFramework": "Windows"` — the project was migrated off
   Windows - Legacy, where the empty provider was tolerated.
4. The job logs note that the runtime resolved the empty `ProviderName` to the
   SqlClient provider while the connection string is an ACE/Excel OLE DB string.

## Evidence chain

1. `uip or folders list --output json` → find the `Finance Operations` folder key.
2. `uip or jobs list --folder-key <key> --state Faulted --output json` → find the faulted `LedgerExportXlsx` job.
3. `uip or jobs get <job-key> --output json` → read the `TypeInitializationException` in `Info`.
4. `uip or jobs logs <job-key> --level Error --output json` → confirm the empty-provider-resolves-to-SqlClient note.
5. Read `process/Main.xaml` + `process/project.json` → confirm empty `ProviderName` + ACE connection string + Windows (migrated) project.

## How this differs from sibling branches

| Dimension | branch 1 (conn string) | branch 2 (bitness) | branch 3 (file lock) | branch 4 (this) |
|---|---|---|---|---|
| Connection string well-formed? | no | yes | yes | **yes** |
| `ProviderName` set correctly? | n/a | yes (`System.Data.OleDb`) | yes | **no — empty → SqlClient** |
| Error anchor | `ArgumentException` / initialization string | "provider is not registered" | "used by another process" | **`Microsoft.Data.SqlClient` type initializer** |
| Fix | correct the connection string | install 64-bit ACE engine | release the file lock | **set `ProviderName="System.Data.OleDb"`** |

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill.
- Agent matched connect-to-database-failures **branch 4** AND reached the same
  root cause as `RESOLUTION.md`: the empty `ProviderName` on the migrated
  Windows project resolves to SqlClient, throwing the
  `Microsoft.Data.SqlClient` type-initializer exception against an Excel/ACE OLE
  DB source.
- Conclusion must recommend setting `ProviderName` explicitly to
  `System.Data.OleDb`, and must NOT land on a connection-string typo, a bitness
  / "provider not registered" mismatch, a file lock, a SQL syntax error, or the
  "switch to Microsoft.Data.SqlClient" anti-pattern (the target is Excel/OLE
  DB).

> **Synthetic note:** All fixtures are hand-authored from the documented
> branch-4 signature, not captured from a live tenant. Replace with verbatim
> `.local/investigations/` captures before treating this as a hard regression
> signal.

## Regenerating from a real session

```bash
python tests/tasks/uipath-troubleshoot/_shared/scripts/generate_scenario.py \
    --investigation <path-to-.local/investigations> \
    --project <path-to-failing-project> \
    --transcript <path-to-session-jsonl> \
    --scenario-name connect-database-provider-init --apply
```
