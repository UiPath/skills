# Final Resolution

Investigation complete. Here is the resolution:

---

**Root Cause:** The invoked workflow **lives outside the main project folder**, so it is not included
in the published package. `Main.xaml`'s `Invoke Workflow File` targets
`..\Shared\EmailHelper.xaml` — a relative path that escapes the project root. The file exists on the
developer machine (one level up from the project), so Studio runs it locally, but it is never packed,
so on publish/run the robot cannot find it and throws `System.IO.FileNotFoundException`.

**What went wrong:** The `WorkflowFileName` is a literal relative path (`..\Shared\EmailHelper.xaml`)
pointing **above** the project directory. Only files inside the project root are packaged. "Works on my
machine, fails on publish/run" is the classic symptom of a dependency that exists in the dev layout but
is excluded from the package.

**Why:**
- `process/Main.xaml` — `<uca:InvokeWorkflowFile>` InvokeWorkflowFile_1, DisplayName "Invoke
  EmailHelper", with `WorkflowFileName="..\Shared\EmailHelper.xaml"`. The `..\` escapes the project
  root.
- `EmailHelper.xaml` is **not present** anywhere inside the project (`process/`). It resolves only
  relative to the developer's folder layout, one level up.
- The path is a literal, not a variable, so the failure is a packaging/location problem, not a null
  path expression.
- The error `System.IO.FileNotFoundException: Cannot find the file 'EmailHelper.xaml'` surfaces at
  publish/run because the file was never packed.

**Evidence:**
- Error string: `System.IO.FileNotFoundException` / `Cannot find the file 'EmailHelper.xaml'`.
- `Main.xaml`: `WorkflowFileName="..\Shared\EmailHelper.xaml"` — path outside the project root.
- No `EmailHelper.xaml` under `process/`; no other project file provides it.
- Runs in Studio (dev layout has the sibling `Shared` folder) but not after publish (file excluded).

**Immediate fix:**
1. **Move `EmailHelper.xaml` inside the main project folder** (e.g. into a subfolder of the project
   like `Shared\`), then update the `Invoke Workflow File`'s `WorkflowFileName` to the in-project
   relative path (e.g. `Shared\EmailHelper.xaml`). All invoked workflows must live inside the project
   so they pack correctly.
   - Where: `Main.xaml` InvokeWorkflowFile_1 `WorkflowFileName`; relocate the `.xaml` under the project
     root.
2. Re-publish and confirm the invoked workflow is included in the package.

**Preventive fix:**
- Keep every invoked `.xaml` inside the project directory; never reference workflows via `..\` paths
  that escape the project root — they are not packaged.
- If a workflow path is ever built dynamically, also verify the path variable resolves to a non-null,
  valid, in-project value before the invoke runs.

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | The invoked `EmailHelper.xaml` sits outside the project root (`..\Shared\`), so it is not packed; the robot cannot find it at run time → `FileNotFoundException`. | high | confirmed | Yes | `Main.xaml` `WorkflowFileName="..\Shared\EmailHelper.xaml"`; no such file under the project; runs in dev but not on publish. | Move the invoked workflow inside the project folder and repoint the invoke to the in-project path. |
| H2 | The `WorkflowFileName` is a variable that resolved to null at run time. | low | eliminated | No | `WorkflowFileName` is a literal string, not an expression/variable. | N/A — path is hardcoded outside the project, not a null variable. |
