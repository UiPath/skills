# Final Resolution

Root Cause: The `If` activity **Check Status Is Yes** in `Main.xaml` evaluates the condition `status.ToString() == "yes"`, but `status` is `null` — the upstream `Assign` **Set Status** sets it to `null`. Resolving the `If` condition calls `.ToString()` on the null reference, throwing `System.NullReferenceException` before either branch runs.

Evidence:

### Orchestrator
- Process **EligibilityRouter**, release version **10007**, folder **Shared**, job key `a7c8e9f0-7777-4abc-9def-000000000007` ended `Faulted`.
- Host **MOCK-HOST**, ErrorCode `Robot`, RuntimeType `Unattended`. Job `InputArguments = {}`.
- `EntryPointPath = Main.xaml`.

### Runtime Exceptions (Root Cause)
- `System.NullReferenceException` — "Object reference not set to an instance of an object.".
- Faulted activity: `If` **Check Status Is Yes** inside `Sequence "Main Sequence"` in `Main.xaml`.
- The fault is in user workflow code — the `If` **Condition** expression, resolved by `CSharpValue.Execute` → `InArgument.TryPopulateValue` → `ActivityInstance.ResolveArguments`, throws **before** either branch runs. It is not inside an activity package.

Immediate fix:

1. Stop leaving `status` null before the `If`, or make the condition null-safe: `status != null && status.ToString() == "yes"` (or `String.Equals(status?.ToString(), "yes")`). Give `status` a real value/default from its intended upstream source so the condition never dereferences null.
  - Where: `Main.xaml`, `Sequence "Main Sequence"` → `If` **Check Status Is Yes** Condition.
  - Who: RPA developer.
  - Source: `references/runtime-exceptions/playbooks/null-reference-exception.md` § Resolution.

Investigation summary:

| # | Hypothesis | Confidence | Status | Root Cause? |
|---|---|---|---|---|
| H1 | `If` **Check Status Is Yes** Condition expression throws `System.NullReferenceException` in user workflow code | High | Confirmed | Yes |
| H2 | Fault originates inside an activity package (not user code) | Low | Rejected | No — stack frames are `CSharpValue`/`ResolveArguments` over the user condition expression |
| H3 | Fault is inside a Then/Else branch activity | Low | Rejected | No — condition resolution precedes branch execution; no branch frame in the stack |
