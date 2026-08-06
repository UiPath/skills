# UIAutomationNext Use Browser — Cannot Communicate With the Browser (Runtime)

Runtime troubleshooting scenario for `UiPath.UIAutomationNext.Activities.NApplicationCard` (the modern
Use Application/Browser container) in a **browser** configuration.

## What this scenario exercises

An unattended job faults on the `Use Browser` scope with `Cannot communicate with the browser.` The
process ran clean on the same schedule and machine for weeks and the automation was not changed. The
agent must recognize this as a **broken browser-automation channel** (the browser is up, but the UiPath
extension / native-messaging bridge cannot carry commands) rather than a launch failure
(`ApplicationOpenException`) or a not-found (`ApplicationNotFoundException`), and prescribe the
extension / native-messaging / browser↔package-version remediation.

## How this test reproduces it

| Layer | Source |
|---|---|
| `process/` | crafted project source: `Main.xaml` with a `Use Browser` `NApplicationCard` (Chrome) wrapping `NTypeInto` / `NClick`; current, aligned package pins (no design-time skew) |

## Success criteria

Scores the **conclusion**, not the trajectory (`skill_triggered` + `llm_judge` against `RESOLUTION.md`):

- Agent invoked the `uipath-troubleshoot` skill.
- Agent identified the broken browser-automation channel and the remediation branches (UiPath extension
  enabled/allowed-in-incognito, native-messaging host not blocked by antivirus/policy, browser↔package
  version alignment), and ruled out launch-failure / not-found.

Playbook: `references/activity-packages/ui-automation/playbooks/browser-communication-failed.md`.

## Fixture isolation

`data/uip-fixture.json` is a finite command/response map mounted only into coder-eval's UID/GID-isolated mock service. The evaluated agent receives a bounded `uip` client and cannot read the fixture or mock implementation.
