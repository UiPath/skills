# Final Resolution

---

**Root Cause:** The `DashboardSnapshotBot` job takes a screenshot,
but the **unattended run has no live interactive desktop to
capture**. `System.Drawing.Graphics.CopyFromScreen` needs a real,
active desktop surface; the robot user runs with
`LoginToConsole: true`, so it attaches to the machine's single
physical console session instead of opening its own RDP session.
Unattended, with no interactive logon at that console, there is no
rendered desktop, so the capture throws
`System.ComponentModel.Win32Exception (6): The handle is invalid.`
This is the `screen-capture-handle-invalid` playbook — a
missing-session-surface problem, not a workflow-logic bug (which is
why it works when a human is logged in at the console on a real
desktop but fails as an unattended scheduled job).

**What went wrong:** Job `ccddeeff-...-ccddee` (DashboardSnapshotBot,
MonitoringOps) ran the earlier steps fine and faulted at the "Take
Screenshot" activity `~8s` in. `jobs traces` shows "Open dashboard"
Succeeded and "Take Screenshot" Faulted with the Win32 invalid-handle
error; `jobs logs` states "no active interactive desktop session is
available for this unattended run. CopyFromScreen has no valid device
context."

**Why:** `uip or users get` for the robot user (`svcmonitor` /
`UIPATH\SVCMON`) shows `LoginToConsole: true`. Attached to the
machine's physical console and running unattended with no interactive
logon there, the robot has no rendered desktop for GDI screen
capture. When a human is logged in at the console the desktop exists,
so the same workflow succeeds — matching the user's observation.

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
  desktop session is available for this unattended run. CopyFromScreen
  has no valid device context.`
- `jobs traces`: "Open dashboard" Succeeded; "Take Screenshot"
  Faulted with the Win32 invalid-handle error
- `uip or users get` (svcmonitor): `LoginToConsole: true` — the robot
  attaches to the machine's single physical console (no rendered
  desktop unattended) instead of opening its own RDP session

---

**Immediate fix:**

1. **Give the robot its own live session — set Login to Console to
   No.**
   - **Why:** Screen capture (`CopyFromScreen`) needs a real desktop
     surface. With `LoginToConsole` on, the robot attaches to the
     machine's physical console, which has no rendered desktop
     unattended. Setting Login to Console to No makes the Robot open
     its own RDP session with a live desktop, so the screenshot has a
     valid device context. (This is the documented unattended config.)
   - **Where:** Orchestrator → Tenant → Users/Robots → the
     `svcmonitor` robot user → Execution Settings → set
     `LoginToConsole = false`.
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
   live interactive session — set Login to Console to No so the robot
   opens its own RDP session; screen capture cannot run headless.
   - **Source:**
     `products/orchestrator/playbooks/screen-capture-handle-invalid.md`
     (Prevention)

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Screen capture with no live interactive desktop (LoginToConsole on → attached to physical console, unattended) | High | Confirmed | Yes | Win32 invalid-handle at CopyFromScreen; log says no active desktop session; users get shows LoginToConsole=true; works when logged in at console, fails unattended | Set Login to Console = No so the robot opens its own RDP session (or keep an RDP session connected); rerun |
| H2 | Workflow-logic bug | Low | Refuted | No | Prior activities Succeeded; fails only at screen capture and only unattended; works interactively | n/a |
| H3 | Generic crash / process exit code | Low | Refuted | No | Managed Win32Exception at CopyFromScreen, not an exit code / external kill | n/a |

---

Would you like help setting Login to Console to No for the svcmonitor
robot, or reworking the capture step to be window-scoped?
