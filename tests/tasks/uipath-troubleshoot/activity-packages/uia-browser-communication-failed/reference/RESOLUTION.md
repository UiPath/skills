# Final Resolution

Investigation complete. Here is the resolution:

---

**Root Cause:** **The browser-automation channel is broken.** The `Use Browser` (`NApplicationCard`)
scope reached a running browser but the UiPath extension / native-messaging bridge between the browser
and the robot could not carry the automation commands, so the scope faulted with `Cannot communicate
with the browser.` This is NOT a launch failure (`ApplicationOpenException`) and NOT a not-found
(`ApplicationNotFoundException`) — the channel between the extension and the robot is the fault.

**What went wrong:** The nightly `CustomerHubSync` unattended job faulted on the `Use CustomerHub
portal` step with `Cannot communicate with the browser.` The same process succeeded on the same machine
and schedule on the prior nights, and the automation source was not changed. A failure that appears
without any automation change, on a channel that previously worked, points at an **environmental change
to the browser-automation channel** — the browser auto-updated to a major version the installed
UIAutomation package/extension no longer attaches to, or the UiPath browser extension was disabled /
removed, or endpoint-security (antivirus) or group policy began blocking the native-messaging host.

**Why:**
- `process/Main.xaml` — a `Use Browser` `NApplicationCard` (`BrowserType=Chrome`,
  `OpenMode=IfNotOpen`) wrapping `NTypeInto` / `NClick`. The scope reached the browser; the inner
  activities never got their commands through.
- `job-get` / `job-logs` — the faulted activity is the `NApplicationCard` scope, exception
  `UiPath.UIAutomationNext.Exceptions.UiAutomationExecutionException: Cannot communicate with the
  browser.` The message is a *communication* failure, not "could not open" or "application not found."
- `jobs-list` — `CustomerHubSync` ran **Successful** on 2026-07-17 and 2026-07-18 (same machine
  MOCK-HOST, same Unattended schedule) and Faulted on 2026-07-19. Unchanged automation + a channel that
  worked days ago = an environmental change to the browser/extension, not a workflow bug.
- Package pins in `project.json` are internally consistent (no design-time skew) — this is a runtime
  channel fault, not a Studio view-generation problem.

**Evidence:**
- Exception `Cannot communicate with the browser.` on the `NApplicationCard` (Use Browser) scope.
- Not `ApplicationOpenException` (launch failed) and not `ApplicationNotFoundException` (app absent) —
  the browser was reachable; the automation channel was not.
- Prior Successful runs of the same process on the same machine immediately before the fault.
- No change to the automation source.

**Immediate fix (work the channel; check the most likely environmental change first):**
1. **Browser ↔ package/extension version skew:** confirm whether the browser auto-updated to a new
   major version. Upgrade `UiPath.UIAutomation.Activities` to a version that supports the current
   browser version (and align the UiPath browser extension), or pin/hold the browser at a supported
   version.
2. **Extension disabled/removed:** on the robot machine, verify the UiPath browser extension is
   installed and **enabled** for the target browser; for private/incognito automation, enable "Allow in
   incognito".
3. **Blocked native-messaging host:** allowlist the UiPath native-messaging host executable and the
   UiPath common-files install folder in the antivirus / endpoint-security product, and allow Native
   Messaging for the UiPath extension in the browser's group policy.

**Preventive fix:**
- Pin/manage the browser version on unattended robots so silent auto-updates don't outrun the installed
  UIAutomation package/extension.
- Add the UiPath extension host and common-files folder to the antivirus allowlist as part of robot
  provisioning.

**Ruled out — attended vs unattended session:** if this process had *only ever* run attended and failed
only when moved to unattended, the cause would be a missing interactive session, not the browser
channel — see the orchestrator logon-failure and application-not-found playbooks. Here the process
already ran **successfully unattended** on the same machine, so the session is fine and the channel
itself is the fault.

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | The browser-automation channel (UiPath extension / native-messaging bridge) is broken — most likely a browser auto-update outran the package/extension, or the extension was disabled, or endpoint security blocked the native-messaging host. | high | confirmed | Yes | `Cannot communicate with the browser.` on the Use Browser `NApplicationCard`; process ran successfully unattended on the same machine the prior two nights; automation unchanged. | Align UIAutomation package/extension with the browser version; verify the extension is enabled (+ incognito); allowlist the native-messaging host in antivirus/policy. |
| H2 | The scope failed to launch the browser (`ApplicationOpenException`). | low | eliminated | No | The exception is `Cannot communicate with the browser.`, not "Could not open target application." — the browser was reachable. | N/A — see application-open-failed.md if a launch failure is seen instead. |
| H3 | Missing interactive session because the job moved from attended to unattended. | low | eliminated | No | The same process already ran **successfully unattended** on the same machine days earlier; the session works. | N/A — see the orchestrator logon-failure playbook only if there were no prior unattended successes. |
