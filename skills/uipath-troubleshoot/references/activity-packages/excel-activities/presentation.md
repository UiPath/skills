# Excel Activities Presentation Rules

- **Activities** — use the display name (e.g., "Invoke VBA", "Excel Process Scope", "Read Range"), not the fully qualified class name (e.g., `UiPath.Excel.Activities.Business.InvokeVBAX`)
- **Workbooks** — refer to workbooks by their filename (e.g., "workbook 'Q3-Report.xlsx'") or full path when ambiguous; not by the variable holding the `WorkbookApplication` reference
- **Worksheets / sheets** — refer to sheets by the tab name visible in Excel (e.g., "sheet 'Summary'"), not by index
- **Code files** — refer to the VBA source file by filename and extension (e.g., "code file `macro.txt`" or "`InvoiceMacros.vba`"), not by the variable holding the path
- **VBA macros** — refer to macros by the `Sub`/`Function` name as it appears in the code file (e.g., "macro `ImportInvoices`"), not by the `EntryMethodName` variable
- **Office versions** — refer to Office by its installed product name and bitness (e.g., "Microsoft 365 Apps for Enterprise (64-bit)", "Office 2019 (32-bit)"), not by internal version numbers like `16.0` unless they are the only identifier available
- **Excel settings** — refer to Trust Center settings by the exact UI label path the user navigates (e.g., `File > Options > Trust Center > Trust Center Settings > Macro Settings > Trust access to the VBA project object model`), so the user can find the toggle without guessing
