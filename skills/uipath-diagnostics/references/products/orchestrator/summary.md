# Orchestrator Playbooks

**Investigation guide:** [investigation_guide.md](./investigation_guide.md) — data correlation rules and testing prerequisites for Orchestrator investigations

| Issue | Confidence | Description | Playbook |
|-------|:---:|-------------|----------|
| Get Asset - Asset Not Found | High | "Could not find an asset with this name" during job execution because the asset is missing or out of folder scope | [get-asset-asset-not-found.md](./playbooks/get-asset-asset-not-found.md) |
| Get Asset Failed | Medium | Get Asset fails with authentication, access, timeout, or value-context mismatch patterns requiring step-by-step diagnosis | [get-asset-failed.md](./playbooks/get-asset-failed.md) |
| Queue Items Failing | Medium | Queue items transitioning to Failed status with various error types | [queue-items-failing.md](./playbooks/queue-items-failing.md) |
| Job Stuck in Running | Low | Job remains in Running state indefinitely with no progress | [job-stuck.md](./playbooks/job-stuck.md) |
