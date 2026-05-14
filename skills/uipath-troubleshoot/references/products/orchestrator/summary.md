# Orchestrator Playbooks

**Investigation guide:** [investigation_guide.md](./investigation_guide.md) — data correlation rules and testing prerequisites for Orchestrator investigations

| Issue | Confidence | Description | Playbook |
|-------|:---:|-------------|----------|
| Robot Credentials / Machine Mismatch | High | "Wrong machine credentials", PendingReason `RobotNoMatchingUsernames`, or `TemplateNoLicense` — robot/machine configuration cannot execute unattended jobs | [robot-credentials.md](./playbooks/robot-credentials.md) |
| Job Faulted — Logon/Session Failure | Medium | Unattended job faults immediately with logon/RDP errors (0x0000052E, error 131092) | [job-faulted-logon-failure.md](./playbooks/job-faulted-logon-failure.md) |
| Queue Items Failing | Medium | Queue items transitioning to Failed status with various error types | [queue-items-failing.md](./playbooks/queue-items-failing.md) |
| Job Stuck in Running | Low | Job remains in Running state indefinitely with no progress | [job-stuck.md](./playbooks/job-stuck.md) |
| Job Pending — No Available Host | High | Job stuck in Pending with "No host is available on the machine template" error | [job-pending-no-host.md](./playbooks/job-pending-no-host.md) |
| Foreground Process Already Running | Medium | `InvalidOperationException: A foreground process is already running. Only one foreground process can run at a time.` — Robot rejects concurrent foreground jobs on the same session | [foreground-already-running.md](./playbooks/foreground-already-running.md) |
