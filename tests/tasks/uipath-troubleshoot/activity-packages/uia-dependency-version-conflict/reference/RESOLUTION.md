# Final Resolution

---

**Root Cause:** The project's dependency set in `project.json` is internally
inconsistent. It pins `UiPath.UIAutomation.Activities` at `[24.10.9]` while
`UiPath.System.Activities` is left at `[22.4.4]` and the developer is on
**UiPath Studio 2022.4** (`studioVersion 22.4.3.0`). The newer UI Automation
package was bumped in isolation; its `UiPath.UIAutomationNext(.Activities)`
runtime expects members that the older System.Activities / Studio-bundled
UIAutomationNext assemblies do not expose. When the workflow is opened or
validated, the UIAutomationNext activities (`NApplicationCard`, `NClick`) bind
against the older assembly and Studio throws
`System.MissingMethodException: Method not found: 'Void
UiPath.UIAutomationNext.Activities...'`. This is **Signature A** of the
UIAutomationNext dependency/version-conflict playbook — a version mismatch
**inside the project's own dependency set**, surfacing at design time /
validation. The process has never executed, so there are no Orchestrator jobs
to inspect.

**What went wrong:** Opening / validating `AccountOnboardingBot` raises
`MissingMethodException` naming `UiPath.UIAutomationNext.Activities`; the
Click activities show errors. There is no faulted job and no runtime log
because the process never ran — the failure is entirely at design time.
`project.json` shows `UiPath.UIAutomation.Activities [24.10.9]` against
`UiPath.System.Activities [22.4.4]` and `studioVersion 22.4.3.0`.

**Why:** `MissingMethodException` / "Method not found" means the
`UiPath.UIAutomationNext.Activities` assembly **loaded** but a member the
caller was compiled against is **absent** — the hallmark of mismatched
versions among the packages that carry UIAutomationNext, not a missing
assembly. Bumping `UiPath.UIAutomation.Activities` far ahead of
`UiPath.System.Activities` (and the Studio line) leaves the resolved
UIAutomationNext runtime older than what the package expects, so the method
lookup fails at bind time.

---

**Evidence:**

### Design-time (Root Cause)
- Symptom: `System.MissingMethodException: Method not found: 'Void UiPath.UIAutomationNext.Activities...'` on opening / validating the workflow in Studio; Click activities show errors. No execution.
- `project.json`: `"UiPath.UIAutomation.Activities": "[24.10.9]"`, `"UiPath.System.Activities": "[22.4.4]"`, `"studioVersion": "22.4.3.0"` — the UI Automation package is bumped out of step with the foundational System.Activities line and the installed Studio.
- The error appears at design time / validation, not as a runtime job fault.

### Orchestrator (ruled out)
- No jobs exist for this process (it has never run); `or jobs list ... --state Faulted` returns an empty list. Job evidence is not the source of this diagnosis — `project.json`'s dependency set is.

### Signature B (ruled out)
- This is NOT the runtime `FileNotFoundException` / `FileLoadException`
  "Could not load file or assembly 'UiPath.UIAutomationNext.Activities'"
  fault (works in Studio, fails in Assistant/robot because the robot's NuGet
  cache or the Orchestrator feed can't supply the pinned version). Here the
  assembly loads — a method is missing — and the failure reproduces in Studio
  at design time. Cleaning `%userprofile%\.nuget\packages` / republishing is
  the WRONG fix for this case; it does not change which versions
  `project.json` resolves.

---

**Immediate fix:**

Align the project's dependency set to a mutually compatible line via **Manage
Packages** — update the packages **together**, not one in isolation.

### Fix path A -- update all foundational packages together (recommended)
- Open `Manage Packages` in Studio, and update `UiPath.System.Activities`
  **and** `UiPath.UIAutomation.Activities` (plus any package that brings
  `UiPath.UIAutomationNext`) to the same latest-stable, mutually compatible
  line, then reopen / revalidate the workflow.

### Fix path B -- match the UI Automation package to the current Studio/System line
- If staying on the Studio 2022.4 / `UiPath.System.Activities 22.4` line,
  downgrade `UiPath.UIAutomation.Activities` to the version that ships
  compatible with that line, so the resolved UIAutomationNext runtime exposes
  the members the activities call.
- **Source:** `ui-automation/playbooks/dependency-version-conflict.md`
  (Signature A).

> Do not chase Orchestrator/runtime evidence and do not clean the NuGet cache
> or republish — the process never ran and the assembly loads fine. The fix
> is version alignment of the project's dependency set in Manage Packages.

---

**Preventive fix:**

1. **Bump activity packages as a compatible set, not individually** -- when
   updating `UiPath.UIAutomation.Activities`, move `UiPath.System.Activities`
   and any UIAutomationNext-bearing sibling/library to a matching line.
   - **Why:** a UI Automation package ahead of the foundational line resolves
     an older UIAutomationNext runtime and throws `MissingMethodException` at
     bind time.
   - **Who:** RPA developer / platform team.

2. **Validate dependency bumps in the target Studio before committing** --
   confirm the project opens and validates cleanly on the Studio line the
   team runs.
   - **Who:** RPA developer.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | project.json pins UiPath.UIAutomation.Activities [24.10.9] out of step with UiPath.System.Activities [22.4.4] / Studio 22.4, so UIAutomationNext binds an older runtime and throws MissingMethodException at design time | Medium | Confirmed | Yes | Design-time MissingMethodException "Method not found: 'Void UiPath.UIAutomationNext.Activities...'" + project.json version skew + never ran (no jobs) | Align all foundational packages to a compatible line via Manage Packages (or downgrade UIAutomation to match the 22.4 line) |

---

Would you like the specific `UiPath.UIAutomation.Activities` /
`UiPath.System.Activities` version pairing known to work on Studio 2022.4, or
guidance on moving the whole set to the latest stable line instead?
