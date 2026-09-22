# Final Resolution

Investigation complete. Here is the resolution:

---

**Root Cause:** **Invalid isolated / target-session combination on the Invoke Workflow File.** In
`Main.xaml` the invoke sets `TargetSession="PictureInPicture"` (a non-`Current` session) while
`UnSafe="False"` (not isolated). Running an invoked workflow in a session other than `Current` requires
isolated execution (`UnSafe = True`); the runtime rejects the combination and the invoke's
`CacheMetadata` validation throws, faulting the job.

**What went wrong:** Job `6b1e4d70-3a92-4c58-8f01-2d7c9a3e5b14` (process **ReportDispatch**, folder
**Shared**, machine **MOCK-HOST**) faulted with a validation error the moment the Invoke Workflow File
was initialized. `TargetSession` was changed to `PictureInPicture` without also enabling `UnSafe`
(Isolated), which is a combination the runtime does not allow.

**Why:**
- Job Info/logs: "When TargetSession is set to a value other than Current, the invoked workflow must
  run isolated. TargetSession 'PictureInPicture' requires UnSafe (Isolated) = True." Stack:
  `System.Activities.InvalidWorkflowException` at
  `UiPath.Core.Activities.InvokeWorkflowFile.CacheMetadata` — a validation fault at the invoke, before
  the child body runs.
- `process/Main.xaml` — `<uca:InvokeWorkflowFile … UnSafe="False" TargetSession="PictureInPicture"
  WorkflowFileName="GenerateReport.xaml" …>`. `UnSafe` (Isolated) is **False** while `TargetSession`
  is **PictureInPicture** (non-`Current`).
- `process/GenerateReport.xaml` — present and valid; the fault is not in the child. The invoke's
  session/isolation configuration is the problem.

**Evidence:**
- Error: `System.Activities.InvalidWorkflowException` at `InvokeWorkflowFile.CacheMetadata`; message
  ties `TargetSession` non-`Current` to the isolated-execution requirement.
- Source: `UnSafe="False"` + `TargetSession="PictureInPicture"` on the invoke in `Main.xaml`.
- Fault localizes to the invoke (validation), not to any activity inside the child.
- Job identity: Key `6b1e4d70-…`, `ReleaseName` ReportDispatch, `EntryPointPath` Main.xaml, `State`
  Faulted, `ErrorCode` Robot, folder **Shared** (`c3d97a20-…`), machine **MOCK-HOST**.

**Immediate fix:**
1. On the `Invoke Workflow File` ("Invoke GenerateReport") in `Main.xaml`, set **`UnSafe` (Isolated) =
   True** so the non-`Current` `TargetSession` (`PictureInPicture`) is allowed.
   - Where: `Main.xaml` InvokeWorkflowFile_1 — `UnSafe="True"`.
2. Or, if the workflow does not actually need to run in PictureInPicture, set **`TargetSession =
   Current`** (and leave `UnSafe="False"`). Choose one supported combination — do not leave a
   non-`Current` session with `UnSafe=False`.

**Preventive fix:**
- Whenever setting `TargetSession` to `Main` or `PictureInPicture` on an Invoke Workflow File, also set
  `UnSafe` (Isolated) = True; a non-`Current` session without isolation always fails validation.

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | The invoke uses `TargetSession="PictureInPicture"` with `UnSafe="False"`; a non-`Current` session requires isolated execution, so `CacheMetadata` validation throws and the job faults. | high | confirmed | Yes | Error names the TargetSession/isolated requirement at `InvokeWorkflowFile.CacheMetadata`; source shows `UnSafe="False"` + `TargetSession="PictureInPicture"`. | Set `UnSafe=True` (or revert `TargetSession` to `Current`). |
| H2 | The invoked workflow `GenerateReport.xaml` threw its own exception. | low | eliminated | No | The fault is a validation error at the invoke's `CacheMetadata`, before the child runs; the child is valid. | N/A — the child never executed. |
