# Final Resolution

---

**Root Cause:** A human operator (`Jane Doe`, `jane.doe@acme.com`)
force-killed the running `LongRunningProcess` job from the
Orchestrator UI via Stop -> Kill. The Kill strategy calls
`TerminateProcess` on the executor, which Windows reports as exit
code `0x40010004` (`DBG_TERMINATE_PROCESS`). The Robot Service
surfaces the missing graceful shutdown as a Faulted job with
`System.Exception: Job stopped with an unexpected exit code:
0x40010004`.

**What went wrong:** Job `LongRunningProcess` (key
`a1c0b2c3-d4e5-4678-9012-3456789aaaaa`) started at
`2026-05-19T08:00:00.500Z` and was running normally. At
`2026-05-19T08:01:30.000Z` (~90s into the run) the operator clicked
Stop -> Kill in Orchestrator. The job transitioned `Running ->
Stopping -> Faulted`, ending at `2026-05-19T08:01:32.105Z`. The
audit log records `Job.Stop` with strategy `Kill` initiated by
`jane.doe@acme.com` from IP `10.50.12.34`.

**Why:** The Kill strategy bypasses the workflow's graceful shutdown
path and calls `TerminateProcess` directly. Windows reports this
as `0x40010004` (`DBG_TERMINATE_PROCESS`), the Robot Service detects
the abrupt exit, and Orchestrator records it as `System.Exception:
Job stopped with an unexpected exit code: 0x40010004`. The state
history (`Stopping -> Faulted`) and the audit event together
distinguish operator-initiated Kill from host-side terminations
(session logoff, OOM, service restart, native crash).

---

**Evidence:**

### Orchestrator (Propagation)
- Failing job: `LongRunningProcess` (key `a1c0b2c3-...`) -- Faulted at
  `2026-05-19T08:01:32.105Z` after ~92s of `Running`
- Folder: `KillScenarios` (key `f1e2d3c4-b5a6-7890-1234-56789abcdef0`)
- Host: `MOCK-HOST`, runtime type `Unattended`
- `Info` field: `System.Exception: Job stopped with an unexpected
  exit code: 0x40010004`
- State history (`uip or jobs history`):
  - `2026-05-19T08:00:00.302Z` -- `Pending`
  - `2026-05-19T08:00:00.500Z` -- `Running`
  - `2026-05-19T08:01:30.000Z` -- `Stopping`  <- operator-initiated
  - `2026-05-19T08:01:32.105Z` -- `Faulted`

### Orchestrator (Root Cause)
- Audit event (`uip admin audit tenant events --search a1c0b2c3-...`):
  - `eventType`: `Job stopped`
  - `eventSource`: `Orchestrator`
  - `actorName`: `Jane Doe`
  - `actorEmail`: `jane.doe@acme.com`
  - `eventSummary`: `Job 'LongRunningProcess' (a1c0b2c3-...) was
    stopped (strategy Kill) by jane.doe@acme.com via Orchestrator UI`
  - `clientInfo.ipAddress`: `10.50.12.34`, `clientInfo.ipCountry`: `US`
  - `createdOn`: `2026-05-19T08:01:30.105Z` -- matches the Stopping
    transition within milliseconds
- The Stopping transition in state history corresponds to the audit
  event timestamp; together they prove the Kill originated in
  Orchestrator, not on the host.

---

**Immediate fix (any one of these resolves the conflict):**

### Orchestrator (Root Cause)
1. Confirm intent with the actor.
   - **Why:** If `jane.doe@acme.com` killed the job deliberately
     (stuck job, runaway behavior), the failure is expected and the
     workflow itself is healthy. No code or config change is needed.
   - **Where:** Talk to the named actor directly.
   - **Who:** Owner of the process / oncall
   - **Source:**
     `products/orchestrator/playbooks/job-stopped-exit-code-0x40010004.md`

