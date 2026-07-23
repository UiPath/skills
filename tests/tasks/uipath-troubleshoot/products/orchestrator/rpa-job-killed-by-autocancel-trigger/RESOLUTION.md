# Final Resolution

---

**Root Cause:** An auto-cancel trigger (`kill-after-10min`) fired
after the running `LongRunningProcess` job exceeded its configured
10-minute (600s) time budget. The trigger called `Stop` with
`strategy=Kill`, which calls `TerminateProcess` on the executor.
Windows reports the abrupt exit as `0x40010004`
(`DBG_TERMINATE_PROCESS`), and the Robot Service surfaces it as a
Faulted job. The actor recorded in the audit log is `System`, not a
human or service account.

**What went wrong:** Job `LongRunningProcess` (key
`c3c0b2c3-d4e5-4678-9012-3456789ccccc`) started at
`2026-05-19T08:00:00.500Z`. The configured auto-cancel trigger
`kill-after-10min` has a `timeBudgetSeconds: 600` policy. At exactly
`2026-05-19T08:10:00.000Z` (`StartTime + 600s`), the trigger fired
and issued `Stop` with strategy `Kill`. The job transitioned
`Running -> Killing -> Faulted`, ending at
`2026-05-19T08:10:00.875Z`.

**Why:** The Kill strategy bypasses the workflow's graceful
shutdown path and calls `TerminateProcess`. Windows reports this as
`0x40010004`, the Robot Service detects the abrupt exit, and
Orchestrator records it as `System.Exception: Job stopped with an
unexpected exit code: 0x40010004`. The Killing transition timestamp
at exactly +600s, combined with the audit `actorName: "System"`
and `eventDetails.triggerType: "AutoCancel"` with `reason:
"TimeBudgetExceeded"`, identifies the system-initiated
trigger-driven cancel.

---

**Evidence:**

### Orchestrator (Propagation)
- Failing job: `LongRunningProcess` (key `c3c0b2c3-...`) -- Faulted
  at `2026-05-19T08:10:00.875Z` after ~600s of `Running`
- Folder: `KillScenarios` (key `f1e2d3c4-b5a6-7890-1234-56789abcdef0`)
- Host: `MOCK-HOST`, runtime type `Unattended`, Source: `Schedule`
- `Info` field: `System.Exception: Job stopped with an unexpected
  exit code: 0x40010004`
- State history (`uip or jobs history`):
  - `2026-05-19T08:00:00.302Z` -- `Pending`
  - `2026-05-19T08:00:00.500Z` -- `Running`
  - `2026-05-19T08:10:00.000Z` -- `Killing` (Source:
    Trigger:kill-after-10min, Reason: TimeBudgetExceeded)  <- +600s
  - `2026-05-19T08:10:00.875Z` -- `Faulted`

### Orchestrator (Root Cause)
- Audit event (`uip admin audit tenant events --search c3c0b2c3-...`):
  - `eventType`: `Job stopped`
  - `eventSource`: `Orchestrator`
  - `actorName`: `System` (not human, not service account)
  - `actorEmail`: `null`
  - `eventSummary`: `Job 'LongRunningProcess' (c3c0b2c3-...) was
    stopped (strategy Kill) by auto-cancel trigger
    'kill-after-10min' (time budget 600s exceeded)`
  - `eventDetails.actorType`: `System`
  - `eventDetails.origin`: `Trigger`
  - `eventDetails.triggerName`: `kill-after-10min`
  - `eventDetails.triggerType`: `AutoCancel`
  - `eventDetails.timeBudgetSeconds`: `600`
  - `eventDetails.reason`: `TimeBudgetExceeded`
  - `clientInfo`: **absent** -- no browser session, no API client
- The combination of (a) `actorName: "System"`, (b)
  `triggerType: "AutoCancel"`, and (c) Killing transition at
  precisely +600s identifies a trigger-initiated cancel.

---

**Immediate fix (any one of these resolves the conflict):**

