# Modern Studio / 2024.10+ Specific Issues

Antipatterns for UiPath Studio 2024.10+ Modern design experience, coded workflows, Object Repository, Data Manager, and Healing Agent.

## Modern Excel + Classic Excel Mixing

**Symptom:** A project contains both `UseExcelFile` (Modern; ClosedXML; no Excel required) and `ExcelApplicationScope` (Classic; requires Excel; COM), or contains `WriteRangeWorkbook` / `ReadRangeWorkbook` inside `UseExcelFile`.

**Impact:** COM conflicts, file locks, corruption, and orphaned Excel processes.

**Detection:** Grep `.xaml` for both `ExcelApplicationScope` and `ExcelApplicationCard`. Grep for `WriteRangeWorkbook` / `ReadRangeWorkbook` as children of `ExcelApplicationCard`.

**Fix:** Choose one approach per project. Use Modern `Use Excel File` for new workflows that do not need macros or pivots; use Classic `Excel Application Scope` for macros, pivots, or charts.

**Severity:** Warning

## Multiple Single Excel Process Scope Activities

**Symptom:** More than one `Single Excel Process Scope` exists across project workflows.

**Impact:** Multiple scopes conflict over the single Excel COM instance and cause runtime COM errors.

**Detection:** Grep all `.xaml` files for `SingleExcelProcessScope`; flag counts above one across the project.

**Fix:** Use one `Single Excel Process Scope` per project. If isolated Excel sessions are genuinely required, use separate workflows invoked sequentially.

**Severity:** Critical

## Modern Excel Read Range Performance Cliff

**Symptom:** Modern `Use Excel File` + `Read Range` reads datasets over 10K rows without mitigation.

**Impact:** Large reads can be orders of magnitude slower than Classic `Excel Application Scope` + `Read Range`, with reports ranging from minutes to tens of minutes for 10K+ rows. SAP-exported data with special characters or images can be especially affected.

**Detection:** Confirm Modern design, `Use Excel File`, `Read Range`, a dataset known to exceed 10K rows, and an unset `ReadOnly` property.

**Fix:** For large read-only reads, use Classic `Excel Application Scope`. If remaining on Modern, set `ReadOnly = True` and read specific ranges instead of whole sheets. For very large data, consider DataTable operations with CSV intermediate storage.

**Severity:** Warning

## Wrong Project Compatibility for Target Runtime

**Symptom:** `project.json` `targetFramework` does not match deployment, such as `Windows` for Linux/container-based serverless robots or `Portable` for projects using UI Automation activities.

**Impact:** Windows projects fail on Linux; cross-platform projects lack UI Automation and Excel COM activity categories. Compatibility is set at creation and cannot be changed; the project must be recreated.

**Detection:** Read `project.json` `targetFramework` and compare it with deployment. Flag `Windows` for Linux/container-based deployment and `Portable` when UI Automation or Excel COM activities are present.

**Fix:** Recreate the project with the correct compatibility and migrate source files manually; no automated converter exists between Windows and Cross-platform.

**Severity:** Critical

## Project Rename Breaks Coded Workflow Assembly References

**Symptom:** A project is renamed after `.cs` coded workflows or Coded Source Files are created.

**Impact:** XAML assembly references become stale and coded types become unresolvable. Cached local builds may succeed while clean builds, publishing, or cross-project invocation fails.

**Detection:** Grep XAML for `AssemblyQualifiedName` or `clr-namespace=...;assembly=` and compare the assembly name with `project.json` `name`.

**Fix:** Do not rename projects containing coded workflows. If required, clean the project, remove all `.cs.json` metadata, rebuild, and fix XAML references manually. Prefer recreating the project and migrating source.

**Severity:** Critical

## Coded Workflow Arguments Without Parameterless Constructor

**Symptom:** A custom data type used as a coded workflow (`[Workflow]`) argument lacks a public parameterless constructor.

**Impact:** Studio cannot serialize or deserialize the argument, causing validation, invocation, or runtime argument-marshaling failures.

**Detection:** Grep `.cs` files for classes used as workflow arguments and check for `public ClassName()` constructors with no parameters.

**Fix:** Add a public parameterless constructor to every such class, or use built-in serializable types such as primitives, `DataTable`, or `JObject`.

**Severity:** Warning

## Coded / XAML Nested Class Argument Interop Failure

**Symptom:** A hybrid `.cs`/`.xaml` project passes nested C# class types between coded and XAML workflows, including through `InvokeWorkflowFile` when the invoked workflow is a `.cs` file.

**Impact:** The XAML engine cannot resolve nested-class types. Local compilation may succeed, but runtime fails with `Value cannot be null (Parameter 'type')` or similar type-resolution errors. This is a documented Studio 2024.10+ limitation.

**Detection:** In hybrid projects, inspect `InvokeWorkflowFile` arguments for invoked `.cs` workflows and verify that argument types are not nested class definitions.

**Fix:** Flatten nested class hierarchies used as arguments. Use top-level public classes or Pydantic-style DTOs.

**Severity:** Warning

## Object Repository Flat Structure (No Application/Screen Hierarchy)

**Symptom:** UI descriptors are dumped directly into `.objects/` without an Application → Screen → Element hierarchy, and different developers create duplicates for the same element.

**Impact:** The repository becomes unmaintainable; UI changes cannot be scoped to a screen, authoritative descriptors are unclear, and descriptor count grows with team size.

**Detection:** Inspect `.objects/`. A flat descriptor list without Application/Screen subfolders is an antipattern. Search for overlapping selectors targeting the same UI element.

**Fix:** Organize descriptors as Application → Screen → Element. Deduplicate so each distinct UI element has one authoritative descriptor. Promote organization-wide descriptors into a published UI Library.

**Severity:** Warning

## Data Manager Global Variable Naming Conflicts

**Symptom:** A Data Manager global variable shares a name with an argument or local variable in a sub-workflow.

**Impact:** The variable silently takes precedence, so the workflow may use the wrong value. This is especially dangerous when globals are unsupported in libraries or isolated invocations.

**Detection:** Parse all XAML for variables scoped at Global and compare global names with argument names in every workflow.

**Fix:** Use distinct conventions, such as `g_ConfigValue` for globals and `in_`, `out_`, or `io_` for arguments; rename collisions.

**Severity:** Warning

## Healing Agent Noise Logs on Classic Activities

**Symptom:** A project uses Classic UI activities (`Attach Window`, classic `FindElement`, classic `GetAttribute`, etc.) without explicitly disabling Healing Agent.

**Impact:** Classic activities generate Healing Agent telemetry such as `Healing agent configuration` even when healing is not enabled. No suppression mechanism exists; noise can obscure real issues at scale.

**Detection:** Grep XAML for Classic UI activity types such as `AttachWindow` and classic `FindElement`, then check governance policy for a Healing Agent disable setting.

**Fix:** Migrate Classic activities to Modern, or explicitly disable Healing Agent through governance policy for projects using Classic activities.

**Severity:** Info

## Object Repository in Project When UI Library Needed

**Symptom:** Multiple projects automate the same target application, each maintaining a local `.objects/` repository.

**Impact:** UI changes require updates in every project, selector fixes do not propagate, and repositories diverge. Healing one project's copy does not help others.

**Detection:** Find projects referencing the same application in `.objects/`. Check `project.json` dependencies for a shared UI Library; absence is an antipattern.

**Fix:** Extract the shared Object Repository into a published UI Library. Reference it from consumers through `project.json` dependencies with pinned versions.

**Severity:** Warning
