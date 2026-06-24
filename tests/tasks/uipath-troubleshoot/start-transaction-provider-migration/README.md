# Start Transaction Failure — Provider Type-Initializer Crash After Migration

This scenario reproduces a runtime `Start Transaction` failure that
begins right after a project is migrated from **Windows - Legacy**
(.NET Framework) to **Windows** (.NET 6+). The `Start Transaction`
(`DatabaseTransaction`) activity still uses
`ProviderName="System.Data.SqlClient"`, so opening the transaction
connection crashes when the provider type initializes:
`System.TypeInitializationException: The type initializer for
'Microsoft.Data.SqlClient.SqlConnection' threw an exception`, which
Orchestrator surfaces as `Start Transaction: A database error occurred`.
The fault is at the Start Transaction connect step — before any child
activity in the scope runs — so it is unmistakably the Start Transaction
activity.

## What this scenario uncovers

**Root Cause:** The project's `targetFramework` is `Windows` (migrated),
but the `Start Transaction` activity was never updated off the legacy
provider. On .NET 6+ the `System.Data.SqlClient` provider's type
initializer fails, so the transaction connection never opens. The fix is
to **switch the Start Transaction provider to `Microsoft.Data.SqlClient`**
and confirm the driver is installed on the Robot host.

This maps to:
`references/activity-packages/database-activities/playbooks/start-transaction-failures.md`
(BRANCH 3 — post-migration provider / type breakage).

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | synthesized UiPath project — `targetFramework: "Windows"`, a `Start Transaction` using `System.Data.SqlClient` wrapping a well-formed parameterized `Execute Non Query` that never runs |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the documented branch-3 signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its fixture |

The decisive evidence chain:

1. `uip or folders list --output json` → the `Finance Operations` folder.
2. `uip or jobs list --folder-key <key> --state Faulted --output json` → the single faulted `InvoicePostingTxn` job.
3. `uip or jobs get <job-key> --output json` → `Info` carries `Start Transaction: A database error occurred` wrapping `System.TypeInitializationException: The type initializer for 'Microsoft.Data.SqlClient.SqlConnection' threw an exception`, with the stack located at `DatabaseTransaction "Start Transaction"` (no child activity ran).
4. `uip or jobs logs <job-key> --output json` → a Trace line showing the transaction connect attempt with `ProviderName 'System.Data.SqlClient'`, immediately followed by the type-initializer Error.
5. `process/project.json` → `targetFramework: "Windows"` (migrated); `process/Main.xaml` → `Start Transaction` with `ProviderName="System.Data.SqlClient"`.

## How this differs from sibling branches

| Dimension | branch 1 (silent rollback) | branch 2 (body-skip bug) | branch 3 (provider migration) (this) | branch 4 (connection not propagated) |
|---|---|---|---|---|
| Job state | **Success** (wrong) | **Success** (empty) | **Faulted** | Faulted (or non-transactional writes) |
| Where the fault is | swallowed child error / no rollback | package version `v1.5.0` | **Start Transaction provider/type after migration** | child `ExistingDbConnection` wiring |
| Error signature | none (green job, partial data) | none (green job, no child logs) | **`Microsoft.Data.SqlClient` type-initializer crash at connect** | `NullReferenceException` / instant `Timeout expired` |
| Fix | re-raise in catch so the scope rolls back | move off the defective package build | **switch Start Transaction to Microsoft.Data.SqlClient + driver on host** | thread the scope's `DatabaseConnection` into every child |

The failing layer here is the **provider / type-initializer breakage on
the Start Transaction activity after migration**, raised at the connect
step before any child runs — not a swallowed rollback, not a package
body-skip, not the child connection wiring, not SQL, not a timeout, and
not the database. The connection string itself is well-formed; the fault
is the legacy PROVIDER failing to initialize on the modern runtime. The
agent must recommend switching to `Microsoft.Data.SqlClient` and
confirming the driver on the Robot host.

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill.
- Agent matched the start-transaction-failures playbook (branch 3) AND reached the same root cause as `RESOLUTION.md`.
- Conclusion must (a) name the `Microsoft.Data.SqlClient` type-initializer crash, (b) attribute it to the Start Transaction activity still using `System.Data.SqlClient` after the project was migrated to Windows, and (c) recommend switching the provider to `Microsoft.Data.SqlClient` and confirming the driver is installed on the Robot host.

## Regenerating from a real session

```bash
python tests/tasks/uipath-troubleshoot/_shared/scripts/generate_scenario.py \
    --investigation <path-to-.local/investigations> \
    --project <path-to-failing-project> \
    --transcript <path-to-session-jsonl> \
    --scenario-name start-transaction-provider-migration --apply
```
