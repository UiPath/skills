---
confidence: medium
---

# Could Not Start Executor — Session / Console / Slot Contention

## Context

An unattended job faults immediately (or waits then times out) because the interactive session or machine slot it needs is already taken — by another job for the same user, another console session, another RDP user, or a session that was torn down mid-start. Distinct from logon failure (credential is fine) and from session-creation timeout (the host can create sessions — one is just already in use).

What this looks like — one of these `Info` / Robot-log signatures:
- `Another interactive job is running for this user. A user can run a single interactive job at a time.`
- `User is running another job. Waiting for the job to finish timed out.`
- `Another interactive job is using the machine's console. Only one interactive job can use the console at a time.`
- `Could not start executor. The workstation is in use by another user. Please retry after the user logs off or disconnects.`
- `Could not start executor. A specified logon session does not exist. It may already have been terminated. (0x80070520)`

Common markers:
- Job state Faulted with near-zero runtime, or Pending → Running → Faulted after a wait
- Credential is valid — no `0x0000052E` / `0x00000775` / `Logon failed` in the log (rules out logon-failure playbook)
- Intermittent: succeeds when run alone, fails under concurrency

What can cause it (branches):
1. **Single-interactive-job-per-user** — two jobs requiring an interactive session are allocated to the same Robot user at once. A user can run only one interactive job at a time. Surfaces as `Another interactive job is running for this user` or, when the second job waited, `User is running another job. Waiting for the job to finish timed out.`
2. **Console contention (High-Density robot)** — `LoginToConsole: true` on an HD robot forces the Robot Service to attach to the single physical console session; only one interactive job can hold the console. Surfaces as `Another interactive job is using the machine's console.`
3. **Machine-template slot over-allocation** — the machine template exposes more unattended slots than the workstation permits concurrent RDP sessions, so extra jobs land with no session to attach to. Surfaces as `The workstation is in use by another user.`
4. **Session torn down mid-start** — the target logon session was logged off / recycled while the Robot was attaching (`0x80070520`). Usually transient (a user logged off, host recycled, or a prior job's session cleanup raced the new start).

## Investigation

1. Get the failing job — read the `Info` field to identify the exact signature and branch:
   `uip or jobs get <job-key> --output json`
   Note `HostMachineName`, `LocalSystemAccount`, `RequiresUserInteraction`, `StartTime`, `EndTime`.
2. Read error-level logs for the confirming Robot-service line:
   `uip or jobs logs <job-key> --level Error --output json`
3. Find concurrent jobs on the same user/machine around the failure window (branch 1/2):
   `uip or jobs list --folder-key <key> --state Running --output json` — look for another interactive job on the same `LocalSystemAccount` or `HostMachineName` overlapping `StartTime`.
   Also list recent jobs (no state filter) to spot a job that was Running at the failure timestamp.
4. Inspect the Robot user's execution settings (branch 1/2):
   `uip or users get <user-key> --output json` — check `LoginToConsole` (true ⇒ console-bound, branch 2) and `RunOnlyOneJobAtATime` (false ⇒ concurrent interactive jobs allowed, branch 1).
5. Compare machine-template slots against workstation RDP capacity (branch 3):
   `uip or machines list --output json` — read the template's runtime/slot count. A template with N unattended slots on a workstation that allows fewer concurrent RDP sessions over-allocates. Correlate with how many jobs were Running when the fault occurred.
6. For `0x80070520` (branch 4): check whether an interactive user logged off, the host restarted, or a prior job's session was cleaned up near the failure timestamp (`uip or jobs history <job-key>` + host event log). If isolated and non-repeating, treat as transient.

## Resolution

- **Branch 1 — single-interactive-job-per-user:** enable **Run only one job at a time** on the Robot user (Orchestrator → Tenant → Users/Robots → edit → Execution Settings) so subsequent jobs queue instead of failing, OR stagger the triggers so two interactive jobs for the same user never overlap. If both jobs genuinely must run concurrently, assign them to different Robot users / machine templates.
- **Branch 2 — console contention (HD robot):** disable **Login to Console** for the High-Density robot (Orchestrator → Tenant → Users/Robots → Execution Settings → `LoginToConsole = false`). Login to Console attaches the Robot to the single console session and is not recommended for HD robots — with it off, each job gets its own RDP session and the console is no longer a shared bottleneck. Rerun the job.
- **Branch 3 — machine-template slot over-allocation:** reduce the machine template's slot count to match the number of concurrent RDP sessions the workstation actually allows (Orchestrator → Tenant → Machines → edit template → decrease runtimes/slots). Over-allocating slots lets Orchestrator dispatch more jobs than the host can seat. After decreasing slots, rerun.
- **Branch 4 — session torn down mid-start (`0x80070520`):** rerun the job. If it recurs, keep the interactive/RDP session stable (do not log off the target user while unattended jobs are scheduled), and prefer **Login to Console** or a dedicated unattended user so the Robot manages its own session rather than borrowing an interactive one.

Prevention:
- One interactive job per Robot user at a time — enable "Run only one job at a time" or sequence triggers.
- Keep machine-template slot counts ≤ the host's real concurrent-session capacity.
- Do not enable Login to Console on High-Density robots.
- Route unattended work to dedicated unattended users, not to accounts that humans also log into interactively.
