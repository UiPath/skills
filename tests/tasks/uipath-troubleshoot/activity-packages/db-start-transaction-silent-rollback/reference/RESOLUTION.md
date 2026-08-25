# Final Resolution

---

**Root Cause:** A child `Execute Non Query` inside the `Start Transaction`
scope of `BatchLedgerPost` failed — the detail-row insert violated a
FOREIGN KEY constraint (`FK_LedgerBatchDetail_Account`) — but the in-scope
`Try Catch` caught `System.Exception` and **only logged** a Warn message
("caught and continuing") with **no `Throw`**. Because the fault never
propagated out of the `Start Transaction` scope, the scope exited normally
and **committed** the partial work (the header insert), the detail rows
were never written, and the job reported **Successful** on incomplete data.

The transaction neither rolled back nor re-raised. The header row was
committed; the detail rows are missing — exactly the "missing or
incomplete ledger entries" the user reported, on a job that looks green.

This maps to the **Start Transaction failures playbook, BRANCH 1 — silent
success / no rollback**
(`references/activity-packages/database-activities/playbooks/start-transaction-failures.md`).

**What went wrong:** The `BatchLedgerPost` job (started
2026-05-30T02:10:01Z) ran a few seconds and ended **Successful** at
2026-05-30T02:10:06Z. Inside the transaction the header insert succeeded,
the detail insert threw a `Microsoft.Data.SqlClient.SqlException` (FK
violation), the in-scope catch swallowed it with a Warn log, and the scope
committed on normal exit — so Orchestrator recorded a clean Success.

**Why:** A `Start Transaction` (`DatabaseTransaction`) scope commits on
normal scope exit and rolls back only when an exception **propagates out**
of the scope. The in-scope `Try Catch` here catches `System.Exception` and
contains only a `Log Message` (Level=Warn) — there is no `Throw`. So a
child fault is absorbed: the all-or-nothing guarantee is lost, the partial
work commits, and the failure is invisible to the job state. The fix is to
**re-raise** the fault in the catch so it leaves the scope and triggers the
rollback.

This is **not** a plain data problem (a child activity explicitly errored
and the error was swallowed), **not** a command timeout, **not** a
null/unpropagated connection (Branch 4 — both inserts correctly consume the
scope's `dbTxn` via `ExistingDbConnection`), **not** a provider mismatch
(Branch 3), **not** a package-version body-skip bug (Branch 2 — the child
activities clearly ran and logged), and **not** a database outage (the
connection opened and a row committed).

---

**Evidence:**

### Orchestrator (Propagation)
- Job: `BatchLedgerPost` — **Successful** at 2026-05-30T02:10:06.402Z (ran ~5 seconds)
- Folder: `Finance Operations` (key `b1f4a2c7-3d5e-4a6b-9c8d-1e2f3a4b5c6d`)
- `uip or jobs list --folder-key <key> --state Faulted --output json` → **empty** list: there is no faulted job — the failure is hidden behind a green Success.
- `uip or jobs get <key> --output json` → `State: "Successful"`, `Info: "Execution ended."` — nothing in the job summary signals a failure.

### Database Activities (Root Cause)
- `uip or jobs logs <key> --output json` (the smoking gun) shows, in order:
  - Trace: `Start Transaction: ... beginning a database transaction ...`
  - Trace: `Execute Non Query: inserted header row for batch 'B-20260530-0210' into LedgerBatchHeader (1 row affected)`
  - **Error**: `Execute Non Query: A database error occurred. Microsoft.Data.SqlClient.SqlException ... The INSERT statement conflicted with the FOREIGN KEY constraint "FK_LedgerBatchDetail_Account" ...`
  - **Info**: `Detail insert failed, caught and continuing: The INSERT statement conflicted with the FOREIGN KEY constraint ...` — the child error was swallowed, not re-raised.
  - Trace: `Start Transaction: scope exited normally; committing database transaction` — the transaction committed despite the child error.
  - Info: `BatchLedgerPost execution ended` — Successful.
- `process/Main.xaml`: the `Start Transaction` (`ui:DatabaseTransaction`) scope wraps a `Try Catch`; the `Try` runs two `Execute Non Query` inserts (both bound to the scope's `[dbTxn]` via `ExistingDbConnection`), and the `Catch` for `System.Exception` contains **only** a `Log Message` (Level=Warn) — **no `Throw`**.

---

**Immediate fix:**

### Database Activities (Root Cause)

1. **Re-raise the child fault in the catch so the transaction rolls back.**
   - **Why:** A `Start Transaction` scope rolls back only when an exception propagates out of it. A catch that logs and continues lets the scope exit normally and commit the partial work, so the job reports a false Success on incomplete data.
   - **Where:** In `Main.xaml`, inside the `Start Transaction` scope's `Try Catch`, add a `Throw` in the `Catch` (re-throw `ex`, or throw a domain exception) after logging — do **not** log-and-continue. The fault then leaves the scope, the transaction rolls back the header insert, and the job faults visibly.
   - **Who:** RPA developer
   - **Source:** `database-activities/playbooks/start-transaction-failures.md` (Branch 1 — silent success / no rollback)

2. **Make the batch all-or-nothing.**
   - **Why:** Only commit (let the scope exit normally) when every in-scope step succeeded; any child failure must leave the scope as an exception so the whole unit rolls back.
   - **Who:** RPA developer

---

**Preventive fix:**

1. **Studio** — Let child faults propagate out of every `Start Transaction` scope; never wrap in-scope statements in a catch that logs and continues.
   - **Why:** A swallowed in-scope exception is the canonical cause of a transaction that commits partial work and a job that reports a false Success (Branch 1).
   - **Who:** RPA developer

2. **Studio / Orchestrator** — Add a **Global Exception Handler** so hidden database exceptions are caught and routed rather than absorbed across processes.
   - **Why:** Broad coverage against silently swallowed faults beyond a single workflow.
   - **Who:** RPA lead

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Silent success / no rollback: a child Execute Non Query inside the Start Transaction scope faulted (FK violation) but an in-scope Try Catch caught System.Exception and only logged (no Throw), so the scope committed partial work and the job reported Success | High | Confirmed | Yes | Successful job with an empty Faulted list; job logs show the FK-violation Error immediately followed by a "caught and continuing" Info line, then the scope committing and the job ending Successful; `Main.xaml` catch holds only a Log Message with no Throw | Add a Throw in the catch so the fault propagates and the transaction rolls back; make the batch all-or-nothing; add a Global Exception Handler |

---

Would you like help applying the fix — editing `Main.xaml` to add a `Throw`
in the `Start Transaction` catch so the transaction rolls back on a child
failure? I can also clean up the `.local/investigations/` folder if you no
longer need it.
