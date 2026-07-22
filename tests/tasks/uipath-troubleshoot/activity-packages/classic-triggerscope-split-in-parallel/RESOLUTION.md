# Final Resolution

Here is the investigation result.

---

**Root Cause:** `Main.xaml` places **two separate `Trigger Scope` blocks inside a single `Parallel`**
(`Monitor Shortcuts`) — `Watch Save Shortcut` and `Watch Submit Shortcut`. A `Trigger Scope`
(Monitor Events) opens a single trigger-monitoring session on the execution, and the local robot
service permits only **one** active monitoring session at a time. When the `Parallel` schedules both
branches, the first scope registers successfully, then the second scope (`Watch Submit Shortcut`)
throws `System.InvalidOperationException: "A trigger monitoring session is already active"` the instant
it tries to register its hook — faulting the whole job ~3 seconds after start, before any shortcut is
ever handled.

**What went wrong:** The attended `OrderEntryAssistant` job faulted on startup because two `Trigger
Scope`s cannot run concurrently under a `Parallel`; nested/parallel Trigger Scopes are not supported.

**Why (full causal chain):**
- `Main.xaml` → `Sequence 'Order Entry Assistant'` → `Parallel 'Monitor Shortcuts'` contains two
  `ui:TriggerScope` children: `Watch Save Shortcut` (hotkey `Ctrl+S`) and `Watch Submit Shortcut`
  (hotkey `Ctrl+Shift+Enter`).
- `Parallel` schedules both branches. `Watch Save Shortcut` starts its monitoring session first and
  succeeds (Info log: "Trigger Scope 'Watch Save Shortcut' started monitoring 1 trigger").
- `Watch Submit Shortcut` then tries to start a **second** concurrent monitoring session in the same
  execution. The robot allows only one, so `TriggerScope.StartMonitoring` throws
  `InvalidOperationException`.
- The exception surfaces from `System.Activities.Statements.Parallel.Execute` on the stack — confirming
  the two scopes are running under a `Parallel`, not sequentially.
- The job is a manually-started attended process; Orchestrator recorded the Faulted state.

**Evidence**

### classic-activities (Root Cause)
- Faulting activity: `Trigger Scope 'Watch Submit Shortcut'` (`ui:TriggerScope`), nested in
  `Parallel 'Monitor Shortcuts'`, in `Main.xaml`.
- Error log (.NET): `System.InvalidOperationException: A trigger monitoring session is already active.`
  … `UiPath.Core.Activities.TriggerScope 'Watch Submit Shortcut' could not start a second concurrent
  monitoring session … nested or parallel Trigger Scopes are not supported`, thrown at
  `TriggerScope.StartMonitoring` → `TriggerScope.Execute`, scheduled from
  `System.Activities.Statements.Parallel.Execute`.
- Source: `Parallel 'Monitor Shortcuts'` holds **two** `ui:TriggerScope` blocks, each with one
  `ui:HotkeyTriggerActivity` (`Ctrl+S` and `Ctrl+Shift+Enter`).
- Info/Trace timeline: first scope registered its trigger, then `Monitor Shortcuts` ended faulted —
  the failure is at scope registration, not while handling a keystroke.

### orchestrator (Propagation)
- Job: `OrderEntryAssistant`, folder `Operations`, job key `4b7c2e19-8a53-4f61-bd02-9c3e1f7a6d84`.
- State transition: Running `2026-07-20T09:15:04Z` → Faulted `2026-07-20T09:15:07Z` (~3s) — too fast
  for any UI interaction, consistent with an immediate startup/registration fault.
- Run mode / machine: Attended, on `MOCK-HOST`. Orchestrator recorded the Faulted job.

**Immediate fix**

### classic-activities (Root Cause)
1. **Consolidate the triggers into a single `Trigger Scope`.** Remove the `Parallel 'Monitor Shortcuts'`
   and the second scope; place **both** `HotkeyTriggerActivity` triggers (`Save Hotkey` Ctrl+S and
   `Submit Hotkey` Ctrl+Shift+Enter) inside **one** shared `Trigger Scope`. A single `Trigger Scope`
   monitors multiple triggers simultaneously and dispatches to the matching branch when one fires — the
   `Parallel` wrapper is unnecessary and unsupported for trigger monitoring.
   - **Where:** `Main.xaml` — the `Parallel 'Monitor Shortcuts'` and its two `ui:TriggerScope` children.
   - **Who:** RPA developer.
2. **Re-validate and re-run.**
   - **Where:** `uip rpa validate --file-path "Main.xaml" --output json` (or validate in Studio), then
     re-run; confirm the single `Trigger Scope` registers and monitoring starts without faulting.

**Preventive fix**

1. **classic-activities** — Standardize on one `Trigger Scope` per attended trigger automation; never
   wrap `Trigger Scope`s in a `Parallel` (or nest them). Add multiple triggers to the same scope instead.
2. **orchestrator** — Add failure alerting on Faulted instances of attended trigger automations so a
   startup fault is caught rather than leaving the assistant silently not listening.

**Investigation summary**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | A hotkey combination is already owned by another app, so a trigger can't bind | Low | Rejected | No | Error is `InvalidOperationException` about an already-active monitoring session, not a key-registration/listen failure | — |
| H2 | Two `Trigger Scope`s split across a `Parallel` — the second can't open a concurrent monitoring session, so it faults on registration | High | Confirmed | **Yes** | `InvalidOperationException` at `TriggerScope.StartMonitoring` scheduled from `Parallel.Execute`; source shows a `Parallel` with two `ui:TriggerScope` blocks; ~3s fault after first scope registered | Consolidate both hotkey triggers into a single shared `Trigger Scope`; drop the `Parallel` |

---

The matched playbook's resolution is interactive — I can apply the consolidation to `Main.xaml`
directly. Here are the exact values involved:

```
Project path: <PROJECT_DIR>
File:         Main.xaml

Misconfigured structure:
  Sequence 'Order Entry Assistant'
    └─ Parallel 'Monitor Shortcuts'                 <-- unsupported wrapper for Trigger Scopes
         ├─ TriggerScope 'Watch Save Shortcut'      (Hotkey: Ctrl+S,  TriggerId trg-save-0001)
         └─ TriggerScope 'Watch Submit Shortcut'    (Hotkey: Ctrl+Shift+Enter, TriggerId trg-submit-0002)

Fix: Replace the Parallel + two Trigger Scopes with ONE Trigger Scope that holds BOTH hotkey triggers.
     A single Trigger Scope monitors multiple triggers at once and runs the matching branch when a
     trigger fires; the Parallel is removed entirely.
```
