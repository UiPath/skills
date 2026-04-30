# Modern Studio / 2024.10+ Specific Issues

Antipatterns specific to UiPath Studio 2024.10+ (Modern design experience, coded workflows, Object Repository, Data Manager, Healing Agent).

## Modern Excel + Classic Excel Mixing

**Symptom:** Same project contains both `UseExcelFile` (Modern — uses ClosedXML, no Excel needed) and `ExcelApplicationScope` (Classic — requires Excel installed, uses COM), OR `WriteRangeWorkbook` / `ReadRangeWorkbook` (Workbook activities) nested inside a `UseExcelFile` scope.

**Impact:** COM object conflicts. Workbook activities and `Use Excel File` fight for the same file handle. Intermittent file lock errors, data corruption, Excel processes left behind in memory.

**Detection:** Grep `.xaml` for both `ExcelApplicationScope` and `ExcelApplicationCard` (UseExcelFile) in the same project. Grep for `WriteRangeWorkbook` / `ReadRangeWorkbook` activities appearing as children of `ExcelApplicationCard`.

**Fix:** Pick one approach per project. For new work, use Modern (`Use Excel File`) for workflows that don't need macros/pivots. Use Classic `Excel Application Scope` when you need Excel-specific features (macros, pivots, charts).

**Severity:** Warning

## Multiple Single Excel Process Scope Activities

**Symptom:** Project contains more than one `Single Excel Process Scope` activity across its workflows.

**Impact:** COM object error at runtime. This activity manages a single Excel COM instance — multiple scopes conflict. Documented erratum since June 2025.

**Detection:** Grep all `.xaml` files for `SingleExcelProcessScope`. Flag if count > 1 across the project.

**Fix:** Consolidate to one `Single Excel Process Scope` per project. If multiple isolated Excel sessions are genuinely required, use separate workflows invoked sequentially.

**Severity:** Critical

## Modern Excel Read Range Performance Cliff

**Symptom:** Using Modern `Use Excel File` + `Read Range` for large datasets (>10K rows) without mitigation.

**Impact:** ~100x slower than Classic `Excel Application Scope` + `Read Range`. 30K rows: ~5s Classic vs >15 minutes Modern. 17K rows reported at 30 minutes. Affects SAP-exported data with special characters / images especially badly.

**Detection:** Project uses Modern design + `Use Excel File` + `Read Range` on datasets known to exceed 10K rows. `ReadOnly` property not set.

**Fix:** For large read-only reads, use Classic `Excel Application Scope`. If staying on Modern, set `ReadOnly = True` and read specific ranges rather than whole sheets. For very large data, consider DataTable operations with CSV intermediate storage.

**Severity:** Warning

## Wrong Project Compatibility for Target Runtime

**Symptom:** Project's `targetFramework` in `project.json` does not match the deployment target — e.g., `Windows` targeting Linux serverless robots, or `Portable` (cross-platform) project using UI Automation activities.

**Impact:** Windows projects fail immediately on Linux with unclear errors. Cross-platform projects lack entire activity categories (UI Automation, Excel interop). The compatibility choice is set at creation and cannot be changed — only recreated.

**Detection:** Read `project.json` `targetFramework`. Cross-check against deployment target: if `Windows` and any deployment target is Linux/container-based, flag. If `Portable` and project contains UI Automation or Excel COM activities, flag.

**Fix:** Recreate the project with correct compatibility for the deployment target. Migrate source files manually (no automated converter between Windows and Cross-platform).

**Severity:** Critical

## Project Rename Breaks Coded Workflow Assembly References

**Symptom:** Project renamed after `.cs` coded workflows or Coded Source Files have been created.

**Impact:** Assembly references in XAML files become stale. Coded types unresolvable. Compiles locally (cached) but fails during clean build, publishing, or cross-project invocation.

**Detection:** Grep XAML for `AssemblyQualifiedName` or `clr-namespace=...;assembly=` references. Compare the assembly name to `project.json` `name` field.

**Fix:** Do not rename projects with coded workflows. If rename is required: clean the project, remove all `.cs.json` metadata, rebuild, and fix XAML references manually. Simpler: recreate the project and migrate source.

**Severity:** Critical

## Coded Workflow Arguments Without Parameterless Constructor

