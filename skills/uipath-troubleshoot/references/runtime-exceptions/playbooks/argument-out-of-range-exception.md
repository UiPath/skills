---
confidence: medium
---

# Argument Out Of Range Exception

## Context

`System.ArgumentOutOfRangeException` in the user's workflow code. An argument was outside the range of valid values for the method. In `Assign` activities this most often comes from `String.Substring` with a start or length past the end of the string, a `List<T>` indexer beyond `Count`, or a `DateTime`/`TimeSpan` constructed with an out-of-range component.

> `List<T>` and `Substring` raise this; raw **arrays** and **strings indexed by position** raise `IndexOutOfRangeException` instead — see that playbook if the type is an array or the access is `arr(n)`/`str(n)`.

**Scope:** only applies when the exception originates from the user's workflow logic — an argument the user's expression passed to a method. If the stack trace shows the fault deep inside an activity package namespace with no user code in the call chain, redirect to that package's troubleshooting.

What this looks like:
- Workflow faults with `System.ArgumentOutOfRangeException`
- Error message names the parameter and the range, e.g.:
  - "Index and length must refer to a location within the string. (Parameter 'length')"
  - "startIndex cannot be larger than length of string. (Parameter 'startIndex')"
  - "Index was out of range. Must be non-negative and less than the size of the collection. (Parameter 'index')"
- Often intermittent — fires when the data is shorter than the code assumes

What can cause it:
- `Assign` expression `text.Substring(start, length)` where `start + length` exceeds the string length (data shorter than expected)
- `Substring(start)` where `start` is past the end
- A `List<T>` accessed at an index `>= Count`
- A negative or too-large argument to a range-checked method
- A `DateTime`/`TimeSpan` built with an invalid component (month 13, etc.)

What to look for:
- The parameter name and range in the message
- The index/length value used versus the actual length/count at fault time
- The data source and why it was shorter than expected (fixed-width parse on variable data, truncated input)

## Investigation

1. **Get the stack trace** — for local execution, list `%localappdata%\UiPath\logs\` and open the log for today's date (if not found, ask for the error date); for Orchestrator, get job traces. Confirm the top stack frames are in the user's workflow, not a package namespace
2. Locate the faulted activity in source code (typically an `Assign`) and read the expression
3. Extract the parameter name and the offending value from the message; compare it to the actual length/count of the target
4. Trace where the data came from and why it was shorter than the code assumed (variable-width input parsed as fixed-width, empty/short field, off-by-one)
5. If intermittent: compare the input value between successful and failed executions

The root cause is WHY the argument fell outside the valid range (short string for a fixed `Substring`, list index past `Count`, invalid date component), not merely which method threw.

## Resolution

- **If `Substring` past the end:** check the length first (`If text.Length >= start + length`), or clamp with `Math.Min`; for variable data prefer `Split`/regex over fixed offsets
- **If `List<T>` index past `Count`:** bounds-check before indexing or use `ElementAtOrDefault(n)`
- **If fixed-width parsing:** validate the input length before slicing; handle short rows explicitly
- **If invalid date/time component:** validate the components before constructing the value
