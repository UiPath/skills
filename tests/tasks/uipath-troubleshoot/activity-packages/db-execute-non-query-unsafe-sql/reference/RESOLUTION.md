# Final Resolution

---

**Root Cause:** The `Execute Non Query` activity in `Main.xaml` builds its
`Sql` text by **string concatenation**:

```
"INSERT INTO Customers (Name, City) VALUES ('" + in_CustomerName + "', '" + in_City + "')"
```

At runtime `in_CustomerName` is `O'Brien`. The embedded apostrophe closes
the SQL string literal early, so the statement the provider actually
receives is malformed:

```
INSERT INTO Customers (Name, City) VALUES ('O'Brien', 'Austin')
```

SQL Server parses `'O'` as a complete string, then chokes on the trailing
`Brien', 'Austin')`. It rejects the statement with
`Unclosed quotation mark after the character string ')'.` /
`Incorrect syntax near 'Brien'.`, which UiPath wraps as
`Execute Non Query: A database error occurred`.

This maps to the **Execute Non Query failures playbook, BRANCH 2 — unsafe
SQL construction / parameter mapping**
(`references/activity-packages/database-activities/playbooks/execute-non-query-failures.md`).

**What went wrong:** The `CustomerUpsert` job (started
2026-06-01T11:20:00Z) faulted ~1.3 seconds after launch. The database is
reachable and the connection opened fine; the failure is the SQL statement
itself, malformed by unsafe concatenation. It only faults on runs whose
customer name contains an apostrophe (or another SQL-significant
character) — which is why it fails on *some* runs, not all.

**Why:** Concatenating a variable directly into a SQL string breaks
whenever the value contains a character that is significant to SQL — an
apostrophe being the classic case. It is also a SQL-injection vector. The
fix is to stop concatenating and let the provider bind each value as a
named parameter.

This is **not** an empty/uninitialized `Sql` (branch 3 —
`CommandText property has not been initialized`), **not** a
stored-procedure output parameter with `Size = 0` (branch 1), **not** a
driver/client library that fails to load (branch 4 — `ErrorCode: 126` /
`DllNotFoundException`), **not** the wrong activity type (this *is* a
modifying `INSERT`, so `Execute Non Query` is correct — not `Execute
Query`), **not** a null/closed/expired connection, and **not** a database
outage. The connection succeeded; only the statement text is broken. The
correct fix is **parameterization**, not escaping or doubling the
apostrophe.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: `CustomerUpsert` — Faulted at 2026-06-01T11:20:01.430Z (ran ~1.3 seconds)
- Folder: `Sales Operations` (key `c7a8b9d0-1e2f-4a3b-8c4d-6e7f80910203`)
- `uip or jobs get <key> --output json` → `Info`:
  `Execute Non Query: A database error occurred` wrapping
  `Microsoft.Data.SqlClient.SqlException ... Unclosed quotation mark after the character string ')'. Incorrect syntax near 'Brien'.`
  raised at `ExecuteNonQuery "Execute Non Query"`.

### Database Activities (Root Cause)
- `uip or jobs logs <key> --output json` Trace line (the smoking gun) shows the **resolved** SQL with the broken quoting:
  `Execute Non Query: executing INSERT INTO Customers (Name, City) VALUES ('O'Brien', 'Austin') against connection 'Server=sqlsales01;Database=CRM'` — the stray apostrophe in `O'Brien` is visible.
- `Main.xaml` `Execute Non Query` activity `Sql` property is the concatenation expression
  `"INSERT INTO Customers (Name, City) VALUES ('" + in_CustomerName + "', '" + in_City + "')"`, with `in_CustomerName` assigned `O'Brien` upstream. There is **no** `Parameters` collection.
- The connection (`Connect to Database`, `Microsoft.Data.SqlClient`) opened successfully — the fault is at the statement, not the connection.

---

**Immediate fix:**

### Database Activities (Root Cause)

1. **Parameterize the statement — do not concatenate.**
   - **Why:** Concatenating `in_CustomerName` into the SQL string breaks on the apostrophe in `O'Brien` and is a SQL-injection risk.
   - **Where:** In `Main.xaml`, change the `Execute Non Query` `Sql` to a static statement with named parameters:
     `INSERT INTO Customers (Name, City) VALUES (@name, @city)`.
     Then add entries to the activity's **Parameters** collection mapping `@name` → `in_CustomerName` and `@city` → `in_City` (direction In, type String). The provider handles quoting and typing, so any value (including `O'Brien`) is bound safely.
   - **Do NOT** instead escape/double the apostrophe (`O''Brien`) or sanitize the input string — that leaves the injection hole open and is fragile against other characters.
   - **Who:** RPA developer
   - **Source:** `database-activities/playbooks/execute-non-query-failures.md` (Branch 2 — unsafe SQL construction / parameter mapping)

---

**Preventive fix:**

1. **Studio** — Parameterize every database statement with named parameters; never build SQL by concatenation.
   - **Why:** Closes both the syntax-fragility (branch 2) and the SQL-injection risk in one move.
   - **Who:** RPA developer

2. **Studio** — For whole-`DataTable` writes, use **Bulk Insert** / **Bulk Update Database** rather than a per-row `Execute Non Query` loop.
   - **Why:** Faster and avoids surfacing type/quote mismatches one row at a time.
   - **Who:** RPA developer

3. **Studio** — Add a workflow analyzer / code-review rule that flags string concatenation feeding a `Sql` property.
   - **Why:** Catches the anti-pattern before it ships.
   - **Who:** RPA lead

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Execute Non Query builds SQL by unsafe string concatenation; the apostrophe in `in_CustomerName` ("O'Brien") closes the literal early, producing malformed SQL | High | Confirmed | Yes | `Unclosed quotation mark` / `Incorrect syntax near 'Brien'` in the wrapped SqlException + resolved SQL `... VALUES ('O'Brien', 'Austin')` in job logs + the concatenation expression in `Main.xaml` (no Parameters collection) | Parameterize with named `@name`/`@city` via the Parameters collection |

---

Would you like help applying the fix — editing `Main.xaml` to use a
parameterized `INSERT` with the Parameters collection? I can also clean up
the `.local/investigations/` folder if you no longer need it.
