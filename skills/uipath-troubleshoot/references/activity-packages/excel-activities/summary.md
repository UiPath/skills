# Excel Activities Playbooks

**Investigation guide:** [investigation_guide.md](./investigation_guide.md) — data correlation rules and testing prerequisites for Excel Activities investigations

| Issue | Confidence | Description | Playbook |
|-------|:---:|-------------|----------|
| Invoke VBA — Trust Access to VBA Project Denied | High | Excel "Trust access to the VBA project object model" setting disabled; activity cannot inject the macro module | [invoke-vba-trust-access.md](./playbooks/invoke-vba-trust-access.md) |
| Invoke VBA — Cannot Run Macro / Code File Unreadable | Medium | External `.txt`/`.vba` code file missing, malformed, wrongly encoded, or not wrapped in a `Sub`/`Function` block | [invoke-vba-code-file-path.md](./playbooks/invoke-vba-code-file-path.md) |
| Invoke VBA — Entry Method Name Mismatch | High | `EntryMethodName` does not resolve to a `Sub`/`Function` declared in the code file (typo, parentheses appended, nested macro) | [invoke-vba-entry-method-name.md](./playbooks/invoke-vba-entry-method-name.md) |
| Invoke VBA — Parameter Type or Shape Mismatch | Medium | `EntryMethodParameters` is not a properly-built `IEnumerable<Object>`, arity is wrong, or values were typed inline in the property window | [invoke-vba-parameter-formatting.md](./playbooks/invoke-vba-parameter-formatting.md) |
| Invoke VBA — COM Interop Failure (0x80010100) | Medium | Excel busy, blocked by a hidden modal dialog, Excel.exe hung, or multiple/wrong-bitness Office installs | [invoke-vba-com-interop-failure.md](./playbooks/invoke-vba-com-interop-failure.md) |
| Lookup Range — Excel Not Installed | High | Classic `Lookup Range` Interop init fails on a host without Excel (`REGDB_E_CLASSNOTREG`); migrate to Workbook Read Range + Lookup Data Table | [lookup-range-excel-not-installed.md](./playbooks/lookup-range-excel-not-installed.md) |
| Lookup Range — Value Not Found (Active Filters) | Medium | Active AutoFilters hide the target row; activity returns null/empty silently and a downstream fault is the first symptom | [lookup-range-active-filters.md](./playbooks/lookup-range-active-filters.md) |
| Lookup Range — Workbook Locked / File In Use | Medium | Workbook held by another process, orphaned `EXCEL.EXE`, concurrent job, or sync/AV client; `being used by another process` | [lookup-range-file-locked.md](./playbooks/lookup-range-file-locked.md) |
| Lookup Range — Object Reference Not Set | Medium | `NullReferenceException` from a missing sheet/range name or the activity running outside an Excel scope | [lookup-range-null-reference.md](./playbooks/lookup-range-null-reference.md) |
| Lookup Range — Invalid Range or Value | Medium | `Range` set to `""` instead of blank, malformed A1 reference, unescaped wildcards, or a text-vs-number type mismatch in the search value | [lookup-range-invalid-range.md](./playbooks/lookup-range-invalid-range.md) |
| Excel Lookup Range — Common Failure Modes (canonical `ExcelLookUpRange`) | Medium | Umbrella reference for the canonical `UiPath.Excel.Activities.ExcelLookUpRange`: silent miss (active filters, formula cells, wildcard misinterpretation), Interop / `Excel is not installed`, and missing container | [excel-lookup-range.md](./playbooks/excel-lookup-range.md) |