### Orchestrator (Root Cause)
1. Raise the time budget on the `kill-after-10min` trigger.
   - **Why:** If `LongRunningProcess` legitimately runs longer than
     10 minutes in some cases, the trigger's threshold is too
     aggressive for this process. Raise it to fit the worst-case
     runtime with margin.
   - **Where:** Orchestrator UI -> Triggers -> `kill-after-10min` ->
     edit the time budget.
   - **Who:** Trigger owner / platform admin
   - **Source:**
     `products/orchestrator/playbooks/job-stopped-exit-code-0x40010004.md`

2. Scope the trigger more narrowly so it does not cover this
   process.
   - **Why:** If the trigger is meant to catch jobs from other
     processes that should never run this long, exclude
     `LongRunningProcess` from the trigger's process filter.
   - **Where:** Orchestrator UI -> Triggers -> `kill-after-10min` ->
     adjust process scope.
   - **Who:** Trigger owner

3. Fix the workflow to consistently finish within the budget.
   - **Why:** If 10 minutes is the right ceiling for this process,
     the workflow is the problem -- profile the slow step and
     optimize (parallelize, cache, batch, switch to async API,
     etc.).
   - **Where:** Studio -> profile and optimize `LongRunningProcess`.
   - **Who:** RPA developer

4. Remove the trigger if it is no longer justified.
   - **Why:** If the original need for the cancel trigger is gone,
     deleting it is the cleanest fix.
   - **Where:** Orchestrator UI -> Triggers -> delete.
   - **Who:** Trigger owner

---

**Preventive fix:**

1. **Orchestrator** -- Document and version-control auto-cancel
   trigger policies.
   - **Why:** Auto-cancel triggers kill silently from the agent's
     perspective. Documenting which triggers exist, what they
     cover, and their thresholds prevents this surprise.
   - **Where:** Repo / wiki documenting all triggers.
   - **Who:** Platform team

2. **Orchestrator** -- Alert on Faulted jobs whose Killing
   transition matches a trigger.
   - **Why:** Trigger-killed jobs look identical to operator-killed
     jobs in the job record. An alert that joins the audit event
     with the trigger inventory surfaces threshold mismatches
     quickly.
   - **Where:** Orchestrator UI -> Alerts.
   - **Who:** Platform team

3. **Workflow** -- Add progress checkpointing for long-running
   steps.
   - **Why:** Trigger kills lose all in-memory work. Persist
     intermediate state so a re-run resumes from the last
     checkpoint.
   - **Where:** Studio -> add Save State / queue updates at logical
     checkpoints.
   - **Who:** RPA developer

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Auto-cancel trigger killed the job after exceeding its time budget | High | Confirmed | Yes | State history shows `Running -> Killing -> Faulted` with Killing at exactly +600s (matches `timeBudgetSeconds: 600`); audit event names `actorName: "System"` with `eventDetails.triggerType: "AutoCancel"`, `triggerName: "kill-after-10min"`, `reason: "TimeBudgetExceeded"` | Raise time budget OR scope trigger more narrowly OR optimize workflow OR remove trigger |
| H2 | Human operator killed the job from Orchestrator UI | Low | Refuted | No | The audit `actorName` is `System`, not a human; `actorEmail` is null; `clientInfo` is absent | n/a |
| H3 | Watchdog service account killed the job via API | Low | Refuted | No | The audit `actorType` is `System`, not `ServiceAccount`; `eventDetails.origin` is `Trigger`, not `API` | n/a |
| H4 | Host-side termination (logoff, OOM, service restart) | Low | Refuted | No | State history has a `Killing` transition before `Faulted` -- operator/trigger kills produce this; host-side terminations would go `Running -> Faulted` directly | n/a |

---

Would you like help applying the fix -- adjusting the
`kill-after-10min` time budget, scoping the trigger to exclude
`LongRunningProcess`, or profiling the workflow's slow step? I can
also clean up the `.investigation/` folder if you no longer need
it.
