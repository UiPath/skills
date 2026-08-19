# Final Resolution

Here is the investigation result.

---

**Root Cause:** The `Execute Query 'Customer Orders'` activity in `Main.xaml` runs
`SELECT * FROM Customers c INNER JOIN Orders o ON c.CustomerId = o.CustomerId` — a **one-to-many**
join (one customer has many orders). `Execute Query` fills a result `DataTable` whose **schema it
infers from the source columns**, so `CustomerId` (the primary key of `Customers`) is marked a
**unique/primary key** on the `DataTable`. Because the join repeats `CustomerId` once per order, the
result set contains **duplicate `CustomerId` values**, so `DataTable.EnableConstraints()` throws
`System.Data.ConstraintException: Failed to enable constraints. One or more rows contain values
violating non-null, unique, or foreign-key constraints.` The query itself is syntactically valid and
executed — the fault is the **shape of the result set vs. the auto-inferred DataTable schema**.

**What went wrong:** The `CustomerOrderReport` job faulted ~2 seconds in, at `Execute Query`, because
the rows it returned violate a unique constraint the activity inferred on the `CustomerId` column — a
duplicate-key mismatch produced by a `SELECT *` over a one-to-many JOIN, not a SQL syntax error and not
a connection problem.

**Why (full causal chain):**
- `Execute Query 'Customer Orders'` has `Sql = "SELECT * FROM Customers c INNER JOIN Orders o ON c.CustomerId = o.CustomerId"`
  and outputs to a `DataTable` (`dt_CustomerOrders`).
- `Execute Query` uses a schema-filling fill (it derives key/uniqueness and nullability for the result
  `DataTable` from the underlying source columns). `CustomerId` carries the `Customers` primary-key
  metadata, so the `DataTable` gets a unique constraint on `CustomerId`.
- The join is one-to-many: each customer with N orders yields N rows, all sharing the same
  `CustomerId`. The result therefore has duplicate `CustomerId` values.
- When the fill completes and constraint enforcement is (re-)enabled, `DataTable.EnableConstraints()`
  finds the duplicate `CustomerId` rows and throws `System.Data.ConstraintException` — surfaced by
  UiPath as `Execute Query: Failed to enable constraints. One or more rows contain values violating
  non-null, unique, or foreign-key constraints.`
- The connection was fine (Connect to Database succeeded), the SQL parsed and ran, and there is no
  provider syntax error — this is a result-shape-vs-schema fault, distinct from the syntax/connection
  branches.

**Evidence**

### database-activities (Root Cause)
- Faulting activity: `Execute Query 'Customer Orders'` (`ui:ExecuteQuery`) in `Main.xaml`, nested in
  `Sequence 'Main Sequence'`.
- Error: `Execute Query: Failed to enable constraints. One or more rows contain values violating
  non-null, unique, or foreign-key constraints.` The inner exception is `System.Data.ConstraintException`
  thrown at `System.Data.DataTable.EnableConstraints()` → `set_EnforceConstraints` → `DbDataAdapter`
  fill → `UiPath.Database.DatabaseConnection.ExecuteQuery`. There is **no** provider syntax error — the
  statement executed.
- Source: `Sql = "SELECT * FROM Customers c INNER JOIN Orders o ON c.CustomerId = o.CustomerId"` — a
  `SELECT *` over a one-to-many `Customers`→`Orders` join; `CustomerId` (Customers' PK) repeats per
  order. Connection is a valid `ExistingDbConnection` from a successful `Connect to Database`.
- Timeline (job logs): "Connect to Database ended" → "Execute Query 'Customer Orders' started" → the
  constraint error. The fault is at result materialization, not connection or parse time.

### orchestrator (Propagation)
- Job: `CustomerOrderReport`, folder `Reporting`, job key `a2f8c3e1-9d47-4b6a-8e02-1c5f7a9b3d64`.
- State: Running `2026-06-18T07:32:10Z` → Faulted `2026-06-18T07:32:12Z` (~2s). Unattended, `MOCK-HOST`.

**Immediate fix**

### database-activities (Root Cause)
1. **Reshape the query so the returned key column is unique.** Stop using `SELECT *`: select the
   explicit columns the report needs at the intended grain. Since the result is one row per order,
   project the order key (`OrderId`, which is unique) and only the customer columns you need — do not
   return `CustomerId` as if it were the table's unique key. This makes the result set consistent with
   the inferred schema.
   - **Where:** `Main.xaml` — the `Execute Query 'Customer Orders'` `Sql`.
   - **Who:** RPA developer.
2. **Do NOT "fix" it by disabling constraint enforcement or blindly adding `SELECT DISTINCT`.**
   Disabling constraints hides the schema mismatch; `SELECT DISTINCT` does not help here because the
   rows are genuinely different (they differ by order), so the duplicate `CustomerId` remains.
3. **Re-run and confirm** the query returns and the `DataTable` populates without the constraint error.

**Preventive fix**

1. **database-activities** — Select explicit columns at the intended grain rather than `SELECT *`; a
   `SELECT *` over a one-to-many join returns duplicate keys that fail `DataTable` constraint
   enablement (and wastes memory/bandwidth).
2. **database-activities** — When a report is intentionally one-to-many, design the query/`DataTable`
   around the child grain (order-level), not the parent key (customer-level).

**Investigation summary**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | The database has bad/dirty data, or the SQL has a syntax error | Low | Rejected | No | Inner exception is `System.Data.ConstraintException` at `DataTable.EnableConstraints`, not a provider syntax error; the query executed | — |
| H2 | The `SELECT *` over a one-to-many `Customers`→`Orders` JOIN returns duplicate `CustomerId`, violating the unique constraint the Execute Query DataTable schema inferred on that column | High | Confirmed | **Yes** | `Failed to enable constraints` / `ConstraintException`; `Sql` is `SELECT *` over a 1-to-many join repeating `CustomerId`; connection + parse succeeded | Reshape the query to return a unique key at the correct grain (explicit columns); do not disable constraints |

---

The matched playbook's resolution is interactive — I can apply the query reshape to `Main.xaml`
directly. Here are the exact values involved:

```
Project path: <PROJECT_DIR>
File:         Main.xaml
Activity:     Execute Query 'Customer Orders'  (ui:ExecuteQuery)

Current Sql (returns duplicate CustomerId — the inferred unique key):
  SELECT * FROM Customers c INNER JOIN Orders o ON c.CustomerId = o.CustomerId

Fix: select explicit columns at the order grain so the returned key is unique, e.g.
  SELECT o.OrderId, o.OrderDate, o.OrderTotal, c.CustomerName
  FROM Customers c INNER JOIN Orders o ON c.CustomerId = o.CustomerId
(Do NOT SELECT *, do NOT rely on SELECT DISTINCT, and do NOT disable constraint enforcement.)
```
