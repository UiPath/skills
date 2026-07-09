# Final Resolution

---

**Root Cause:** The `ExpenseValidation` workflow is incorrectly
published as a **foreground** (UI-interactive) process even though its
`Main.xaml` performs no UI interaction — it only uses `LogMessage`
and `Delay` activities. When another foreground job
(`AttendedReportJob`, key `e1f2a3b4-...`) was already running on the
same Robot session, the Robot rejected the start of
`ExpenseValidation` (key `d1e2f3a4-...`) with
`System.InvalidOperationException: A foreground process is already
running. Only one foreground process can run at a time.` The
misconfiguration is the actionable defect — the workflow has no
business holding the foreground slot at all.

**What went wrong:** A `ExpenseValidation` job (key
`d1e2f3a4-b5c6-4789-abcd-ef0123456789`, created
`2026-05-13T14:20:45.302Z`, started 14:20:45.500Z) faulted ~0.7s
after start. A `AttendedReportJob` job (key
`e1f2a3b4-c5d6-4789-abcd-ef0123456789`, started 14:20:30.000Z) was
in `Running` state on the same machine (`MOCK-HOST`) and was holding
the foreground slot.

**Why:** Inspection of the project source reveals the defect:

1. `process/Main.xaml` contains a `Sequence` with three activities —
   `LogMessage (start)`, `Delay 00:00:30`, `LogMessage (end)`. There
   are **no UI automation activities** (no `NApplicationCard`,
   `NClick`, `NTypeInto`, browser/desktop interactions, etc.).
2. `process/project.json` sets `runtimeOptions.requiresUserInteraction:
   true` — declaring the workflow is foreground (UI-interactive).
3. The two declarations are inconsistent: a workflow that does no
   UI work has no need to be foreground. Marking it foreground
   forces it to compete for the single foreground job slot on the
   Robot session, where it will fault any time another foreground
   job is running.

The `AttendedReportJob` job that triggered this fault is itself a
legitimate foreground workload — it stays foreground. The fix targets
`ExpenseValidation` specifically.

---

**Evidence:**

### Orchestrator (Propagation)
- Failing job: `ExpenseValidation` (key `d1e2f3a4-...`) —
  Faulted at `2026-05-13T14:20:46.218Z` (ran ~0.72s)
- Failing job type: `Unattended`, `RequiresUserInteraction: true`,
  triggered manually by user `user1` on machine `MOCK-HOST`
- Folder: `ComputeJobs` (key `b2c3d4e5-f6a7-8901-2345-6789abcdef01`)
- Concurrent foreground job: `AttendedReportJob` (key `e1f2a3b4-...`)
  in `Running` state at the time of failure
  (`StartTime: 2026-05-13T14:20:30.000Z`, EndTime
  `2026-05-13T14:21:30.412Z`)
- Failing job's `Info` field contains the exception:
  `System.InvalidOperationException: A foreground process is
  already running. Only one foreground process can run at a time.`

### Project Source (Root Cause — the misconfig)
- File: `process/Main.xaml` — activities used: `LogMessage` (×2),
  `Delay` (×1). **Zero UI activities.**
- File: `process/project.json` — `runtimeOptions.requiresUserInteraction:
  true`. This is the misconfiguration: the workflow declares it
  needs a UI session but never uses one.

### Orchestrator (Triggering Context)
- Robot Service log at `2026-05-13T14:20:46.190Z`: `[Robot] Cannot
  start foreground job 'd1e2f3a4-...' (ReleaseName=ExpenseValidation).
  Another foreground job ('e1f2a3b4-...',
  ReleaseName=AttendedReportJob, started 2026-05-13T14:20:30.000Z) is
  currently running on this session. Only one foreground process can
  run at a time.`

---

**Immediate fix — PRIMARY (targeted at ExpenseValidation):**

### Studio (source — preferred)
1. Open the `ExpenseValidation` project in Studio.
2. Project Settings → **"Starts in Background"** = **Yes**. This sets
   `runtimeOptions.requiresUserInteraction: false` in
   `project.json`.
3. Republish.
4. **Why:** The workflow does no UI interaction. Background is the
   correct mode. It no longer consumes the foreground job slot, so
   it can run concurrently with `AttendedReportJob` (or any other
   foreground job) without contention.
5. **Source:**
   `products/orchestrator/playbooks/foreground-already-running.md`
   ("Process does not actually need UI interaction" branch).

### Orchestrator (deployment-layer override — alternative)
- Alternative if a Studio republish is not immediately possible:
  Orchestrator UI → Processes → `ExpenseValidation` → Settings
  → **"Background Process"** = true. This overrides the deployed
  process's foreground attribute without changing the source.
  Eventually flip the source via Studio so the misconfig does not
  get re-deployed.

**Do NOT fix this by:**
- Sequencing the triggers / staggering schedules — masks the
  underlying misconfig and leaves the same trap for future jobs
  scheduled against this process.
- Enabling "Run only one job at a time" on the Robot — same masking;
  also impacts unrelated workloads.
- Converting `AttendedReportJob` to background — that workflow
  legitimately uses the UI; it's not the misconfigured one.

---

**Preventive fix:**

1. **Studio** — Default new projects to background unless they
   genuinely use UI activities.
   - **Why:** This entire failure class is preventable at project
     creation time. Only flip "Starts in Background" to **No** when
     the workflow uses UI Automation activities (`NApplicationCard`,
     `NClick`, etc.).
   - **Where:** Studio → New Project / Project Settings → "Starts in
     Background".
   - **Who:** RPA developer.
   - **Source:**
     `products/orchestrator/playbooks/foreground-already-running.md`.

2. **CI / publish pipeline** — Add a check that flags any published
   process whose `runtimeOptions.requiresUserInteraction` is `true`
   but whose XAML files contain no activities from
   `UiPath.UIAutomation.Activities`.
   - **Why:** Catches the misconfig before a job ever runs and
     surfaces it to the developer instead of an oncall.
   - **Where:** Pre-publish hook or `uip rpa build`-time analyzer
     rule.
   - **Who:** Platform team.

3. **Orchestrator** — Configure an alert subscription for faulted
   jobs in the `ComputeJobs` folder filtered on the
   `InvalidOperationException` message.
   - **Why:** Surfaces the contention pattern early so a second
     instance of the misconfig is caught.
   - **Where:** Orchestrator UI → Alerts.
   - **Who:** Admin or platform team.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | ExpenseValidation is wrongly published as foreground despite having no UI activities; it loses the foreground slot to a legitimate foreground job and faults | High | Confirmed | Yes | `Main.xaml` uses only `LogMessage` + `Delay` (no UI); `project.json` has `requiresUserInteraction: true`; concurrent `AttendedReportJob` job in Running state at failing job's start time; exception message + Robot log explicitly name the blocking job | Set `requiresUserInteraction: false` in `project.json` (Studio: "Starts in Background: Yes"), republish |
| H2 | Both jobs are legitimate foreground and the right fix is trigger sequencing | Medium | Refuted | No | Refuted by source inspection — `ExpenseValidation`'s `Main.xaml` performs no UI work, so it does not need to be foreground in the first place | n/a |
| H3 | Missing unattended robot configuration (sibling `#1230` playbook) | Low | Refuted | No | The error is `System.InvalidOperationException` (Robot-side guard), not HTTP 409 / `#1230` | n/a |

---

Would you like help applying the fix — flipping
`requiresUserInteraction` to false in `project.json` and rebuilding,
or setting "Background Process: true" at the Orchestrator deployment
layer as a faster interim? I can also clean up the `.investigation/`
folder if you no longer need it.
