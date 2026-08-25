# Runtime Exceptions

General .NET runtime exceptions originating from the user's own workflow code — variable handling, data processing, argument passing, and control flow logic. Also covers **design-time Studio validation errors** raised on the user's own expressions (e.g. `If` compiler errors and `Assign` type mismatches surfaced in the Studio Error List at open/validate/build) and **silent control-flow faults** where a workflow runs Successful but takes the wrong branch — these are fixed in the same `.xaml`/`.cs` the user owns, so they live here rather than under any activity package.

## Scope Boundary

These playbooks ONLY cover exceptions where the root cause is in the user's workflow code (`.xaml` or `.cs` files they wrote). The user has access to this code and can fix it.

**If the stack trace shows the exception originates inside an activity package** (e.g., `UiPath.UIAutomationNext.Activities`, `UiPath.Core.Activities`, or any third-party package namespace), this is NOT a runtime exception issue — route to the relevant activity package troubleshooting instead. The user cannot fix code inside packages they don't own.

**How to tell:** check the top frames of the stack trace. If the faulting method is in a `UiPath.*` or third-party namespace, it's a package issue. If it's in the user's workflow (activity DisplayName, workflow filename, or user-authored C# code), it belongs here.

## Investigation Sources

### Local Workflow Execution (Studio / Robot)

The user ran the workflow locally. Troubleshooting data comes from:
- **Execution logs** in `%localappdata%\UiPath\logs\` (Windows) — list files in this directory and select the appropriate log based on date
- **Source code** — the project directory containing `.xaml`, `.cs`, or `project.json` files

Ask the user for the project location.

### Orchestrator Job Execution

The workflow ran as an Orchestrator job. Troubleshooting data comes from:
- **Job traces** via `uip or` CLI commands
- **Job error details** (OutputArguments, Info field)
- **Source code** — if available, provides the full picture

## Common Exception Types

| Exception | Description |
|-----------|-------------|
| `System.NullReferenceException` | Code attempted to use an object reference that is null |
| `System.ArgumentNullException` | A method received a null argument where non-null was required |
| `Compiler error(s) encountered processing expression` / `Option Strict On disallows implicit conversions` (design-time) | Studio Error List error on an `If` (or `Assign`) whose expression is not the required type or compares mismatched types |
| Wrong branch taken (no exception) | An `If` runs Successful but takes the wrong branch — case/whitespace/type mismatch in the Condition (silent logic fault) |
| `System.InvalidOperationException` (`The source contains no data rows`) | LINQ `.CopyToDataTable()` in an `Assign` when the query matched zero rows |
| `Cannot assign from type '<X>' to '<Y>'` (design-time) | Studio Error List validation error on an `Assign` — RHS expression type ≠ target variable type (e.g. `System.Object`→`System.String`) |
| `System.InvalidOperationException` | An operation is invalid for the object's current state (empty/unmatched LINQ sequence, missing `Nullable` value, collection modified mid-enumeration) |
| `System.ArgumentException` | A method argument is invalid for reasons other than null/range (undefined enum name, duplicate key, bad format) |
| `System.IO.DirectoryNotFoundException` | A file/directory operation targeted a path whose directory portion does not exist |
| `System.IndexOutOfRangeException` | An array or string was indexed outside its bounds |
| `System.Collections.Generic.KeyNotFoundException` | A dictionary was indexed with a key it does not contain |
| `System.ArgumentOutOfRangeException` | An argument was outside the range of valid values (`Substring`, `List<T>` index, date/time component) |
| `Expression Activity type 'VisualBasicValue`1' requires compilation` | An expression activity was not AOT-compiled and runtime JIT is disabled (modern `Windows`/`Portable` .NET projects) — caused by invalid/smart quotes, expression-language mismatch, or post-`Legacy` migration |
