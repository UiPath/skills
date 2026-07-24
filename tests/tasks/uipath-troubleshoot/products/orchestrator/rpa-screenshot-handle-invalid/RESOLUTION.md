# Final Resolution

---

**Root Cause:** The `DashboardSnapshotBot` job takes a screenshot,
but the **unattended run has no live interactive desktop to
capture**. `System.Drawing.Graphics.CopyFromScreen` needs a real,
active desktop surface; the robot user runs with
`LoginToConsole: false` and no RDP session was established, so there
is no device context and the capture throws
`System.ComponentModel.Win32Exception (6): The handle is invalid.`
This is the `screen-capture-handle-invalid` playbook — a
missing-session-surface problem, not a workflow-logic bug (which is
why it works when run interactively on a real desktop but fails as an
unattended scheduled job).

**What went wrong:** Job `ccddeeff-...-ccddee` (DashboardSnapshotBot,
MonitoringOps) ran the earlier steps fine and faulted at the "Take
Screenshot" activity `~8s` in. `jobs traces` shows "Open dashboard"
Succeeded and "Take Screenshot" Faulted with the Win32 invalid-handle
error; `jobs logs` states "no active interactive desktop session is
available for this unattended run (LoginToConsole is off and no RDP
session is established). CopyFromScreen has no valid device context."

**Why:** `uip or users get` for the robot user (`svcmonitor` /
`UIPATH\SVCMON`) shows `LoginToConsole: false`. Unattended, with no
console session and no RDP, there is no desktop for GDI screen
capture. Interactively (a human logged in) the desktop exists, so
the same workflow succeeds — matching the user's observation.

**Ruled out:**
- **Workflow-logic bug** — the non-screen activities succeeded; the
  fault is specific to screen capture and to the unattended session
  context. It works interactively.
- **Generic crash / exit code** — this is a managed
  `Win32Exception` at `CopyFromScreen`, not a process exit code or
  external kill.

---

**Evidence:**

### Orchestrator
- Failing job `ccddeeff-...-ccddee` — DashboardSnapshotBot, Faulted
  `2026-06-29T03:30:09Z`, `LocalSystemAccount: UIPATH\SVCMON`
- Job `Info`: `System.ComponentModel.Win32Exception (6): The handle
  is invalid. at System.Drawing.Graphics.CopyFromScreen(...)`
- `jobs logs`: `Screen capture requested but no active interactive
  desktop session is available for this unattended run
  (LoginToConsole is off and no RDP session is established).
  CopyFromScreen has no valid device context.`
- `jobs traces`: "Open dashboard" Succeeded; "Take Screenshot"
  Faulted with the Win32 invalid-handle error
- `uip or users get` (svcmonitor): `LoginToConsole: false`

---

**Immediate fix:**

1. **Give the robot a live interactive session — enable Login to
   Console.**
   - **Why:** Screen capture (`CopyFromScreen`) needs a real desktop
     surface. With `LoginToConsole` off and no RDP session, the
     unattended run has none. Enabling Login to Console makes the
     Robot create its own console session with a live desktop, so the
     screenshot has a valid device context.
   - **Where:** Orchestrator → Tenant → Users/Robots → the
     `svcmonitor` robot user → Execution Settings → set
     `LoginToConsole = true`.
   - **Who:** Tenant / robot admin
   - **Source:**
     `products/orchestrator/playbooks/screen-capture-handle-invalid.md`

2. **Rerun** the job; the screenshot now runs against a live desktop.

---

**Alternative / hardening:**

- If running via a persistent RDP session instead, keep that session
  **connected and unlocked** for the duration of the run (do not log
  off / lock / minimize).
- Prefer element- or window-scoped capture over full-screen
  `CopyFromScreen` where possible, and `Activate` the target window
  before capturing.

---

**Preventive fix:**

1. **Design rule** — Any unattended automation that takes
   screenshots or uses image-based / CV activities MUST run with a
   live interactive session (Login to Console) — screen capture
   cannot run headless.
   - **Source:**
     `products/orchestrator/playbooks/screen-capture-handle-invalid.md`
     (Prevention)

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Screen capture with no live interactive desktop (LoginToConsole off, unattended) | High | Confirmed | Yes | Win32 invalid-handle at CopyFromScreen; log says no active desktop session; users get shows LoginToConsole=false; works interactively, fails unattended | Enable Login to Console (or keep an RDP session connected); rerun |
| H2 | Workflow-logic bug | Low | Refuted | No | Prior activities Succeeded; fails only at screen capture and only unattended; works interactively | n/a |
| H3 | Generic crash / process exit code | Low | Refuted | No | Managed Win32Exception at CopyFromScreen, not an exit code / external kill | n/a |

---

Would you like help enabling Login to Console for the svcmonitor
robot, or reworking the capture step to be window-scoped?
