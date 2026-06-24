---
confidence: medium
---

# Read Range — Sheet With The Specified Name Does Not Exist

## Context

A `UiPath.Excel.Activities` Read Range (or any range-addressed Excel activity) opens the workbook successfully but fails when it tries to resolve the configured `SheetName` against the workbook's actual sheet titles. No sheet in the workbook matches the configured name exactly, so the activity throws before any range parsing or cell reads happen.

What this looks like:
- Activity fails with `UiPath.Excel.BusinessException: The sheet with the name '<configured-name>' does not exist.` (legacy `Excel Application Scope` family) or `UiPath.Excel.ExcelException: Sheet '<configured-name>' does not exist in the workbook.` (modern `Use Excel File` family). Exact wording shifts across package versions; the constant signal is the literal configured `SheetName` echoed back in the error.
- The configured workbook path is correct — the file opened (no preceding `IOException`, `FileNotFoundException`, or password-protection error).
- The error names a `SheetName` that the user believes exists. Comparing against the workbook's actual sheets is the next step.
- Affects every range-addressed Excel activity: `Read Range`, `Read Cell`, `Read Column`, `Read Row`, `Write Range`, `Write Cell`, `Append Range`, `Filter Range`, `Pivot Range`, `Sort Range`, `For Each Row in Excel`, etc.

What can cause it (cause-branches — pick the right one from evidence):

1. **Typo in the configured sheet name** — `SheetName` literal differs from the actual sheet by one or more characters. Most common when the value is hard-coded in the workflow and the workbook is authored by a different person. Symptom: error names a sheet that simply isn't in the workbook's sheet list.
2. **Case mismatch under the OpenXML provider** — `Use Excel File` running on the OpenXML provider (Excel not installed or COM fallback not triggered) treats sheet names **case-sensitively**. Excel COM (legacy `Excel Application Scope`, or `Use Excel File` falling back to COM) is case-insensitive. Symptom: same workflow that worked on a Studio dev box (where Excel is installed → COM) fails on a headless Robot host (no Excel → OpenXML). The configured name differs from the actual sheet only by letter casing.
3. **Sheet was renamed upstream** — the workbook publisher renamed the sheet (`Sheet1` → `January 2026`, `Data` → `Raw Data`, etc.). The workflow's configured name is now stale. Symptom: error names the OLD sheet; opening the workbook in Excel shows the NEW sheet name.
4. **Sheet was deleted upstream** — the workbook publisher removed the sheet entirely. Symptom: error names a sheet that no longer exists; the data the workflow is meant to read may have been moved to a different sheet.
5. **Leading or trailing whitespace** — the configured `SheetName` is `"Data "` (trailing space) or `" Data"` (leading space) and the actual sheet is `"Data"` (or vice versa). Common when the name comes from a variable concatenated with another string (`"Data " + month`) or from an external source (queue item, asset, CSV) where whitespace is not trimmed. Symptom: error wording shows the whitespace if you copy it byte-exact; visually the configured name looks correct.
6. **Non-ASCII or look-alike characters** — sheet name contains characters that look identical but are different code points: regular space (`U+0020`) vs. non-breaking space (`U+00A0`), Latin `a` (`U+0061`) vs. Cyrillic `а` (`U+0430`), straight quote vs. curly quote. Common when the name was copy-pasted from email, Word, or an internationalized data source. Symptom: configured name and actual name look identical in the UI but bytes differ.
7. **Variable resolved to wrong value at runtime** — the `SheetName` property is a dynamic expression (`row("Region").ToString()`, `Environment.GetEnvironmentVariable(...)`, etc.) that resolved to an unexpected value at runtime. Symptom: error names a sheet that nobody configured deliberately — possibly `Null`, an empty string `""`, a row index like `0`, or an unrelated cell value.
8. **Sheet is hidden or very-hidden** — the configured sheet name DOES exist in the workbook but is set to `xlSheetHidden` or `xlSheetVeryHidden` visibility. The OpenXML provider returns hidden sheets in lookups, but historical bug reports show legacy `Excel Application Scope` skipping very-hidden sheets when resolving by name on some `UiPath.Excel.Activities` versions. Symptom: an interactive admin can see the sheet via Excel's `Format → Sheet → Unhide`, but the activity reports it missing; `Get Workbook Sheets` may or may not list it depending on provider and version.

