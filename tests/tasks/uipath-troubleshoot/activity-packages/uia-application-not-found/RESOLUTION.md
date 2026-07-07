# Final Resolution

---

**Root Cause:** The `Use Application` scope (`NApplicationCard`,
DisplayName "Use AcmeBooks accounting app") in `Main.xaml` has
`OpenMode="Never"`. AcmeBooks.exe was not running on the robot machine
when the job started, so the scope refused to launch it and threw
`UiPath.UIAutomationNext.Exceptions.ApplicationNotFoundException` at
scope entry. This is a **scope-level** failure — the exception fires
before any inner activity runs, not because of a broken selector on an
element.

**What went wrong:** The `ExpenseImporter` unattended job
(`2c4f8a91-3e7d-4b6c-9a1e-5f8d2b7c3091`) faulted ~2.5 seconds after
launch on 2026-05-12T02:00:02Z. The job runs a single workflow,
`Main.xaml`, whose first UI activity is a `Use Application` scope
targeting AcmeBooks.exe.

**Why:** The workflow assumes AcmeBooks is already running on the
robot when the job starts — an internal IT runbook normally keeps the
app open continuously on the finance robot machine. The
`Use Application` scope is configured with `OpenMode="Never"`, which
tells the runtime to attach to an existing window only and never to
launch the app itself. On the failing run, IT shut down AcmeBooks at
2026-05-11T23:00Z for maintenance and did not restart it before
02:00Z. When the job started, no AcmeBooks window existed, so
`NApplicationCard` could not attach and threw
`ApplicationNotFoundException` with the default friendly message
`"Could not find target application."`

This is distinct from `ApplicationOpenException`, which fires when
`OpenMode != Never` (`IfNotOpen` / `Always`) **and** the scope's
attempt to launch the app failed. Here, `OpenMode=Never` means the
scope never attempted a launch at all.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: ExpenseImporter — Faulted at 2026-05-12T02:00:04.620Z (ran for ~2.5 seconds)
- Job type: Unattended, triggered by Trigger "Nightly Expense Import" on machine MOCK-HOST
- Job runtime folder: Finance Automations (key `f3e8d4b1-9c2a-4f5e-b8d7-c1a0e6f9b3d2`)
- `Info`: `UiPath.UIAutomationNext.Exceptions.ApplicationNotFoundException: Could not find target application.`

### UI Automation (Root Cause)
- Faulted activity: `NApplicationCard` (DisplayName: "Use AcmeBooks accounting app") in `Main.xaml`
- Activity selector (TargetApp.Selector): `<wnd app='acmebooks.exe' cls='Afx:00007FF6:0' />`
- Activity property: **`OpenMode="Never"`** — the gating condition for the exception
- Exception class: `UiPath.UIAutomationNext.Exceptions.ApplicationNotFoundException`
- Error message at 2026-05-12T02:00:04.587Z: `"Could not find target application."` (no closest-match diagnostic — the process was absent, not just renamed)
- Stack frame originates in `UiPath.UIAutomationNext.Activities.NApplicationCard.GetAppNotFoundExceptionAsync` and propagates through `ProcessAppNotFoundAsync`
- Source code confirmed: `Main.xaml` line 121 — `<ui:NApplicationCard ... OpenMode="Never" ...>` wrapping the entire process body

---

**Immediate fix:**

### UI Automation (Root Cause)

1. **Change `OpenMode` on the Use Application scope from `Never` to `IfNotOpen`**
   - **Why:** `OpenMode=Never` blocks the scope from launching AcmeBooks even when the workflow could legitimately do so. `IfNotOpen` lets the scope attach to a running instance when one exists and launches the app only when it isn't running — handles both the steady-state and the post-maintenance case.
   - **Where:** `Main.xaml` → `<ui:NApplicationCard ... OpenMode="Never" ...>` → change to `OpenMode="IfNotOpen"`. Also populate `FileName` with the AcmeBooks executable path (e.g., `C:\Program Files\AcmeBooks\AcmeBooks.exe`) and `Arguments` if any are needed. Save, rebuild, republish the `ExpenseImporter` package.
   - **Who:** RPA developer
   - **Source:** Playbook `application-not-found.md` — Branch A ("Workflow assumed the app was running but OpenMode=Never blocks the launch")

