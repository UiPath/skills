# Runtime Exceptions Investigation Guide

## Scope Check — First Step

Before investigating, verify the exception originates from the user's workflow code, not from an activity package:

1. Read the full stack trace from logs or job traces
2. Check the top frames — if the faulting method is in a package namespace (`UiPath.UIAutomationNext.*`, `UiPath.Core.Activities.*`, or any third-party assembly), **stop and redirect** to the relevant package's diagnostics
3. Only proceed if the exception is in the user's workflow logic: activity DisplayName, workflow `.xaml` file, or user-authored `.cs` code

## Data Correlation

Before using any fetched data, verify it matches the user's reported problem:

- **Exception type** — the exception in the data is the exact type the user reported (e.g., `NullReferenceException` not `ArgumentNullException`)
- **Stack trace location** — the faulted activity or line in the stack trace matches the workflow the user is asking about
- **Workflow file** — if multiple workflows exist in the project, the error originates from the correct one
- **Timestamp** — log entries or job traces fall within the time window the user described
- **Input data** — if the error is data-dependent, confirm you're looking at the same transaction/queue item/input that caused the failure

If the data doesn't match: **discard it**. Do NOT use unrelated data as a proxy. Report the mismatch and ask for clarification.

## Local Log Directory

On Windows, UiPath Robot execution logs are in:

```
%localappdata%\UiPath\logs\
```

**Reading local logs:**
1. Resolve `%localappdata%` to the actual path (typically `C:\Users\{username}\AppData\Local`)
2. List the files in the logs directory to identify available log files
3. Select the most recent log file relevant to the reported error — start with today's date. If no log for today exists, ask the user what date the error occurred
4. Search the selected log file for the exception type (e.g., `NullReferenceException`)
5. Extract the full stack trace — it spans multiple lines after the exception message
6. Identify the faulted activity name, workflow file, and source line from the stack trace

## Source Code Analysis

Two source formats exist:

### XAML Workflows (RPA)
- Activities are XML elements with `DisplayName` attributes
- Variables are declared in `<Variable>` sections within scope containers
- Arguments are in `.xaml` file headers or `project.json`
- Trace the data flow: where does the null variable get assigned? What upstream activity produces it?

### Coded Workflows (C#)
- Standard C# files in the project directory
- Stack trace line numbers map directly to source lines
- Check null-coalescing patterns, nullable types, and guard clauses

## Testing Prerequisites

1. **Full stack trace** — extract from local logs or Orchestrator job traces
2. **Source code path** — the project directory; required to trace variable assignments and data flow
3. **Faulted activity/line** — identify the specific activity (XAML) or line (C#) from the stack trace
4. **Variable origin** — trace backward from the null variable to find where it was supposed to be assigned
5. **Input data** — check what data the workflow received (arguments, queue item, asset values) for the failing execution
6. **Conditional paths** — check if the null value comes from a branch that doesn't assign the variable