What to look for:
- **The literal configured `SheetName` echoed in the error** — the authoritative input at runtime. Don't trust the design-time expression alone; the runtime value may differ.
- **The workbook's actual sheet titles** — open the workbook in Excel, or enumerate via a one-off `Get Workbook Sheets` activity in a scratch project. Compare verbatim against the configured name.
- **Provider in use** — COM or OpenXML. Determines whether case-sensitivity applies. Legacy `Excel Application Scope` is always COM. Modern `Use Excel File`: OpenXML by default; falls back to COM when `Read Formatting`, `Edit Password`, or macro-related properties are set.
- **Whether the workbook was recently re-authored** — ask whether the upstream owner renamed, deleted, or restructured sheets. A `git log` / SharePoint version history check on the workbook itself is conclusive.
- **Whether `SheetName` is a literal or a dynamic expression** — workflow source. Dynamic expressions point at branch 7.
- **Byte-level comparison if the names look identical** — for branches 5 and 6. Paste both into a hex viewer or use `[char]<n>` in PowerShell to inspect code points.

## Investigation

Go in this order — cheaper checks first.

1. **Confirm the activity, configured `SheetName`, and workbook.** From workflow source: which activity (`Read Range` / `Read Cell` / etc.), which scope (`Excel Application Scope` vs. `Use Excel File`), and the configured `SheetName` expression — literal string or dynamic. From `uip or jobs get <job-key> --output json` → `Info`: the exception class, the workbook path, and the `<configured-name>` echoed in the error string.

2. **Distinguish branch 7 (variable resolved wrong) immediately.** If the `SheetName` expression in source is dynamic, the runtime value is what matters. If the error names something nonsensical (`Null`, empty string, `0`, an integer, a row value, a path fragment), the variable resolved to the wrong thing — go to step 7. If the error names a plausible sheet (`Sheet1`, `Data`, `January 2026`), continue with branches 1-6.

3. **Enumerate the workbook's actual sheets.** If the user can open the workbook in Excel, list the sheet titles verbatim. If they cannot (headless host, file lives on a share they don't access), have them run a one-off scratch workflow with `Get Workbook Sheets` against the same path on the same host. The returned `IEnumerable<String>` is the authoritative list.

4. **Compare verbatim against the configured name.**
   - **Identical match in the list** → not this playbook. The activity should not have failed; check the next-most-likely playbook (file-locked, file-not-found) or look for a version-specific package bug.
   - **No similar name in the list** → branch 4 (deleted) or branch 1 (typo big enough that no close match exists).
   - **A close-but-different name in the list** → continue with branches 1, 2, 3, 5, or 6 per the diff:
     - Exactly one character different → branch 1 (typo).
     - Same letters, different casing → branch 2 (case mismatch).
     - Different word entirely, recent rename → branch 3.
     - Same visible characters but one has leading/trailing space → branch 5 (whitespace).
     - Same visible characters, no obvious diff → branch 6 (look-alike characters). Continue to step 5.

5. **Detect whitespace / look-alike characters when the names look identical.**
   ```powershell
   $configured = '<configured-name>'
   $actual = '<actual-name-from-workbook>'
   "configured: $($configured.Length) chars  bytes: $(([System.Text.Encoding]::UTF8.GetBytes($configured) | ForEach-Object { $_.ToString('X2') }) -join ' ')"
   "actual:     $($actual.Length) chars  bytes: $(([System.Text.Encoding]::UTF8.GetBytes($actual) | ForEach-Object { $_.ToString('X2') }) -join ' ')"
   ```
   - Length differs → branch 5 (whitespace at one end).
   - Length equal, byte sequences differ → branch 6 (look-alike character at some position).
   - Length equal, byte sequences equal → not a name-mismatch issue; recheck step 4.

6. **Determine the provider in use (branch 2 confirmation).** Legacy `Excel Application Scope` is always COM (case-insensitive sheet lookups) — branch 2 is impossible here. Modern `Use Excel File`:
   - If the activity inputs include `Read Formatting: True`, `Edit Password`, or macro-related properties → COM fallback, case-insensitive.
   - If none of those are set → OpenXML, case-sensitive on the OpenXML version in use.
   - Verify by re-running on a host where Excel **is** installed; if the same workflow succeeds there with the same workbook, branch 2 is confirmed.

