# Final Resolution

Root Cause: The `Assign` **Parse Day Of Week** in `Main.xaml` runs `Enum.Parse(typeof(DayOfWeek), inputDay)` where `inputDay` is `"Funday"`. `"Funday"` is not a defined `DayOfWeek` name, so `Enum.Parse` throws `System.ArgumentException: Requested value 'Funday' was not found.`

Evidence:

### Orchestrator
- Process **ScheduleParser**, release version **10002**, folder **Shared**, job key `b2d3f4a5-2222-4abc-9def-000000000002` ended `Faulted`.
- Host **MOCK-HOST**, ErrorCode `Robot`, RuntimeType `Unattended`. Job `InputArguments = {}`.
- `EntryPointPath = Main.xaml`.

### Runtime Exceptions (Root Cause)
- `System.ArgumentException` — "Requested value 'Funday' was not found.".
- Faulted activity: `Assign` **Parse Day Of Week** inside `Sequence "Main Sequence"` in `Main.xaml`.
- The fault is in user workflow code (the `Assign` value expression resolved by `CSharpValue.Execute` → `InArgument.TryPopulateValue` → `ActivityInstance.ResolveArguments`), not inside an activity package.

Immediate fix:

1. Validate the input before parsing: use `Enum.TryParse(inputDay, out DayOfWeek d)` (or `Enum.IsDefined`) and handle the invalid case, instead of `Enum.Parse` which throws on any name the enum does not define. Fix the upstream source that produced `"Funday"`.
  - Where: `Main.xaml`, `Sequence "Main Sequence"` → `Assign` **Parse Day Of Week**.
  - Who: RPA developer.
  - Source: `references/runtime-exceptions/playbooks/argument-exception.md` § Resolution.

Investigation summary:

| # | Hypothesis | Confidence | Status | Root Cause? |
|---|---|---|---|---|
| H1 | `Assign` **Parse Day Of Week** expression throws `System.ArgumentException` in user workflow code | High | Confirmed | Yes |
| H2 | Fault originates inside an activity package (not user code) | Low | Rejected | No — stack frames are `CSharpValue`/`ResolveArguments` over the user expression |
