# Final Resolution

---

**Root Cause:** Two foreground (UI-interactive) `ForegroundHolder`
jobs were scheduled against the same Robot session with overlapping
start times. The earlier job was still in `Running` state when the
second job tried to start, and the Robot's
single-foreground-job-per-session guard rejected the second start
with `System.InvalidOperationException: A foreground process is
already running. Only one foreground process can run at a time.`

**What went wrong:** A `ForegroundHolder` job (key
`c0a1b2c3-d4e5-4678-9012-3456789abcde`, started
`2026-05-12T10:15:00.500Z`) faulted ~0.7s after start because an
earlier `ForegroundHolder` job (key
`b0a1b2c3-d4e5-4678-9012-3456789abcde`, started
`2026-05-12T10:14:50.000Z`) was still running on the same machine
(`MOCK-HOST`) and still occupied the foreground job slot.

**Why:** `ForegroundHolder` is configured as a foreground process
(`runtimeOptions.requiresUserInteraction: true` in `project.json`,
echoed as `RequiresUserInteraction: true` on the job record). Its
workflow holds the slot for ~60s via a `Delay` activity. Two
triggers fired against this process within a 10-second window — the
earlier one started at 10:14:50Z and was scheduled to complete
around 10:15:50Z, but a second trigger started another job at
10:15:00Z. The Robot enforces a single-foreground-job constraint
per Windows session; the second start raised
`System.InvalidOperationException` and the job faulted immediately.
No UI activities even had a chance to run — the rejection is at
the process-start level, not inside the workflow.

---

**Evidence:**

### Orchestrator (Propagation)
- Failing job: `ForegroundHolder` (key `c0a1b2c3-...`) — Faulted at
  `2026-05-12T10:15:01.218Z` (ran for ~0.72s)
- Failing job type: `Unattended`, `RequiresUserInteraction: true`,
  triggered manually by user `user1` on machine `MOCK-HOST`
- Folder: `ForegroundDemo` (key
  `a1b2c3d4-e5f6-7890-1234-56789abcdef0`)
- Overlapping job in same folder/machine: `ForegroundHolder` (key
  `b0a1b2c3-...`) — `Running` at the time the failing job was
  created (`StartTime: 2026-05-12T10:14:50.000Z`, EndTime
  `2026-05-12T10:15:50.412Z` — i.e. still active when the failing
  job started).
- Failing job's `Info` field contains the exception:
  `System.InvalidOperationException: A foreground process is
  already running. Only one foreground process can run at a time.`

### Orchestrator (Root Cause)
- Robot Service log at `2026-05-12T10:15:01.190Z`:
  `[Robot] Cannot start foreground job 'c0a1b2c3-...'. Another
  foreground job ('b0a1b2c3-...') is currently running on this
  session.`
- Both jobs reference the same `ReleaseName` (`ForegroundHolder`)
  and the same machine — overlap is on a single Robot session, not
  across machines.
- The Robot's foreground constraint is per-session and is enforced
  at job-start time, before the workflow body executes.

---

**Immediate fix (any one of these resolves the conflict):**

### Orchestrator (Root Cause)
1. Sequence the triggers so they cannot overlap.
   - **Why:** The failure is a scheduling collision. Either widen
     the trigger interval (so it exceeds the typical run duration)
     or chain the jobs via a parent workflow that waits for the
     previous run to complete before starting the next.
   - **Where:** Orchestrator UI → Triggers — stagger cron
     expressions, or convert the second trigger to a chained
     dependency.
   - **Who:** RPA developer / scheduler admin
   - **Source:**
     `products/orchestrator/playbooks/foreground-already-running.md`

2. Enable "Run only one job at a time" on the Robot.
   - **Why:** With this setting, subsequent foreground jobs queue
     on the Robot instead of being rejected. The exception is
     replaced with a wait, then a normal start.
   - **Where:** Orchestrator UI → Tenant → Robots → edit the
     affected Robot → Execution Settings → enable "Run only one
     job at a time".
   - **Who:** Tenant admin
   - **Source:**
     `products/orchestrator/playbooks/foreground-already-running.md`

3. Convert `ForegroundHolder` to a background process **if it
   does not actually need UI interaction**.
   - **Why:** The current `Main.xaml` only uses `LogMessage` and
     `Delay` activities — no UI automation. Marking it foreground
     is unnecessary and causes it to compete for the foreground
     slot. Flipping it to background eliminates the contention.
   - **Where:** Studio → Project Settings → "Starts in
     Background" = Yes (sets
     `runtimeOptions.requiresUserInteraction = false` in
     `project.json`) → republish. Alternatively, at the
     deployment layer: Orchestrator UI → Process → Settings →
     "Background Process" = true.
   - **Who:** RPA developer (Studio fix) or admin (Orchestrator
     fix)
   - **Source:**
     `products/orchestrator/playbooks/foreground-already-running.md`

---

**Preventive fix:**

1. **Studio** — Default new projects to background unless they
   genuinely require UI interaction.
   - **Why:** Foreground is exclusive per Windows session.
     Defaulting to background prevents accidental slot
     contention for purely computational or API-only workflows.
   - **Where:** When creating a project, leave "Starts in
     Background" = Yes. Only flip to foreground when the
     workflow uses `UiPath.UIAutomation.Activities` activities
     (`NApplicationCard`, `NClick`, `NTypeInto`, etc.).
   - **Who:** RPA developer
   - **Source:**
     `products/orchestrator/playbooks/foreground-already-running.md`

2. **Orchestrator** — Configure an alert subscription for
   foreground job faults in the `ForegroundDemo` folder.
   - **Why:** Concurrent-foreground rejections look identical
     to other immediate-start failures from Orchestrator's
     summary view. An alert keyed on the exception message
     surfaces the pattern early.
   - **Where:** Orchestrator UI → Alerts → severity "Error" +
     folder filter for `ForegroundDemo`.
   - **Who:** Admin or platform team
   - **Source:**
     https://docs.uipath.com/orchestrator/automation-cloud/latest/user-guide/alerts

3. **Orchestrator** — Audit Robot execution settings.
   - **Why:** "Run only one job at a time" is off by default
     on most Robots, which is correct for background-heavy
     fleets but wrong for any Robot expected to run multiple
     foreground processes.
   - **Where:** Orchestrator UI → Tenant → Robots → for each
     Robot, confirm Execution Settings against the expected
     workload profile.
   - **Who:** Tenant admin

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Concurrent foreground job on the same Robot session blocked the second start | High | Confirmed | Yes | Earlier `ForegroundHolder` job (`b0a1b2c3-...`) still Running when failing job (`c0a1b2c3-...`) started; both `RequiresUserInteraction: true`; failing job's Info contains `System.InvalidOperationException: A foreground process is already running.` | Sequence triggers OR enable "Run only one job at a time" OR convert to background |
| H2 | Missing unattended robot configuration (sibling `#1230` playbook) | Low | Refuted | No | The error is `System.InvalidOperationException` (Robot-side guard), not HTTP 409 / `#1230`. Unattended robot is correctly configured — the earlier job ran successfully on the same Robot. | n/a |

---

Would you like help applying the fix — staggering the triggers,
flipping `requiresUserInteraction` to false in `project.json`, or
enabling "Run only one job at a time" on the Robot? I can also
clean up the `.investigation/` folder if you no longer need it.