2. Train operators to use `SoftStop` before `Kill`.
   - **Why:** `SoftStop` (`uip or jobs stop <key> --strategy
     SoftStop`) lets the workflow's `ShouldStop` path run and exit
     gracefully -- the job finishes as `Stopped`, not `Faulted` with
     this exit code. `Kill` should be reserved for jobs that are
     genuinely stuck and not responding to SoftStop.
   - **Where:** Operator runbook / Orchestrator UI training.
   - **Who:** Operations / platform team
   - **Source:**
     `products/orchestrator/playbooks/job-stopped-exit-code-0x40010004.md`

3. Restrict who holds `Jobs.Edit` on the folder.
   - **Why:** If the kill was unintended (wrong job, accidental
     click), tighten the role so only on-call operators can stop
     running jobs.
   - **Where:** Orchestrator UI -> Roles -> edit the actor's role ->
     remove `Jobs.Edit` for the affected folder.
   - **Who:** Folder admin / tenant admin
   - **Source:**
     `products/orchestrator/playbooks/job-stopped-exit-code-0x40010004.md`

---

**Preventive fix:**

1. **Orchestrator** -- Audit folder permissions.
   - **Why:** `Jobs.Edit` grants both Restart and Stop. Folders
     hosting long-running or high-value processes should grant
     `Jobs.Edit` only to operators, not to all viewers.
   - **Where:** Orchestrator UI -> Tenant -> Folders -> per folder,
     review the principals holding `Jobs.Edit`.
   - **Who:** Tenant admin
   - **Source:**
     `products/orchestrator/playbooks/job-stopped-exit-code-0x40010004.md`

2. **Orchestrator** -- Subscribe to alerts on jobs that end with
   exit code `0x40010004`.
   - **Why:** This exit code is always external termination, never
     a workflow bug. An alert lets the team correlate kills with
     audit events in near-real-time and catch unintended stops.
   - **Where:** Orchestrator UI -> Alerts -> severity Error, filter
     on `Info contains "0x40010004"`.
   - **Who:** Platform team
   - **Source:**
     `products/orchestrator/playbooks/job-stopped-exit-code-0x40010004.md`

3. **Workflow** -- Add checkpointing for long-running steps.
   - **Why:** If the workflow performs work that takes minutes to
     complete, an interrupting Kill loses everything since the last
     state save. Persist intermediate state (Storage Buckets, queue
     items, Maestro persistence) so a re-run resumes rather than
     restarts.
   - **Where:** Studio -> add `Save State` / queue updates at logical
     checkpoints in the workflow.
   - **Who:** RPA developer
   - **Source:**
     `products/orchestrator/playbooks/job-stopped-exit-code-0x40010004.md`

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Operator killed the job from the Orchestrator UI | High | Confirmed | Yes | State history shows `Running -> Stopping -> Faulted`; audit event names `jane.doe@acme.com` issuing `Job.Stop` with strategy `Kill` via Orchestrator UI; timestamps line up within milliseconds | Train operators on SoftStop vs Kill OR restrict `Jobs.Edit` OR confirm intent |
| H2 | Host-side termination (session logoff, RDP disconnect, service restart, OOM, native crash) | Low | Refuted | No | State history has a `Stopping` transition before `Faulted` -- operator-initiated stops produce this; host-side terminations would go `Running -> Faulted` directly. No Windows event log evidence sought because the audit log already named the actor. | n/a |
| H3 | Workflow itself faulted with an unhandled exception | Low | Refuted | No | The `Info` field is `System.Exception: Job stopped with an unexpected exit code: 0x40010004` -- a Robot-service wrapper around an external `TerminateProcess`, not a workflow stack trace. Execution logs show no exception from inside the workflow. | n/a |

---

Would you like help applying the fix -- confirming intent with
`jane.doe@acme.com`, adjusting role assignments, or adding workflow
checkpointing? I can also clean up the `.investigation/` folder if
you no longer need it.
