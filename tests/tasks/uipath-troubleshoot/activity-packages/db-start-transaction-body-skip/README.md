# Start Transaction Failure — Scope Skips Its Body (Package v1.5.0 Bug)

This scenario reproduces a `Start Transaction` failure where the **job
reports Success** every night, yet the reconciliation it should perform
never happens — **no rows are written and there is no error**. The project
pins `UiPath.Database.Activities` **v1.5.0**, a defective build in which the
`Start Transaction` scope **skips its body entirely**: the scope enters and
exits cleanly, committing an empty transaction, and **none** of its child
activities ever execute.

## What this scenario uncovers

**Root Cause:** The `UiPath.Database.Activities` v1.5.0 build has a defect
where the `Start Transaction` (`DatabaseTransaction`) scope never invokes
its body. The well-formed child activities inside the scope — a
parameterized `Execute Non Query` (the reconciliation `UPDATE`, bound to the
scope's `dbTxn` via `ExistingDbConnection`) and an `Info` `Log Message` —
are simply skipped. Nothing throws, nothing rolls back, and the scope
commits an empty transaction, so Orchestrator records a clean Success on a
job that accomplished nothing. The fix is a **package-version change**:
upgrade `UiPath.Database.Activities` to **v1.7.1+** (or downgrade to a
known-good **v1.4.0**) via Manage Packages — it is **not** a workflow
change.

This maps to:
`references/activity-packages/database-activities/playbooks/start-transaction-failures.md`
(BRANCH 2 — transaction scope skips its body).

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | synthesized UiPath project — a `Start Transaction` (`ui:DatabaseTransaction`, `Microsoft.Data.SqlClient`) scope wrapping a `Sequence` with a parameterized `Execute Non Query` (`ExistingDbConnection="[dbTxn]"`) and a `Log Message` (Info); `project.json` pins `UiPath.Database.Activities` **`[1.5.0]`** |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the documented branch-2 signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its fixture |

The decisive evidence chain:

1. `uip or folders list --output json` → the `Finance Operations` folder.
2. `uip or jobs list --folder-key <key> --state Faulted --output json` → **empty** list (no faulted job; the failure hides behind a green Success).
3. `uip or jobs list --folder-key <key>` (no state) / `--state Successful` → the single **Successful** `NightlyReconcileTxn` job.
4. `uip or jobs get <job-key> --output json` → `State: "Successful"`, benign `Info: "Execution ended."`.
5. `uip or jobs logs <job-key> --level Error --output json` → **empty** list — there is no error at any level.
6. `uip or jobs logs <job-key> --output json` → the smoking gun: the `Start Transaction` scope starts on `UiPath.Database.Activities v1.5.0` and **immediately** commits/exits, with **zero** child-activity log lines in between and no error anywhere.
7. `process/project.json` → `"UiPath.Database.Activities": "[1.5.0]"` — the defective build.
8. `process/Main.xaml` → the child `Execute Non Query` + `Log Message` that should have run but never executed.

## How this differs from sibling branches

| Dimension | branch 1 (silent rollback) | branch 2 (package body-skip) (this) | branch 3 (provider mismatch) | branch 4 (connection not propagated) |
|---|---|---|---|---|
| Job state | Successful (false green) | **Successful (false green)** | Faulted | Faulted (or non-transactional writes) |
| Child activities run? | yes — and one errored | **no — body skipped entirely** | n/a (fails at connect) | yes |
| Error present? | yes — a child Error, then swallowed | **no error anywhere** | yes — type-initializer crash | yes — null-ref / instant timeout |
| Signature | child Error + "caught, continuing" Info, then commit | **empty scope (start then immediate commit), no child logs, no error, on v1.5.0** | `Keyword not supported` / type-initializer crash | `Object reference not set` / instant `Timeout expired`, or auto-committed writes |
| Where the fault is | swallowed in-scope catch (no Throw) | **package version (v1.5.0 defect)** | provider/driver after migration | child `ExistingDbConnection` wiring |
| Fix | re-raise (Throw) so the transaction rolls back | **change the package version (upgrade to v1.7.1+ / downgrade to v1.4.0)** | switch to `Microsoft.Data.SqlClient` | thread the scope's `DatabaseConnection` into every child |

**The branch-1-vs-branch-2 distinction is the crux of this test.** Both
report a false-green Success, but they are opposites in the logs:

- **Branch 1 (silent rollback):** a child activity **ran and errored**, and
  the error was **swallowed** by a no-`Throw` catch. The logs carry a child
  Error line immediately followed by a "caught and continuing" line.
- **Branch 2 (this scenario):** **no child ran at all** and there is **no
  error anywhere**. The logs show only the scope start and the scope commit
  with nothing in between. The tell is the empty scope plus the pinned
  v1.5.0 package version — there is no swallowed exception to find.

The failing layer here is the **`UiPath.Database.Activities` package
version**, not the workflow logic, the exception flow, the connection
wiring, the provider, the data, or the schedule. The agent must recommend a
**version change** (upgrade to v1.7.1+ or downgrade to v1.4.0) — not a
Try Catch, a Throw, a retry, added logging, or any workflow edit.

## Synthetic fixtures

The `fixtures/mocks/responses/*.json` files are **hand-authored** from the
documented branch-2 signature, not captured from a real
`.local/investigations/` run. They are internally consistent (one
Successful job, an empty Faulted list, an empty error-level log, and job
logs carrying the empty-scope smoking gun) so the mock dispatcher resolves
the full discovery chain. Replace them with verbatim captures from a real
investigation before treating this scenario as a hard regression signal.

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill.
- Agent matched the start-transaction-failures playbook (branch 2) AND reached the same root cause as `RESOLUTION.md`.
- Conclusion must (a) identify that the `Start Transaction` scope executed none of its child activities with no error, (b) attribute it to the defective `UiPath.Database.Activities` v1.5.0 build (body-skip bug), and (c) recommend upgrading to v1.7.1+ (or downgrading to v1.4.0).

## Regenerating from a real session

```bash
python tests/tasks/uipath-troubleshoot/_shared/scripts/generate_scenario.py \
    --investigation <path-to-.local/investigations> \
    --project <path-to-failing-project> \
    --transcript <path-to-session-jsonl> \
    --scenario-name start-transaction-body-skip --apply
```
