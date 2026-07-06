# Final Resolution

Root Cause: A C# input-argument expression on the `Copy File` activity in `ERN.xaml` dereferences a variable that the workflow itself sets to `null` before the activity runs.

What went wrong: `Copy File`'s `Path` argument evaluates `myVar.ToString()`, but `myVar` is `null` at that moment, so argument resolution throws `System.NullReferenceException` and the job faulted.

Why: Inside `Sequence 'ERN'`, the variable `myVar` (type `Object`) is declared with no Default value. The only upstream activity is an `Assign` that unconditionally sets `myVar = null`. The next activity, `Copy File`, binds its `Path` `InArgument` to the C# expression `myVar.ToString()`. During `InArgument.TryPopulateValue` → `ActivityInstance.ResolveArguments`, the compiled user-expressions assembly (`Namespace_fmq3zcn67w.ERN_Expressions.__Expr2Get`, the second `CSharpValue` in XAML order — `Copy File.Path`) calls `.ToString()` on the null reference and throws. Job ran ~860 ms (process ERN v53410, folder Shared, host MOCK-HOST). Empty `InputArguments` are consistent but not the direct cause — `myVar` is a Sequence Variable, not an in-argument, so the workflow itself produces the null.

Evidence:

### Orchestrator
- Process **ERN**, release version **53410**, folder **Shared**, job key `77dc53dd-5c45-4a77-b39f-a52e9e7ef163` ended `Faulted`.
- Host **MOCK-HOST**, ErrorCode `Robot`. Start `2026-05-13T07:32:22.603Z`, end `2026-05-13T07:32:23.463Z`.
- Job `InputArguments = {}`.

### Runtime Exceptions (Root Cause)
- `System.NullReferenceException` — "Object reference not set to an instance of an object".
- Stack: `Namespace_fmq3zcn67w.ERN_Expressions.__Expr2Get` invoked by `CSharpValue.Execute` → `InArgument.TryPopulateValue` → `ActivityInstance.ResolveArguments` (fault is in argument resolution).
- Faulted activity: `Copy File` (id `CopyFile_1`) inside `Sequence 'ERN'` in `ERN.xaml`.
- `Copy File.Path` expression: `myVar.ToString()` (`CSharpValue\`1_2`).
- `myVar` declared in `Sequence 'ERN'`, type `x:Object`, no Default.
- Upstream `Assign_1` sets `myVar = null` (literal).
- `__Expr2Get` maps to the second `CSharpValue` in XAML order — `Copy File.Path`.

Immediate fix:

### Runtime Exceptions (Root Cause)
1. Stop assigning `null` to `myVar` and provide a real source-path value before `Copy File` runs.
  - Why: The upstream `Assign myVar = null` guarantees `myVar.ToString()` on `Copy File.Path` null-derefs every run.
  - Where: ``, `Sequence 'ERN'` → `Assign_1`. Replace the `null` expression with the intended source file path (literal, in-argument, or upstream activity output), or remove the Assign and give `myVar` a usable Default / upstream assignment.
  - Who: RPA developer.
  - Source: `references/runtime-exceptions/playbooks/null-reference-exception.md` § Resolution — uninitialized variable.
2. Tighten the `myVar` variable declaration: change type to `String` and provide a Default (or promote to a workflow `In` argument bound to the source path).
  - Why: Evidence shows `myVar` is `Object` with `Default = null`; a typed, defaulted variable removes argument-resolution null-refs.
  - Where: `ERN.xaml` Variables panel for `Sequence 'ERN'`.
  - Who: RPA developer.
  - Source: same playbook § Resolution.

Preventive fix:

1. Runtime Exceptions — Guard `Copy File.Path` against null.
  - Why: A future upstream null (config read, lookup) would reproduce this. Use `myVar?.ToString()` plus an `If String.IsNullOrEmpty(...) Then Throw new BusinessException("source path missing")` so the failure is an explicit business error rather than a raw NRE.
  - Where: `ERN.xaml`, `Copy File.Path` and a preceding validation `If` in `Sequence 'ERN'`.
  - Who: RPA developer.
  - Source: same playbook § Resolution — null-check after activity output.
2. Orchestrator — Pass the source path as a workflow `In` argument when starting from folder **Shared**.
  - Why: Job `InputArguments` was `{}`; promoting `myVar` to an in-argument makes the input contract explicit and fails fast at job-start.
  - Where: Studio — promote `myVar` to `In String`; Orchestrator — set `InputArguments` on the process/trigger, or read from an Orchestrator Asset in **Shared** via a preceding `Get Asset`.
  - Who: RPA developer + Orchestrator admin.
  - Source: playbook § Investigation step 5; `references/products/orchestrator/presentation.md`.

Investigation summary:

| # | Hypothesis | Confidence | Status | Root Cause? |
|---|---|---|---|---|
| H1 | `Copy File` Path expression dereferences null `myVar` | High | Confirmed | Yes |
| H2 | Chained member access on upstream null result | Medium | Not pursued | No — expression is bare `myVar.ToString()` |
| H3 | Variable scope / non-taken conditional branch | Medium | Not pursued | No — `myVar` is same-scope; no conditionals upstream |
| H4 | External input (Asset/queue/config) returned null | Medium | Not pursued | No — no external-read activity precedes `Copy File` |

Want me to clean up `.investigation/`?
