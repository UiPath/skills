---
confidence: medium
---

# Invoke VBA — Cannot Run Macro / Code File Unreadable

## Context

What this looks like:
- Activity `Invoke VBA` (`UiPath.Excel.Activities.Business.InvokeVBAX`) faults while loading or compiling the macro source from the external code file
- Error message contains one of: `Cannot run the macro`, `Compile error`, `Syntax error`, `Sub or Function not defined`, `Expected: end of statement`, or a generic VBA compiler error citing a line number in the injected module
- Job faults synchronously the moment `Invoke VBA` runs, after `Excel Process Scope` opened successfully and before any macro logic executes

What can cause it (more than one may apply):
- **Code not wrapped in a `Sub`/`Function` block** — the file contains bare VBA statements at the top level. `Invoke VBA` injects the file's contents as a module, which only accepts procedure declarations at the top level.
- **Non-UTF-8 encoding or hidden control characters** — the code file is UTF-16, has a UTF-8 BOM, or contains zero-width / non-printable characters that the VBA compiler rejects. Common when the file was created via UiPath Studio's built-in editor on Windows (which may save as UTF-16 LE with BOM) or copied from a Word document.
- **`CodeFilePath` does not resolve** — the path points to a file that does not exist on the robot machine, is locked by another process, or is a relative path that resolves against the project folder rather than the workbook folder.
- **VBA syntax errors in the macro source** — typos, missing `End Sub`, mismatched parentheses, references to undefined VBA functions.
- **Code authored inside an `.xlsm`** — the user wrote the macro inside the workbook's VBA editor and pointed `CodeFilePath` at the `.xlsm`. `Invoke VBA` does not read macros from an `.xlsm`; the source must be in an external `.txt`/`.vba`/`.bas` file.

## Investigation

1. Read the `InvokeVBAX` node from the workflow `.xaml` and capture the literal `CodeFilePath` value.
2. Resolve the path against the robot's working directory at job run time. Confirm the file exists on the robot machine and is readable by the robot's Windows user.
3. Open the file and confirm:
   - It is a plain-text file (`.txt`, `.vba`, or `.bas`), not an `.xlsm` workbook.
   - The first non-blank line is a `Sub <Name>` or `Function <Name>` declaration. There are no bare executable statements outside a procedure block.
   - The declared procedure name matches `EntryMethodName` exactly (apart from case — VBA is case-insensitive in source, but see the entry-method playbook for `Application.Run` caveats).
4. Check the file encoding (open in Notepad++ / VS Code status bar, or run `file` on the path from WSL/Git Bash). It must be UTF-8 without BOM, or pure ASCII. UTF-16 or UTF-8-with-BOM will compile-fail.
5. If steps 1–4 all pass, copy the file's contents into Excel's VBA editor manually and try `Run` — if VBA itself reports a compile error there, the macro source has a defect independent of UiPath.

## Resolution

- **If `CodeFilePath` does not resolve on the robot machine** — fix the path. Prefer an absolute path that is reachable from the robot, or place the code file inside the project folder and reference it with a project-relative path. Re-deploy and re-run.
- **If the code is not wrapped in a `Sub`/`Function`** — edit the code file and wrap the executable statements:
  ```vb
  Sub MyMacro()
      ' existing statements
  End Sub
  ```
  Then set `EntryMethodName` to `MyMacro` on the activity.
- **If the file is UTF-16, has a UTF-8 BOM, or contains hidden control characters** — re-create the file externally (Notepad, Notepad++, VS Code). In Notepad++, set `Encoding > Convert to UTF-8` (without BOM); in VS Code, click the encoding indicator in the status bar and select `Save with Encoding > UTF-8` (no BOM). Replace the original file at `CodeFilePath`.
- **If the macro source has VBA syntax errors** — fix them in the external file, validating by opening the file's content in Excel's VBA editor (`Alt+F11`) and pressing `Debug > Compile VBAProject`. Re-save and re-run.
- **If the user wrote the macro inside an `.xlsm`** — extract the macro to an external `.txt` or `.vba` file: open the `.xlsm`, press `Alt+F11`, copy the `Sub`/`Function` text out of the VBA editor, paste into a new text file, save as UTF-8 (no BOM), and point `CodeFilePath` at that file.

If after all of the above the error still cites a missing `Sub` or `Function`, the failure is not in the code file — see the entry-method-name playbook.
