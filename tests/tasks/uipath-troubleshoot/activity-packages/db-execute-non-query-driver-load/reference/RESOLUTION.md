# Final Resolution

---

**Root Cause:** The `Execute Non Query` activity in `Main.xaml` runs an
`UPDATE` against an Oracle database using `ProviderName =
"Oracle.DataAccess.Client"`. That provider depends on the Oracle Client
**native** libraries (e.g. `OraOps12.dll`) being installed on the Robot
host. On the host that ran the job those native libraries are **missing
or the wrong bitness**, so the native load fails with
`Failed to load library (ErrorCode: 126)` / `System.DllNotFoundException`.
This is a **host driver / client library** problem — not a SQL, schema,
parameter, or connection-string problem. It maps to
`execute-non-query-failures.md` **Branch 4 (driver / client library not
loadable)**.

**What went wrong:** The `OracleLedgerSync` job (started
2026-05-21T08:15:02Z) faulted ~1.5 seconds after launch, before the SQL
statement could be sent to the database. The provider failed to
initialize because its native client DLL could not be loaded.

**Why:** `ErrorCode: 126` is the Windows "the specified module could not
be found" code surfaced through `System.DllNotFoundException`. The
`Oracle.DataAccess.Client` provider is a thin managed wrapper over the
Oracle Client native libraries; when those libraries are absent — or
present at a bitness that does not match the **process** — the load
fails before any query runs. The project's `targetFramework` is
`Windows`, which means the Robot executes it as a **64-bit** process, so
it requires the **64-bit** Oracle Client. A 32-bit Oracle Client (the
common case when the client was installed to match 32-bit Office or a
developer's machine) does not satisfy a 64-bit process and produces the
same `ErrorCode: 126`.

This is **not** a SQL syntax error, **not** an empty `Sql`, **not** an
output-parameter size issue, **not** a null/expired connection, **not**
the wrong activity, **not** a "database is down" outage, and **not** a
connection-string typo. The statement never reached the database — the
provider could not load its driver.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: `OracleLedgerSync` — Faulted at 2026-05-21T08:15:03.642Z (ran ~1.5 seconds)
- Folder: `Finance Automations` (key `7c3e9a1d-5b8f-4a2c-9e6d-3f1a2b4c5d6e`) — folder exists
- Executing robot: `RobotUser2` on host `MOCK-HOST`
- `ErrorCode: "Robot"` — failure originated on the Robot host, not Orchestrator-side

### Job error (`uip or jobs get`)
- `Info`: `Execute Non Query: A database error occurred. ---> System.DllNotFoundException: Unable to load DLL 'OraOps12.dll' or one of its dependencies: Failed to load library (ErrorCode: 126)`
- Stack: `at ExecuteNonQuery "Execute Non Query"` → `at Sequence "Main Sequence"` → `at Main "Main"`
- Wrapper: `UiPath.Database.Activities.DatabaseException` with inner `System.DllNotFoundException`

### Job logs (`uip or jobs logs --level Error`)
- `[Execute Non Query] A database error occurred. ---> System.DllNotFoundException: Unable to load DLL 'OraOps12.dll' ... Failed to load library (ErrorCode: 126)`
- `The Oracle Data Provider for .NET requires the Oracle Client native libraries to be installed on the host. ErrorCode 126 = the specified module could not be found.`

### Workflow source (`Main.xaml`) — Root Cause
- Activity: `ExecuteNonQuery` (DisplayName "Execute Non Query")
- `ProviderName`: `Oracle.DataAccess.Client` — requires the Oracle Client native libraries
- `Sql`: `UPDATE GL_ENTRIES SET POSTED = 1 WHERE BATCH_ID = :batchId AND POSTED = 0` — well-formed, parameterized; not the cause
- `CommandType`: `Text` (no output parameters → rules out Branch 1)
- `ConnectionString`: well-formed Oracle TNS descriptor → connection-string typo ruled out

### Project (`project.json`) — bitness anchor
- `targetFramework`: `Windows` → the Robot runs this as a **64-bit** process
- Declares `UiPath.Database.Activities` `[1.7.0]` (a current package; rules out a stale-build / patched-version branch)

---

**Immediate fix:**

The fix is **on the Robot host**, not in the workflow, the SQL, or
Orchestrator.

### Robot host (Root Cause)

1. **Install the matching-bitness Oracle Client / database driver on every Robot host that runs this process.**
   - **Why:** `ErrorCode: 126` means the provider's native client DLL (`OraOps12.dll` and its dependencies) could not be found. The provider cannot initialize without it.
   - **What:** Install the **64-bit** Oracle Client (ODP.NET / Instant Client) — match the **process** bitness (`targetFramework: Windows` = 64-bit), **not** the bitness of Office or the developer's machine. A 32-bit client on a 64-bit process reproduces the same `ErrorCode: 126`.
   - **Who:** Platform / host-provisioning team (the person diagnosing here has Orchestrator access only and cannot get on the host — hand this instruction to whoever owns the Robot machine).
   - **Source:** `execute-non-query-failures.md` Branch 4 ("Driver / client library not loadable").

2. **Verify the connection from the host with Configure Connection.**
   - **Why:** After installing the client, confirm the activity can load the driver and reach the database before re-running the job.
   - **Where:** Open the project in Studio on the Robot host → the `Execute Non Query` activity → **Configure Connection** → test against the Oracle data source. A successful test confirms the native client now loads.
   - **Who:** RPA developer / host owner.
   - **Related:** This is the same driver/bitness family as `connect-to-database-failures.md` Branch 2 (provider not registered / architecture mismatch).

3. **Re-run the job once the client is installed and the connection tests clean.**

---

**Preventive fix:**

1. **Robot host provisioning** — Bake the correct-bitness DB client/driver into the Robot host image.
   - **Why:** Driver-load faults are environment drift, not code defects; provisioning the 64-bit Oracle Client as part of host setup prevents the next job from faulting at `ErrorCode: 126`.
   - **Who:** Platform / SRE team.

2. **Studio** — Wrap `Execute Non Query` driver/connection setup so a host-level driver fault is reported distinctly from a SQL fault.
   - **Why:** A `DllNotFoundException` mixed in with generic `A database error occurred` is easy to misroute to the SQL author instead of the host owner. A wrapped, host-naming exception speeds the next incident.
   - **Who:** RPA developer.

3. **Standardize provider choice** — Prefer the fully-managed Oracle provider (`Oracle.ManagedDataAccess.Client`) where the workload allows, since it removes the native-client dependency that causes `ErrorCode: 126`.
   - **Why:** The managed provider ships as a pure .NET assembly with no native client install, eliminating the bitness-mismatch failure mode entirely.
   - **Who:** RPA developer / architecture team.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | The Oracle Client / DB driver is missing or wrong-bitness on the Robot host (native load fails, ErrorCode 126) | High | Confirmed | Yes | `System.DllNotFoundException` loading `OraOps12.dll` + `Failed to load library (ErrorCode: 126)` at the `Execute Non Query` step; `ProviderName = Oracle.DataAccess.Client` (native-client provider); `targetFramework: Windows` (64-bit process); SQL/connection-string well-formed | Install matching-bitness (64-bit) Oracle Client on the host; verify with Configure Connection |
| H2 | SQL syntax / unsafe concatenation (Branch 2) | Low | Rejected | No | `Sql` is a well-formed parameterized `UPDATE`; the inner exception is `DllNotFoundException`, not a provider syntax error | — |
| H3 | Empty `Sql` (Branch 3, `CommandText not initialized`) | Low | Rejected | No | `Sql` is a literal non-empty statement | — |
| H4 | Output-parameter `Size = 0` over ODBC (Branch 1) | Low | Rejected | No | `CommandType: Text`, no output parameters, not an ODBC provider | — |
| H5 | Null / expired connection | Low | Rejected | No | Error is a native driver load failure before any connection use, not `Object reference not set` | — |

---

Would you like help applying the fix — drafting the exact host-side
instruction for the Robot machine owner (install the 64-bit Oracle
Client and verify with Configure Connection), or evaluating a switch to
the fully-managed `Oracle.ManagedDataAccess.Client` provider so the
native-client dependency disappears? I can also clean up the
`.local/investigations/` folder if you no longer need it.
