# UI Automation Playbooks

**Investigation guide:** [investigation_guide.md](./investigation_guide.md) — data correlation rules and testing prerequisites for UI Automation investigations

| Issue | Confidence | Description | Playbook |
|-------|:---:|-------------|----------|
| Selector Failure — Healing Fix Available | High | Selector mismatch with Healing Agent fix in `healing-fixes.json` | [selector-failure-healing-fix.md](./playbooks/selector-failure-healing-fix.md) |
| Selector Failure — Healing Disabled | High | Selector mismatch with Healing Agent not enabled on the process | [selector-failure-healing-disabled.md](./playbooks/selector-failure-healing-disabled.md) |
| Selector Failure — Manual Investigation | Medium | Selector mismatch requiring manual analysis (HA produced no fix or source code available) | [selector-failure-manual.md](./playbooks/selector-failure-manual.md) |
| Timeout Issue | Low | UI automation activity exceeded its timeout waiting for an element or application state | [timeout-issue.md](./playbooks/timeout-issue.md) |
| Healing Agent — No Recovery Data | Low | Healing Agent enabled but no recovery data generated after failure | [no-recovery-data.md](./playbooks/no-recovery-data.md) |
