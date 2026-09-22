# Final Resolution

Investigation complete. Here is the resolution:

---

**Root Cause:** **Assign type mismatch — an `Object`-typed expression assigned to a `String` variable.**
The `Assign` activity "Read account name from config" reads `config("AccountName")` from a
`Dictionary(Of String, Object)` — the dictionary indexer returns `System.Object` — and assigns it to
`accountName`, which is declared `System.String`. Studio's validation rejects the narrowing
conversion, so the Error List shows `Cannot assign from type 'System.Object' to 'System.String'`. This
is a **design-time / Studio validation error**, not a faulted robot job — there is no Orchestrator job,
log, or trace.

**What went wrong:** The right-hand-side expression's return type (`System.Object`, from the
`Dictionary(Of String, Object)` lookup) cannot be assigned to the left-hand-side target's declared
type (`System.String`) without an explicit conversion. The activity is otherwise well-formed; only the
type contract is violated.

**Why:**
- `process/Main.xaml` — the `Assign` "Read account name from config" (`Assign_ReadName`) has
  `Assign.To` = `accountName` (an `OutArgument x:TypeArguments="x:String"`) and `Assign.Value` =
  `config("AccountName")` (an `InArgument x:TypeArguments="x:String"`).
- `config` is declared in the Main Sequence as `Dictionary(Of String, Object)`; its default indexer
  returns `System.Object`.
- Assigning `System.Object` into a `System.String` target is a narrowing conversion that VB (Option
  Strict) / the workflow validator rejects → `Cannot assign from type 'System.Object' to
  'System.String'`.

**Evidence:**
- Error appears in Studio's **Error List** at open/validate/build; no job, log, or trace exists.
- `<SOURCE>` in the message = `System.Object` (the dictionary lookup's return type); `<TARGET>` =
  `System.String` (the `accountName` variable / Assign target type).
- The `Assign` node in `Main.xaml` is structurally valid — the fault is purely the type contract of the
  RHS expression vs the target.

**Immediate fix:**
1. Append `.ToString()` to the right-hand-side expression so it returns a `String`:
   `config("AccountName").ToString()`.
2. (If the value could be missing, guard it first — e.g. check the key exists / is non-null before
   `.ToString()` — to avoid a `NullReferenceException` at runtime.)
3. Re-validate — the Error List entry clears once the RHS type matches the `String` target.

Alternative, when the value is genuinely not a string: cast to the intended type instead of
`.ToString()` — e.g. `CInt(config("Retries"))` / `Convert.ToInt32(config("Retries"))` for an integer
target — or change the target variable's declared type to match the value.

**Do NOT** "fix" this by only deleting and re-adding the Assign hoping Studio re-validates — the source
type mismatch is real and will re-appear. Delete/re-add only helps when the expression is already
correct but the editor cached a stale validation.

**Preventive fix:**
- When reading from a `Dictionary(Of String, Object)` (e.g. an RE Framework `Config`), always convert
  the `Object` value to the target type at the point of use (`.ToString()`, `CInt(...)`,
  `Convert.ToDateTime(...)`), or store strongly-typed values.
- Keep the target variable's declared type aligned with what the expression actually produces.

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | An `Object`-returning RHS (`config("AccountName")` on a `Dictionary(Of String, Object)`) is assigned to a `String` variable, so Studio rejects the narrowing conversion at design time. | high | confirmed | Yes | `Assign_ReadName` in `Main.xaml`: `Assign.To` String `accountName`, `Assign.Value` `config("AccountName")`; `config` is `Dictionary(Of String, Object)` → indexer returns `System.Object`. | Append `.ToString()` (or cast to the intended type) to the RHS so it matches the `String` target. |
| H2 | A robot job faulted at runtime. | low | eliminated | No | No Orchestrator job, log, or trace exists; the error is raised in Studio's Error List at design time. | N/A — design-time validation error. |
| H3 | The `.xaml` is corrupt and must be rebuilt. | low | eliminated | No | The `Assign` node is well-formed; only the RHS expression type conflicts with the target type. | N/A — fix the expression/target type, do not rebuild the file. |
