# Final Resolution

---

**Root Cause:** The `Execute Query` activity in `Main.xaml` builds its
`Sql` text by **string concatenation**:

```
"SELECT * FROM Customers WHERE LastName = '" + in_LastName + "'"
```

At runtime `in_LastName` is `O'Brien`. The embedded apostrophe closes
the SQL string literal early, so the statement the provider actually
receives is malformed:

```
SELECT * FROM Customers WHERE LastName = 'O'Brien'
```

SQL Server parses `'O'` as a complete string, then chokes on the
trailing `Brien'`. It rejects the statement with
`Incorrect syntax near 'Brien'.` / `Unclosed quotation mark after the
character string ''`, which UiPath wraps as
`Execute Query: A database error occurred`.

This maps to the **Execute Query failures playbook, BRANCH 3 — SQL
syntax error / unsafe string concatenation**
(`references/activity-packages/database-activities/playbooks/execute-query-failures.md`).

**What went wrong:** The `CustomerLookup` job (started
2026-05-21T09:14:02Z) faulted ~1.5 seconds after launch. The database
is reachable and the connection opened fine; the failure is the SQL
statement itself, malformed by unsafe concatenation.

**Why:** Concatenating a variable directly into a SQL string breaks
whenever the value contains a character that is significant to SQL — an
apostrophe being the classic case. It is also a SQL-injection vector.
The fix is to stop concatenating and let the provider bind the value as
a parameter.

This is **not** a database outage, **not** a wrong/missing table, **not**
a timeout, **not** a connection problem, **not** a provider/driver
mismatch, and **not** a wrong-activity-type issue. The connection
succeeded; only the statement text is broken.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: `CustomerLookup` — Faulted at 2026-05-21T09:14:03.642Z (ran ~1.5 seconds)
- Folder: `Sales Automation` (key `3a1f6c8e-7b2d-4e9a-8c1f-5d6e7a8b9c0d`)
- `uip or jobs get <key> --output json` → `Info`:
  `Execute Query: A database error occurred` wrapping
  `Microsoft.Data.SqlClient.SqlException ... Incorrect syntax near 'Brien'. Unclosed quotation mark after the character string ''.`
  raised at `ExecuteQuery "Execute Query"`.

### Database Activities (Root Cause)
- `uip or jobs logs <key> --output json` Trace line (the smoking gun) shows the **resolved** SQL with the broken quoting:
  `Execute Query: executing SQL against connection 'Server=sqlprod01;Database=Sales': SELECT * FROM Customers WHERE LastName = 'O'Brien'`
- `Main.xaml` `Execute Query` activity `Sql` property is the concatenation expression
  `"SELECT * FROM Customers WHERE LastName = '" + in_LastName + "'"`, with `in_LastName` defaulting to `O'Brien`.
- The connection (`Connect to Database`, `Microsoft.Data.SqlClient`) opened successfully — the fault is at the query, not the connection.

---

**Immediate fix:**

### Database Activities (Root Cause)

1. **Parameterize the query — do not concatenate.**
   - **Why:** Concatenating `in_LastName` into the SQL string breaks on the apostrophe in `O'Brien` and is a SQL-injection risk.
   - **Where:** In `Main.xaml`, change the `Execute Query` `Sql` to a static statement with a named parameter:
     `SELECT * FROM Customers WHERE LastName = @lastName`.
     Then add an entry to the activity's **Parameters** collection mapping `@lastName` → the `in_LastName` variable (direction In, type String). The provider handles quoting and typing, so any value (including `O'Brien`) is bound safely.
   - **Who:** RPA developer
   - **Source:** `database-activities/playbooks/execute-query-failures.md` (Branch 3 — SQL syntax / unsafe concatenation)

---

**Preventive fix:**

1. **Studio** — Parameterize every database query with named parameters; never build SQL by concatenation.
   - **Why:** Closes both the syntax-fragility (branch 3) and the SQL-injection risk in one move.
   - **Who:** RPA developer

2. **Studio** — Add a workflow analyzer / code-review rule that flags string concatenation feeding a `Sql` property.
   - **Why:** Catches the anti-pattern before it ships.
   - **Who:** RPA lead

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Execute Query builds SQL by unsafe string concatenation; the apostrophe in `in_LastName` ("O'Brien") closes the literal early, producing malformed SQL | High | Confirmed | Yes | `Incorrect syntax near 'Brien'` / `Unclosed quotation mark` in the wrapped SqlException + resolved SQL `... LastName = 'O'Brien'` in job logs + the concatenation expression in `Main.xaml` | Parameterize with a named `@lastName` via the Parameters collection |

---

Would you like help applying the fix — editing `Main.xaml` to use a
parameterized query with the Parameters collection? I can also clean up
the `.local/investigations/` folder if you no longer need it.