2. **Re-run the job once the package is republished to confirm the scope can launch AcmeBooks**
   - **Why:** A green run with the new `OpenMode` value validates that the launch path works on the robot machine (executable path correct, file present, no permission issues). Skipping this verification risks the next nightly run failing for a different reason (e.g., `ApplicationOpenException`).
   - **Where:** Orchestrator → Finance Automations folder → ExpenseImporter → Start Job
   - **Who:** RPA developer

---

**Preventive fix:**

1. **UI Automation — Choose `OpenMode` deliberately and document the assumption**
   - **Why:** `OpenMode=Never` is correct only when an upstream process is guaranteed to keep the app running. Any deviation (maintenance window, machine reboot, app crash) silently breaks the workflow. Defaulting to `IfNotOpen` and treating `Never` as an explicit opt-in surfaces the dependency.
   - **Where:** Team coding standards for UiPath workflows — require a comment next to any `OpenMode="Never"` documenting the upstream guarantor.
   - **Who:** RPA team lead

2. **Orchestrator — Add an alert subscription for faulted jobs in the Finance Automations folder**
   - **Why:** This failure ran overnight and was only noticed the next morning. An alert on `ApplicationNotFoundException` (or any UI Automation exception in this folder) would have notified the on-call rotation immediately.
   - **Where:** Orchestrator UI → Alerts → severity "Error" + folder filter for `Finance Automations`.
   - **Who:** Admin or platform team

3. **Robot ops — Add an AcmeBooks health check before the ExpenseImporter trigger fires**
   - **Why:** Even with `OpenMode=IfNotOpen`, a robot-side guard that ensures AcmeBooks is up before triggering the job (e.g., a scheduled task that starts the app at 01:55Z if not running) prevents cold-start races on first launch.
   - **Where:** Windows Scheduled Task on the finance robot machine — start AcmeBooks at 01:55Z daily.
   - **Who:** Platform / robot operations

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | `Use Application` scope's `OpenMode=Never` blocks launch when AcmeBooks is not running; scope throws `ApplicationNotFoundException` | High | Confirmed | Yes | Job `Info` carries the exception class verbatim; `Main.xaml` shows `OpenMode="Never"` on the scope; no element-level selector errors in the log | Change `OpenMode` to `IfNotOpen`, set `FileName`, rebuild, republish |
| H2 | Selector failure on an inner `NClick` / `NTypeInto` | Low | Eliminated | No | Faulted activity is `NApplicationCard` (scope), not an inner element activity; exception class is `ApplicationNotFoundException`, not `SelectorNotFoundException`; no closest-match diagnostic in log message | n/a |
| H3 | Application launched but a launch failure was reported (would be `ApplicationOpenException`) | Low | Eliminated | No | Log message and `Info` field show `ApplicationNotFoundException`, not `ApplicationOpenException`; the two are returned by the same factory based on `OpenMode` value | n/a |

---

---

**Required closing interaction:**

The agent MUST end the investigation with an explicit `AskUserQuestion`
that surfaces the concrete edit (file `Main.xaml`, activity
`NApplicationCard "Use AcmeBooks accounting app"` / IdRef
`NApplicationCard_AcmeBooks`, `OpenMode` value change from `Never` to
`IfNotOpen`, plus setting `FileName`) and asks the user whether to
apply it. The agent MUST NOT silently edit `Main.xaml`. Sharing the
project path earlier in the conversation is not approval — it covers
reading only.

Would you like help applying the fix — updating `Main.xaml` to set
`OpenMode="IfNotOpen"` with the correct `FileName`, and republishing
the package? I can also clean up the `.local/investigations/` folder
if you no longer need it.
