# Connect to Database Failure — Malformed Connection String (Unquoted Extended Properties)

This scenario reproduces a runtime `Connect to Database` failure caused by a
**malformed connection string**. A **Windows** process reads an Excel workbook
as a database through the ACE OLE DB provider, but the `Extended Properties`
value in the connection string is **not quoted**, so the ADO.NET
connection-string parser cannot parse it. Orchestrator returns
`System.ArgumentException: Format of the initialization string does not conform
to specification starting at index 47.`

## What this scenario uncovers

**Root Cause:** The `Connect to Database` activity (`DatabaseConnect`) uses
`ProviderName="System.Data.OleDb"` and the connection string
`Provider=Microsoft.ACE.OLEDB.12.0;Data Source=C:\Finance\Recon.xlsx;Extended
Properties=Excel 12.0 Xml;HDR=YES;`. A connection string is parsed as
`keyword=value;` pairs. The `Extended Properties` value itself contains `;`, so
it must be quoted (`Extended Properties="Excel 12.0 Xml;HDR=YES;"`). Without the
quotes, the parser reads the embedded `;` as a key/value separator and rejects
the string before the provider, the file, or the query are ever touched. The
fix is to **quote** the `Extended Properties` value.

This maps to:
`references/activity-packages/database-activities/playbooks/connect-to-database-failures.md`
— **branch 1 (malformed / wrong connection string)**.

> **Package note:** `Connect to Database` lives in
> `UiPath.Database.Activities`, NOT the Excel package. Reading an Excel file
> through it is the deliberate "Excel-as-a-database" pattern.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | synthesized UiPath project — Connect to Database (ACE OLE DB) with an **unquoted** `Extended Properties` + a downstream Execute Query over `[Sheet1$]`, project type Windows |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the documented branch-1 signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its fixture |

The decisive evidence:

1. The error: `System.ArgumentException: Format of the initialization string does not conform to specification starting at index 47.` pinned to the `Connect to Database` step, with frames in `System.Data.Common.DbConnectionOptions` and `UiPath.Database.DatabaseConnection.Connect` (`or jobs get` / `or jobs logs`).
2. `Main.xaml` shows the **unquoted** `Extended Properties=Excel 12.0 Xml;HDR=YES;` in the ACE OLE DB connection string — the embedded `;` breaks the `keyword=value;` layout.
3. `ProviderName="System.Data.OleDb"` is correct (rules out provider-init / wrong-provider branch 4); the failure is a connection-string *format* error, not a driver, file, or query error.

## Evidence chain

The agent diagnoses from Orchestrator evidence plus the workflow source:

1. `uip or folders list --output json` → find the `Finance Operations` folder key.
2. `uip or jobs list --folder-key <key> --state Faulted --output json` → find the faulted `MonthlyReconImport` job.
3. `uip or jobs get <job-key> --output json` → read the `ArgumentException` / "initialization string" message in `Info`.
4. `uip or jobs logs <job-key> --level Error --output json` → confirm the fault is at `Connect to Database`, in the connection-string parser.
5. Read `process/Main.xaml` → confirm the unquoted `Extended Properties` in the ConnectionString.

## How this differs from sibling branches

| Dimension | branch 1 (this) | branch 2 (provider not registered) | branch 3 (file lock) | branch 4 (provider init) |
|---|---|---|---|---|
| Connection string well-formed? | **no (unquoted Extended Properties)** | yes | yes | yes |
| `ProviderName` set correctly? | yes (`System.Data.OleDb`) | yes | yes | no / empty → SqlClient |
| Error anchor | **`ArgumentException` / "initialization string"** | "provider is not registered" | "used by another process" | `Microsoft.Data.SqlClient` type initializer |
| Fix | **quote the Extended Properties value** | install 64-bit ACE engine | release the file lock | set `ProviderName` explicitly |

## Synthetic fixtures

The `fixtures/mocks/responses/*.json` are **hand-authored** from the documented
branch-1 signature, not captured from a real `.local/investigations/` session.
Replace them with verbatim captures before treating this as a regression
signal (see `../_shared/scripts/generate_scenario.py`).

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill.
- Agent matched connect-to-database-failures **branch 1** AND reached the same
  root cause as `RESOLUTION.md`: the malformed connection string — the
  unquoted `Extended Properties` value — causes the parser to throw "Format of
  the initialization string does not conform to specification".
- Conclusion must recommend **quoting** the `Extended Properties` value
  (`Extended Properties="Excel 12.0 Xml;HDR=YES;"`), and must NOT land on
  provider-not-registered / bitness (branch 2), a file lock (branch 3),
  provider-init / wrong `ProviderName` (branch 4), a SQL syntax error, a missing
  file/sheet, or a database outage.

## Regenerating from a real session

```bash
python tests/tasks/uipath-troubleshoot/_shared/scripts/generate_scenario.py \
    --investigation <path-to-.local/investigations> \
    --project <path-to-failing-project> \
    --transcript <path-to-session-jsonl> \
    --scenario-name connect-database-malformed-connstring --apply
```
