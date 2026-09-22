# Final Resolution

Root Cause: An explicit `null` literal is assigned to the variable bound to the Copy File activity's Path (and Destination) in Main.xaml, so the activity passes null to `new DirectoryInfo(...)`, which throws `System.ArgumentNullException`.

What went wrong: Process `ERN` (v1.0.6) faulted ~43ms into execution because its Copy File activity received a null path.

Why: Main.xaml declares a String variable `myVar` with no default, then unconditionally assigns the C# literal `null` to it in the Assign immediately before Copy File. Copy File binds both `Path` and `Destination` to `myVar`, so `CopyFile.Execute` calls `new DirectoryInfo(null)`, which raises `ArgumentNullException: Value cannot be null. (Parameter 'path')`. The package is a near-default "Blank Process" template that was published and run without any real path wiring. Orchestrator did not cause the failure — it received the unhandled exception from the robot, marked the job Faulted, and surfaced the stack trace verbatim. No automatic retry occurred (attended jobs do not auto-retry).

Evidence:

### Orchestrator (Propagation)
- Job `ERN` (key `0686cab1-35c6-4d92-aed2-c91d9c275524`) in folder `Shared`, State=`Faulted`, Source=`Agent`, Type=`Attended`, host `MOCK-HOST`, user `original_email@test.com`.
- Duration: StartTime `2026-05-13T08:42:11.170Z` → EndTime `2026-05-13T08:42:12.977Z` (~1.8s). Fault logged at `08:42:11.563Z` (+43ms after start).
- `InputArguments`: `{}` — no inputs supplied by the attended invocation.
- `Info`: `Value cannot be null. (Parameter 'path')` … `at UiPath.Core.Activities.CopyFile.Execute(CodeActivityContext context)` … `at System.IO.DirectoryInfo..ctor(String path)`.
- Process: `ERN` v1.0.6, Description "Blank Process", EntryPoint `Main.xaml`.
- Logs (unfiltered Verbose): only 3 entries — execution started, the Copy File error, execution ended. Job traces contain a single root `RobotJob` span with no activity child spans. No upstream activity emitted output before the fault.

### Runtime-Exceptions (Root Cause)
- File: `` (lines 86–119 of the extract).
- Variable: `myVar` (`x:String`), scoped to `Main Sequence`, no `Default` attribute → initialized to null.
- Assign (Main Sequence): `Assign.To = myVar` (CSharpReference), `Assign.Value = CSharpValue 'null'` — explicit literal null, unconditional (not inside If/Switch/TryCatch), positioned immediately before Copy File.
- Copy File bindings: `Path = CSharpValue "myVar"`, `Destination = CSharpValue "myVar"` (both point to the same null variable; destination would also be invalid).
- Stack: `System.ArgumentNullException.Throw(String paramName)` → `System.IO.DirectoryInfo..ctor(String path)` → `UiPath.Core.Activities.CopyFile.Execute`. User workflow is in the call chain (`at CopyFile "Copy File" at Sequence "Main Sequence" at Main "Main"`), so this is a user-code fault, not an activity-package bug.

Immediate fix:

### Runtime-Exceptions (Root Cause)
1. Open `Main.xaml` in Studio and remove the null assignment to `myVar`. Replace it with either (a) a literal source path or expression that yields a non-null string, or (b) delete the Assign entirely and add an In argument (e.g., `in_SourcePath`) on `Main`, then bind `Copy File`'s `Path` to that argument.
   - Why: the Assign sets `myVar = null` (CSharpValue `null`), which Copy File then dereferences via `new DirectoryInfo(null)` — see `main-xaml-extract.xml` lines 7–19 and the stack in `triage-jobs-get.json` `Data.Info`.
   - Where: ``, `Main Sequence` → `Assign` activity (and the `Variables` panel if introducing an argument instead).
   - Who: RPA developer.
   - Source: `references/runtime-exceptions/playbooks/argument-null-exception.md` § Resolution ("If null file path" / "If null activity input").
2. Bind `Copy File`'s `Destination` to a separate, non-null destination expression — it currently also reads `myVar`, so even after fixing `Path` the activity will fail if `Destination` is null or identical to the source.
   - Why: XAML shows `CopyFile.Destination = CSharpValue "myVar"` (identical to `Path`).
   - Where: `Main.xaml` → `Copy File` activity properties → `Destination`.
   - Who: RPA developer.
   - Source: `argument-null-exception.md` § Resolution ("If null activity input").
3. Validate in Studio (no design-time warnings) and re-publish the process; if you introduced In arguments, supply non-null values via Orchestrator job InputArguments when starting the job.
   - Why: job ran with `InputArguments: {}`; any new required In argument must be provided at invocation.
   - Where: Orchestrator → Tenant → Folder `Shared` → Processes → `ERN` → Start job → Arguments.
   - Who: RPA developer / process owner.
   - Source: `argument-null-exception.md` § Resolution.

### Orchestrator (Propagation)
1. After republishing, restart the job manually from Orchestrator — faulted attended jobs do not auto-retry.
   - Where: Orchestrator → Folder `Shared` → Jobs → select faulted `ERN` job → `Restart`.
   - Who: process owner.
   - Source: https://docs-staging.uipath.com/orchestrator/standalone/2020.10/user-guide/managing-jobs

Preventive fix:

1. Runtime-Exceptions — wrap I/O activities in a guard (`If String.IsNullOrEmpty(path) Then Throw`) before invocation, and prefer In arguments over uninitialized variables for path inputs.
   - Source: `argument-null-exception.md` § Resolution.
2. Runtime-Exceptions — remove "Blank Process" scaffolding before publishing. Process `ERN` v1.0.6 still has Description=`Blank Process` and the only logic is `Assign myVar=null` → `Copy File(myVar, myVar)`.
   - Where: Studio project properties (`project.json` description) and `Main.xaml` body before `uipath publish`.
3. Orchestrator — faulted jobs require manual restart. If resilience matters, redesign queue-driven (queue item retries) or add a webhook/alert on `job.faulted` for folder `Shared`.
   - Source: https://docs-staging.uipath.com/orchestrator/automation-cloud/latest/user-guide/job-states

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | CopyFile.Path resolves to null at execution | medium | confirmed | no (symptom) | Stack `DirectoryInfo..ctor(null)` → `CopyFile.Execute`; fault at +43ms; `InputArguments={}` | Mechanism only; root cause is H4 |
| H2 | Asset / Config lookup returned null | medium | eliminated | no | Main.xaml has no Get Asset / config-read activities | n/a |
| H3 | Missing In argument from caller / job inputs | medium | eliminated | no | `project.json` Main `input=[]`; no Invoke Workflow in Main | n/a |
| H4 | Upstream Assign produced null path | medium | confirmed | **yes** | `main-xaml-extract.xml`: unconditional `Assign myVar = null` immediately before Copy File; `Path` & `Destination` both bound to `myVar` | Replace null Assign with a real path / In argument; bind Destination separately; validate and republish |

---

Want me to clean up `.investigation/`, or edit `Main.xaml` to apply the fix (replace the `null` Assign and bind `Destination` to a separate value)?
