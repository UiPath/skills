---
confidence: medium
---

# Expression Activity 'VisualBasicValue`1' Requires Compilation

## Context

`System.NotSupportedException`: **"Expression Activity type 'VisualBasicValue`1' requires compilation in order to run."** The same error also appears as `'CSharpValue`1'`. Thrown at robot/Orchestrator runtime when an expression activity in the workflow was **not compiled ahead-of-time (AOT)** and the project runtime has **runtime JIT compilation disabled**.

Modern projects (`targetFramework: Windows` or `Portable`, i.e. .NET 6+) disable runtime expression JIT — every expression must be compiled into the published package at build time. Only `Windows-Legacy` (.NET Framework 4.6.1) permits runtime JIT. So an expression that fails to AOT-compile loads fine but throws this error the moment the activity executes.

**Scope:** the user's own workflow expressions. The error names an expression node (`VisualBasicValue` / `CSharpValue`), not an activity-package type — it is a workflow-code issue the user can fix.

What it looks like:
- The designer shows the expression as **valid (green)**; `validate` and `build`/publish can pass.
- The job **faults at run** — on the robot or in Orchestrator — often on one specific activity.
- Error message contains `requires compilation in order to run`.

What can cause it:
1. **Invalid characters in an expression** — smart/curly quotes (`“ ” ‘ ’`, U+201C/U+201D/U+2018/U+2019) or a non-breaking space (U+00A0) instead of straight ASCII `"` `'` and a normal space. These get pasted in from Microsoft Word, Teams, Outlook, or web forums. The AOT compiler cannot parse the token, so the expression is left uncompiled. The bad character is often hidden in an **Activity DisplayName, an In/Out argument Default value, a Variable Default value, or an imported argument** — not the obvious expression.
2. **Expression-language mismatch** — a `VisualBasicValue` left in a project whose `expressionLanguage` is `CSharp` (or vice versa). `[bracket]` shorthand and non-literal attribute-form bindings deserialize as `VisualBasicValue<T>`; in a C# (non-Legacy) project, runtime JIT is off, so that stray VB expression cannot compile at runtime. Frequently from pasting activities copied out of a VB project.
3. **Windows-Legacy → Windows (.NET) migration** — Legacy allowed runtime JIT and tolerated loose syntax. After converting to modern Windows, every expression must AOT-compile; any that does not throws this at the first run.

What to look for:
- Which expression node the error names — `VisualBasicValue` vs `CSharpValue` — vs the project's `expressionLanguage`. A mismatch is sub-cause 2.
- `targetFramework` in `project.json` — `Windows`/`Portable` (JIT off) vs `Legacy` (JIT on).
- The literal expression text, checked for non-ASCII quotes/spaces — including DisplayNames and default values.

## Investigation

1. **Get the error** — for Orchestrator, read the faulted job's `Info` field (`uip or jobs get <KEY> --output json`) and error logs (`uip or jobs logs <KEY> --level Error --output json`); for local execution, list `%localappdata%\UiPath\logs\` and open today's log. Confirm the message is `Expression Activity type 'VisualBasicValue`1' requires compilation in order to run` (or `'CSharpValue`1'`).
2. **Read `project.json`** — record `expressionLanguage` (`VisualBasic` / `CSharp`) and `targetFramework` (`Windows` / `Portable` / `Legacy`). Non-Legacy means runtime JIT is disabled, which is the precondition for this error.
3. **Locate the faulting expression** — use the stack frame's expression index / faulting activity to open the workflow file and find the activity. The error itself names the language of the offending node.
4. **Inspect the expression text for invalid characters** — search the workflow for curly quotes (`“ ” ‘ ’`) and non-breaking spaces. Check the visible expression AND the hidden carriers: activity `DisplayName`, In/Out argument `Default` values, `Variable` `Default` values, and imported arguments. A single pasted `“` is enough.
5. **Check for a language mismatch** — if `expressionLanguage` is `CSharp` but the error names `VisualBasicValue` (or the XAML contains `<VisualBasicValue>` / `[bracket]` / non-literal attribute-form bindings), the expression is in the wrong language for the project.
6. **Check migration history** — if the project was recently converted from `Windows-Legacy`, suspect loose expressions that previously relied on runtime JIT.

The root cause is WHY an expression could not be AOT-compiled (invalid character, wrong-language node, or post-migration loose syntax) — not merely that compilation was required.

## Resolution

- **Invalid characters:** delete and **retype the quotes/spaces from the keyboard** (straight ASCII `"` and `'`, normal space). Fix every carrier, not just the obvious expression — also the activity `DisplayName`, argument `Default` values, and `Variable` `Default` values. Then `build` and re-run.
- **Expression-language mismatch (C# project):** replace VB expressions with C# — use `<CSharpValue>` / `<CSharpReference>` child elements, never `[bracket]` shorthand or non-literal attribute-form bindings (these deserialize as `VisualBasicValue<T>`). Keep `expressionLanguage` consistent across the project.
- **Legacy → Windows migration:** rebuild the offending expressions in the project's expression language, then `build` so they AOT-compile. Do not rely on Legacy runtime JIT; a modern project will not provide it.
- **Rebuild before deploy:** update `UiPath.System.Activities` to the latest stable version and `build`/republish so every expression is compiled into the package. A green designer is not proof — only a clean build + smoke run is.
- **Prevention:** type expressions directly in Studio rather than pasting from Word/Teams/web; after any framework migration, run a build + smoke test before publishing.
