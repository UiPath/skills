# Final Resolution

---

**Root Cause:** The `InvoicePostingTxn` project was migrated from
**Windows - Legacy** (.NET Framework) to **Windows** (.NET 6+) —
`project.json` now sets `targetFramework: "Windows"`. The
`Start Transaction` (`DatabaseTransaction`) activity in `Main.xaml` was
**not** updated: it still sets `ProviderName="System.Data.SqlClient"`.
Under the modern runtime, opening the transaction connection crashes when
the provider type initializes:

```
System.TypeInitializationException: The type initializer for 'Microsoft.Data.SqlClient.SqlConnection' threw an exception.
```

UiPath wraps it as `Start Transaction: A database error occurred`. The
fault is the **provider / type-initializer breakage**, thrown at the
Start Transaction connect step — *before* any child activity runs.

This maps to the **Start Transaction failures playbook, BRANCH 3 —
post-migration provider / type breakage**
(`references/activity-packages/database-activities/playbooks/start-transaction-failures.md`).

**What went wrong:** The `InvoicePostingTxn` job (started
2026-05-30T06:20:00Z) faulted ~1 second after launch — at the Start
Transaction connect step, before the transaction body's `Execute Non
Query` ever ran. The failure began immediately after the
Windows-Legacy → Windows migration.

**Why:** The legacy `System.Data.SqlClient` provider does not initialize
on the modern .NET runtime — its type initializer throws, so the
`Microsoft.Data.SqlClient.SqlConnection` the transaction tries to open
never constructs. The fix is to move the Start Transaction activity to
`Microsoft.Data.SqlClient` and ensure that provider's driver is present
on every Robot host.

This is **not** a null / out-of-scope / not-propagated connection
(branch 4 — the child `Execute Non Query` correctly consumes the scope's
`dbTxn` connection, and it never even runs), **not** a swallowed-rollback
/ silent-success (branch 1 — the job clearly Faulted), **not** a
package-version body-skip bug (branch 2 — the `UiPath.Database.Activities`
pin is `1.7.0`, not a defective build, and the scope threw rather than
silently skipping its body), **not** a SQL syntax error, **not** a
command timeout, and **not** a database/network outage. It is also **not**
a merely malformed connection string — the connection string is
well-formed; the fault is the PROVIDER's type initializer failing on the
migrated runtime, raised before the connection-string is even used to
connect.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: `InvoicePostingTxn` — Faulted at 2026-05-30T06:20:01.503Z (ran ~1 second)
- Folder: `Finance Operations` (key `d3a6c4e9-5f70-4c8d-9eaf-3a4b5c6d7e8f`)
- `uip or jobs get <key> --output json` → `Info`:
  `Start Transaction: A database error occurred` wrapping
  `System.TypeInitializationException: The type initializer for 'Microsoft.Data.SqlClient.SqlConnection' threw an exception`,
  with the `Info` stack location
  `at DatabaseTransaction "Start Transaction"` → `at Sequence "Main Sequence"` → `at Main "Main"` —
  the fault is at the Start Transaction step; no child activity ran.

### Database Activities (Root Cause)
- `uip or jobs logs <key> --output json` Trace line (the smoking gun) shows the transaction connect attempt:
  `Start Transaction: opening transaction connection with ProviderName 'System.Data.SqlClient' and connection string 'Server=sqlfin01;Database=Invoices;Integrated Security=SSPI;Encrypt=true'`
  immediately followed by the type-initializer Error.
- `process/project.json` → `targetFramework: "Windows"` confirms the project was migrated off Windows - Legacy.
- `process/Main.xaml` → the `Start Transaction` (`DatabaseTransaction`) activity sets `ProviderName="System.Data.SqlClient"`; its in-scope `Execute Non Query` is well-formed and correctly bound to the scope's `dbTxn` connection (it never runs because the connect fails).

---

**Immediate fix:**

### Database Activities (Root Cause)

1. **Switch the Start Transaction provider to `Microsoft.Data.SqlClient`.**
   - **Why:** On a **Windows** (.NET 6+) project, the legacy
     `System.Data.SqlClient` provider's type initializer fails, so
     opening the transaction connection throws
     `System.TypeInitializationException` before any work runs.
   - **Where:** In `Main.xaml`, on the `Start Transaction` activity, set
     `ProviderName="Microsoft.Data.SqlClient"`. The existing connection
     string (`Server=sqlfin01;Database=Invoices;Integrated Security=SSPI;Encrypt=true`)
     is valid for the modern provider; adjust a keyword only if the
     provider rejects it.
   - **Who:** RPA developer
   - **Source:** `database-activities/playbooks/start-transaction-failures.md` (Branch 3 — post-migration provider / type breakage)

2. **Confirm the `Microsoft.Data.SqlClient` driver is installed on every Robot host.**
   - **Why:** The legacy runtime bundled providers implicitly; after
     migration the matching managed driver must be present on each Robot
     host, not only the developer machine.
   - **Who:** RPA developer / infrastructure

---

**Preventive fix:**

1. **Studio** — After migrating any project from **Windows - Legacy** to
   **Windows**, audit every Database activity's `ProviderName`
   (`Connect to Database` AND `Start Transaction`) and update legacy
   providers to `Microsoft.Data.SqlClient` / `System.Data.Odbc`.
   - **Why:** Provider/type breakage is the canonical post-migration
     Database-activity failure (branch 3).
   - **Who:** RPA developer

2. **Orchestrator / Infrastructure** — Standardize the required database
   driver on all Robot hosts as part of the migration checklist.
   - **Why:** Prevents dev-vs-prod skew where the provider initializes on
     the developer machine but fails on the Robot.
   - **Who:** RPA lead / infrastructure

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Post-migration provider / type breakage: the Windows project's Start Transaction still uses `System.Data.SqlClient`, whose type initializer fails on the modern runtime | High | Confirmed | Yes | `Microsoft.Data.SqlClient.SqlConnection` type-initializer exception in the wrapped fault + `targetFramework: "Windows"` in `project.json` + `ProviderName="System.Data.SqlClient"` on the `Start Transaction` activity in `Main.xaml` + connect-step Trace in job logs; fault at `DatabaseTransaction "Start Transaction"`, no child ran | Switch the Start Transaction provider to `Microsoft.Data.SqlClient`, confirm driver installed on Robot host |
| H2 | Connection not propagated to the child Execute Non Query (branch 4) | Low | Eliminated | No | The child `Execute Non Query` is wired to the scope's `dbTxn` connection and never runs — the fault precedes it at the Start Transaction connect step | n/a |
| H3 | Silent rollback / swallowed child error (branch 1) or package body-skip (branch 2) | Low | Eliminated | No | The job Faulted (not Success), threw at connect, and the package pin is `1.7.0` (not a defective build) | n/a |

---

Would you like help applying the fix — editing `Main.xaml` to switch the
Start Transaction provider to `Microsoft.Data.SqlClient`? I can also
clean up the `.local/investigations/` folder if you no longer need it.
