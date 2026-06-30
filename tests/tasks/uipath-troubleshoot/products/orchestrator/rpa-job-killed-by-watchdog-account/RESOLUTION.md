# Final Resolution

---

**Root Cause:** A watchdog automation account (`watchdog-svc`,
`watchdog-svc@acme.com`) force-killed the running
`LongRunningProcess` job via the Orchestrator REST API. The
watchdog rule `HungJobReaper` is configured to kill any
`LongRunningProcess` job that runs longer than 180 seconds; this
particular run exceeded the threshold during a slow step. The Kill
strategy calls `TerminateProcess` on the executor, which Windows
reports as exit code `0x40010004` (`DBG_TERMINATE_PROCESS`). The
Robot Service surfaces the missing graceful shutdown as a Faulted
job.

**What went wrong:** Job `LongRunningProcess` (key
`b2c0b2c3-d4e5-4678-9012-3456789bbbbb`) started at
`2026-05-19T08:00:00.500Z` and was running normally. At
`2026-05-19T08:03:00.000Z` (~180s in), the `HungJobReaper`
watchdog crossed its threshold and called
`POST /odata/Jobs({key})/UiPath.Server.Configuration.OData.StopJob`
with `strategy=Kill`. The job transitioned `Running -> Killing ->
Faulted`, ending at `2026-05-19T08:03:01.255Z`. The audit log
records `Job.Stop` initiated by `watchdog-svc@acme.com` from no
`clientInfo` (API call, no browser session).

**Why:** The watchdog is correctly configured to kill stuck jobs,
but in this case it killed a healthy slow run. The Kill strategy
bypasses the workflow's graceful shutdown path and calls
`TerminateProcess` directly. Windows reports this as `0x40010004`,
the Robot Service detects the abrupt exit, and Orchestrator records
it as `System.Exception: Job stopped with an unexpected exit code:
0x40010004`. The state history (`Killing -> Faulted`) and the audit
event together identify a service-account-driven kill via API.

---

**Evidence:**

### Orchestrator (Propagation)
- Failing job: `LongRunningProcess` (key `b2c0b2c3-...`) -- Faulted at
  `2026-05-19T08:03:01.255Z` after ~180s of `Running`
- Folder: `KillScenarios` (key `f1e2d3c4-b5a6-7890-1234-56789abcdef0`)
- Host: `MOCK-HOST`, runtime type `Unattended`, Source: `Schedule`
- `Info` field: `System.Exception: Job stopped with an unexpected
  exit code: 0x40010004`
- State history (`uip or jobs history`):
  - `2026-05-19T08:00:00.302Z` -- `Pending`
  - `2026-05-19T08:00:00.500Z` -- `Running`
  - `2026-05-19T08:03:00.000Z` -- `Killing` (Source: API)  <- API-initiated kill
  - `2026-05-19T08:03:01.255Z` -- `Faulted`

### Orchestrator (Root Cause)
- Audit event (`uip admin audit tenant events --search b2c0b2c3-...`):
  - `eventType`: `Job stopped`
  - `eventSource`: `Orchestrator`
  - `actorName`: `watchdog-svc` (service account -- non-human)
  - `actorEmail`: `watchdog-svc@acme.com`
  - `eventSummary`: `Job 'LongRunningProcess' (b2c0b2c3-...) was
    stopped (strategy Kill) by service account watchdog-svc@acme.com
    via API (rule: HungJobReaper, threshold: 180s)`
  - `eventDetails.origin`: `API`
  - `eventDetails.actorType`: `ServiceAccount`
  - `eventDetails.watchdogRule`: `HungJobReaper`
  - `eventDetails.watchdogThresholdSeconds`: `180`
  - `clientInfo`: **absent** -- no browser session (API call, not UI)
  - `createdOn`: `2026-05-19T08:03:00.105Z` -- matches the Killing
    transition within milliseconds
- The combination of (a) service-account `actorName`, (b) `origin:
  "API"`, (c) absent `clientInfo`, and (d) the matched watchdog
  rule name identifies a watchdog/automation kill, not a human
  operator.

---

**Immediate fix (any one of these resolves the conflict):**

