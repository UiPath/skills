---
confidence: medium
---

# Argument Null Exception

## Context

`System.ArgumentNullException` ("Value cannot be null") in the user's workflow code. A null value was passed to a method or activity that requires a non-null argument. Unlike `NullReferenceException` (which occurs when you USE a null value), this occurs when you PASS a null value to something that rejects it.

**Scope:** only applies when the exception originates from the user's workflow logic — a null argument passed by the user's code to a method or activity. If the stack trace shows the fault deep inside an activity package namespace with no user code in the call chain, redirect to that package's diagnostics.

What this looks like:
- Workflow faults with `System.ArgumentNullException`
- Error message: "Value cannot be null" typically followed by `(Parameter 'paramName')`
- May occur intermittently when the null argument depends on input data or configuration

What can cause it:
- Invoke Workflow File doesn't supply a required In argument (or the mapped variable is null)
- Config dictionary lookup returns null (key doesn't exist or value is empty)
- File/folder path variable is null when passed to I/O activities (Read Range, Move File, Path Exists)
- Activity receives null for a required input property (Type Into with null text, Add Data Row with null array)
- Collection variable is null when passed to a method expecting non-null (String.Join, LINQ query)

What to look for:
- The parameter name in the exception message — directly identifies which argument was null
- The faulted activity or method in the stack trace
- The source of the null value (variable, config, argument binding)

## Investigation

1. **Get the stack trace** — for local execution, list `%localappdata%\UiPath\logs\` and open the log for today's date (if not found, ask for the error date); for Orchestrator, get job traces. Confirm the fault originates from the user's workflow code
2. Extract the parameter name from the error message (`Parameter 'paramName'`) — this is the key diagnostic signal
3. Locate the faulted activity in source code and match the parameter name to the activity's input properties or the method being called
4. Trace the argument source: find where the null value originates (variable assignment, activity output, config lookup, argument binding). Check if the assignment is conditional or depends on external data
5. Check for missing defaults — does the variable have a default value? Is there a fallback for null?
6. If intermittent: compare input data between successful and failed executions

The root cause is WHY the argument was null, not which parameter rejected it. A confirmed finding must trace back to the missing assignment, empty config key, or unset argument.

## Resolution

- **If missing Invoke Workflow argument:** map the required In argument in the caller; verify the source variable has a value at invocation time
- **If null config or asset value:** verify the config key exists and has a non-empty value in the current environment; add a fallback or default
- **If null file path:** verify the path source (config, asset, environment variable) has a value; add validation before the file operation
- **If null activity input:** add a null check before the activity; handle the upstream source that produced null
- **If null collection:** initialize the collection before passing it (New List, New Dictionary, empty array)
