# Screen Capture Failed — Win32 "The handle is invalid"

Reproduces the `screen-capture-handle-invalid` playbook: a screenshot
activity throws a Win32 exception because the unattended run has no
live interactive desktop to capture.

```
System.ComponentModel.Win32Exception (6): The handle is invalid.
   at System.Drawing.Graphics.CopyFromScreen(...)
```

## What this scenario uncovers

**Root Cause:** `DashboardSnapshotBot` runs unattended with
`LoginToConsole: false` and no RDP session, so `CopyFromScreen` has
no desktop surface / device context. It works interactively (a real
desktop exists) but fails as a scheduled unattended job. Fix: enable
Login to Console (or keep an RDP session connected) so the robot has
a live desktop.

Maps to:
`references/products/orchestrator/playbooks/screen-capture-handle-invalid.md`.

## How this test reproduces it

| Layer | Source |
|---|---|
| `m/uip` + `m/uip.cmd` | shared from `../../../_shared/mock_template/` |
| `process/` | minimal unattended UiPath project (dashboard snapshot) |
| `data/m/r/*.json` | **synthetic** canned `uip` responses — jobs get/list/logs, `jobs traces` (Take Screenshot faulted, prior succeeded), `users get` (LoginToConsole=false) |
| `data/m/r/manifest.json` | dispatch table |

> Fixtures authored from the playbook signature, not captured from a
> real session.

## Distinguishing fingerprint

The "works interactively, fails unattended" clue plus
`LoginToConsole: false` and the `CopyFromScreen` failure point at a
missing interactive desktop surface, not a workflow-logic bug. The
graded fix is giving the robot a live session (Login to Console), not
editing the workflow.

## Success criteria

Scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill.
- Agent identified the missing interactive desktop session
  (LoginToConsole off, unattended) as the reason screen capture
  fails, and recommended enabling Login to Console (or keeping an
  RDP session connected) rather than changing the workflow logic.
