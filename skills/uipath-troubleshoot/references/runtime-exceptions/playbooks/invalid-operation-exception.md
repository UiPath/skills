---
confidence: medium
---

# Invalid Operation Exception

## Context

`System.InvalidOperationException` in the user's workflow code. The operation is not valid for the object's current state. In `Assign` activities this most often comes from a LINQ query expression (`First`/`Single`/`Last` over a sequence with no — or too many — matching elements), a `Nullable<T>.Value` read when the value is absent, or a collection mutated while it is being enumerated.

**Scope:** only applies when the exception originates from the user's workflow logic (an `Assign`/expression or user-authored C# code). If the stack trace shows the fault inside an activity package namespace (e.g., `UiPath.*` or a third-party package), redirect to that package's troubleshooting — the user cannot fix package internals.

What this looks like:
- Workflow faults with `System.InvalidOperationException`
- The message names the specific invalid state:
  - "Sequence contains no matching element" — `First(predicate)`/`Single(predicate)` matched nothing
  - "Sequence contains no elements" — `First()`/`Single()`/`Last()` on an empty collection
  - "Sequence contains more than one matching element" — `Single(predicate)` matched several
  - "Nullable object must have a value" — `.Value` on a `Nullable<T>` whose `HasValue` is false
  - "Collection was modified; enumeration operation may not execute" — a collection was changed inside a loop over itself
- May occur intermittently when the data that drives the match varies

What can cause it:
- `Assign` LINQ expression `dt.AsEnumerable().First(r => …)` when no row matches the predicate
- `First()`/`Single()` on a query/collection that returned empty (filter excluded everything, upstream query found nothing)
- `Single(...)` where the data contains duplicates
- Reading `nullableVar.Value` without checking `HasValue`
- Adding to / removing from a `List`/`Dictionary` inside a `For Each` over that same collection

What to look for:
- The exact message — it disambiguates which of the causes above applies
- The LINQ operator or operation in the `Assign` expression
- The source collection and *why* it is empty, unmatched, or has duplicates

## Investigation

1. **Get the stack trace** — for local execution, list `%localappdata%\UiPath\logs\` and open the log for today's date (if not found, ask for the error date); for Orchestrator, get job traces. Confirm the top stack frames are in the user's workflow, not a package namespace
2. Locate the faulted activity in source code by `DisplayName` (XAML) or line number (C#) — typically an `Assign`
3. Read the expression and match the exception message to the operation (e.g., "no matching element" → a `First(predicate)`/`Single(predicate)`)
4. Determine why the sequence is empty, unmatched, or duplicated: trace the source collection back to its query/filter/activity output. Check whether the populating step is conditional or data-dependent
5. If data-dependent: for Orchestrator jobs, compare the input/queue data between successful and failed runs; for local execution, check the arguments or config that drove the query

The root cause is WHY the operation was invalid for the object's state (empty sequence, no match, missing value, concurrent modification), not merely which operator threw. A confirmed finding must trace back to the data or control-flow that produced that state.

## Resolution

- **If `First`/`Single` found no match:** use `FirstOrDefault`/`SingleOrDefault` and null-check the result, or guard with `If collection.Any(predicate)` before the query
- **If the collection was empty:** handle the no-data case explicitly before the query (the upstream filter/query produced nothing)
- **If `Single` hit duplicates:** switch to `Where(...).First()` or dedupe upstream; `Single` asserts exactly one
- **If `Nullable.Value` on no value:** check `.HasValue` first, or use `.GetValueOrDefault()`
- **If collection modified during enumeration:** iterate a snapshot (`.ToList()`), or collect changes and apply them after the loop
