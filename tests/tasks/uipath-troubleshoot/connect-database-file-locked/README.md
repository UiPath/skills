# Connect to Database Failure — Workbook Held Open by Another Process (File Lock)

This scenario reproduces a runtime `Connect to Database` failure caused by a
**file lock / sharing violation**. A **Windows** process reads an Excel workbook
as a database through a well-formed ACE OLE DB connection string, but the target
workbook `C:\Finance\Invoices.xlsx` is held open by another process at run time,
so the file-based provider cannot acquire it. Orchestrator returns
`System.IO.IOException: The process cannot access the file
'C:\Finance\Invoices.xlsx' because it is being used by another process.`

## What this scenario uncovers

**Root Cause:** The `Connect to Database` activity (`DatabaseConnect`) uses a
well-formed ACE OLE DB connection string
(`Provider=Microsoft.ACE.OLEDB.12.0;Data Source=C:\Finance\Invoices.xlsx;...`)
with `ProviderName="System.Data.OleDb"`. The connection string, provider, and
downstream SQL are all correct. The workbook is held open by another process —
the Excel UI, an orphaned `EXCEL.EXE` from a prior run, a concurrent job, or a
OneDrive / sync / AV client. File-based providers request a write lock by
default, so the ACE provider cannot acquire the locked file and the connect
throws a sharing violation. The fix is to ensure the workbook is closed (kill
orphan processes) before the run and, for read-only SELECTs, open the connection
read-only (`Mode=Read`).

This maps to:
`references/activity-packages/database-activities/playbooks/connect-to-database-failures.md`
— **branch 3 (file lock / sharing violation)**.

> **Package note:** `Connect to Database` lives in
> `UiPath.Database.Activities`, NOT the Excel package. Reading an Excel file
> through it is the deliberate "Excel-as-a-database" pattern.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | synthesized UiPath project — Connect to Database (ACE OLE DB, well-formed string) + Execute Query over `[Invoices$]`, project type Windows |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the documented branch-3 signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its fixture |

The decisive evidence:

1. The error: `System.IO.IOException: The process cannot access the file
   'C:\Finance\Invoices.xlsx' because it is being used by another process.`
   pinned to the `Connect to Database` step (`or jobs get` / `or jobs logs`),
   with frames into `OleDbConnection.Open` and
   `UiPath.Database.DatabaseConnection.Connect`.
2. `Main.xaml` shows a **well-formed** ACE OLE DB connection string and the
   correct `ProviderName="System.Data.OleDb"` — ruling out the connection-string
   (branch 1), provider-not-registered (branch 2), and provider-init (branch 4)
   branches.
3. The exception class is `System.IO.IOException` with the "used by another
   process" text — a sharing violation, not a configuration error.

## Evidence chain (Orchestrator-only persona)

The reporting user has Orchestrator access and the workflow source. The agent
diagnoses from Orchestrator evidence plus the workflow source, then hands back a
host-side fix:

1. `uip or folders list --output json` → find the `Finance Operations` folder key.
2. `uip or jobs list --folder-key <key> --state Faulted --output json` → find the faulted `DailyInvoiceLoad` job.
3. `uip or jobs get <job-key> --output json` → read the `IOException` ("used by another process") in `Info`.
4. `uip or jobs logs <job-key> --level Error --output json` → confirm the fault is at `Connect to Database`.
5. Read `process/Main.xaml` + `process/project.json` → confirm well-formed ACE connection string + correct provider.

## How this differs from sibling branches

| Dimension | branch 1 (conn string) | branch 2 (provider not registered) | branch 3 (this) | branch 4 (provider init) |
|---|---|---|---|---|
| Connection string well-formed? | no | yes | **yes** | yes |
| `ProviderName` set correctly? | n/a | yes (`System.Data.OleDb`) | **yes (`System.Data.OleDb`)** | no / empty → SqlClient |
| Error anchor | `ArgumentException` / initialization string | "provider is not registered" | **`IOException` "used by another process"** | `Microsoft.Data.SqlClient` type initializer |
| Fix | correct the connection string | install 64-bit ACE engine | **release the file lock (close / kill orphan; `Mode=Read`)** | set `ProviderName` explicitly |

## Synthetic data note

All fixtures are **synthetic**, hand-authored from the documented branch-3
signature in the playbook — not captured from a real tenant. The job key, folder
key, host name, and account are mock values (`MOCK-HOST`, `RobotUser1`). Replace
with verbatim captures from a real `.local/investigations/` before treating this
as a hardened regression signal.

## Success criteria

The test **scores the conclusion, not the trajectory**:

- Agent invoked the `uipath-troubleshoot` skill.
- Agent matched connect-to-database-failures **branch 3** AND reached the same
  root cause as `RESOLUTION.md`: the workbook is held open by another process
  (file lock / sharing violation), and the connection string and provider are
  fine.
- Conclusion must recommend closing/releasing the file (kill orphan process)
  and/or opening the connection read-only (`Mode=Read`), and must NOT land on a
  connection-string typo (branch 1), provider-not-registered / bitness (branch
  2), provider-init / wrong `ProviderName` (branch 4), a SQL syntax error, or a
  "file not found / wrong path / missing sheet" conclusion (the file exists — it
  is locked).

## Regenerating from a real session

```bash
python tests/tasks/uipath-troubleshoot/_shared/scripts/generate_scenario.py \
    --investigation <path-to-.local/investigations> \
    --project <path-to-failing-project> \
    --transcript <path-to-session-jsonl> \
    --scenario-name connect-database-file-locked --apply
```