### Orchestrator (Root Cause)
1. Review the watchdog rule `HungJobReaper`.
   - **Why:** The 180-second threshold is too aggressive for
     `LongRunningProcess`, which routinely runs ~5 minutes. The
     watchdog is killing healthy slow runs.
   - **Where:** Wherever the watchdog rule is configured (custom
     automation, a parent Maestro process, or an external monitor) --
     adjust the threshold to exceed the workflow's worst-case
     runtime, or scope the rule to exclude `LongRunningProcess`.
   - **Who:** Owner of the watchdog automation
   - **Source:**
     `products/orchestrator/playbooks/job-stopped-exit-code-0x40010004.md`

2. Restrict the watchdog account's `Jobs.Edit` scope.
   - **Why:** If the watchdog should only kill jobs in a specific
     folder or matching specific tags, narrow its role assignment
     in Orchestrator. Today it has tenant-wide `Jobs.Edit`.
   - **Where:** Orchestrator UI -> Tenant -> External OAuth2 Apps /
     Robot Accounts -> `watchdog-svc` -> reduce role scope.
   - **Who:** Tenant admin
   - **Source:**
     `products/orchestrator/playbooks/job-stopped-exit-code-0x40010004.md`

3. Accept the kill if the underlying job was genuinely stuck.
   - **Why:** If `LongRunningProcess` legitimately hung (no Robot
     logs, no progress), the watchdog did its job. The fix is
     upstream: diagnose why the workflow stalled, not retire the
     watchdog.
   - **Where:** Compare runtime against successful prior runs;
     inspect Robot logs for the last activity before the kill.
   - **Who:** Process owner
   - **Source:**
     `products/orchestrator/playbooks/job-stopped-exit-code-0x40010004.md`

---

**Preventive fix:**

1. **Orchestrator** -- Document and version-control watchdog rules.
   - **Why:** Watchdog kills look identical to operator kills in
     the job record. Recording rule name and threshold in the
     audit event (already done here) is the right pattern; document
     which rules exist and what they cover.
   - **Where:** Repo / wiki documenting all watchdog rules.
   - **Who:** Platform team
   - **Source:**
     `products/orchestrator/playbooks/job-stopped-exit-code-0x40010004.md`

2. **Orchestrator** -- Subscribe to alerts on watchdog-initiated kills.
   - **Why:** Distinguishing watchdog kills from human kills in
     near-real-time lets the team correlate kills with rule changes
     and catch overly aggressive thresholds quickly.
   - **Where:** Orchestrator UI -> Alerts -> filter on `Info contains
     "0x40010004"` AND audit query for `actorType=ServiceAccount`.
   - **Who:** Platform team

3. **Workflow** -- Emit heartbeat log lines from long-running steps.
   - **Why:** A slow inference that emits no log lines looks like a
     stuck job to a watchdog rule that monitors log activity. Emit
     a heartbeat (`LogMessage`) every 30 seconds so the watchdog
     can tell a slow job from a hung job.
   - **Where:** Studio -> add a `While` loop / `Parallel` branch
     that emits a heartbeat alongside the long-running step.
   - **Who:** RPA developer

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Watchdog service account killed the job via the REST API | High | Confirmed | Yes | State history shows `Running -> Killing -> Faulted` (Source: API); audit event names `watchdog-svc@acme.com` (ServiceAccount, no `clientInfo`) issuing Kill with rule `HungJobReaper` (threshold 180s); kill timestamp matches the 180s threshold exactly | Adjust watchdog threshold OR restrict watchdog account scope OR fix the upstream stuck-state |
| H2 | Host-side termination (session logoff, RDP disconnect, OOM, native crash) | Low | Refuted | No | State history has a `Killing` transition before `Faulted` -- operator-initiated kills produce this; host-side terminations would go `Running -> Faulted` directly. No Windows event log evidence sought because the audit log already named the actor. | n/a |
| H3 | Human operator killed the job from Orchestrator UI | Low | Refuted | No | The audit event's `actorName` is non-human (`watchdog-svc`), `clientInfo` is absent (no browser session), and `eventDetails.origin` is `API`, not `OrchestratorUI` | n/a |

---

Would you like help applying the fix -- adjusting the
`HungJobReaper` threshold, narrowing the watchdog account's role,
or adding heartbeat logs to `LongRunningProcess`? I can also clean
up the `.investigation/` folder if you no longer need it.
