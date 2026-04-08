# Runtime Exceptions

General .NET runtime exceptions originating from the user's own workflow code — variable handling, data processing, argument passing, and control flow logic.

## Scope Boundary

These playbooks ONLY cover exceptions where the root cause is in the user's workflow code (`.xaml` or `.cs` files they wrote). The user has access to this code and can fix it.

**If the stack trace shows the exception originates inside an activity package** (e.g., `UiPath.UIAutomationNext.Activities`, `UiPath.Core.Activities`, or any third-party package namespace), this is NOT a runtime exception issue — route to the relevant activity package diagnostics instead. The user cannot fix code inside packages they don't own.

**How to tell:** check the top frames of the stack trace. If the faulting method is in a `UiPath.*` or third-party namespace, it's a package issue. If it's in the user's workflow (activity DisplayName, workflow filename, or user-authored C# code), it belongs here.

## Investigation Sources

### Local Workflow Execution (Studio / Robot)

The user ran the workflow locally. Diagnostic data comes from:
- **Execution logs** in `%localappdata%\UiPath\logs\` (Windows) — list files in this directory and select the appropriate log based on date
- **Source code** — the project directory containing `.xaml`, `.cs`, or `project.json` files

Ask the user for the project location.

### Orchestrator Job Execution

The workflow ran as an Orchestrator job. Diagnostic data comes from:
- **Job traces** via `uip or` CLI commands
- **Job error details** (OutputArguments, Info field)
- **Source code** — if available, provides the full picture

## Common Exception Types

| Exception | Description |
|-----------|-------------|
| `System.NullReferenceException` | Code attempted to use an object reference that is null |
| `System.ArgumentNullException` | A method received a null argument where non-null was required |
