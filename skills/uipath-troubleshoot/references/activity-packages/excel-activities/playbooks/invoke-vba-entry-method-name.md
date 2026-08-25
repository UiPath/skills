---
confidence: high
---

# Invoke VBA — Entry Method Name Mismatch

## Context

What this looks like:
- Activity `Invoke VBA` (`UiPath.Excel.Activities.Business.InvokeVBAX`) faults at the moment it calls `Application.Run("<EntryMethodName>", ...)`
- Error message contains one of: `Cannot run the macro '<name>'. The macro may not be available in this workbook or all macros may be disabled`, `Sub or Function not defined`, or `The macro '<name>' cannot be found`
- The code file at `CodeFilePath` exists, is well-formed VBA, and compiles — but the named entry point cannot be resolved

What can cause it:
- **Typo or whitespace** in `EntryMethodName` — the string passed to `Application.Run` does not match any declared `Sub`/`Function` in the injected module (extra trailing space, hyphen vs. underscore, missing letter).
- **Parentheses appended** — `EntryMethodName` set to `MyMacro()` instead of `MyMacro`. `Application.Run` expects the bare identifier; the parentheses are interpreted as part of the name and fail to resolve.
- **Case mismatch on legacy Excel builds** — VBA source is case-insensitive, but `Application.Run` on some older Excel builds has been observed to reject case-mismatched names. Modern Office matches case-insensitively, but the safest practice is to copy the name exactly from the code file.
- **Macro is nested inside another `Sub`/`Function` or declared `Private`** — VBA only exposes top-level `Public` (or unmarked, which defaults to `Public` at module scope) procedures to `Application.Run`. A nested or `Private`-marked `Sub` is unreachable.
- **Wrong code file loaded** — `CodeFilePath` points to a different file than the user expects (stale path, similarly-named file in a different folder), and the macro the user named genuinely doesn't exist in the loaded file.

## Investigation

1. Read the `InvokeVBAX` node from the workflow `.xaml` and capture the literal `EntryMethodName` value, with any trailing whitespace.
2. Open the file at `CodeFilePath` and find every `Sub` and `Function` declaration. Capture each declared name and its scope keyword (`Public`, `Private`, or unmarked).
3. Compare `EntryMethodName` to the declared names. Check:
   - Exact character match (no extra spaces, no trailing `()`, no zero-width characters).
   - Whether the matching declaration is `Private` or nested inside another procedure.
4. If multiple `.txt`/`.vba` files exist under the project, confirm `CodeFilePath` resolves to the file the user intends — not a similarly-named one.

## Resolution

- **If `EntryMethodName` has trailing parentheses** — remove them. Set the property to the bare identifier (e.g., `MyMacro`, not `MyMacro()`).
- **If `EntryMethodName` has a typo or whitespace mismatch** — fix the property to match the declared `Sub`/`Function` name exactly, character for character.
- **If the matching declaration is `Private` or nested** — edit the code file: make the target procedure top-level (move it out of the enclosing `Sub`/`Function`) and either mark it `Public` or remove the `Private` keyword. Save and re-run.
- **If the declared name uses different casing than `EntryMethodName`** — fix `EntryMethodName` to match the case shown in the code file. This is defensive against older Excel builds even when the current build is case-insensitive.
- **If the code file genuinely does not contain a `Sub`/`Function` with that name** — either add the missing procedure in the code file, or fix `CodeFilePath` to point at the file that does declare it.