**Symptom:** Custom data types used as coded workflow (`[Workflow]`) arguments without a public parameterless constructor.

**Impact:** Studio cannot serialize/deserialize arguments. Surfaces as Studio validation errors, inability to invoke the workflow, or runtime failures during argument marshaling.

**Detection:** Grep `.cs` files for classes used as workflow arguments. Check each for a `public ClassName()` constructor (no parameters).

**Fix:** Add a public parameterless constructor to every class used as a workflow argument, or use built-in serializable types (primitives, DataTable, JObject).

**Severity:** Warning

## Coded / XAML Nested Class Argument Interop Failure

**Symptom:** Hybrid project (both `.cs` and `.xaml`) passing arguments whose types are nested C# classes between coded and XAML workflows.

**Impact:** XAML engine cannot resolve types from nested classes. Compiles locally but fails at runtime with `"Value cannot be null (Parameter 'type')"` or similar type-resolution errors. Documented Studio 2024.10+ limitation.

**Detection:** In hybrid projects, check `InvokeWorkflowFile` arguments where the invoked workflow is a `.cs` file. Verify argument types are not nested class definitions.

**Fix:** Flatten nested class hierarchies used as arguments. Use top-level public classes or Pydantic-style DTOs.

**Severity:** Warning

## Object Repository Flat Structure (No Application/Screen Hierarchy)

**Symptom:** All UI descriptors dumped into `.objects/` without organizing into the Application → Screen → Element hierarchy. Duplicate descriptors for the same UI element created by different developers.

**Impact:** Unmaintainable descriptor soup. When target UI changes, no way to scope updates to one screen. Duplicate descriptors cause "which is authoritative?" confusion. Descriptor count grows linearly with team size.

**Detection:** Inspect `.objects/` folder structure. Flat list of descriptors (no Application/Screen subfolders) = antipattern. Search for descriptors with overlapping selectors targeting the same UI element.

**Fix:** Restructure using Application → Screen → Element hierarchy. Deduplicate — each distinct UI element gets one authoritative descriptor. Promote org-wide descriptors into a published UI Library.

**Severity:** Warning

## Data Manager Global Variable Naming Conflicts

**Symptom:** Global variables created via Data Manager share names with arguments or local variables in sub-workflows.

**Impact:** Variables and arguments with the same name = variable takes precedence silently. Workflow uses the wrong value. Especially dangerous when globals are not supported in libraries / isolated invocations.

**Detection:** Parse all XAML for variables scoped at Global. Check if any global name matches an argument name in any workflow.

**Fix:** Use distinct naming conventions for globals (e.g., `g_ConfigValue` prefix) vs arguments (`in_`, `out_`, `io_`). Rename to eliminate collisions.

**Severity:** Warning

## Healing Agent Noise Logs on Classic Activities

**Symptom:** Project uses Classic UI activities (`Attach Window`, classic `FindElement`, classic `GetAttribute`) and Healing Agent is not explicitly disabled.

**Impact:** Classic activities trigger Healing Agent telemetry logging ("Healing agent configuration") even when healing is not enabled. No suppression mechanism exists. Log noise clutters monitoring and masks real issues, especially at scale.

**Detection:** Grep XAML for Classic UI activity types (`AttachWindow`, classic `FindElement`, etc.). Check governance policy for Healing Agent disable setting.

**Fix:** Either migrate Classic activities to Modern (which uses Healing Agent cleanly), OR explicitly disable Healing Agent for projects using Classic activities via governance policy.

**Severity:** Info

## Object Repository in Project When UI Library Needed

**Symptom:** Multiple projects in the org automate the same target application (e.g., SAP, Salesforce), each with its own local `.objects/` Object Repository for that app.

**Impact:** UI changes require updating every project's local copy. Selector fixes don't propagate. Teams end up with divergent descriptors — "works on my project, fails on theirs." Healing Agent healing one project's copy doesn't help the others.

**Detection:** Find all projects referencing the same application in `.objects/`. Check `project.json` dependencies for a shared UI Library. Absence = antipattern.

**Fix:** Extract the shared Object Repository into a published UI Library. Consumers reference it via `project.json` dependencies with pinned versions.

**Severity:** Warning
