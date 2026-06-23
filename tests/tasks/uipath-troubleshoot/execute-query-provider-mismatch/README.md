# Execute Query Failure — Driver/Provider Mismatch After Migration

This scenario reproduces a runtime `Execute Query` failure that begins
right after a project is upgraded from **Windows - Legacy**
(.NET Framework) to **Windows** (.NET 6+). The `Connect to Database`
activity still uses `ProviderName="System.Data.SqlClient"` with a
connection string carrying a keyword the modern provider rejects
(`Provider=SQLOLEDB;...`). The modern connection-string parser
(`Microsoft.Data.SqlClient`) throws
`System.ArgumentException: Keyword not supported: 'Provider'`, which
Orchestrator surfaces as `Execute Query: A database error occurred`.

## What this scenario uncovers

**Root Cause:** The project's `targetFramework` is `Windows` (migrated),
but the Database activity was never updated off the legacy provider. On
.NET 6+ the `System.Data.SqlClient` / OLE-DB keyword combination is
invalid; `Microsoft.Data.SqlClient` rejects `Provider=SQLOLEDB`. The fix
is to **switch the provider to `Microsoft.Data.SqlClient`**, drop/adjust
the rejected connection-string keyword(s), and confirm the driver is
installed on the Robot host.

This maps to:
`references/activity-packages/database-activities/playbooks/execute-query-failures.md`
(BRANCH 2 — driver/provider mismatch after migration).

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | synthesized UiPath project — `targetFramework: "Windows"`, a `Connect to Database` using `System.Data.SqlClient` with a `Provider=SQLOLEDB;...` connection string feeding an `Execute Query` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the documented branch-2 signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its fixture |

The decisive evidence chain:

1. `uip or folders list --output json` → the `Finance Automation` folder.
2. `uip or jobs list --folder-key <key> --state Faulted --output json` → the single faulted `InvoiceReconciliation` job.
3. `uip or jobs get <job-key> --output json` → `Info` carries `Execute Query: A database error occurred` wrapping `System.ArgumentException: Keyword not supported: 'Provider'.` raised in the `Microsoft.Data.SqlClient` connection-string parser at `Connect to Database`.
4. `uip or jobs logs <job-key> --output json` → a Trace line showing the connect attempt with `ProviderName 'System.Data.SqlClient'` and the `Provider=SQLOLEDB;...` connection string.
5. `process/project.json` → `targetFramework: "Windows"` (migrated); `process/Main.xaml` → `Connect to Database` with `ProviderName="System.Data.SqlClient"` and the offending connection string.

## How this differs from sibling branches

| Dimension | branch 1 (null connection) | branch 2 (provider mismatch) (this) | branch 3 (concatenation) | branch 5 (timeout) |
|---|---|---|---|---|
| Connection opens? | no | **no — parser rejects keyword** | yes | yes |
| Error signature | `NullReferenceException` | **`Keyword not supported: 'Provider'` (ArgumentException)** | `A database error occurred` + `Incorrect syntax near ...` | `Timeout expired` |
| Where the fault is | wiring/scope | **provider/driver after migration** | the SQL text | DB-side duration |
| Fix | wire/scope the connection | **switch to Microsoft.Data.SqlClient + fix keyword + install driver** | parameterize the query | raise `TimeoutMS` / fix the query |

The failing layer here is the **provider/connection-string
configuration after migration**, not the connection wiring, the SQL
text, a timeout, or the database. The agent must recommend switching to
`Microsoft.Data.SqlClient` and adjusting the rejected keyword(s) — not
blame a null connection, SQL syntax, a timeout, a CLR crash, the wrong
activity, or a DB outage.

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill.
- Agent matched the execute-query-failures playbook (branch 2) AND reached the same root cause as `RESOLUTION.md`.
- Conclusion must (a) name the `Keyword not supported` ArgumentException from the connection-string parser, (b) attribute it to the Windows migration while the activity still uses `System.Data.SqlClient` with a rejected keyword, and (c) recommend switching to `Microsoft.Data.SqlClient`, adjusting the keyword(s), and confirming the driver is installed on the Robot host.

## Regenerating from a real session

```bash
python tests/tasks/uipath-troubleshoot/_shared/scripts/generate_scenario.py \
    --investigation <path-to-.local/investigations> \
    --project <path-to-failing-project> \
    --transcript <path-to-session-jsonl> \
    --scenario-name execute-query-provider-mismatch --apply
```
