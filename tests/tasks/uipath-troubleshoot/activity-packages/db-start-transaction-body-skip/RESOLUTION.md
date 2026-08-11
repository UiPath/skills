# Final Resolution

---

**Root Cause:** The `NightlyReconcileTxn` project pins
`UiPath.Database.Activities` **v1.5.0** — a defective build in which the
`Start Transaction` (`DatabaseTransaction`) scope **skips its body
entirely**. The scope opens its connection, enters, and exits cleanly,
committing an empty transaction; **none** of the child activities inside
the scope ever execute. There is **no error** at any level. The job reports
**Successful** even though nothing was read or written — the reconciliation
the user expects simply never runs.

This is a package defect, not a workflow-configuration problem. The
workflow inside the scope is well-formed (an `Execute Non Query` that posts
the reconciliation `UPDATE`, both correctly bound to the scope's output
`dbTxn` via `ExistingDbConnection`, and a `Log Message`), but on v1.5.0 the
body is never invoked, so those children produce no log lines and write no
rows.

This maps to the **Start Transaction failures playbook, BRANCH 2 —
transaction scope skips its body (package-version bug)**
(`references/activity-packages/database-activities/playbooks/start-transaction-failures.md`).

**What went wrong:** The `NightlyReconcileTxn` job (started
2026-05-31T01:30:01Z) ran ~2 seconds and ended **Successful** at
2026-05-31T01:30:03Z. The job logs show the `Start Transaction` scope
starting on `UiPath.Database.Activities v1.5.0` and immediately exiting and
committing — with **zero** child-activity log lines in between and **no**
error or warning anywhere. The `Execute Non Query` and `Log Message` inside
the scope never ran.

**Why:** A `Start Transaction` (`DatabaseTransaction`) scope is supposed to
run the activities in its body under one transaction and commit on normal
exit. The v1.5.0 build has a defect where the body is never executed: the
scope enters and exits as a no-op. Because no child runs, nothing throws,
nothing rolls back, and the scope commits an empty transaction — so
Orchestrator records a clean Success on a job that accomplished nothing. The
fix is to move off the defective build via **Manage Packages** — it is a
package-version fix, not a workflow change.

**This is NOT branch 1 (silent success / no rollback).** In branch 1 a
child activity *ran and errored* and the error was *swallowed* by an
in-scope catch (the logs carry a child Error line followed by a
"caught and continuing" line). Here **no child ran at all** and there is
**no error anywhere** — the logs contain the scope start and the scope
commit with nothing in between. There is no swallowed exception to find.

This is also **not branch 3** (post-migration provider / type breakage —
there is no `Microsoft.Data.SqlClient` type-initializer crash and no
unresolvable `DatabaseConnection`; the job did not fault), **not branch 4**
(the connection was correctly propagated — both children carry
`ExistingDbConnection="[dbTxn]"`, and nothing null-referenced or timed out),
**not a data problem** (no rows were even touched, so there is no data to
mismatch), and **not a trigger / schedule issue** (the scheduled job clearly
*did* run and reported Successful).

---

**Evidence:**

### Orchestrator (Propagation)
- Job: `NightlyReconcileTxn` — **Successful** at 2026-05-31T01:30:03.402Z (ran ~2 seconds)
- Folder: `Finance Operations` (key `c4a7e2f9-1b3d-4e5a-8c6f-9d0e1f2a3b4c`)
- `uip or jobs list --folder-key <key> --state Faulted --output json` → **empty** list: there is no faulted job — the failure hides behind a green Success.
- `uip or jobs get <key> --output json` → `State: "Successful"`, `Info: "Execution ended."` — nothing in the job summary signals a failure.
- `uip or jobs logs <key> --level Error --output json` → **empty** list: there is no error at any level — confirming nothing inside the scope threw.

### Database Activities (Root Cause)
- `uip or jobs logs <key> --output json` (the smoking gun) shows, in order:
  - Info: `NightlyReconcileTxn execution started`
  - Trace: `Start Transaction: scope started (UiPath.Database.Activities v1.5.0)`
  - Trace: `Start Transaction: scope exited; committing transaction` — **immediately** after the scope start, with **no** `Execute Query` / `Execute Non Query` / `Log Message` lines in between.
  - Info: `NightlyReconcileTxn execution ended` — Successful.
  - The empty, instantaneous scope with zero in-scope activity logs and no error is the branch-2 body-skip signature.
- `process/project.json`: pins `"UiPath.Database.Activities": "[1.5.0]"` — the known body-skip build. `targetFramework: "Windows"`.
- `process/Main.xaml`: the `Start Transaction` (`ui:DatabaseTransaction`, `Microsoft.Data.SqlClient`) scope wraps a `Sequence` with an `Execute Non Query` (parameterized reconciliation `UPDATE`, bound to the scope's `[dbTxn]` via `ExistingDbConnection`) and a `Log Message` (Level=Info). Both children are well-formed and correctly wired — they are NOT the bug; they simply never executed on v1.5.0.

---

**Immediate fix:**

### Database Activities (Root Cause)

1. **Move `UiPath.Database.Activities` off the defective v1.5.0 build.**
   - **Why:** v1.5.0 has a defect where the `Start Transaction` scope skips its body, so the child activities never execute and the job reports a false Success. A version change is the fix.
   - **Where:** Open **Manage Packages** in Studio and upgrade `UiPath.Database.Activities` to the latest stable (**v1.7.1** or newer), or downgrade to a known-good older release (**v1.4.0**). Republish the process.
   - **Who:** RPA developer
   - **Source:** `database-activities/playbooks/start-transaction-failures.md` (Branch 2 — transaction scope skips its body)

2. **Validate the transaction body executes after the version change.**
   - **Why:** Confirm the fix — after upgrading, the job logs should show the in-scope `Execute Non Query` and `Log Message` running and rows being written.
   - **Who:** RPA developer

---

**Preventive fix:**

1. **Studio** — Pin and track the `UiPath.Database.Activities` version across environments and avoid known-defective builds (notably v1.5.0).
   - **Why:** The body-skip defect is version-specific; pinning a known-good build keeps it out of production.
   - **Who:** RPA lead

2. **Studio / Orchestrator** — After any Database Activities version change, validate that the `Start Transaction` body actually executes (the in-scope activities log and the expected rows commit) before promoting.
   - **Why:** A green job state alone does not prove the transaction body ran — an empty scope also reports Success.
   - **Who:** RPA developer

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Transaction scope skips its body on the defective UiPath.Database.Activities v1.5.0 build: the Start Transaction scope enters and exits with no error, every child activity is skipped, nothing is written, and the job reports Success | High | Confirmed | Yes | Successful job with an empty Faulted list and an empty error-level log; job logs show the Start Transaction scope start (v1.5.0) followed immediately by the commit with zero in-scope activity lines and no error; `project.json` pins v1.5.0; `Main.xaml` holds a well-formed Execute Non Query + Log Message that never ran | Upgrade UiPath.Database.Activities to v1.7.1+ (or downgrade to v1.4.0) via Manage Packages; validate the body executes after the change |

---

Would you like help applying the fix — bumping `UiPath.Database.Activities`
to v1.7.1+ (or v1.4.0) in `project.json` and republishing? I can also clean
up the `.local/investigations/` folder if you no longer need it.