7. **Trace the dynamic `SheetName` expression (branch 7).** If the configured name is a variable / expression:
   - Add a `LogMessage` immediately before the failing activity that logs `String.Format("[SheetName resolved to: '{0}']", <expression>)`. Re-run and observe the runtime value.
   - Or inspect `jobs logs` if the workflow already logs the value.
   - Trace the upstream variable assignments to find where the bad value was produced (null-safe lookup, queue item field missing, asset typo, etc.).

The root cause is **which specific kind of mismatch** between the configured `SheetName` and the workbook's actual sheet titles — not "the sheet doesn't exist" generically. A confirmed finding names the configured name verbatim, the actual sheet name(s), and one of the cause-branches.

## Resolution

Map the branch identified in Investigation to the fix:

- **Branch 1 — Typo:**
  - Update the `SheetName` property on the activity to match the actual sheet name verbatim. If the value is a literal in the workflow, edit it directly. If it comes from a config asset or argument, fix the source.
  - Prevention: enumerate sheets via `Get Workbook Sheets` at job start when the workbook is authored externally and the sheet name is not stable. Validate the configured name against the list before reading; fail fast with a clear message if not present.

- **Branch 2 — Case mismatch on OpenXML:**
  - **Match casing in the workflow** — change the configured `SheetName` to the exact casing the workbook uses. This is the cheapest fix and avoids depending on provider behavior.
  - **Or force the COM provider** — set `Read Formatting: True` (or another COM-forcing property) on the `Use Excel File` scope so the activity uses Excel COM, which is case-insensitive. Requires Excel installed on the host.
  - **Or normalize at read time** — if the casing is unstable across workbook versions, enumerate sheets via `Get Workbook Sheets` and look up the actual case via `sheets.First(Function(s) s.Equals(target, StringComparison.OrdinalIgnoreCase))`.
  - Prevention: do not assume case-insensitive sheet lookups on `Use Excel File`. Default to case-sensitive matching; document the convention.

- **Branch 3 — Sheet was renamed upstream:**
  - Update the configured `SheetName` to the new name.
  - Coordinate with the workbook publisher: agree on a stable sheet name convention, or use a sentinel header row / named range that the workflow can locate independent of sheet title.
  - Prevention: do not hard-code sheet names that the workbook publisher may rename. If the workbook layout is owned by a different team, encode the layout contract somewhere stable (sheet name AND header-row signature; named ranges; a metadata sheet).

