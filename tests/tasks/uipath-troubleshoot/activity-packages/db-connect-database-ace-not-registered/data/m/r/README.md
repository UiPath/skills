# Connect to Database Failure — ACE OLE DB Provider Not Registered (Bitness Mismatch)

This scenario reproduces a runtime `Connect to Database` failure caused by a
**provider bitness mismatch**. A **Windows** (64-bit) process reads an Excel
workbook as a database through the ACE OLE DB provider, but the Robot host only
has the **32-bit** Microsoft Access Database Engine installed (bundled with
32-bit Office). Orchestrator returns
`System.InvalidOperationException: The 'Microsoft.ACE.OLEDB.12.0' provider is
not registered on the local machine.`

## What this scenario uncovers

**Root Cause:** The `Connect to Database` activity (`DatabaseConnect`) uses a
well-formed ACE OLE DB connection string
(`Provider=Microsoft.ACE.OLEDB.12.0;Data Source=C:\Data\SomeBook.xlsx;...`) with
`ProviderName="System.Data.OleDb"`. `project.json` is **Windows**, so the
process runs 64-bit. The host has only the 32-bit ACE engine, which the 64-bit
process cannot load — so the provider is "not registered" for that process. The
fix is to install the **64-bit** Microsoft Access Database Engine on the Robot
host. The driver bitness must match the **process** bitness, not Office's.

This maps to:
`references/activity-packages/database-activities/playbooks/connect-to-database-failures.md`
— **branch 2 (provider not registered / architecture (bitness) mismatch)**.

> **Package note:** `Connect to Database` lives in
> `UiPath.Database.Activities`, NOT the Excel package. Reading an Excel file
> through it is the deliberate "Excel-as-a-database" pattern.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | synthesized UiPath project — Connect to Database (ACE OLE DB) + Execute Query over `[Sheet1$]`, project type Windows (64-bit) |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the documented branch-2 signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its fixture |

The decisive evidence:

1. The error: `System.InvalidOperationException: The 'Microsoft.ACE.OLEDB.12.0' provider is not registered on the local machine.` pinned to the `Connect to Database` step (`or jobs get` / `or jobs logs`).
2. `Main.xaml` shows a well-formed ACE OLE DB connection string and `ProviderName="System.Data.OleDb"` — ruling out connection-string and provider-init branches.
3. `project.json` `"targetFramework": "Windows"` — the process is 64-bit, so it needs the 64-bit ACE engine.

## Evidence chain (Orchestrator-only persona)

The reporting user is off the Robot host and has Orchestrator access only. The
agent diagnoses from Orchestrator evidence plus the workflow source, then hands
back a host-side fix:

1. `uip or folders list --output json` → find the `Finance Automations` folder key.
2. `uip or jobs list --folder-key <key> --state Faulted --output json` → find the faulted `ExcelDbReport` job.
3. `uip or jobs get <job-key> --output json` → read the `InvalidOperationException` in `Info`.
4. `uip or jobs logs <job-key> --level Error --output json` → confirm the fault is at `Connect to Database`.
5. Read `process/Main.xaml` + `process/project.json` → confirm well-formed ACE connection string + Windows (64-bit) project.

## How this differs from sibling branches

| Dimension | branch 1 (conn string) | branch 2 (this) | branch 3 (file lock) | branch 4 (provider init) |
|---|---|---|---|---|
| Connection string well-formed? | no | **yes** | yes | yes |
| `ProviderName` set correctly? | n/a | **yes (`System.Data.OleDb`)** | yes | no / empty → SqlClient |
| Error anchor | `ArgumentException` / initialization string | **"provider is not registered"** | "used by another process" | `Microsoft.Data.SqlClient` type initializer |
| Fix | correct the connection string | **install 64-bit ACE engine** | release the file lock | set `ProviderName` explicitly |

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill.
- Agent matched connect-to-database-failures **branch 2** AND reached the same
  root cause as `RESOLUTION.md`: the 64-bit ACE OLE DB provider is not
  registered because only the 32-bit engine is installed (bitness mismatch).
- Conclusion must recommend installing the **64-bit** Access Database Engine on
  the Robot host (match process bitness, `/quiet` if 32-bit Office blocks it),
  and must NOT land on a connection-string typo, file lock, wrong path, SQL
  syntax error, or the "install 32-bit ACE to match 32-bit Office"
  anti-pattern.

## Regenerating from a real session

```bash
python tests/tasks/uipath-troubleshoot/_shared/scripts/generate_scenario.py \
    --investigation <path-to-.local/investigations> \
    --project <path-to-failing-project> \
    --transcript <path-to-session-jsonl> \
    --scenario-name connect-database-ace-not-registered --apply
```
