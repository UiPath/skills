# Final Resolution

---

**Root Cause:** The `Execute Query` activity in `Main.xaml` runs an
expensive, un-indexed query that takes longer than the activity's
`TimeoutMS`. The `Sql` is:

```
SELECT * FROM Orders WHERE UPPER(Notes) LIKE '%urgent refund%'
```

`UPPER(Notes)` wrapped in a leading-wildcard `LIKE` is not sargable, and
`Orders` has no index on `Notes`, so the provider performs a full-table
scan. `TimeoutMS` is left at the default **`30000` (30 s, milliseconds)**.
The scan runs past 30 s, the SQL Server provider aborts the command, and
UiPath surfaces:

```
Execute Query: Timeout expired. The timeout period elapsed prior to
completion of the operation or the server is not responding.
```

This maps to the **Execute Query failures playbook, BRANCH 5 — command
timeout exceeded**
(`references/activity-packages/database-activities/playbooks/execute-query-failures.md`).

**What went wrong:** The `OrderNotesSearch` job (started
2026-05-22T11:02:08Z) faulted ~30 seconds after launch — the run duration
matches `TimeoutMS` almost exactly, the signature of a command that was
killed by its own timeout rather than by the DB being down.

**Why:** This is a **runaway** query, not a legitimately long one. The
predicate `UPPER(Notes) LIKE '%...%'` cannot use an index (the function
and the leading `%` defeat any index on `Notes`), forcing a full scan
that scales with table size. Because the cause is the query plan, raising
`TimeoutMS` alone would only delay the same failure and hold the Robot
hostage longer. The real fix is on the DB side: make the predicate
sargable and add a supporting index (or narrow the result set).

This is **not** a null / out-of-scope connection, **not** a SQL syntax
error, **not** a provider/driver mismatch, **not** a CLR crash
(`0xE0434352`), **not** a wrong-activity-type issue, and **not** a
database outage. The connection opened, the SQL parsed and started
executing — it simply did not finish within the timeout.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: `OrderNotesSearch` — Faulted at 2026-05-22T11:02:38.731Z (ran ~30 seconds, ≈ the 30000 ms `TimeoutMS`)
- Folder: `Sales Automation` (key `7d2e9f1c-3a8b-4c5d-9e6f-2a1b3c4d5e6f`)
- `uip or jobs get <key> --output json` → `Info`:
  `Execute Query: Timeout expired. The timeout period elapsed prior to completion of the operation or the server is not responding.`
  wrapping `Microsoft.Data.SqlClient.SqlException` raised at `ExecuteQuery "Execute Query"`.

### Database Activities (Root Cause)
- `uip or jobs logs <key> --output json` Trace lines (the smoking gun):
  - The connection opened fine: `Connect to Database: connection opened to 'Server=sqlprod01;Database=Sales' ...`.
  - `Execute Query: TimeoutMS=30000; executing SQL ...: SELECT * FROM Orders WHERE UPPER(Notes) LIKE '%URGENT REFUND%'`.
  - `Execute Query: command aborted after 30000 ms; the query did not complete within TimeoutMS. Orders has no index on Notes and UPPER(Notes) is not sargable, so the provider performed a full-table scan.`
- `Main.xaml` `Execute Query` activity: `Sql` is the un-indexed scan above (built from `in_SearchTerm`), and `TimeoutMS="30000"` (the default 30 s).
- The connection (`Connect to Database`, `Microsoft.Data.SqlClient`) opened successfully — the fault is the query DURATION, not the connection or the statement text.

---

**Immediate fix:**

### Database Activities (Root Cause)

1. **Fix the query / index — this is the real fix, not the timeout.**
   - **Why:** The query is a runaway full-table scan; `UPPER(Notes) LIKE '%...%'` is not sargable and `Orders` has no index on `Notes`. Enlarging the timeout on a runaway query only delays the same failure and ties up the Robot longer.
   - **Where:** On the DB side — add an index that supports the search (or a full-text index for substring search on `Notes`), make the predicate sargable (drop the `UPPER(...)` wrap and use a case-insensitive collation, avoid the leading `%` where possible), and `SELECT` only the needed columns instead of `*`. In `Main.xaml`, narrow the `WHERE` so the query returns a bounded result set.
   - **Who:** DBA + RPA developer
   - **Source:** `database-activities/playbooks/execute-query-failures.md` (Branch 5 — command timeout exceeded)

2. **Stopgap only — raise `TimeoutMS` (milliseconds).**
   - **Why:** Acceptable as a *temporary* measure if the run must succeed before the query/index fix lands. It does NOT resolve the runaway query.
   - **Where:** In `Main.xaml`, the `Execute Query` `TimeoutMS` property is in **milliseconds** (default `30000` = 30 s). Raise it above the query's worst observed duration, e.g. `60000` = 60 s. Remove this once the index/query fix is in place.
   - **Who:** RPA developer

---

**Preventive fix:**

1. **Database** — Index columns used in `WHERE`/`JOIN`/`ORDER BY`; for substring search on text, use full-text indexing rather than `LIKE '%...%'`.
   - **Why:** Keeps query duration bounded as the table grows, so it never approaches `TimeoutMS`.
   - **Who:** DBA

2. **Studio** — Set `TimeoutMS` deliberately per query based on its measured worst-case duration; never rely on the default for queries that can scan large tables.
   - **Why:** Surfaces slow queries at design time instead of as production faults.
   - **Who:** RPA developer

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Execute Query runs a runaway un-indexed query (`UPPER(Notes) LIKE '%...%'`, full-table scan) that exceeds the default `TimeoutMS` of 30000 ms, so the provider aborts with `Timeout expired` | High | Confirmed | Yes | `Timeout expired ...` in the wrapped SqlException + ~30 s run duration ≈ `TimeoutMS` + `command aborted after 30000 ms ... full-table scan` Trace line + `TimeoutMS="30000"` and the un-indexed `Sql` in `Main.xaml` | Fix the index/query (sargable predicate + supporting index, narrow the result set); raise `TimeoutMS` (ms) only as a stopgap |

---

Would you like help applying the fix — narrowing the query in `Main.xaml`
and/or raising `TimeoutMS` as a temporary measure while the index lands?
I can also clean up the `.local/investigations/` folder if you no longer
need it.
