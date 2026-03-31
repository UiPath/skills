# Integration Service Playbooks

**Investigation guide:** [investigation_guide.md](./investigation_guide.md) — data correlation rules and testing prerequisites for Integration Service investigations

| Issue | Confidence | Description | Playbook |
|-------|:---:|-------------|----------|
| Connection Invalid or No Access | High | "connection is invalid or you do not have access" — connection missing, disabled, or caller lacks permissions | [connection-invalid.md](./playbooks/connection-invalid.md) |
| Connection Authentication Expired | High | Connection was working but now fails — OAuth token expired or revoked | [connection-auth-expired.md](./playbooks/connection-auth-expired.md) |
| Trigger Not Firing | Medium | IS trigger configured but events not starting jobs/instances — subscription, permissions, or event mismatch | [trigger-not-firing.md](./playbooks/trigger-not-firing.md) |
| Operation Failed | Medium | IS activity returns error during execution — bad request, unsupported method, or input validation | [operation-failed.md](./playbooks/operation-failed.md) |
