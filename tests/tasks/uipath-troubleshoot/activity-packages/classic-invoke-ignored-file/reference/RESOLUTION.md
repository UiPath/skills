# Final Resolution

Investigation complete. Here is the resolution:

---

**Root Cause:** The invoked workflow is **excluded from the published package** by
`project.json`. `Main.xaml` invokes `Helpers\CalculateTax.xaml`, and that file — although present in the
project source — is listed under `designOptions.processOptions.ignoredFiles`, so it is not packed.
The process runs in Studio (the file is on disk in the dev layout) but on the robot the invoke cannot
load the missing file and throws `System.IO.FileNotFoundException`.

**What went wrong:** Job `3c8f1a52-7b09-4d64-9e28-1a5c0f3e7b26` (process **TaxProcessing**, folder
**Shared**, robot **MOCK-HOST**, unattended) faulted with `FileNotFoundException` for
`Helpers\CalculateTax.xaml`. "Works in Studio, fails on the robot" is the signature of a file that
exists in source but was excluded from the package — here explicitly via `ignoredFiles`.

**Why:**
- `process/Main.xaml` — `<uca:InvokeWorkflowFile … WorkflowFileName="Helpers\CalculateTax.xaml" …>`
  (DisplayName "Invoke CalculateTax").
- `process/Helpers/CalculateTax.xaml` — **present** in the project source (so it runs locally).
- `process/project.json` — `designOptions.processOptions.ignoredFiles` contains
  `"Helpers\\CalculateTax.xaml"`. Files listed there are excluded from the published package, so the
  `.xaml` is absent on the robot at run time.
- The stack shows the fault at `UiPath.Core.Activities.InvokeWorkflowFile.LoadWorkflow` — the invoke
  fails to load the file, not the child body throwing. A prior run on machine **DEV-STUDIO-01**
  succeeded, consistent with the file existing in the dev layout but not in the package.

**Evidence:**
- Error: `System.IO.FileNotFoundException: Could not find file 'Helpers\CalculateTax.xaml'` at
  `InvokeWorkflowFile.LoadWorkflow`.
- `project.json` `ignoredFiles` = `["Helpers\\CalculateTax.xaml"]` — the exact invoked file.
- The invoked file is present in source but excluded from packing; runs in Studio, fails on the robot.
- Job identity: Key `3c8f1a52-…`, `ReleaseName` TaxProcessing, `EntryPointPath` Main.xaml, `State`
  Faulted, `ErrorCode` Robot, folder **Shared** (`d4e08b31-…`), robot **MOCK-HOST**, unattended.

**Immediate fix:**
1. Remove `Helpers\CalculateTax.xaml` from `designOptions.processOptions.ignoredFiles` in
   `project.json` so the invoked workflow is included in the package.
   - Where: `project.json` → `designOptions.processOptions.ignoredFiles` (delete the entry).
2. Re-publish and confirm `Helpers\CalculateTax.xaml` is present in the package, then re-run on the
   robot.

**Preventive fix:**
- Do not add invoked workflows to `ignoredFiles`; only exclude files that are truly not needed at run
  time. After changing `ignoredFiles`, verify every `Invoke Workflow File` target is still packaged.

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | `Helpers\CalculateTax.xaml` is in `project.json` `ignoredFiles`, so it is excluded from the package; the robot cannot load it and the invoke throws `FileNotFoundException`. | high | confirmed | Yes | `ignoredFiles` lists the exact invoked file; file present in source; fault at `InvokeWorkflowFile.LoadWorkflow`; runs in Studio but not on the robot. | Remove the file from `ignoredFiles` and re-publish. |
| H2 | The invoked workflow path is simply wrong / the file was never created. | low | eliminated | No | `Helpers\CalculateTax.xaml` exists in the project at the path the invoke references; the problem is packaging exclusion, not a bad path. | N/A. |
