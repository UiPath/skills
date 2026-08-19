# Final Resolution

---

**Root Cause:** The `Assign 'Build Greeting'` value expression in `Main.xaml`
contains curly/smart double quotes (U+201C and U+201D) instead of straight ASCII
double quotes (U+0022), so the expression could not be compiled ahead-of-time.
The project is `expressionLanguage: VisualBasic` with `targetFramework: Windows`
(.NET 6+), which disables runtime expression JIT — so at run the uncompiled
`VisualBasicValue` throws `requires compilation in order to run`.

**What went wrong:** The greeting expression reads (smart quotes shown as [LQ]/[RQ]
for U+201C/U+201D): `[LQ]Dear [RQ] + customerName + [LQ],[RQ]`. The smart quotes
were introduced by pasting the expression from a rich-text source (Word / Teams /
web). They are not valid ASCII string delimiters for the compiler, so the
expression is left uncompiled in the published package.

**Why:** Modern UiPath projects (`Windows` / `Portable`, .NET 6+) compile every
expression into the package at build time and disable runtime JIT. An expression
that fails to AOT-compile still loads, but the moment `Assign 'Build Greeting'`
executes, the runtime has no compiled delegate and JIT is off, so it raises
`System.NotSupportedException: Expression Activity type 'VisualBasicValue`1'
requires compilation in order to run`. The Studio designer validates the workflow
as green, which is why this was not caught before publish.

---

**Evidence:**

### Orchestrator (Root cause)
- Faulted job `a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d`, process `InvoiceNotifier`, folder `Shared`, host `MOCK-HOST`, `ErrorCode: Robot`.
- Error (verbatim): `Expression Activity type 'VisualBasicValue`1' requires compilation in order to run.`
- Stack: `Microsoft.VisualBasic.Activities.VisualBasicValue`1.Execute` -> `InArgument`1.TryPopulateValue` -> `ActivityInstance.ResolveArguments` (fault during argument resolution).
- Faulting activity: `Assign 'Build Greeting'` inside `Sequence 'Notify Customer'` in `Main.xaml`.

### Workflow source (decisive)
- `Assign 'Build Greeting'` value uses smart double quotes (U+201C/U+201D) around the string literals instead of straight ASCII quotes.
- `project.json`: `expressionLanguage: VisualBasic`, `targetFramework: Windows` — modern .NET, runtime JIT disabled.

### Cross-check — what this is NOT
- Not a `NullReferenceException` — `customerName` has a Default (`Acme Corp`); the fault is expression compilation, not a null deref.
- Not an expression-language mismatch — the project IS VisualBasic and the error names `VisualBasicValue`; the problem is the invalid quote characters, not a stray-language node.
- Not a missing dependency — `UiPath.System.Activities` is present; the error is a compilation fault, not a type-resolution failure.

---

**Recommended Fix (Resolution):**

### Primary fix
1. Open `Main.xaml`, select the `Assign 'Build Greeting'` value, delete the smart
   quotes, and retype the string delimiters using the keyboard so they are
   straight ASCII quotes (U+0022): `"Dear " + customerName + ","`.
2. Build the project (`uip rpa build`) so the expression AOT-compiles, then re-run.
   A green designer is not sufficient proof — only a clean build + run confirms it.

### Also check
- Inspect the other smart-quote carriers for the same paste corruption: activity
  `DisplayName` values, In/Out argument `Default` values, and `Variable` `Default`
  values. A single hidden smart quote reproduces the fault.

### Prevention
- Type expressions directly in Studio instead of pasting from Word / Teams / web.
- Run a build + smoke run before publishing; do not rely on the designer's
  green-validation state.

Source: `references/runtime-exceptions/playbooks/visualbasicvalue-requires-compilation.md` § Resolution — invalid characters.
