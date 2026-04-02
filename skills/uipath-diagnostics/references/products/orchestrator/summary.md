# Orchestrator Playbooks

**Investigation guide:** [investigation_guide.md](./investigation_guide.md) — data correlation rules and testing prerequisites for Orchestrator investigations

| Issue | Confidence | Description | Playbook |
|-------|:---:|-------------|----------|
| Robot Credentials / Machine Mismatch | High | "Wrong machine credentials", PendingReason `RobotNoMatchingUsernames`, or `TemplateNoLicense` — robot/machine configuration cannot execute unattended jobs | [robot-credentials.md](./playbooks/robot-credentials.md) |
| Queue Items Failing | Medium | Queue items transitioning to Failed status with various error types | [queue-items-failing.md](./playbooks/queue-items-failing.md) |
| Job Stuck in Running | Low | Job remains in Running state indefinitely with no progress | [job-stuck.md](./playbooks/job-stuck.md) |
