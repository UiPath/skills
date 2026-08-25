# Final Resolution

Root Cause: The `Assign` **Find First Over 100** in `Main.xaml` runs the LINQ expression `numbers.First(n => n > 100)`, but no element of `numbers` (`{1, 2, 3}`) is greater than 100, so `First(predicate)` throws `System.InvalidOperationException: Sequence contains no matching element.`

Evidence:

### Orchestrator
- Process **OrderRecordLookup**, release version **10001**, folder **Shared**, job key `a1c2e3f4-1111-4abc-9def-000000000001` ended `Faulted`.
- Host **MOCK-HOST**, ErrorCode `Robot`, RuntimeType `Unattended`. Job `InputArguments = {}`.
- `EntryPointPath = Main.xaml`.

### Runtime Exceptions (Root Cause)
- `System.InvalidOperationException` — "Sequence contains no matching element.".
- Faulted activity: `Assign` **Find First Over 100** inside `Sequence "Main Sequence"` in `Main.xaml`.
- The fault is in user workflow code (the `Assign` value expression resolved by `CSharpValue.Execute` → `InArgument.TryPopulateValue` → `ActivityInstance.ResolveArguments`), not inside an activity package.

Immediate fix:

1. Replace `First(predicate)` with `FirstOrDefault(predicate)` and handle the no-match result, or guard with `If numbers.Any(n => n > 100)` before the query. `First` asserts a match exists; the data does not guarantee one.
  - Where: `Main.xaml`, `Sequence "Main Sequence"` → `Assign` **Find First Over 100**.
  - Who: RPA developer.
  - Source: `references/runtime-exceptions/playbooks/invalid-operation-exception.md` § Resolution.

Investigation summary:

| # | Hypothesis | Confidence | Status | Root Cause? |
|---|---|---|---|---|
| H1 | `Assign` **Find First Over 100** expression throws `System.InvalidOperationException` in user workflow code | High | Confirmed | Yes |
| H2 | Fault originates inside an activity package (not user code) | Low | Rejected | No — stack frames are `CSharpValue`/`ResolveArguments` over the user expression |
