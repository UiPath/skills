# Export to PDF Failure - Malformed Output Path / Missing .pdf

This scenario reproduces an `Export to PDF` failure where the output path is
built by string concatenation **without a `.pdf` extension**
(`outFolder + "\" + reportName` → `C:\Reports\MonthlyReport`), so the
activity throws `ArgumentException: The export file path must specify a .pdf
file`.

## What this scenario uncovers

**Root Cause:** `WordExportToPdf` requires the output to be a file ending in
`.pdf`. The concatenated path omits the extension, so the resolved value is
an invalid PDF target. The document opens fine — the failure is purely the
malformed output path.

This maps to:
`references/activity-packages/word-activities/playbooks/export-pdf-output-path-format.md`

The correct agent behavior is to tie the fault to the missing `.pdf`
extension / path formatting (via the XAML expression + the error's `Value
was 'C:\Reports\MonthlyReport'`) and recommend `Path.Combine(folder, name &
".pdf")` — not blaming a missing folder, COM, or the document.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project; `Export to PDF` `FileName = outFolder + "\" + reportName` (no `.pdf`) |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** The faulted job's `ArgumentException` names the exact
> malformed value (`C:\Reports\MonthlyReport`), matching the XAML expression;
> the input opens first, locating the fault at the output path. Distinct from
> the generic `Command Failed` of the missing-output-directory scenario.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `export-pdf-output-path-format.md`
- Agent identified the output path lacking the `.pdf` extension as the cause
  and recommended a `.pdf`-suffixed path (`Path.Combine` / append `".pdf"`) —
  without blaming a missing folder/COM/document or fabricating actions
