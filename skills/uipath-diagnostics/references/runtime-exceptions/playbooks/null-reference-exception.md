---
confidence: medium
---

# Null Reference Exception

## Context

`System.NullReferenceException` ("Object reference not set to an instance of an object") in the user's workflow code. The workflow attempted to access a member on a variable or expression that is `null`.

**Scope:** only applies when the exception originates from the user's workflow logic (activity, variable expression, or user-authored C# code). If the stack trace shows the fault inside an activity package namespace (e.g., `UiPath.UIAutomationNext.*`), redirect to that package's diagnostics — the user cannot fix package internals.

What this looks like:
- Workflow faults with `System.NullReferenceException`
- Error message: "Object reference not set to an instance of an object"
- May occur intermittently when the null value depends on input data

What can cause it:
- Variable declared but never assigned (or assigned only in a conditional branch that wasn't taken)
- Activity output was null and used directly without a null check (e.g., data table lookup with no match, JSON path that doesn't exist, regex with no match)
- Queue item field missing or null (`TransactionItem.SpecificContent("fieldName")` with wrong field name)
- External system returned null or empty response (HTTP Request, database query, SOAP call)
- Collection used before initialization (array, List, DataTable)

What to look for:
- Full stack trace — confirms the fault is in workflow code, not a package
- The specific activity or line where the null access occurred
- The variable or expression that was null

## Investigation

1. **Get the stack trace** — for local execution, list `%localappdata%\UiPath\logs\` and open the log for today's date (if not found, ask for the error date); for Orchestrator, get job traces. Confirm the top stack frames are in the user's workflow, not a package namespace
2. Locate the faulted activity in source code by `DisplayName` (XAML) or line number (C#)
3. Identify which variable or expression was null — read the activity's input properties
4. Trace the variable backward: find every assignment (Assign activities, activity outputs, argument bindings). Check if any assignment is conditional (If/Else, Switch, Flowchart branch) or inside a Try/Catch that swallows errors
5. If data-dependent: for Orchestrator jobs, compare TransactionItem/SpecificContent between successful and failed runs; for local execution, check what arguments or config values were passed
6. Verify variable scope — a variable declared in an inner scope is null if accessed from an outer scope (XAML)

The root cause is WHY the variable was null, not which variable was null. A confirmed finding must trace back to the origin of the null value (missing assignment, conditional gap, missing input data, failed upstream activity).

## Resolution

- **If uninitialized variable:** add a default value or ensure all conditional branches assign the variable before it's used
- **If activity returned null:** add a null check (If/Then) after the activity before using the output; handle the "no data" case explicitly
- **If queue item field missing:** verify field names match exactly (case-sensitive) between Add Queue Item and Get Transaction Item; add null check before accessing SpecificContent
- **If external system returned null:** add response validation; handle empty/null responses as an expected case
- **If collection not initialized:** initialize the collection (New List, Build Data Table) before first use
