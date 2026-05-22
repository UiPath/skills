# UI Automation Playbooks

**Investigation guide:** [investigation_guide.md](./investigation_guide.md) — data correlation rules and testing prerequisites for UI Automation investigations

| Issue | Confidence | Description | Playbook |
|-------|:---:|-------------|----------|
| Selector Failure — Healing Fix Available | High | Selector mismatch with Healing Agent fix in `healing-fixes.json` | [selector-failure-healing-fix.md](./playbooks/selector-failure-healing-fix.md) |
| Selector Failure — Healing Disabled | High | Selector mismatch with Healing Agent not enabled on the process | [selector-failure-healing-disabled.md](./playbooks/selector-failure-healing-disabled.md) |
| Selector Failure — Manual Investigation | Medium | Selector mismatch requiring manual analysis (HA produced no fix or source code available) | [selector-failure-manual.md](./playbooks/selector-failure-manual.md) |
| Selector Failure — Scope Container Attached to Wrong Page/Window | Medium | Scope container (`NApplicationCard`, `NBrowser`, `Use Application/Browser`, `NWindow`) attached to a different page/window than the inner selector expects; the selector itself is correct for its intended page | [scope-container-wrong-page.md](./playbooks/scope-container-wrong-page.md) |
| Disabled Element — AlterIfDisabled Not Enabled | High | `UiNodeDisabledElementException` from any UIAutomationNext interaction activity (NClick, NTypeInto, NSetText, NCheck, NSelectItem, NSAPClickPictureOnScreen) where the target was found but disabled and `AlterIfDisabled` was not set | [disabled-element.md](./playbooks/disabled-element.md) |
| Timeout Issue | Low | UI automation activity exceeded its timeout waiting for an element or application state | [timeout-issue.md](./playbooks/timeout-issue.md) |
| Healing Agent — No License / Heals Available | High | Robot log contains `"No available license / Agentic units to perform healing analysis and recovery"` (or, corroborating: HA enabled + 22-byte healing-data ZIP + `Allowed.AgentService == 0`) | [healing-agent-no-license.md](./playbooks/healing-agent-no-license.md) |
| Healing Agent — No Recovery Data | Low | Healing Agent enabled but no recovery data generated after failure (license OK; connectivity / classic activity / image-only target) | [no-recovery-data.md](./playbooks/no-recovery-data.md) |
| Application Not Found | High | `ApplicationNotFoundException` thrown by `NApplicationCard` (Use Application / Use Browser) when target app can't be located and `OpenMode=Never`. Covers `OpenMode` misconfiguration, selector drift, crashed-app, no-visible-window, cold-start race. Distinct from `ApplicationOpenException` (launch attempted) and `WrongTargetApplicationException` (wrong window matched). | [application-not-found.md](./playbooks/application-not-found.md) |
