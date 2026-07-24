# Final Resolution

---

**Root Cause:** The `Assign 'Build Route Key'` value in `Main.xaml` is a
`VisualBasicValue` node (`"ORDER:" & orderId`, using the VB `&` concatenation
operator), but the project is `expressionLanguage: CSharp` with
`targetFramework: Windows` (.NET 6+). Modern .NET projects disable runtime
expression JIT, so the stray VB expression has no compiled delegate at run and
throws `Expression Activity type 'VisualBasicValue`1' requires compilation in
order to run`.

**What went wrong:** The activity was pasted in from a VisualBasic project, so its
value expression deserialized as a `Microsoft.VisualBasic.Activities.VisualBasicValue`
node rather than a `CSharpValue`. The project's other expressions (the `Assign.To`
and the `Log Message`) are correctly `CSharpReference` / `CSharpValue`, which is
why only `Assign 'Build Route Key'` faults.

**Why:** A C# (non-Legacy) project AOT-compiles its C# expressions at build time
and disables runtime JIT. The lone VB expression is not part of the C# compiled
set, so at run there is no compiled delegate for it and JIT is off — the runtime
raises `System.NotSupportedException`. The Studio designer validates the workflow
as green, so this is not caught before publish.

---

**Evidence:**

### Orchestrator (Root cause)
- Faulted job `bb22cc33-dd44-ee55-ff66-778899001122`, process `OrderRouter`, folder `Shared`, host `MOCK-HOST`, `ErrorCode: Robot`.
- Error (verbatim): `Expression Activity type 'VisualBasicValue`1' requires compilation in order to run.`
- Stack: `Microsoft.VisualBasic.Activities.VisualBasicValue`1.Execute` -> `InArgument`1.TryPopulateValue` -> `ActivityInstance.ResolveArguments`.
- Faulting activity: `Assign 'Build Route Key'` inside `Sequence 'Route Order'` in `Main.xaml`.

### Workflow source (decisive)
- `project.json`: `expressionLanguage: CSharp`, `targetFramework: Windows`.
- `Main.xaml`: `Assign 'Build Route Key'` value is `<mva:VisualBasicValue x:TypeArguments="x:String">"ORDER:" & orderId</mva:VisualBasicValue>` — a VB expression (note the `&` concatenation) in a C# project.
- The sibling expressions (`Assign.To` = `CSharpReference`, `Log Message.Message` = `CSharpValue`) are correctly C#, confirming the mismatch is isolated to this one node.

### Cross-check — what this is NOT
- Not invalid/smart quotes — the string delimiters are straight ASCII; the offending element is the expression-node language, not a bad character.
- Not a `NullReferenceException` — `orderId` has a Default (`ORD-4471`); the fault is expression compilation, not a null deref.
- Not a missing dependency — `UiPath.System.Activities` is present; the error is a compilation fault, not type resolution.

---

**Recommended Fix (Resolution):**

### Primary fix
1. In `Main.xaml`, replace the `Assign 'Build Route Key'` value's `VisualBasicValue`
   node with a C# expression using `<CSharpValue>`: `"ORDER:" + orderId` (C# `+`
   concatenation), matching the project's `expressionLanguage: CSharp`.
2. Build the project (`uip rpa build`) so the expression AOT-compiles, then re-run.
   A green designer is not sufficient proof — only a clean build + run confirms it.

### Also check
- Scan the rest of the project for other pasted-from-VB nodes: any `[bracket]`
  shorthand or non-literal attribute-form binding in a C# project also deserializes
  as `VisualBasicValue` and will fault the same way. Keep `expressionLanguage`
  consistent across every expression.

### Prevention
- Do not paste activities from a VB project into a C# project (or vice versa); the
  expression nodes carry their source language.
- Run a build + smoke run before publishing; do not rely on the designer's
  green-validation state.

Source: `references/runtime-exceptions/playbooks/visualbasicvalue-requires-compilation.md` § Resolution — expression-language mismatch.
