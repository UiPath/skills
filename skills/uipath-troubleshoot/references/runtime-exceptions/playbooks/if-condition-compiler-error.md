---
confidence: high
---

# If — Condition Compiler / Expression Error (Design-Time / Studio Validation)

## Context

An `If` activity (`System.Activities.Statements.If`) fails Studio validation because the **Condition
expression does not compile to a `Boolean`**. This is a design-time / Studio Error List validation
error, NOT a faulted robot job — there is no Orchestrator job, log, or trace. The error surfaces in
Studio's **Error List** panel (and as a red icon on the `If`) when the file is opened, validated, or
built.

What this looks like (quote verbatim — routing greps for these):
- `Compiler error(s) encountered processing expression "<expr>"` — the Condition expression is
  malformed or does not evaluate to `Boolean` (e.g. an isolated string/object, an assignment, or a
  method call that returns non-`Boolean`).
- `Option Strict On disallows implicit conversions from '<X>' to '<Y>'` — the Condition compares two
  mismatched types (e.g. an `Integer` variable to a `String` literal, a `String` to a `DateTime`).
- Both messages frequently appear together: Studio wraps the inner `Option Strict` / type error inside
  the outer `Compiler error(s) encountered processing expression` line for the `If.Condition`.

What can cause it:
- **Condition is not a Boolean.** The field holds a bare variable/literal/object (`myVariable`,
  `"Success"`, `row("Col")`) instead of a comparison — an `If` needs an expression that returns
  `True`/`False`.
- **Mismatched-type comparison (Option Strict On).** Comparing different types with `=` / `>` / `<` —
  `Integer` vs `String` literal (`responseCode = "200"`), `String` vs number, `String` vs `DateTime` —
  which VB (Option Strict On, the Studio default) refuses to convert implicitly.
- **Wrong operator.** Using `=` intending assignment, or `.Equals` on a null target, or a C#-vs-VB
  operator mismatch for the project's `expressionLanguage`.

What to look for:
- The error occurs on **open/validate/build in Studio**, not during a run — confirm there is no
  faulted job.
- The offending expression is echoed inside the message (`processing expression "<expr>"`) and, for
  type errors, `'<X>'` / `'<Y>'` name the two incompatible types.
- In the `.xaml`, the `If` has a `Condition="[<expr>]"` (or `<If.Condition>` element) that is not a
  clean `Boolean` comparison; check the declared types of the variables it references.

## Investigation

1. Confirm this is design-time: there is no Orchestrator job / robot log / trace — the error is in
   Studio's **Error List** at open/validate/build time. (A user pasting the message as a symptom is
   fine; verify no job exists before treating it as a runtime fault.)
2. Read the echoed expression and, for `Option Strict` errors, the `'<X>'` → `'<Y>'` type pair — they
   identify the fault without guessing.
3. Locate the `If` in source (ask for the project directory if not provided). Read its `Condition` and
   the declared types of every variable/argument the Condition references (Variables / Arguments
   panel).
4. Classify:
   - Condition is a bare value/object, not a comparison → **not Boolean**.
   - Condition compares two different declared types → **type mismatch (Option Strict)**.
   - Condition uses an operator that doesn't fit the operands or the `expressionLanguage` → **operator
     error**.

The root cause is WHY the Condition does not yield a `Boolean` (missing comparison vs incompatible
types) — not merely "the If is red." A confirmed finding names the expression and the specific defect.

## Resolution

- **Condition is not a Boolean:** make it a real comparison that returns `True`/`False` — use
  `=`, `<>`, `>`, `<`, `>=`, `<=`, `And`, `Or`, `.Equals(...)`, `.Contains(...)`,
  `String.IsNullOrEmpty(...)`, etc. Example: replace `myVariable` with `myVariable = "Success"`, or
  `myNumber` with `myNumber > 10`.
- **Type-mismatch comparison (Option Strict On):** compare like types — convert one side explicitly.
  Compare numbers as numbers (`responseCode = 200`), or convert: `CInt(stringVar) = intVar` /
  `Convert.ToInt32(stringVar) = intVar`, or `intVar.ToString() = stringVar`. For dates, parse the
  string (`DateTime.Parse(s) > cutoff`) rather than string-comparing.
- **Wrong operator / language:** use the comparison operator for the project's `expressionLanguage`
  (VB `=` / `<>` / `AndAlso`; C# `==` / `!=` / `&&`) and ensure it is a comparison, not an assignment.
- **Null-safety in the fix:** if a side can be null, guard before dereferencing — VB
  `myVariable IsNot Nothing AndAlso myVariable = "Target"` (`AndAlso` short-circuits). A raw
  `myVariable = "Target"` that later throws at runtime is a different failure — see
  [null-reference-exception.md](./null-reference-exception.md).
- **`If` activity missing / not found in the Activities panel, or "Missing or Invalid Activities" on
  open:** this is a package/restore problem, not a Condition error. In **Manage Packages** ensure
  `UiPath.System.Activities` is installed/updated and restored; use the Activities-panel filter
  (**Show Classic** / **Group by Packages**) to locate the classic `If` (newer Studio groups it under
  Workflow → Control Flow). If dependencies are broken, restore them and reopen the project.
