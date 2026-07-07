# Start Transaction Failure — Connection Not Propagated to Child

This scenario reproduces a runtime `Start Transaction`
(`DatabaseTransaction`) failure where the scope opens its connection
**successfully**, but a child `Execute Query` inside the scope body is
left with an **empty `ExistingDbConnection`** — it is never bound to the
scope's output `DatabaseConnection` (`dbTxn`). At runtime the child runs
with a `null` connection and throws
`System.NullReferenceException: Object reference not set to an instance of
an object`, which Orchestrator surfaces as
`Execute Query: Object reference not set to an instance of an object`.

## What this scenario uncovers

**Root Cause:** The `Start Transaction` scope connected fine on
`Microsoft.Data.SqlClient` and assigned a live `DatabaseConnection` to
`dbTxn`. The child `Execute Query` inside the scope, however, has no
`ExistingDbConnection` binding (the property is empty, not `[dbTxn]`), so
it executes against a null connection. The transaction's connection was
**never propagated** to the child. The fix is to **bind `dbTxn` into the
child's `ExistingDbConnection`** so the child runs inside the
transaction — not to wrap it in a Try Catch, add a null check, or give
the child its own inline connection.

This maps to:
`references/activity-packages/database-activities/playbooks/start-transaction-failures.md`
(BRANCH 4 — output connection not propagated to child activities).

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | synthesized UiPath project — a `Start Transaction` scope (`Microsoft.Data.SqlClient`, output `dbTxn`) wrapping an `Execute Query` whose `ExistingDbConnection` is left empty (not bound to `dbTxn`) |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the documented branch-4 signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its fixture |

The decisive evidence chain:

1. `uip or folders list --output json` -> the `Sales Operations` folder.
2. `uip or jobs list --folder-key <key> --state Faulted --output json` -> the single faulted `OrderSettlementTxn` job.
3. `uip or jobs get <job-key> --output json` -> `Info` carries `Execute Query: Object reference not set to an instance of an object.` wrapping `System.NullReferenceException`, with the stack at `ExecuteQuery "Execute Query"` -> `DatabaseTransaction "Start Transaction"` -> `Sequence "Main Sequence"` -> `Main "Main"`.
4. `uip or jobs logs <job-key> --output json` -> the smoking gun: a Trace showing `Start Transaction` opened its connection and assigned it to `dbTxn` **successfully**, then a Trace showing `Execute Query` ran with `ExistingDbConnection = (null)`, then the `NullReferenceException` Error lines.
5. `process/Main.xaml` -> the child `Execute Query` has no `ExistingDbConnection` binding while the scope outputs `DatabaseConnection` to `dbTxn`; `process/project.json` -> `UiPath.Database.Activities [1.7.0]` (a healthy build, ruling out branch 2).

## How this differs from sibling branches

| Dimension | branch 1 (silent rollback) | branch 2 (body skip) | branch 3 (provider/type after migration) | branch 4 (connection not propagated) (this) |
|---|---|---|---|---|
| Job state | Success | Success | Faulted | **Faulted** |
| Scope connection opens? | yes | n/a | **no — type/provider crash** | **yes — opens fine** |
| Child runs? | yes (errored, swallowed) | **no — body skipped** | no | **yes — but with null connection** |
| Error signature | none surfaced | none | type-initializer / unresolvable type | **`NullReferenceException` at the child** |
| Fix | re-throw in catch so scope rolls back | move off the defective package version | switch to `Microsoft.Data.SqlClient` + clear cache | **bind `dbTxn` into the child's `ExistingDbConnection`** |

The failing layer here is the **child's connection wiring**, not the
scope's connection (which opened fine), not a swallowed rollback, not a
package-version body-skip, not a post-migration provider crash, not a bad
connection string, not SQL syntax, and not a timeout. The agent must
recommend **propagating the scope's connection** (`dbTxn`) into the
child's `ExistingDbConnection` — not blame the connection string, a
provider mismatch, a package bug, a swallowed rollback, or a timeout, and
not settle for a Try Catch / null check as the primary fix.

## Synthetic fixtures

The `fixtures/mocks/responses/*.json` files are **hand-authored** from the
documented branch-4 signature, not captured from a live tenant. All
identifiers (folder key, job key, machine, account) are synthetic and
valid hex. Replace with verbatim captures from a real
`.local/investigations/` before treating this as a hard regression signal.

## Success criteria

The test scores the **conclusion, not the trajectory**:

- Agent invoked the `uipath-troubleshoot` skill.
- Agent matched the start-transaction-failures playbook (branch 4) AND reached the same root cause as `RESOLUTION.md`.
- Conclusion must (a) identify that the child `Execute Query`'s `ExistingDbConnection` is empty / not bound to the `Start Transaction` output, (b) explain that is why it threw `NullReferenceException` while the scope's own connection was fine, and (c) recommend binding `dbTxn` into the child's `ExistingDbConnection`.
