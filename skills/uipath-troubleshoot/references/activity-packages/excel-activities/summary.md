# Excel Activities Playbooks

**Investigation guide:** [investigation_guide.md](./investigation_guide.md) — data correlation rules and testing prerequisites for Excel Activities investigations

| Issue | Confidence | Description | Playbook |
|-------|:---:|-------------|----------|
| Invoke VBA — Trust Access to VBA Project Denied | High | Excel "Trust access to the VBA project object model" setting disabled; activity cannot inject the macro module | [invoke-vba-trust-access.md](./playbooks/invoke-vba-trust-access.md) |
| Invoke VBA — Cannot Run Macro / Code File Unreadable | Medium | External `.txt`/`.vba` code file missing, malformed, wrongly encoded, or not wrapped in a `Sub`/`Function` block | [invoke-vba-code-file-path.md](./playbooks/invoke-vba-code-file-path.md) |
| Invoke VBA — Entry Method Name Mismatch | High | `EntryMethodName` does not resolve to a `Sub`/`Function` declared in the code file (typo, parentheses appended, nested macro) | [invoke-vba-entry-method-name.md](./playbooks/invoke-vba-entry-method-name.md) |
| Invoke VBA — Parameter Type or Shape Mismatch | Medium | `EntryMethodParameters` is not a properly-built `IEnumerable<Object>`, arity is wrong, or values were typed inline in the property window | [invoke-vba-parameter-formatting.md](./playbooks/invoke-vba-parameter-formatting.md) |
| Invoke VBA — COM Interop Failure (0x80010100) | Medium | Excel busy, blocked by a hidden modal dialog, Excel.exe hung, or multiple/wrong-bitness Office installs | [invoke-vba-com-interop-failure.md](./playbooks/invoke-vba-com-interop-failure.md) |
