# Final Resolution

---

**Root Cause:** The `StagingCleanup` workflow uses an **`Execute Query`**
activity — which is for `SELECT` statements and returns a `DataTable` —
to run a **modification** statement:

```
DELETE FROM TempStaging WHERE LoadDate < '2026-05-01'
```

A modification (`DELETE`/`INSERT`/`UPDATE`) produces **no result set**, so
`Execute Query` always hands back an **empty `DataTable`** (`dt_Deleted`,
0 rows). The downstream `Assign` activity "Compute deleted count"
evaluates:

```
deletedCount = CInt(dt_Deleted.Rows(0)(0))
```

Reading `Rows(0)` on an empty `DataTable` throws:

```
System.ArgumentOutOfRangeException: There is no row at position 0.
```

UiPath surfaces it as `Assign: There is no row at position 0.` The fault
is raised at the `Assign`, but the originating defect is the **wrong
activity choice** at the `Execute Query` — the empty `DataTable` is the
structural consequence of running a `DELETE` through a `SELECT` activity.

This maps to the **Execute Query failures playbook, BRANCH 7 — wrong
activity for the statement type**
(`references/activity-packages/database-activities/playbooks/execute-query-failures.md`).

**What went wrong:** The nightly `StagingCleanup` job (started
2026-05-29T03:05:00.402Z) faulted ~0.9 seconds after launch. The
`Connect to Database` step succeeded and the `DELETE` executed; the fault
came at the `Assign` that tried to read a deleted-row count out of the
(empty) `DataTable`.

**Why:** `Execute Query` materializes a query's result set into a
`DataTable`. A `DELETE` returns no result set, so the `DataTable` is
empty on every run regardless of how many rows the `DELETE` removed. The
row count of a modification lives in `Execute Non Query`'s
`AffectedRecords` output (an `Int32`), not in a `DataTable`. The correct
fix is to use the activity that matches the statement verb.

This is **not** branch 1 (the connection opened fine — see the
`Microsoft.Data.SqlClient` connect Trace), **not** branch 2 (no
provider/keyword mismatch; the project is `Windows` and the provider is
already `Microsoft.Data.SqlClient`), **not** branch 3 (the `DELETE`
parsed and ran — no syntax error), **not** branch 5 (it faulted in
~0.9 s, no `Timeout expired`), **not** branch 6 (a clean activity-level
`ArgumentOutOfRangeException`, not a `0xE0434352` process exit), and
**not a database outage**. It is also **not a data problem** — the
`DELETE` ran successfully; `Execute Query` returns an empty `DataTable`
for any modification, so the `Rows(0)` fault is structural, not
dependent on how many rows matched. And the fix is **not** to add an
empty-`DataTable` guard / `Try-Catch` around the existing `Execute Query`
(that is the playbook's named anti-pattern — it hides the wrong-activity
defect and leaves the deleted-row count unobtainable).

---

**Evidence:**

### Orchestrator (Propagation)
- Job: `StagingCleanup` — Faulted at 2026-05-29T03:05:01.302Z (ran ~0.9 seconds)
- Folder: `Data Operations` (key `8c4e1a7d-3f6b-4e2a-9d8c-0a5f3b7e1c4d`)
- `uip or jobs get <key> --output json` → `Info`:
  `Assign: There is no row at position 0.` wrapping
  `System.ArgumentOutOfRangeException: There is no row at position 0.`
  raised at `System.Data.DataRowCollection.get_Item(Int32 index)`, stack
  `at Assign "Compute deleted count"` → `at Sequence "Main Sequence"` →
  `at Main "Main"`.

### Database Activities (Root Cause)
- `uip or jobs logs <key> --output json` Trace lines (the smoking gun):
  - `Execute Query: executing 'DELETE FROM TempStaging WHERE LoadDate < ''2026-05-01''' (CommandType=Text); result set returned 0 rows` — `Execute Query` ran a `DELETE` and produced **0 rows**.
  - `Assign 'Compute deleted count': evaluating CInt(dt_Deleted.Rows(0)(0)) against an empty DataTable (0 rows)` — the empty `DataTable` reaches the `Rows(0)` read.
