# Final Resolution

Investigation complete. Here is the resolution:

---

**Root Cause:** A **package-version mismatch** on `UiPath.System.Activities`. `Main.xaml` contains an
`Invoke Workflow File` that serializes an `ArgumentsVariable` member, but `project.json` pins
`UiPath.System.Activities` to an **older** version (`[22.10.4]`) whose `InvokeWorkflowFile` type does
not declare that member. When Studio deserializes the XAML against the pinned package, it cannot set
the unknown member and reports the compile error.

**What went wrong:** This is a **design-time / build-time** compile error, not a robot job fault. The
`.xaml` was authored (or a shared workflow edited) with a newer `UiPath.System.Activities` in which
`Invoke Workflow File` exposes `ArgumentsVariable`; the project itself is still pinned to `[22.10.4]`,
which predates that property. The deserializer rejects the member it does not recognize.

**Why:**
- `process/Main.xaml` — the `<uca:InvokeWorkflowFile>` node (`IdRef` InvokeWorkflowFile_1, DisplayName
  "Invoke CalculateTotals", targeting `CalculateTotals.xaml`) carries the attribute
  `ArgumentsVariable="{x:Null}"`. This is the exact member named in the error:
  `UiPath.Core.Activities.InvokeWorkflowFile.ArgumentsVariable`.
- `process/project.json` — `dependencies` pins `"UiPath.System.Activities": "[22.10.4]"`. That version
  is older than the one that introduced `ArgumentsVariable`; the type it ships has no such property, so
  setting it during XAML load fails.
- The mismatch (member present in the XAML, older package pinned) is the package-version regression the
  playbook describes — introduced by an upgrade of the project layout or by editing the workflow with a
  newer package while the project pin lagged behind.

**Evidence:**
- Error string: `Cannot set unknown member 'UiPath.Core.Activities.InvokeWorkflowFile.ArgumentsVariable'`.
- `Main.xaml`: `uca:InvokeWorkflowFile ... ArgumentsVariable="{x:Null}" WorkflowFileName="CalculateTotals.xaml"`.
- `project.json`: `"UiPath.System.Activities": "[22.10.4]"`.
- The invoked child `CalculateTotals.xaml` exists in the project — the failure is member deserialization,
  not a missing file.
- No Orchestrator job, log, or trace is involved; this surfaces in Studio's Error List at open/validate.

**Immediate fix:**
1. **Align the `UiPath.System.Activities` version.** In Package Manager, update the project's
   `UiPath.System.Activities` pin to the version that introduced `ArgumentsVariable` (the version the
   workflow was authored with) — or, if you must stay on `22.10.4`, downgrade / re-save the shared
   workflow against `22.10.4` so it no longer serializes `ArgumentsVariable`.
   - Where: `project.json` `dependencies.UiPath.System.Activities`.
2. **Refresh the invocation.** Right-click the workflow → **Find References**, open each `Invoke
   Workflow File`, and click **Import Arguments** to regenerate the parameter layout for the aligned
   package version.

**Preventive fix:**
- Keep `UiPath.System.Activities` at a single, consistent version across the project and any shared
  workflows so an `Invoke Workflow File` is never saved with a member the pinned package cannot load.
- Do not hand-edit dependency versions; change them through Package Manager so the XAML and the pin stay
  in step.

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | `Invoke Workflow File` serializes `ArgumentsVariable`, but `project.json` pins an older `UiPath.System.Activities` (`22.10.4`) that lacks the member, so Studio cannot set it on load. | high | confirmed | Yes | `Main.xaml` `ArgumentsVariable="{x:Null}"` on InvokeWorkflowFile_1; `project.json` pins `UiPath.System.Activities [22.10.4]`; error names exactly that member. | Align the `UiPath.System.Activities` version, then Import Arguments on the invoke. |
| H2 | The invoked file `CalculateTotals.xaml` is missing. | low | eliminated | No | `CalculateTotals.xaml` is present in the project; the error is about an unknown member, not a missing file. | N/A. |
