# Final Resolution

Here is the investigation result.

---

**Root Cause:** The classic UI Automation scope `Open Application 'msedge.exe Google'` in `Workflow.xaml` is the wrong scope type for its target. It is a **desktop** Open Application (launching `chrome.exe`) but was given a **browser-style** html selector with no application window, so it never produces a usable context window. Its child `Click 'push button'` faults the instant the scope hands it an uninitialized window — before the Click's own (valid) selector is ever evaluated.

**What went wrong:** The `Legacy` process job faulted in ~5 seconds because a desktop Open Application scope, fed a browser html selector and a null window, could not initialize its context window, so the nested Click had nothing to act against.

**Why (full causal chain):**
- In `Workflow.xaml`, the scope `Open Application 'msedge.exe Google'` (`ui:OpenApplication` — a classic desktop Open Application) has `FileName = C:\Program Files\Google\Chrome\Application\chrome.exe` (a launchable desktop executable), `Selector = <html app='chrome.exe' title='Google' />` (a **browser** html selector shape, produced by browser scopes like Open Browser / Attach Browser, not by a native desktop scope), and `ApplicationWindow = {x:Null}` (no explicit window object).
- A desktop Open Application is built to anchor on a native top-level window. Given a browser html selector its type cannot resolve, and no explicit `ApplicationWindow`, the scope's `ContextWindow` UiElement is never initialized.
- The nested `Click 'push button'` inherits this uninitialized scope context. At `Target.FindByElement`, the runtime validates the search arguments against the (uninitialized) context window and throws `UninitializedNodeException: "The UiElement is not initialized"`, wrapped as `ElementNotSetException` and surfaced at `ScopeActivity.OnFaulted` — the scope's fault callback, not a leaf-property error.
- The Click's own `Target.Selector` (`<webctrl aaname='...Creating a Doodle...' .../>`) is intact and valid; it never executes because the scope faulted first. This is why the leaf error text describes the *symptom* at the leaf, while the *cause* is upstream in the scope.
- The job is a manually-startable Legacy attended process; Orchestrator recorded the resulting Faulted state but did not (and by default cannot) auto-recover it — the propagation surface.

> **Cause refinement (depth-check gap):** The precise defect — a browser html selector placed on a desktop Open Application scope (wrong scope type) — is **not** one of the enumerated causes in the matched playbook. The closest playbook bullet ("a scope given neither a Browser/Window nor a Selector") does not literally apply, because this scope **does** carry a selector — it is just the wrong *shape* for its scope type. Treat this as an adjacent variant of that playbook signature, not an exact bullet match.

**Evidence**

### classic-activities (Root Cause)
- Faulting activity: `Click 'push button'`, nested in scope `Open Application 'msedge.exe Google'`, in `Workflow.xaml`.
- Scope `Open Application 'msedge.exe Google'` (`ui:OpenApplication`):
  - `FileName = C:\Program Files\Google\Chrome\Application\chrome.exe` (desktop launchable exe)
  - `Selector = <html app='chrome.exe' title='Google' />` (browser html selector)
  - `ApplicationWindow = {x:Null}`
- Child `Click 'push button'` target selector is intact and valid: `<webctrl aaname='...Creating a Doodle...' parentid='glue-drawer-2465973' tag='A' />`, `Target.Element = {x:Null}` (normal for selector targeting).
- Exception (.NET stack): `ElementNotSetException ---> UninitializedNodeException: "The UiElement is not initialized"`, thrown at `UiElement.ValidateSearchArgs -> UiElement.FindFirst -> Target.FindByElement(...)`, surfacing at `ScopeActivity.OnFaulted`. The exception fires in `ValidateSearchArgs` *before* any element search runs — no `SelectorNotFoundException` anywhere.
- Activity tree on the stack matches the XAML exactly: `Click -> Sequence 'Do' -> OpenApplication 'msedge.exe Google' -> Sequence 'Workflow'`.
- Corroborating inconsistency: scope `DisplayName` says `msedge.exe` while `FileName` points to `chrome.exe` — consistent with the scope being retargeted/mis-typed during authoring.

### orchestrator (Propagation)
- Job: `Legacy` process, package `UiPath.UIAutomation.Activities 22.4.3`, folder `Shared`. Job key `35c669cb-7f46-4282-b90d-ca7abd52c59f`.
- State transition: Running `2026-06-04T10:50:07Z` → Faulted `2026-06-04T10:50:12Z` (~5s) — too fast for a selector-search timeout, consistent with an immediate scope-startup configuration fault.
- Run mode / machine: Attended, on machine `MOCK-HOST`. Orchestrator recorded the Faulted job but did not auto-recover it.

**Immediate fix**

