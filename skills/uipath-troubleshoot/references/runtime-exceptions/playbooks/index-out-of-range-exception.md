---
confidence: medium
---

# Index Out Of Range Exception

## Context

`System.IndexOutOfRangeException` in the user's workflow code. Code indexed an **array** or **string** with a position outside its bounds. In `Assign` activities this comes from expressions like `arr(n)`, `str(n)`, or `Split(...)(n)` where `n` is greater than or equal to the length.

> Arrays and strings throw `IndexOutOfRangeException`. `List<T>` and `Substring` throw `ArgumentOutOfRangeException` instead — see that playbook if the type is a `List` or the call is `Substring`.

**Scope:** only applies when the exception originates from the user's workflow logic (an `Assign`/expression or user-authored C# code). If the stack trace shows the fault inside an activity package namespace, redirect to that package's troubleshooting.

What this looks like:
- Workflow faults with `System.IndexOutOfRangeException`
- Error message: "Index was outside the bounds of the array."
- Often intermittent — fires only when the input data is shorter than the code assumes

What can cause it:
- A `Split` result accessed at a fixed index when the delimiter produced fewer parts (e.g., `parts(3)` when `"A-B".Split("-"c)` returned 2 items)
- An array accessed at a hardcoded index without checking `.Length`
- Off-by-one: using `.Length`/`.Count` as an index instead of `.Length - 1`
- A loop index that runs past the array bound
- A `DataRow` accessed by a column **index** that doesn't exist

What to look for:
- The index expression and the index value used
- The array/string and its actual length at fault time
- The source of a short input (delimiter mismatch, truncated data, unexpected format)

## Investigation

1. **Get the stack trace** — for local execution, list `%localappdata%\UiPath\logs\` and open the log for today's date (if not found, ask for the error date); for Orchestrator, get job traces. Confirm the top stack frames are in the user's workflow, not a package namespace
2. Locate the faulted activity in source code (typically an `Assign`) and read the indexing expression
3. Determine the actual length of the array/string versus the index used. If it is a `Split`, check the delimiter against the real input
4. Trace where the data came from and why it was shorter than expected (input format change, empty field, different delimiter)
5. If intermittent: compare the input value between successful and failed executions

The root cause is WHY the index exceeded the bounds (short Split result, off-by-one, unexpected input length), not merely which expression threw.

## Resolution

- **If indexing a `Split` result:** validate the expected part count (`If parts.Length > n`) before accessing; handle short inputs explicitly
- **If fixed array index:** check `arr.Length` before indexing, or use `ElementAtOrDefault(n)` for a bounds-safe read
- **If off-by-one:** the last valid index is `.Length - 1`
- **If looping:** bound the loop by `.Length - 1` (or use `For Each`)
- **If `DataRow` by index:** access by column name instead of position, which is stable against schema changes
