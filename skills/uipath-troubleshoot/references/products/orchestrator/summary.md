# Orchestrator Playbooks

**Investigation guide:** [investigation_guide.md](./investigation_guide.md) — data correlation rules and testing prerequisites for Orchestrator investigations

| Issue | Confidence | Description | Playbook |
|-------|:---:|-------------|----------|
| Robot Credentials / Machine Mismatch | High | "Wrong machine credentials", PendingReason `RobotNoMatchingUsernames`, or `TemplateNoLicense` — robot/machine configuration cannot execute unattended jobs | [robot-credentials.md](./playbooks/robot-credentials.md) |
| Could Not Start Executor — Logon Failed | Medium | Unattended job faults immediately with `Could not start executor` / `Logon failed for user` / `RDP connection failed` (codes `0x0000052E`, `0x00000775`, `0x00000532`, `131092`). Covers session-config mismatch, AD lockout, password mismatch, lockout loop, MFA/Conditional Access, and RDP slot conflict | [job-faulted-logon-failure.md](./playbooks/job-faulted-logon-failure.md) |
| Queue Items Failing | Medium | Queue items transitioning to Failed status with various error types | [queue-items-failing.md](./playbooks/queue-items-failing.md) |
| Job Stuck in Running | Low | Job remains in Running state indefinitely with no progress | [job-stuck.md](./playbooks/job-stuck.md) |
| Job Pending — No Available Host | High | Job stuck in Pending with "No host is available on the machine template" error AND template has zero connected runtimes | [job-pending-no-host.md](./playbooks/job-pending-no-host.md) |
| Job Pending — Stale Dispatch-Time PendingReasons | High | Job stuck in Pending with no-host-family `PendingReasons.Errors` BUT a runtime IS connected, credentials/mode/license are valid, and `JobHistory` has only the original entry — Orchestrator never re-evaluated. Fix: stop + re-trigger | [job-pending-stale-dispatch.md](./playbooks/job-pending-stale-dispatch.md) |
| Foreground Process Already Running | Medium | `InvalidOperationException: A foreground process is already running. Only one foreground process can run at a time.` — Robot rejects concurrent foreground jobs on the same session | [foreground-already-running.md](./playbooks/foreground-already-running.md) |