- `process/Main.xaml` → an `ExecuteQuery` activity whose `Sql` is
  `"DELETE FROM TempStaging WHERE LoadDate < '2026-05-01'"`, output
  `DataTable` `dt_Deleted`; followed by an `Assign` "Compute deleted
  count" setting `deletedCount = CInt(dt_Deleted.Rows(0)(0))`.
- `process/Main.xaml` → `Connect to Database` uses
  `ProviderName="Microsoft.Data.SqlClient"` with a clean connection
  string — the connection is fine, ruling out branches 1 and 2.

---

**Immediate fix:**

### Database Activities (Root Cause)

1. **Replace the `Execute Query` with an `Execute Non Query` for the `DELETE`.**
   - **Why:** `Execute Query` is for `SELECT` and returns a `DataTable`; a `DELETE`/`INSERT`/`UPDATE` returns no result set, so the `DataTable` is always empty. `Execute Non Query` is the activity for modifications and exposes the affected-row count.
   - **Where:** In `Main.xaml`, swap the `ExecuteQuery` node (Sql `"DELETE FROM TempStaging WHERE LoadDate < '2026-05-01'"`) for an `ExecuteNonQuery` activity with the same `ExistingDbConnection="[dbConnection]"` and `Sql`.
   - **Who:** RPA developer
   - **Source:** `database-activities/playbooks/execute-query-failures.md` (Branch 7 — wrong activity for the statement type)

2. **Read the deleted-row count from `AffectedRecords`, not from a `DataTable`.**
   - **Why:** `Execute Non Query` returns the affected-row count in its `AffectedRecords` output, an `Int32`. Bind that to `deletedCount` directly: `deletedCount = AffectedRecords`. Remove the `CInt(dt_Deleted.Rows(0)(0))` expression and the `dt_Deleted` variable.
   - **Who:** RPA developer

> Do **not** "fix" this by wrapping the `Execute Query` in a `Try-Catch`
> or adding an empty-`DataTable` guard (`If dt_Deleted.Rows.Count > 0`).
> That swallows the wrong-activity defect, leaves the deleted-row count
> permanently unavailable, and is the playbook's named anti-pattern.

---

**Preventive fix:**

1. **Studio** — Choose the Database activity by statement verb up front: `Execute Query` for `SELECT` (output → `DataTable`), `Execute Non Query` for `INSERT`/`UPDATE`/`DELETE`/DDL (output → `AffectedRecords`, an `Int32`). Bind the output to the matching type.
   - **Why:** Using `Execute Query` for a modification returns an empty/meaningless `DataTable` and faults any downstream code that assumes rows (branch 7).
   - **Who:** RPA developer

2. **Code review** — Flag any `Execute Query` whose `Sql` begins with `INSERT`/`UPDATE`/`DELETE`/`MERGE`/DDL during review.
   - **Why:** Catches the wrong-activity mistake before it ships to a nightly schedule.
   - **Who:** RPA lead

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Wrong activity for the statement type: `Execute Query` (a SELECT activity) was used to run a `DELETE`, so the `DataTable` is always empty and the downstream `Assign` reading `Rows(0)` throws `ArgumentOutOfRangeException` | High | Confirmed | Yes | `Execute Query: executing 'DELETE ...'; result set returned 0 rows` Trace + `Assign ... evaluating CInt(dt_Deleted.Rows(0)(0)) against an empty DataTable` Trace + `ArgumentOutOfRangeException: There is no row at position 0` in jobs get `Info` + `Main.xaml` `ExecuteQuery` running a `DELETE` feeding an `Assign` that reads `Rows(0)` | Switch the `DELETE` to `Execute Non Query`, read `AffectedRecords` (Int32) for the count, drop the empty `DataTable` read |

---

Would you like help applying the fix — editing `Main.xaml` to replace
the `Execute Query` with an `Execute Non Query` and rewire
`deletedCount` to its `AffectedRecords` output? I can also clean up the
`.local/investigations/` folder if you no longer need it.