### classic-activities (Root Cause)
1. Correct the scope so it produces a real context window — either convert it to a browser scope, or give the desktop scope a real window.
   - **Option A (recommended, matches the target):** Replace the desktop `Open Application 'msedge.exe Google'` with a browser scope — **Use Application/Browser** (or classic **Open Browser** / **Attach Browser**) pointed at the Chrome page/URL. This makes the existing browser html selector resolvable, and the child `Click 'push button'` (whose `webctrl` selector is already valid) will then resolve against an initialized browser context.
   - **Option B:** Keep the desktop **Open Application** but give it a native top-level window selector (a `wnd`/native selector) **and** a valid `ApplicationWindow` object — not a browser `html` selector.
   - **Where:** `workflow.xaml` — the `ui:OpenApplication` activity `Open Application 'msedge.exe Google'`.
   - **Who:** RPA developer.
   - **Source:** `evidence/H2-source_code.json → resolution_values.fix_summary` (the playbook has no exactly-matching resolution branch — see gap below).

> **Resolution-alignment gap (depth-check):** The playbook's branch "If a scope has neither: provide one of them" does **not** fit, because this scope already has a selector — adding a Browser/Window will not correct a browser-selector-on-a-desktop-scope defect. The corrective action is therefore taken from the evidence file, not a playbook resolution branch.

2. After editing, re-validate the workflow before re-running.
   - **Where:** `uip rpa validate --file-path "workflow.xaml" --output json` (or validate in Studio).
   - **Who:** RPA developer.

**Preventive fix**

1. **orchestrator** — Add failure alerting and a manual-restart workflow for faulted jobs of the `Legacy` process in the `Shared` folder.
   - **Why:** This was an attended job that faulted and was not auto-recovered; faulted jobs in Orchestrator must be restarted manually, so the team needs to be alerted rather than relying on someone noticing.
   - **Where:** Configure alerts on **Faulted instances** (scoped to process/folder/tenant); triage via **Job Details**; restart via the Managing Jobs flow.
   - **Who:** Platform team / process owner.
   - **Source:** UiPath docs — job-states, alerts, managing-jobs.

2. **classic-activities** — Standardize scope selection in UI automations and review the Click's target stability.
   - **Why:** The root defect was a scope-type/selector-shape mismatch authored into the workflow; a `DisplayName` ("msedge.exe") that disagrees with the `FileName` (chrome.exe) is a tell-tale of an un-reviewed retarget. Additionally, the Click's selector anchors on a Google **Doodle** link (`aaname='...Creating a Doodle...'`), which is not stably present and would likely cause an element-not-found failure even *after* the scope is fixed.
   - **Where:** `workflow.xaml` — use a browser scope for browser targets and re-author the Click selector against a stable element rather than the Doodle link.
   - **Who:** RPA developer.

**Investigation summary**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | `Click 'push button'` has no usable Target Element/Selector | High | Inconclusive | No | Source shows Click `Target.Selector` is a non-empty valid `webctrl` — primary claim disproven; playbook *signature* confirmed | Mechanism disproven; re-scoped to H2 |
| H2 | Enclosing scope is the wrong scope type — desktop Open Application (`chrome.exe`) given a browser html selector + `ApplicationWindow={x:Null}`, so its context window never initializes and the child Click faults | Medium | Confirmed | **Yes** | `FileName=chrome.exe` + browser `html` selector + null window; `UninitializedNodeException` in `Target.FindByElement` at `ScopeActivity.OnFaulted`; all eliminations passed | Use a browser scope, or give the desktop scope a native window selector + valid `ApplicationWindow`; then re-validate |

> **Confidence note:** H2 is accepted at MEDIUM. The depth-check returned "shallow" with two **textual** gaps (cause label not an exact playbook bullet; no exactly-matching resolution branch). Both are narrative gaps in source-grounded evidence, not factual gaps — surfaced above.

---

The matched playbook's resolution is interactive — I can apply the scope fix to `workflow.xaml` directly. Here are the exact values involved:

```
Project path: <PROJECT_DIR>
File:         workflow.xaml
(EntryPointPath recorded as 'Workflow.xaml'; actual on-disk filename is lowercase 'workflow.xaml')

Misconfigured scope — Open Application 'msedge.exe Google'  (ui:OpenApplication, classic desktop Open Application):
  FileName          = C:\Program Files\Google\Chrome\Application\chrome.exe   (desktop launchable exe)
  Selector          = <html app='chrome.exe' title='Google' />                (BROWSER html selector — wrong shape for a desktop scope)
  ApplicationWindow = {x:Null}                                                (no explicit window)

Child activity — Click 'push button'  (selector is INTACT and valid; do not change to fix the fault):
  Target.Selector   = <webctrl aaname='                   Creating a Doodle                 ' parentid='glue-drawer-2465973' tag='A' />
  Target.Element    = {x:Null}
  (Note: this selector anchors on a Google Doodle link and is unlikely to be stably present — flag for later review, separate from the scope fault.)

Fix: Use a browser scope (Open Browser / Attach Browser / Use Application-Browser pointed at the Chrome page/URL)
     instead of a desktop Open Application, OR give the desktop Open Application a native top-level window
     selector plus a valid ApplicationWindow. Then the child Click 'push button' can resolve against an
     initialized context window.
```
