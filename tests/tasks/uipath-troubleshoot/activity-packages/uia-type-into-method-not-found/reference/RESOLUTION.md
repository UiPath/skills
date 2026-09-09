# Final Resolution

Investigation complete. Here is the resolution:

---

**Root Cause:** **`UiPath.UIAutomation.Activities` package version skew between the authoring/debug
environment and the unattended robot.** The `Method not found: 'Void
UiPath.UIAutomationNext.Activities.NTypeInto...'` fault is a `MissingMethodException`: the compiled
workflow binds to a method signature in the `UiPath.UIAutomationNext.Activities` assembly that does not
exist in the version actually restored on the robot. The `.xaml` and selectors are fine — the activity
simply cannot bind against a different package build than the one it was authored against.

**What went wrong:** The `Enter invoice number` `Type Into` (`NTypeInto`) faulted the job the moment it
executed, with `Method not found: 'Void
UiPath.UIAutomationNext.Activities.NTypeInto.set_DelayBetweenKeys(System.Activities.InArgument`1<System.Int32>)'`.
The member the compiled activity expects is absent from the `UiPath.UIAutomation.Activities` assembly
resolved at runtime — the classic symptom of the robot running a different package version than the one
the project was built/debugged with.

**Why:**
- `process/project.json` pins `UiPath.UIAutomation.Activities` at `[24.10.3]`, but the robot restored a
  different version whose `NTypeInto` does not expose the same `set_DelayBetweenKeys` signature.
- `MissingMethodException` at the first UIAutomationNext activity, faulting immediately, is assembly
  version skew — not a selector, target, or logic defect.
- It works in Studio Debug on the developer machine (which has the matching package restored) but
  faults on the robot (different restored version) — the "works on my machine" signature of a
  dependency mismatch across environments.

**Evidence:**
- Job `f7a2e5c8-9d31-4b62-a074-6c1e3f9b2d58` `State = Faulted`; `JobError.Type =
  System.MissingMethodException`; Error log: `Enter invoice number: Method not found: 'Void
  UiPath.UIAutomationNext.Activities.NTypeInto.set_DelayBetweenKeys(...)'`.
- `project.json` dependency `UiPath.UIAutomation.Activities: [24.10.3]`.
- Fails on the unattended robot, runs in local Studio Debug — the two environments have different
  restored versions of the package.

**Immediate fix:**
1. Open **Manage Packages** → Project Dependencies and read the installed `UiPath.UIAutomation.Activities`
   version.
2. Set it to a **single stable version that is identical across every environment** — the authoring
   Studio, the robot, and any other machine that runs the project. Upgrade or downgrade so they match,
   and pin the exact version in `project.json` (not a floating range).
3. Restore / rebuild (`mustRestoreAllDependencies` is already true) and republish the package so the
   robot picks up the aligned dependency.
4. Re-run on the robot — the `Method not found` clears once the restored assembly exposes the method
   signature the `.xaml` was built against.

**Do NOT** rebuild the `.xaml`, re-indicate the `Type Into` target, or change the selector — the
activity and target are intact. Do NOT treat this as a UI targeting or timeout failure; it faults
before any UI interaction, at activity load/bind time.

**Preventive fix:**
- Pin exact activity-package versions in `project.json` and keep them consistent across dev, test, and
  production robots; align versions before publishing.
- Use a shared/governed feed and `mustRestoreAllDependencies` so every environment restores the same
  build; avoid floating version ranges for UI Automation packages.

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | `UiPath.UIAutomation.Activities` version skew: the robot restored a different package version than the project was built against, so `NTypeInto` binds to a missing method. | high | confirmed | Yes | `MissingMethodException` `Method not found: 'Void UiPath.UIAutomationNext.Activities.NTypeInto.set_DelayBetweenKeys(...)'`; `project.json` pins `[24.10.3]`; works in Debug, faults on robot. | Align `UiPath.UIAutomation.Activities` to one stable version across all environments, pin it, restore/republish. |
| H2 | Selector / UI targeting failure on the invoice field. | low | eliminated | No | No `SelectorNotFoundException`/`UiElementNotFoundException`; job faults at activity bind time before any UI interaction, with a `MissingMethodException`. | N/A |
| H3 | Activity timeout / element never appeared. | low | eliminated | No | No `RuntimeTimeoutException`/`TimeoutException`; job faulted in ~4s at load, not after a wait. | N/A |
| H4 | Corrupt `.xaml` / activity must be re-added. | low | eliminated | No | The `NTypeInto` node is well-formed; the failure is a runtime assembly bind, resolved by version alignment, not by rebuilding the activity. | N/A |
