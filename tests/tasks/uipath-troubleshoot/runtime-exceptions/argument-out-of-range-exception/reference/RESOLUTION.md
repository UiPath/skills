# Final Resolution

Root Cause: The `Assign` **Slice Year From Invoice Id** in `Main.xaml` runs `invoiceId.Substring(10)`, but `invoiceId` is `"INV-7"` (length 5). A start index of 10 is past the end of the string, so `String.Substring` throws `System.ArgumentOutOfRangeException: startIndex cannot be larger than length of string. (Parameter 'startIndex')`.

Evidence:

### Orchestrator
- Process **InvoiceIdSlicer**, release version **10006**, folder **Shared**, job key `f6b7d8e9-6666-4abc-9def-000000000006` ended `Faulted`.
- Host **MOCK-HOST**, ErrorCode `Robot`, RuntimeType `Unattended`. Job `InputArguments = {}`.
- `EntryPointPath = Main.xaml`.

### Runtime Exceptions (Root Cause)
- `System.ArgumentOutOfRangeException` — "startIndex cannot be larger than length of string. (Parameter 'startIndex')".
- Faulted activity: `Assign` **Slice Year From Invoice Id** inside `Sequence "Main Sequence"` in `Main.xaml`.
- The fault is in user workflow code (the `Assign` value expression resolved by `CSharpValue.Execute` → `InArgument.TryPopulateValue` → `ActivityInstance.ResolveArguments`), not inside an activity package.

Immediate fix:

1. The code assumes a fixed invoice-id layout longer than the actual data. Check `invoiceId.Length` before slicing (or clamp with `Math.Min`), and for variable-width data prefer `Split`/regex over fixed offsets. Validate input length before fixed-position parsing.
  - Where: `Main.xaml`, `Sequence "Main Sequence"` → `Assign` **Slice Year From Invoice Id**.
  - Who: RPA developer.
  - Source: `references/runtime-exceptions/playbooks/argument-out-of-range-exception.md` § Resolution.

Investigation summary:

| # | Hypothesis | Confidence | Status | Root Cause? |
|---|---|---|---|---|
| H1 | `Assign` **Slice Year From Invoice Id** expression throws `System.ArgumentOutOfRangeException` in user workflow code | High | Confirmed | Yes |
| H2 | Fault originates inside an activity package (not user code) | Low | Rejected | No — stack frames are `CSharpValue`/`ResolveArguments` over the user expression |
