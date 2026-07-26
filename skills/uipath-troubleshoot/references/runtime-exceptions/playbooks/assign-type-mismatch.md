---
confidence: high
---

# Assign — Type Mismatch (Design-Time / Studio Validation)

## Context

An `Assign` activity (`System.Activities.Statements.Assign`) fails Studio validation because the
**right-hand-side expression returns a type that cannot be assigned to the left-hand-side target
variable/argument**. This is a design-time / Studio Error List validation error, NOT a faulted robot
job — there is no Orchestrator job, log, or trace. The error surfaces in Studio's **Error List** panel
(and as a red icon on the Assign) when the file is opened, validated, or built.

What this looks like (quote verbatim — routing greps for these):
- `Cannot assign from type 'System.Object' to 'System.String'`
- `Cannot assign from type 'System.String' to 'System.String[]'`
- `Cannot assign from type '<SOURCE>' to '<TARGET>'` (the general form; `<SOURCE>` is the expression's
  return type, `<TARGET>` is the target variable/argument type)
- Also seen as compiler variants: VB `BC30311 Value of type '<X>' cannot be converted to '<Y>'`;
  C# `CS0266 Cannot implicitly convert type '<X>' to '<Y>'`.

What can cause it:
- **`Object`/`dynamic` RHS into a typed target.** The expression evaluates to `System.Object` —
  `Dictionary(Of String, Object)` config lookup (`config("Key")`), `DataRow` indexer
  (`row("Column")`), `JToken`/`JObject` member, or an activity output typed `Object` — assigned to a
  `String` (or other typed) variable. This is the `System.Object` → `System.String` case.
- **Scalar RHS into a collection/array target (or vice versa).** A single `String` assigned to a
  `String[]` / `List(Of String)` variable (the `System.String` → `System.String[]` case), or an array
  assigned to a scalar.
- **Wrong numeric/date type.** `Int32` into `Double`, `String` into `Int32`/`DateTime`, etc. — the RHS
  is a different, non-convertible primitive than the target.
- **Target variable declared with the wrong type** in the Variables/Arguments panel (the real intent
  was a different type).

What to look for:
- The error occurs on **open/validate/build in Studio**, not during a run — confirm there is no
  faulted job for it.
- `<SOURCE>` and `<TARGET>` in the message name the exact type collision. `<SOURCE>` = what the
  expression returns; `<TARGET>` = the declared type of the Assign's `To` variable/argument.
- In the `.xaml`, the offending `Assign` has an `<Assign.Value>` `InArgument`/`CSharpValue` whose
  expression returns `<SOURCE>` while its `x:TypeArguments` (and the `<Assign.To>` `OutArgument`) is
  `<TARGET>`.

## Investigation

1. Confirm this is design-time: there is no Orchestrator job / robot log / trace — the error is in
   Studio's **Error List** at open/validate/build time. (A user pasting the message as a symptom is
   fine; verify no job exists before treating it as a runtime fault.)
2. Read `<SOURCE>` and `<TARGET>` straight from the message — they identify the collision without
   guessing.
3. Locate the faulted `Assign` in source. Ask for the project directory if not provided (top-level
   `project.json` + the `.xaml`). In the `.xaml`, find the `Assign` whose `<Assign.Value>` expression
   returns `<SOURCE>` and whose `<Assign.To>` / `x:TypeArguments` is `<TARGET>`.
4. Classify the collision:
   - `<SOURCE>` = `System.Object` (or `dynamic`) → the RHS is an untyped lookup/output (config
     dictionary, `DataRow` column, JSON token, `Object` activity output).
   - `<SOURCE>` scalar, `<TARGET>` array/collection (or vice versa) → shape mismatch.
   - both primitives → wrong numeric/date conversion.
5. Decide whether the fix is on the RHS (convert/cast the expression) or on the target declaration
   (the variable was declared with the wrong type). Check the target variable's declared type in the
   Variables/Arguments panel to tell which.

The root cause is WHICH type the expression returns vs WHAT the target declares — not merely "there is
a mismatch." A confirmed finding names both types and the specific conversion/declaration change.

## Resolution

- **`System.Object` → `System.String` (config/DataRow/JSON/Object output):** append `.ToString()` to
  the RHS expression (e.g. `config("AccountName").ToString()`, `row("AccountName").ToString()`). For a
  non-string typed target, cast to the real type instead: `CType(config("Retries"), Int32)` /
  `Convert.ToInt32(config("Retries"))` (VB), `(int)config["Retries"]` (C#). Guard against a null
  lookup first if the value can be missing — see
  [null-reference-exception.md](./null-reference-exception.md).
- **`System.String` → `System.String[]` (scalar into array):** wrap the value in an array/collection
  initializer: `{"Your Text Value"}` for `String[]`, or `New List(Of String) From {"Your Text Value"}`
  for `List(Of String)`. To split one delimited string into many elements, use
  `yourString.Split(","c)` instead.
- **Wrong numeric/date primitive:** convert explicitly — `Int32.Parse(s)` / `Convert.ToInt32(s)`,
  `Double`, `DateTime.Parse(s, ...)`, `CDbl(i)` — matching the target type.
- **Target declared with the wrong type:** if the expression's type is actually correct, change the
  target **variable/argument type** in the Variables/Arguments panel to match, rather than converting
  the value.
- **RHS is genuinely null (uninitialized complex object), not a type collision:** if the real error is
  `Object reference not set…` when the RHS is a `DataTable`/`List`/`Dictionary` used before
  initialization, that is a null-init problem — initialize it (`New System.Data.DataTable()`,
  `New List(Of String)()`) per [null-reference-exception.md](./null-reference-exception.md).
- **Studio caches a stale expression validation:** if the expression is already correct but the Error
  List still flags it, the RHS expression editor can get stuck — delete the `Assign`, drop a fresh
  one, and re-enter the target then the value. If that alone does not clear it, close Studio and delete
  the project's `.local` / `bin` / `obj` cache, then reopen.
