# Final Resolution

---

**Root Cause:** The `InvoiceReconciliation` project was migrated from
**Windows - Legacy** (.NET Framework) to **Windows** (.NET 6+) —
`project.json` now sets `targetFramework: "Windows"`. The
`Connect to Database` activity in `Main.xaml` was **not** updated: it
still sets `ProviderName="System.Data.SqlClient"` and supplies a
connection string that carries a keyword the modern provider rejects:

```
Provider=SQLOLEDB;Server=sqlprod02;Database=Finance;Integrated Security=SSPI;Encrypt=true
```

Under the modern runtime the connection-string parser
(`Microsoft.Data.SqlClient`) does not recognize the `Provider` keyword
and throws:

```
System.ArgumentException: Keyword not supported: 'Provider'.
```

UiPath wraps it as `Execute Query: A database error occurred`. The fault
is the **provider/keyword configuration**, raised while opening the
connection — not the SQL, not the connection wiring/scope, not a
timeout, and not the database.

This maps to the **Execute Query failures playbook, BRANCH 2 — driver /
provider mismatch after migration**
(`references/activity-packages/database-activities/playbooks/execute-query-failures.md`).

**What went wrong:** The `InvoiceReconciliation` job (started
2026-05-28T07:32:11Z) faulted ~1.5 seconds after launch — at the
connect step, before any query ran. The failure began immediately after
the Windows-Legacy → Windows migration.

**Why:** The legacy `System.Data.SqlClient` provider and its
OLE-DB-style connection-string keywords (`Provider=SQLOLEDB`) are not the
modern default after migration. `Microsoft.Data.SqlClient` rejects the
`Provider` keyword outright. The fix is to move to the modern provider
and connection-string keyword form, and ensure that provider's driver is
present on every Robot host.

This is **not** a null/out-of-scope connection, **not** a SQL syntax
error / unsafe concatenation, **not** a command timeout, **not** a
CLR-level crash (`0xE0434352`), **not** a wrong-activity-type issue, and
**not** a database/network outage. The exception is thrown by the
connection-string parser before the connection even opens.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: `InvoiceReconciliation` — Faulted at 2026-05-28T07:32:12.871Z (ran ~1.5 seconds)
- Folder: `Finance Automation` (key `5e2c9a7b-1d4f-4a6c-b3e8-7f0a2c5d9b1e`)
- `uip or jobs get <key> --output json` → `Info`:
  `Execute Query: A database error occurred` wrapping
  `System.ArgumentException: Keyword not supported: 'Provider'.`
  raised in the `Microsoft.Data.SqlClient` connection-string parser at
  `DatabaseConnect "Connect to Database"`.

### Database Activities (Root Cause)
- `uip or jobs logs <key> --output json` Trace line (the smoking gun) shows the connect attempt:
  `Connect to Database: opening connection with ProviderName 'System.Data.SqlClient' and connection string 'Provider=SQLOLEDB;Server=sqlprod02;Database=Finance;Integrated Security=SSPI;Encrypt=true'`
- `process/project.json` → `targetFramework: "Windows"` confirms the project was migrated off Windows - Legacy.
- `process/Main.xaml` `Connect to Database` activity sets `ProviderName="System.Data.SqlClient"` with the `Provider=SQLOLEDB;...` connection string — the legacy provider/keyword combination the modern runtime rejects.

---

**Immediate fix:**

### Database Activities (Root Cause)

1. **Switch the provider to `Microsoft.Data.SqlClient` and fix the rejected keyword(s).**
   - **Why:** On a **Windows** (.NET 6+) project, `System.Data.SqlClient` is not the modern default, and `Microsoft.Data.SqlClient` rejects the OLE-DB `Provider=SQLOLEDB` keyword with `Keyword not supported: 'Provider'`.
   - **Where:** In `Main.xaml`, on the `Connect to Database` activity, set `ProviderName="Microsoft.Data.SqlClient"`. Remove `Provider=SQLOLEDB;` from the connection string and use the modern SqlClient keyword form, e.g. `Server=sqlprod02;Database=Finance;Integrated Security=true;Encrypt=true`.
   - **Who:** RPA developer
   - **Source:** `database-activities/playbooks/execute-query-failures.md` (Branch 2 — driver/provider mismatch after migration)

2. **Confirm the `Microsoft.Data.SqlClient` driver is installed on every Robot host.**
   - **Why:** The legacy runtime bundled providers implicitly; after migration the matching managed/ODBC driver must be present on each Robot host, not only the developer machine.
   - **Who:** RPA developer / infrastructure

---

**Preventive fix:**

1. **Studio** — After migrating any project from **Windows - Legacy** to **Windows**, audit every Database activity's `ProviderName` and `ConnectionString` and update legacy providers/keywords.
   - **Why:** Provider/keyword mismatches are the canonical post-migration Database-activity failure (branch 2).
   - **Who:** RPA developer

2. **Orchestrator / Infrastructure** — Standardize the required database driver on all Robot hosts as part of the migration checklist.
   - **Why:** Prevents dev-vs-prod skew where the connection opens on the developer machine but fails on the Robot.
   - **Who:** RPA lead / infrastructure

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Post-migration provider/keyword mismatch: the Windows project still uses `System.Data.SqlClient` with `Provider=SQLOLEDB`, which `Microsoft.Data.SqlClient` rejects | High | Confirmed | Yes | `Keyword not supported: 'Provider'` ArgumentException in the wrapped exception + `targetFramework: "Windows"` in `project.json` + `ProviderName="System.Data.SqlClient"` and `Provider=SQLOLEDB;...` in `Main.xaml` + connect-step Trace in job logs | Switch to `Microsoft.Data.SqlClient`, drop the `Provider` keyword, confirm driver installed on Robot host |

---

Would you like help applying the fix — editing `Main.xaml` to switch the
provider to `Microsoft.Data.SqlClient` and clean up the connection
string? I can also clean up the `.local/investigations/` folder if you
no longer need it.
