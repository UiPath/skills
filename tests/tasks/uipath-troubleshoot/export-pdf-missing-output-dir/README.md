# Export to PDF Failure - Generic "Command Failed" (Output Directory Missing)

This scenario reproduces an `Export to PDF` failure that surfaces only as a
generic `Command Failed` because the output directory
(`C:\Output\2026\Invoices\`) does not exist and the activity does not
auto-create it (no `Create Folder` precedes the export).

## What this scenario uncovers

**Root Cause:** `WordExportToPdf` writes to a nested dated folder that isn't
created; the activity won't build the directory, so the save fails and
reports only `Command Failed`. The input document opens fine — the failure
is on the write side.

This maps to:
`references/activity-packages/word-activities/playbooks/export-pdf-missing-output-dir.md`

The correct agent behavior is to tie the generic error to the missing output
directory (via the XAML output path + the absence of a `Create Folder`) and
recommend adding a `Create Folder` before the export — not blaming Word/COM,
the input document, or a missing install. This tests disambiguating a
detail-free `Command Failed`.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project; `Word Application Scope` + `Export to PDF` to `C:\Output\2026\Invoices\Invoice.pdf`, no Create Folder |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** The job log shows the input opening (`Document
> 'data\\Invoice.docx' opened`) before `Export to PDF: Command Failed`,
> locating the fault at the write; the `.xaml` shows the nested output path
> and no `Create Folder`. The error itself is intentionally detail-free.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `export-pdf-missing-output-dir.md`
- Agent identified the non-existent output directory (activity won't
  auto-create) as the cause and recommended a `Create Folder` before the
  export — without blaming Word/COM/document or fabricating actions
