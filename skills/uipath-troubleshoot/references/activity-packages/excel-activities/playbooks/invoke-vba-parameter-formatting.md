---
confidence: medium
---

# Invoke VBA — Parameter Type or Shape Mismatch

## Context

What this looks like:
- Activity `Invoke VBA` (`UiPath.Excel.Activities.Business.InvokeVBAX`) faults when marshaling `EntryMethodParameters` into the COM call
- Error message contains one of: `Type mismatch`, `Wrong number of arguments or invalid property assignment`, `Unable to cast object of type ... to type ...`, or an `InvalidCastException` referencing `IEnumerable<Object>`
- Alternative symptom: Studio freezes or crashes when the user types a parameter expression directly into the `EntryMethodParameters` field in the property panel
- The code file compiles, `EntryMethodName` resolves correctly, but the macro never executes its first statement

What can cause it:
- **`EntryMethodParameters` not an `IEnumerable<Object>`** — the property is typed `IEnumerable<Object>` but the bound expression evaluates to a `String`, a single `Object`, or a strongly-typed array that does not implement the expected interface.
- **Arity mismatch** — the array passed has more or fewer elements than the macro's `Sub`/`Function` signature accepts.
- **Element type mismatch** — array elements are the wrong VBA type for the macro signature (e.g., a `String` passed to a `Sub TakesNumber(n As Long)`).
- **Property-window inline typing** — typing a complex `New Object() {...}` expression directly into the `EntryMethodParameters` field in the property panel can freeze or crash Studio while it tries to re-parse on every keystroke. This is a Studio editor pathology, not a runtime error, but presents as the same activity failing to run.
- **`Nothing` / `null` array** — `EntryMethodParameters` was never assigned, leaving the bound variable `null`. The activity passes `null` to `Application.Run`, which faults on the marshal.

## Investigation

1. Read the `InvokeVBAX` node from the workflow `.xaml` and capture the literal expression bound to `EntryMethodParameters`.
2. Identify the type of that expression at the binding site (look at the declared type of the variable, or the type the expression evaluates to). Confirm it is `IEnumerable<Object>` or `Object[]`.
3. Read the code file and capture the `Sub`/`Function` signature for `EntryMethodName` — parameter count and declared VBA types (`String`, `Long`, `Double`, `Variant`, `Boolean`, etc.).
4. Compare:
   - Parameter count in the array vs. parameter count in the signature.
   - Element types in the array vs. declared VBA types.
   - Whether any element is `Nothing`/`null` when the matching VBA parameter is not declared `Optional`.
5. If the user reports Studio freezing or crashing during property edit (not at runtime), that is a distinct symptom — the property-window inline typing pathology.

## Resolution

- **If `EntryMethodParameters` is bound to a non-array value** — refactor to build an `Object` array via an `Assign` activity placed before `Invoke VBA`:
  ```vb
  ' Assign: macroParams = New Object() { param1, param2, param3 }
  ```
  Then bind `EntryMethodParameters` to `macroParams`.
- **If arity is wrong** — match the array length to the macro signature exactly. If the macro takes no parameters, set `EntryMethodParameters` to `New Object() {}` (empty array) — not `Nothing`.
- **If element types don't match** — cast each element to the matching VBA-compatible .NET type at the `Assign` site. `Long` ↔ `Int64`, `Integer` ↔ `Int32`, `Double` ↔ `Double`, `String` ↔ `String`, `Boolean` ↔ `Boolean`, `Variant` accepts any. Date values should be passed as `DateTime`.
- **If `EntryMethodParameters` is `Nothing` because the variable was never assigned** — initialize the variable to `New Object() {}` (or the populated array) before `Invoke VBA` runs.
- **If Studio froze during property edit** — close Studio, re-open the project, and build the parameter array via an `Assign` activity instead of typing the expression inline in the property panel. Bind the property field to the resulting variable name only. This avoids the per-keystroke re-parse pathology and is the documented authoring pattern for this property.

If the parameter expression is correct and the macro still faults on the first statement, the failure is inside the macro itself — debug the VBA logic in Excel directly rather than continuing under this playbook.
