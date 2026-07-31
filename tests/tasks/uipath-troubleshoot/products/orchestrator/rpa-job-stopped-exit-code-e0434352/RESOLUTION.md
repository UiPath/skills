# Final Resolution

---

**Root Cause:** An **unhandled `System.Collections.Generic.
KeyNotFoundException`** was thrown inside the workflow and escaped
to the process boundary, collapsing to the raw CLR exit code
`0xE0434352` (the code for a managed .NET exception that reached the
process exit). The real exception — recovered from the job's
execution traces — is: *"The given key 'EMEA-NORTH' was not present
in the dictionary"*, thrown at the **"Lookup region total" Assign**
while indexing a `Dictionary` with a key that did not exist. No
top-level Try/Catch or Global Exception Handler caught it, so the
exception escaped to the process boundary and the job `Info`/error
logs carry only the raw exit code — the exception detail stays in the
execution traces. This is the `0xE0434352` branch of the
`job-stopped-generic-exit-code` playbook.

**What went wrong:** Job `aacc44ee-...-1122` (ReportCompiler)
faulted at `2026-06-22T06:00:39Z` with
`System.Exception: Job stopped with an unexpected exit code:
0xE0434352`. The job Info and error logs carry **only** the raw
code — the executor log records the process exit code and points to
the traces. `uip or jobs traces` shows the "Lookup region
total (Assign)" activity Faulted with an unhandled
`KeyNotFoundException` for key `EMEA-NORTH`; every prior activity
succeeded.

**Why it started now:** the data contained a new/renamed region key
(`EMEA-NORTH`) that is absent from the lookup dictionary. Because
the lookup is unguarded and there is no top-level handler, the
exception was fatal and surfaced only as the OS exit code — nothing
caught it before the process boundary.

**Ruled out:**
- **`0x40010004` external kill** — different code; that playbook is
  for `TerminateProcess` (operator Kill / service restart). Here the
  process died from its own managed exception, not an external kill.
- **`0xC0000005` native access violation** — the traced exception is
  a managed `KeyNotFoundException`, not a native crash.
- **Session teardown (`0xC000026B`)** — no logoff/shutdown; the
  fault is in workflow logic.

---

**Evidence:**

### Orchestrator
- Failing job `aacc44ee-...-1122` — ReportCompiler, Faulted
  `2026-06-22T06:00:39.870Z`, `HostMachineName: MOCK-HOST`
- Job `Info`: `System.Exception: Job stopped with an unexpected exit
  code: 0xE0434352`
- Executor log: `Executor process exited with code 0xE0434352 (CLR
  unhandled managed exception). No top-level handler caught it, so
  only the process exit code is logged here. Inspect execution traces
  for the managed exception detail.`
- `uip or jobs traces`: `Lookup region total (Assign)` → **Faulted**,
  `Error.Type: System.Collections.Generic.KeyNotFoundException`,
  `Error.Message: The given key 'EMEA-NORTH' was not present in the
  dictionary`, `Handled: false`; stack trace through
  `Dictionary.get_Item` → `VisualBasicValue.Execute`
- `uip or machines list`: `ReportingRuntime` → `RobotVersion:
  23.4.0` (checked to rule out a known robot-build defect; the
  version is not the cause — the fault is workflow logic)

---

**Immediate fix:**

1. **Guard the dictionary lookup at "Lookup region total".**
   - **Why:** The exception is a missing-key access on a
     `Dictionary`. Check presence before indexing so a new/unknown
     region does not throw.
   - **Where:** Studio → ReportCompiler → the "Lookup region total"
     Assign. Use `dict.ContainsKey(key)` (or `TryGetValue`) and
     handle the missing-key case (default value, skip, or explicit
     business error) instead of `dict(key)` directly.
   - **Who:** Automation developer
   - **Source:**
     `products/orchestrator/playbooks/job-stopped-generic-exit-code.md`
     (0xE0434352 branch)

2. **Add top-level exception handling so the real error is logged,
   not collapsed to an OS code.**
   - **Why:** With no Global Exception Handler / top-level Try-Catch,
     any unhandled exception escapes to the process boundary and
     surfaces only as `0xE0434352`. A handler logs the exception
     type, message, and stack so the next incident is diagnosable
     from the job Info directly.
   - **Where:** Studio → add a Global Exception Handler to the
     project (or wrap Main in Try/Catch) that logs the exception.
   - **Who:** Automation developer

3. **(Not the fix) Do not treat the robot version as the cause.**
   - **Why:** The exit code is produced by the unhandled exception
     itself, not the robot build; upgrading the robot will not stop a
     missing-key access from faulting. The remedy is the guard (fix 1)
     plus the handler (fix 2). Keeping robots on a current, supported
     version is worthwhile fleet hygiene, but it is not the resolution
     for this fault.
   - **Who:** Platform / machine admin (hygiene, separate from the fix)
   - **Source:**
     `products/orchestrator/playbooks/job-stopped-generic-exit-code.md`
     (Prevention)

---

**Preventive fix:**

1. **Workflow** — Never index a dictionary/collection with an
   unvalidated key; use `ContainsKey`/`TryGetValue` and handle the
   miss. Add a Global Exception Handler to every unattended process.
2. **Fleet** — Keep robots on a current, supported version as
   general hygiene (not a substitute for handling the exception).

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Unhandled KeyNotFoundException surfacing as 0xE0434352 (generic-exit-code playbook) | High | Confirmed | Yes | Traces: "Lookup region total" Assign Faulted with unhandled `KeyNotFoundException` (key 'EMEA-NORTH'); 0xE0434352 = CLR managed-exception code; no top-level handler, so only the exit code is logged | Guard the lookup + add Global Exception Handler |
| H2 | External kill (0x40010004) | Low | Refuted | No | Code is 0xE0434352, not 0x40010004; process died from its own managed exception | n/a |
| H3 | Native access violation (0xC0000005) | Low | Refuted | No | Traced exception is managed (KeyNotFoundException), not a native crash | n/a |
| H4 | Session teardown (0xC000026B) | Low | Refuted | No | No logoff/shutdown; fault is in workflow logic | n/a |

---

Would you like help applying the fix — adding the `ContainsKey`
guard at "Lookup region total" or scaffolding a Global Exception
Handler?
