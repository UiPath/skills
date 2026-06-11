# Start Transaction Failure — Silent Success / No Rollback

This scenario reproduces a `Start Transaction` failure where the **job
reports Success** even though the work it should have committed is missing
or incomplete. A child `Execute Non Query` inside the `Start Transaction`
scope faults on a FOREIGN KEY violation, but an in-scope `Try Catch`
catches `System.Exception` and **only logs** a Warn message (no `Throw`).
The fault never propagates out of the scope, so the transaction does not
roll back: the scope exits normally, **commits** the partial work (the
header insert), and the job ends **Successful** on incomplete data.

## What this scenario uncovers

**Root Cause:** The in-scope catch swallows the child fault, so the
all-or-nothing guarantee of the transaction is lost. The header row
commits, the detail rows are never written, and Orchestrator records a
clean Success — the bug is exactly that it looks green. The fix is to
**re-raise (`Throw`)** in the catch so the fault leaves the `Start
Transaction` scope and the transaction **rolls back** (and the job faults
visibly) — not log-and-continue.

This maps to:
`references/activity-packages/database-activities/playbooks/start-transaction-failures.md`
(BRANCH 1 — silent success / no rollback).

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | synthesized UiPath project — a `Start Transaction` (`ui:DatabaseTransaction`, `Microsoft.Data.SqlClient`) scope wrapping a `Try Catch` over two `Execute Non Query` inserts (both bound to the scope's `[dbTxn]`); the `Catch` for `System.Exception` holds only a `Log Message` (Warn) with no `Throw` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the documented branch-1 signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its fixture |

The decisive evidence chain:

1. `uip or folders list --output json` → the `Finance Operations` folder.
2. `uip or jobs list --folder-key <key> --state Faulted --output json` → **empty** list (no faulted job; the failure hides behind a green Success).
3. `uip or jobs list --folder-key <key>` (no state) / `--state Successful` → the single **Successful** `BatchLedgerPost` job.
4. `uip or jobs get <job-key> --output json` → `State: "Successful"`, benign `Info: "Execution ended."`.
5. `uip or jobs logs <job-key> --output json` → the smoking gun: the header insert succeeds, the detail insert logs an **Error** (FK violation), an **Info** "caught and continuing" line immediately follows, then the scope **commits** and the job ends Successful — the child error was swallowed and the transaction still committed.
6. `process/Main.xaml` → the in-scope `Try Catch` whose `Catch` contains only a `Log Message` (Warn) with no `Throw`.

## How this differs from sibling branches

| Dimension | branch 1 (silent rollback) (this) | branch 2 (package body-skip) | branch 3 (provider mismatch) | branch 4 (connection not propagated) |
|---|---|---|---|---|
| Job state | **Successful (false green)** | Successful | Faulted | Faulted (or non-transactional writes) |
| Child activities run? | **yes — and one errored** | no (body skipped) | n/a (fails at connect) | yes |
| Signature | **child Error + "caught, continuing" Info, then commit** | empty scope, no logs, on v1.5.0 | `Keyword not supported` / type-initializer crash | `Object reference not set` / instant `Timeout expired`, or auto-committed writes |
| Where the fault is | **swallowed in-scope catch (no Throw)** | package version | provider/driver after migration | child `ExistingDbConnection` wiring |
| Fix | **re-raise (Throw) so the transaction rolls back** | change package version | switch to `Microsoft.Data.SqlClient` | thread the scope's `DatabaseConnection` into every child |

The failing layer here is the **exception flow inside the transaction
scope** — a child error swallowed by a no-`Throw` catch — not a data
problem, a timeout, the connection wiring, the provider, the package
version, or the database. The agent must recommend **re-raising (`Throw`)**
in the catch so the transaction rolls back — not blame the data, a timeout,
a null connection, a provider mismatch, a package bug, or a DB outage.

## Synthetic fixtures

The `fixtures/mocks/responses/*.json` files are **hand-authored** from the
documented branch-1 signature, not captured from a real
`.local/investigations/` run. They are internally consistent (one
Successful job, an empty Faulted list, and job logs carrying the
swallowed-error smoking gun) so the mock dispatcher resolves the full
discovery chain. Replace them with verbatim captures from a real
investigation before treating this scenario as a hard regression signal.

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill.
- Agent matched the start-transaction-failures playbook (branch 1) AND reached the same root cause as `RESOLUTION.md`.
- Conclusion must (a) identify that a child activity inside the `Start Transaction` scope failed and the error was swallowed by an in-scope catch with no `Throw`, (b) explain that the transaction committed / did not roll back so the job reports Success on incomplete data, and (c) recommend re-raising (`Throw`) in the catch so the transaction rolls back.

## Regenerating from a real session

```bash
python tests/tasks/uipath-troubleshoot/_shared/scripts/generate_scenario.py \
    --investigation <path-to-.local/investigations> \
    --project <path-to-failing-project> \
    --transcript <path-to-session-jsonl> \
    --scenario-name start-transaction-silent-rollback --apply
```
