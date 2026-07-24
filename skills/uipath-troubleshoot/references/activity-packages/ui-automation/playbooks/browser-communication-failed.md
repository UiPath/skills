---
confidence: high
---

# Browser Communication Failed — Extension / Native Messaging Channel Broken

## Context

A `Use Browser` scope (the `NApplicationCard` activity with a browser target) or an inner browser
activity (`NClick`, `NTypeInto`, `NGoToUrl`, `NGetText`) faulted at runtime because the automation
layer **cannot talk to a browser that is actually running**. The browser process exists; the channel
between the UiPath extension and the robot is broken.

What this looks like:
- `Cannot communicate with the browser.`
- `Cannot access the indicated browser window.`
- The scope reached the browser (it did not fail to *launch*), but the extension / native-messaging
  bridge could not carry the automation commands.

This is distinct from the launch/lookup faults — route those to the sibling playbooks:
- Scope tried to launch the browser and the launch failed →
  [application-open-failed.md](./application-open-failed.md) (`ApplicationOpenException`).
- Scope with `OpenMode=Never` couldn't find the browser window →
  [application-not-found.md](./application-not-found.md) (`ApplicationNotFoundException`).
- A classic (`Open Browser` / `Attach Browser`) scope, not UIAutomationNext →
  [../../classic-activities/playbooks/browser-open-or-attach-failed.md](../../classic-activities/playbooks/browser-open-or-attach-failed.md).

What can cause it:
- **UiPath browser extension disabled, removed, or not enabled.** The extension is the transport for
  UIAutomationNext browser automation; without it the robot cannot drive the page. For private/InPrivate
  sessions the extension must additionally be allowed in incognito.
- **Native Messaging host blocked by antivirus or group policy.** The extension talks to the robot
  through a native-messaging host process; endpoint-security software or a Chromium `NativeMessaging`
  policy can block that executable (commonly under the UiPath install / common-files folder), silently
  killing the channel.
- **Browser ↔ package version skew.** The browser auto-updated to a major version the installed
  `UiPath.UIAutomation.Activities` package does not yet support, so the extension/driver can no longer
  attach.
- **Runs attended, fails unattended.** Attended runs have a live interactive desktop; an unattended
  robot without a real interactive console session has no session for the browser to render into, so
  the channel never establishes. See the cross-redirects under Resolution.

What to look for:
- Whether the UiPath extension is installed **and enabled** for the target browser on the robot
  machine (and "Allow in incognito" is on for private sessions).
- Whether antivirus / endpoint policy or a `NativeMessaging` group policy is blocking the UiPath
  native-messaging host or the UiPath common-files folder.
- The browser's major version on the robot versus the version the installed UIAutomation package
  supports.
- The attended-vs-unattended pattern: does the same process succeed attended and fault only unattended?
  (Compare job history — a session/logon problem, not a browser-extension problem.)

## Investigation

1. From the faulted job, capture the exception message and the faulting activity/scope (confirm it is
   a `Use Browser` NApplicationCard or an inner browser activity, and that the message is a
   *communication* failure — the browser was up, the channel was down).
2. Confirm this is not a launch failure (`ApplicationOpenException`) or a not-found
   (`ApplicationNotFoundException`) — if it is, use the sibling playbook.
3. On the robot machine, check the UiPath browser extension: installed, enabled for the target
   browser, and allowed in incognito if the workflow uses a private window.
4. Check antivirus / endpoint-security logs and any Chromium `NativeMessaging` group policy for a block
   on the UiPath native-messaging host executable or the UiPath common-files folder.
5. Compare the robot's browser major version against the installed `UiPath.UIAutomation.Activities`
   package's supported range.
6. If the process succeeds attended but faults unattended, treat it as a session/logon problem, not an
   extension problem — see the cross-redirects below.

## Resolution

- **Extension disabled/missing:** install and enable the UiPath extension for the target browser on
  the robot. For private/InPrivate automation, enable **Allow in incognito**.
- **Blocked by antivirus / policy:** allowlist the UiPath native-messaging host executable and the
  UiPath common-files install folder in the endpoint-security product, and allow Native Messaging for
  the UiPath extension in the browser's group policy.
- **Browser ↔ package version skew:** upgrade `UiPath.UIAutomation.Activities` to a version that
  supports the browser's current major version (or pin/hold the browser at a supported version). Keep
  the extension version aligned with the package.
- **Attended works, unattended fails:** ensure the unattended robot has a genuine interactive session
  for the browser to render into — configure the machine/robot logon per your unattended architecture
  (`LoginToConsole` and a stable resolution as your setup requires). This is a session/logon fault, not
  an extension fault: see
  [../../../products/orchestrator/playbooks/job-faulted-logon-failure.md](../../../products/orchestrator/playbooks/job-faulted-logon-failure.md)
  and, for the scope's `Open`/`Close` mode when the app is pre-launched versus self-launched,
  [application-not-found.md](./application-not-found.md).
