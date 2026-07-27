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
`LoginToConsole: true`, so the robot attaches to the machine's single
physical console session instead of opening its own RDP session; with
no interactive logon at that console there is no desktop for
`CopyFromScreen`. It works when a human is logged in at the console (a
real desktop exists) but fails as a scheduled unattended job. Fix: set
Login to Console to No so the robot opens its own RDP session (or keep
an RDP session connected) with a live desktop.

Maps to:
`references/products/orchestrator/playbooks/screen-capture-handle-invalid.md`.

## How this test reproduces it

| Layer | Source |
|---|---|
| `m/uip` + `m/uip.cmd` | shared from `../../../_shared/mock_template/` |
| `process/` | minimal unattended UiPath project (dashboard snapshot) |
| `data/m/r/*.json` | **synthetic** canned `uip` responses — jobs get/list/logs, `jobs traces` (Take Screenshot faulted, prior succeeded), `users get` (LoginToConsole=true) |
| `data/m/r/manifest.json` | dispatch table |

> Fixtures authored from the playbook signature, not captured from a
> real session.

## Distinguishing fingerprint

The "works when logged in at the console, fails unattended" clue plus
`LoginToConsole: true` and the `CopyFromScreen` failure point at a
missing interactive desktop surface, not a workflow-logic bug. The
graded fix is giving the robot its own live session (set Login to
Console to No), not editing the workflow.

## Success criteria

Scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill.
- Agent identified the missing interactive desktop session
  (LoginToConsole on → attached to the physical console, unattended)
  as the reason screen capture fails, and recommended setting Login
  to Console to No so the robot opens its own RDP session (or keeping
  an RDP session connected) rather than changing the workflow logic.
