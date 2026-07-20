# Final Resolution

---

**Root Cause:** The `ExcelWriteCellProcess` workflow's `Write Cell`
activity targets cell `D1` with `Value = "=SUM(A1;A10)"`. The
formula uses SEMICOLON separators between parameters. UiPath
passes the formula string to Excel COM verbatim, and Excel COM
requires COMMA separators in parameter lists regardless of the
host's Windows regional setting. The Excel UI displays semicolons
in non-US locales (so a workflow author copying a formula from
Excel may see `=SUM(A1;A10)` and assume it's the right syntax),
but the COM API does not accept semicolons. The formula parser
rejects the malformed input and Excel surfaces the
`UiPath.Excel.BusinessException: The data you want to write has
a wrong format, or Excel is busy.` error.

**What went wrong:** Failing job
`22bb2222-2222-3333-4444-555566667777` started at
`2026-05-20T08:00:01.300Z`. The `Use Excel File` scope opened the
workbook successfully. The `Write Cell` activity then attempted
to write the formula `=SUM(A1;A10)` to cell `D1` on sheet
`Sales`. Excel COM's `Range.Formula = ...` call rejected the
formula string with the canonical "wrong format" BusinessException.

**Why:** Two distinct Write Cell failure modes share the exact
same error wording — `UiPath.Excel.BusinessException: The data
you want to write has a wrong format, or Excel is busy.`:

- **Branch 2 (formula syntax rejected):** the formula has invalid
  syntax. The most common subcase is parameter separators —
  Excel COM accepts only commas, while the Excel UI in non-US
  locales displays semicolons. Other subcases: unbalanced or
  unescaped inner quotes, function names that require an unloaded
  add-in, function names misspelled.
- **Branch 3 (loop-induced Excel-is-busy / COM thrash):** the
  formula is fine but the Write Cell is called repeatedly inside
  a tight loop, and Excel COM's state becomes corrupt after N
  iterations. The "or Excel is busy" clause of the error is
  misleading on branch 2 (nothing is busy) but accurate on
  branch 3.

Distinguishing the two requires reading both the workflow source
(is the Value a formula? does it contain `;`?) AND the loop
context (is Write Cell inside `For Each` / `For Each Row` /
`While`?). The user's exclusion of loops + the semicolon in the
formula + the single Write Cell invocation in the logs all point
unambiguously at branch 2.

---

**Evidence:**

### Orchestrator (Root cause)
- Failing job: `ExcelWriteCellProcess` (key `22bb2222-...`) --
  Faulted at `2026-05-20T08:00:02.812Z`.
- Folder: `ExcelWrites` (key
  `f0022222-2222-3333-4444-555566667777`).
- Host: `MOCK-HOST`. Robot user: `UIPATH\AUTOMATION1`.
- Error (verbatim from `or jobs get`):
  `UiPath.Excel.BusinessException: The data you want to write
  has a wrong format, or Excel is busy.`
- Faulting activity: `WriteCell_1` (`Write Cell: =SUM(A1;A10)`)
  at `Main.xaml`.

### Workflow source (decisive)
- `Main.xaml`:
  - `<uix:UseExcelFile WorkbookPath="C:\Robot\Data\sales-2026-05.xlsx" ...>`
    --- Modern scope.
  - Inside its `Body`:
    `<uix:WriteCell Range="D1" SheetName="Sales"
    Value="=SUM(A1;A10)" .../>` --- **formula with SEMICOLON
    separators**.
  - The activity is NOT inside any loop (`For Each`,
    `For Each Row`, `While`, etc.).

### Job logs (decisive disambiguation from branch 3)
- `Use Excel File: sales-2026-05.xlsx -- workbook opened`
- `Write Cell: =SUM(A1;A10) -- attempting to write formula to D1`
- `Write Cell: =SUM(A1;A10) -- UiPath.Excel.BusinessException:
  The data you want to write has a wrong format, or Excel is
  busy.`
- The logs show ONE Write Cell invocation that failed. If this
  were branch 3 (loop thrash), the logs would show many
  successful Write Cell invocations preceding the failure.

### User exclusion (decisive)
- "No loop, no parallel work, no other Excel jobs." Explicitly
  rules out branch 3 (loop thrash). Combined with the single
  Write Cell invocation in the logs, branch 3 is conclusively
  excluded.

### Cross-check -- what this is NOT
- Not branch 1 (file locked / scope conflict): the error class
  is `BusinessException`, not `IOException`. The file opened
  successfully.
- Not branch 3 (loop-induced thrash): single invocation; no
  loop in workflow source; user explicitly excludes loops.
- Not branch 4 (sheet not found): the error wording is "wrong
  format", not "sheet with the name '<x>' does not exist".
- Not branch 5 (protected sheet / workbook): the error class
  would be `COMException` with protection wording, not
  BusinessException with "wrong format".
- Not branch 6 (invalid cell reference): `D1` is valid A1
  notation. The error wording would be "cell reference '<x>'
  is invalid".

---

**Recommended Fix (Resolution):**

### Primary fix -- replace semicolons with commas

1. Open `Main.xaml` in Studio (or edit XAML directly).
2. Find the `Write Cell` activity targeting `D1` and change the
   `Value` property from `"=SUM(A1;A10)"` to `"=SUM(A1,A10)"`.
3. Re-run the job to verify.

### Generalized fix -- audit other formula activities

If the workflow has multiple formula-bearing activities (Write
Cell, Write Range with formula columns, etc.), audit every
formula for semicolon usage:

```
grep -rE '=[A-Z]+\([^)]*;' Main.xaml *.xaml
```

Replace `;` with `,` in every parameter list.

### Verify the fix at runtime

Add a `Log Message` immediately before the `Write Cell`:

```vb
Log Message Level=Info Message=$"Formula about to write: {formulaExpression}"
```

Re-run and confirm the logged formula uses commas. If the formula
is built dynamically from variables, this catches the bug at the
source rather than at the Excel COM rejection point.

### What NOT to do

- **Do NOT add a `Retry Scope` around the Write Cell.** Retrying
  an invalid formula produces the same rejection every time.
  Retries only help when the underlying state is transient;
  formula syntax is not transient.
- **Do NOT recommend the branch 3 (loop thrash) fix** (replace
  Write Cell with Read Range → in-memory DataTable mutation →
  Write Range). The user has explicitly excluded loops, and
  there is no loop in the workflow source. The branch 3 fix is
  expensive and inappropriate here.
- **Do NOT change the host's Windows regional setting.** Excel
  COM does not honor regional separators — changing the regional
  setting changes only the Excel UI display, not the COM API
  contract.

### Prevention

- When authoring formulas in UiPath, always use commas as
  parameter separators. Treat the Excel UI's semicolon display
  as a localization preference, not an API contract.
- Validate formula strings before passing to Write Cell. Build
  formulas via a helper function that asserts the
  comma-separator rule:
  ```vb
  Public Function AssertCommaFormula(formula As String) As String
      If formula.Contains(";"c) Then
          Throw New InvalidOperationException(
              $"Formula uses semicolon separators: {formula}. Use commas.")
      End If
      Return formula
  End Function
  ```
- For workflows that may run on hosts with different regional
  settings, the comma-separator rule is the safe default — it
  works on every locale.
- When copying formulas FROM the Excel UI, remember that what's
  displayed may be locale-specific. Convert semicolons to commas
  before pasting into a UiPath activity property.
