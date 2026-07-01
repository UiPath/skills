# Final Resolution

---

**Root Cause:** The `CustomerLedgerSync` workflow has its Database
activity fields **crossed**. The SQL `SELECT` was pasted into the
`Connect to Database` activity's `ConnectionString` property, and the
real connection string was pasted into the `Execute Query` activity's
`Sql` property. In `Main.xaml`:

```
Connect to Database  -> ConnectionString = "SELECT CustomerId, Balance, Region FROM CustomerLedger WHERE Region = 'EU'"
Execute Query        -> Sql              = "Server=sqlprod07;Database=Sales;Integrated Security=true;Encrypt=true"
```

When the `Connect to Database` step runs, the connection-string parser
(`Microsoft.Data.SqlClient`) tries to parse the `SELECT` text as a
connection string and throws:

```
System.ArgumentException: Format of the initialization string does not conform to specification starting at index 0.
```

UiPath wraps it as `Connect to Database: A database error occurred`. The
fault is a **connection-string parse failure** at the connect step,
raised before any SQL ever executes — the parser cannot make
`key=value;` pairs out of `SELECT CustomerId, Balance, ...`.

This maps to the **Execute Query failures playbook, BRANCH 4 — query
text in the connection-string property**
(`references/activity-packages/database-activities/playbooks/execute-query-failures.md`).

**What went wrong:** The `CustomerLedgerSync` job (started
2026-05-29T09:14:00Z) faulted ~1.2 seconds after launch — at the connect
step, before any query ran. It faults on every run because the
misconfiguration is static in the workflow.

**Why:** The two field values were swapped between the two activities.
The connection-string parser reads its input as a list of `keyword=value`
pairs separated by `;`. A `SELECT` statement is not that shape, so the
parser rejects it at index 0 with "Format of the initialization string
does not conform to specification". The `Execute Query` activity never
runs, because the connect step throws first.

This is **NOT** branch 3 (a SQL syntax error / unsafe concatenation): the
message is "Format of the initialization string does not conform to
specification", **NOT** "Incorrect syntax near ...". The parser that
fails is the **connection-string** parser, not the SQL engine — no SQL
was ever sent to a database. It is also **not** a null/out-of-scope
connection (branch 1), **not** a driver/provider mismatch (branch 2),
**not** a command timeout (branch 5), **not** a CLR-level crash
(`0xE0434352`, branch 6), **not** a wrong-activity-type issue (branch 7),
and **not** a database/network outage. Do not read the error as "the
database does not exist" — the parser fails before any database lookup;
the offending value is SQL text, not a database name.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: `CustomerLedgerSync` — Faulted at 2026-05-29T09:14:01.623Z (ran ~1.2 seconds)
- Folder: `Finance Automation` (key `6a3d9f1c-2e5b-4d8a-9c7f-1b4e0a6d3c8f`)
- `uip or jobs get <key> --output json` -> `Info`:
  `Connect to Database: A database error occurred` wrapping
  `System.ArgumentException: Format of the initialization string does not conform to specification starting at index 0.`
  raised in the `Microsoft.Data.SqlClient` connection-string parser at
  `DatabaseConnect "Connect to Database"`.

### Database Activities (Root Cause)
- `uip or jobs logs <key> --output json` Trace line (the smoking gun) shows the connect attempt reading the SELECT as a connection string:
  `Connect to Database: opening connection with ProviderName 'Microsoft.Data.SqlClient' and connection string 'SELECT CustomerId, Balance, Region FROM CustomerLedger WHERE Region = ''EU'''`
- `process/Main.xaml` `Connect to Database` activity's `ConnectionString` InArgument is the SELECT text; the `Execute Query` activity's `Sql` InArgument is `Server=sqlprod07;Database=Sales;Integrated Security=true;Encrypt=true` — the two fields are crossed.

---

**Immediate fix:**

### Database Activities (Root Cause)

1. **Un-cross the fields — put the connection string in `ConnectionString` and the SELECT in `Sql`.**
   - **Why:** The connection-string parser cannot parse a `SELECT` statement; it expects `keyword=value;` pairs. The SELECT belongs in the query property, and the `Server=...;Database=...;...` string belongs in the connection property.
   - **Where:** In `Main.xaml`, set the `Connect to Database` activity's `ConnectionString` to `Server=sqlprod07;Database=Sales;Integrated Security=true;Encrypt=true`, and set the `Execute Query` activity's `Sql` to `SELECT CustomerId, Balance, Region FROM CustomerLedger WHERE Region = 'EU'`.
   - **Who:** RPA developer
   - **Source:** `database-activities/playbooks/execute-query-failures.md` (Branch 4 — query text in the connection-string property)

2. **Balance the quotes in the connection string.**
   - **Why:** A stray/unbalanced quote in the connection string truncates the parsed value and produces the same class of connection-string parse error. Confirm the corrected `ConnectionString` has matched quotes after the swap.
   - **Who:** RPA developer

---

**Preventive fix:**

1. **Studio** — When configuring Database activities, verify at design time that the `ConnectionString` field holds `Server=...;Database=...;...` (or a DSN) and the `Sql` field holds the statement. Do not cross them.
   - **Why:** Crossed fields are a static misconfiguration that faults on every run (branch 4).
   - **Who:** RPA developer

2. **Studio** — Add workflow validation / a peer review check that flags a `ConnectionString` value beginning with a SQL verb (`SELECT`/`INSERT`/`UPDATE`/`DELETE`) and a `Sql` value shaped like a connection string.
   - **Why:** Catches the crossed-fields mistake before publish.
   - **Who:** RPA lead

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Crossed fields: the SQL SELECT was placed in the Connect to Database `ConnectionString` property, so the connection-string parser rejects it with "Format of the initialization string does not conform to specification" | High | Confirmed | Yes | "Format of the initialization string does not conform to specification" ArgumentException in the wrapped exception at `Connect to Database` + the connect-step Trace showing the SELECT used as a connection string + `ConnectionString` = SELECT and `Sql` = connection string in `Main.xaml` | Move the SELECT to `Sql` and the connection string to `ConnectionString`; balance the quotes |

---

Would you like help applying the fix — editing `Main.xaml` to swap the
SELECT and the connection string back into their correct
`Sql` / `ConnectionString` properties? I can also clean up the
`.local/investigations/` folder if you no longer need it.
