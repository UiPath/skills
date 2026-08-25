---
confidence: medium
---

# Argument Exception

## Context

`System.ArgumentException` in the user's workflow code. A method received an argument that is invalid for reasons other than being null (that is `ArgumentNullException`) or out of range (that is `ArgumentOutOfRangeException`). In `Assign` activities this commonly comes from `Enum.Parse` with a name the enum doesn't define, adding a duplicate key to a `Dictionary`, a duplicate `DataColumn` name, or an invalid format/culture string.

**Scope:** only applies when the exception originates from the user's workflow logic — an argument the user's expression passed to a method or activity. If the stack trace shows the fault deep inside an activity package namespace with no user code in the call chain, redirect to that package's troubleshooting.

What this looks like:
- Workflow faults with `System.ArgumentException`
- The message names the specific problem, often with `(Parameter 'paramName')`:
  - "Requested value 'X' was not found." — `Enum.Parse` with an undefined name
  - "An item with the same key has already been added. Key: X" — `Dictionary.Add` of an existing key
  - "A column named 'X' already belongs to this DataTable." — duplicate `DataColumn`
  - format/culture errors from parse/format methods
- May occur intermittently when the invalid value depends on input data

What can cause it:
- `Assign` expression `Enum.Parse(typeof(SomeEnum), inputText)` where `inputText` isn't a defined name (typo, unexpected value, case mismatch)
- `dict.Add(key, value)` when `key` already exists (duplicate insertion instead of upsert)
- `dt.Columns.Add("Name")` for a column that already exists
- Invalid format string or culture name passed to `ToString`/`Parse`/`Convert`

What to look for:
- The parameter name in the message — identifies which argument was rejected
- The invalid value and its source (input data, config, prior activity output)
- The method or activity that rejected it

## Investigation

1. **Get the stack trace** — for local execution, list `%localappdata%\UiPath\logs\` and open the log for today's date (if not found, ask for the error date); for Orchestrator, get job traces. Confirm the fault originates from the user's workflow code
2. Locate the faulted activity in source code (typically an `Assign`) and read the expression
3. Extract the parameter name and the invalid value from the message; match them to the method being called
4. Trace where the invalid value came from (variable, activity output, config lookup, argument binding). Check whether it depends on external data
5. If intermittent: compare the input data between successful and failed executions to find the value that triggered it

The root cause is WHY the argument was invalid (undefined enum name, duplicate key, malformed format), not merely which method rejected it. A confirmed finding must trace back to the value's origin.

## Resolution

- **If `Enum.Parse` of an undefined name:** validate with `Enum.IsDefined` or use `Enum.TryParse` and handle the false case; normalize case before parsing
- **If duplicate dictionary key:** use the indexer `dict[key] = value` for upsert semantics, or guard with `If Not dict.ContainsKey(key)` before `Add`
- **If duplicate column:** check `dt.Columns.Contains("Name")` before `Add`, or build the schema once
- **If bad format/culture:** validate the format/culture string; use an explicit `CultureInfo` (e.g., `CultureInfo.InvariantCulture`)