- **Branch 4 — Sheet was deleted upstream:**
  - Confirm where the deleted sheet's data went (moved to another sheet? rolled up? archived elsewhere?). Update the workflow to read from the new location.
  - If the deletion was unintentional, restore from version history (SharePoint / OneDrive: Version History → Restore; local file: Excel's `File → Info → Version History`).
  - Prevention: treat the workbook layout as a contract. Don't delete sheets without coordinating with downstream consumers.

- **Branch 5 — Leading or trailing whitespace:**
  - **If the workbook's sheet name has the whitespace** (the publisher named it `"Data "`): either ask the publisher to rename without whitespace (cleanest), or update the workflow's configured name to include the whitespace verbatim.
  - **If the workflow's configured name has the whitespace** (it came from a variable or concatenation): trim. `SheetName = sheetVar.Trim()`. Audit the upstream source.
  - Prevention: always `.Trim()` external-sourced sheet names. Reject names with whitespace at the boundaries at validation time.

- **Branch 6 — Non-ASCII / look-alike characters:**
  - Identify the offending code point from the byte comparison in investigation step 5. Replace it with the intended character in whichever side has the wrong code point (usually the workflow's configured name).
  - Prevention: when sheet names come from external sources (especially emails, Word docs, internationalized data), normalize: `System.Text.RegularExpressions.Regex.Replace(name, " ", " ")` for NBSP, or stronger Unicode normalization (`String.Normalize(NormalizationForm.FormC)`) for combining characters.

- **Branch 7 — Variable resolved to wrong value:**
  - Fix the upstream source of the variable. Common patterns:
    - Null-safe queue item field access (`If(item.SpecificContent.ContainsKey("Sheet"), item.SpecificContent("Sheet").ToString(), defaultSheet)`).
    - Asset / config lookup that returned empty — make the asset required and validate at job start.
    - String concatenation that included an unexpected value (`"Data " + month` where `month` was `Nothing`).
  - Add a guard before the activity that fails the workflow with a clear message when the resolved name is empty, null, or doesn't match a known sheet — rather than letting the BusinessException surface generically.
  - Prevention: validate dynamic sheet names against `Get Workbook Sheets` output at the start of the job. Treat an unresolved sheet name as a configuration error, not a runtime error.

- **Branch 8 — Hidden or very-hidden sheet:**
  - Unhide the sheet in Excel: `Format → Sheet → Unhide` (for `xlSheetHidden`), or open the VBA editor (`Alt+F11`) and set the sheet's `Visible` property to `xlSheetVisible` (for `xlSheetVeryHidden` — Excel's `Unhide` dialog does not list very-hidden sheets).
  - If the sheet must remain hidden (presentation reasons), update the workflow to enumerate sheets via a method that includes hidden ones, and confirm the configured name still matches verbatim.
  - Upgrade `UiPath.Excel.Activities` to the latest version if the project is on an older release; historical bug reports show legacy `Excel Application Scope` skipping very-hidden sheets in some versions.
  - Prevention: do not very-hide data sheets that workflows depend on. Either keep them visible, OR document the dependency in the workbook itself (cover sheet / metadata sheet listing all programmatically-read sheets).

## Anti-patterns (what NOT to do)

Two common pieces of advice for this failure mode are anti-patterns that hide the bug without fixing it. The agent should NOT recommend either as a primary resolution.

- **Switching from `Use Excel File` to `Excel Application Scope` (or vice versa) as a "magic fix".** Provider divergence between OpenXML and Excel COM is the cause of branch 2 (case mismatch) — switching scopes coincidentally hides that one branch by replacing case-sensitive lookup with case-insensitive lookup. It does NOT fix branches 1, 3, 4, 5, 6, 7, or 8, and it ties the workflow to a host that must have Excel installed (Excel Application Scope is COM-only). The real fix for branch 2 is to match the casing in the workflow, or to force COM explicitly via a documented property. Treat "try the other scope" as a debugging step (does the same workflow succeed under COM?), not as the resolution.

- **Wrapping the activity in a Try Catch to "handle missing tabs gracefully" with no real recovery path.** A bare `Catch System.Exception` (or `UiPath.Excel.BusinessException`) that only logs and continues turns the workflow into a silent-failure pipeline: the DataTable is empty, downstream activities produce zeros / empty reports / no queue items, and the operator sees a job that completed Successfully despite reading nothing. Use Try Catch only as part of a real recovery path: fall back to a different sheet, send a notification, mark a queue item Failed, or re-throw a domain-specific exception. The same anti-pattern is called out as an orphan-cause in [`read-range-file-locked.md`](./read-range-file-locked.md) — silent exception suppression around Excel scopes is consistently harmful, not helpful.

## Prevention (cross-branch)

- Enumerate sheets at job start (`Get Workbook Sheets`) and validate every configured sheet name against the actual list. Fail fast with a message that includes the configured name AND the actual list — saves operators 20 minutes of guessing.
- Treat the workbook layout as a contract between publisher and consumer. Sheet renames are a breaking change; coordinate them.
- Default to case-sensitive matching in your workflows even when the provider is currently case-insensitive — you may switch to a headless OpenXML-only host later.
- `.Trim()` any sheet name that comes from outside the workflow's literal source code.
- Normalize Unicode for names sourced from email / Word / internationalized data.
- Log the resolved sheet name at the start of any Excel scope when the name is dynamic; future debugging gets significantly cheaper.

## Related

- Other Excel Read Range failure fingerprints (file-locked, file-not-found, null-reference on formatted files) are separate playbooks — see [`../summary.md`](../summary.md).
- For shared / cloud Excel workbooks accessed via Microsoft Graph rather than the local filesystem, see [`o365-activities/overview.md`](../../o365-activities/overview.md).
