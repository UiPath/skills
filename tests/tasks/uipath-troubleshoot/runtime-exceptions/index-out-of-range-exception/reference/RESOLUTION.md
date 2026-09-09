# Final Resolution

Root Cause: The `Assign` **Extract Region Segment** in `Main.xaml` reads `parts[3]`, but `parts` came from `"INV-2026".Split('-')` which yields only 2 elements (indexes 0 and 1). Index 3 is past the end, so the array access throws `System.IndexOutOfRangeException: Index was outside the bounds of the array.`

Evidence:

### Orchestrator
- Process **InvoiceCodeParser**, release version **10004**, folder **Shared**, job key `d4f5b6c7-4444-4abc-9def-000000000004` ended `Faulted`.
- Host **MOCK-HOST**, ErrorCode `Robot`, RuntimeType `Unattended`. Job `InputArguments = {}`.
- `EntryPointPath = Main.xaml`.

### Runtime Exceptions (Root Cause)
- `System.IndexOutOfRangeException` — "Index was outside the bounds of the array.".
- Faulted activity: `Assign` **Extract Region Segment** inside `Sequence "Main Sequence"` in `Main.xaml`.
- The fault is in user workflow code (the `Assign` value expression resolved by `CSharpValue.Execute` → `InArgument.TryPopulateValue` → `ActivityInstance.ResolveArguments`), not inside an activity package.

Immediate fix:

1. The code assumes the invoice code splits into at least 4 segments; this input splits into 2. Validate `parts.Length` before indexing (`If parts.Length > 3`), handle short inputs explicitly, and fix the off-by-one / wrong-index assumption. Prefer named parsing (regex) over fixed positional indexes on variable data.
  - Where: `Main.xaml`, `Sequence "Main Sequence"` → `Assign` **Extract Region Segment**.
  - Who: RPA developer.
  - Source: `references/runtime-exceptions/playbooks/index-out-of-range-exception.md` § Resolution.

Investigation summary:

| # | Hypothesis | Confidence | Status | Root Cause? |
|---|---|---|---|---|
| H1 | `Assign` **Extract Region Segment** expression throws `System.IndexOutOfRangeException` in user workflow code | High | Confirmed | Yes |
| H2 | Fault originates inside an activity package (not user code) | Low | Rejected | No — stack frames are `CSharpValue`/`ResolveArguments` over the user expression |
