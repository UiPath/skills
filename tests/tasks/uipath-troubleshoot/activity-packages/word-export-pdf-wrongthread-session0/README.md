# Save Document as PDF — COM Wrong-Thread (Unattended Session-0 / Off-STA)

This scenario reproduces a `Save Document as PDF` (`WordExportToPdf`) COM
failure that faults casting the document to
`Microsoft.Office.Interop.Word._Document` with
`0x8001010E RPC_E_WRONG_THREAD` on an **unattended Session-0 / background**
runtime. No external Word is involved — the run surface itself is the cause.

## What this scenario uncovers

**Root Cause:** Word COM interop requires an interactive STA session. The job
ran **unattended in Session 0** (non-interactive), so the worker thread that
executed `Save Document as PDF` is not the interactive STA that can own the
`_Document` COM object, and the cross-apartment `QueryInterface` failed with
`RPC_E_WRONG_THREAD`. The workflow is structurally correct (the export is the
sole child of the scope that opened the document) and there is **no** external
Word warning in the log — distinguishing this from the external-attach /
mid-run-close cause.

This maps to:
`references/activity-packages/word-activities/playbooks/word-export-pdf-com-wrong-thread.md`

The correct agent behavior is to tie `RPC_E_WRONG_THREAD` + the IID
`{0002096B-...}` (`_Document`) to the off-STA / Session-0 run surface (using
the unattended/non-interactive run evidence and the absence of any external
Word), and recommend either running the automation attended in an interactive
session or migrating the export to the **System Word** (background)
activities — without blaming the document or the output path.

## How this test reproduces it

| Layer | Source |
|---|---|
| `process/` | hand-authored `NightlyReportPdf`; `Word Application Scope` opens `data\Report.docx`, `Save Document as PDF` → `data\out\Report.pdf` (structurally correct); `project.json` is a background process (`requiresUserInteraction: false`) |

> **Note on fixtures.** Synthetic. The decisive evidence is the unattended /
> Session-0 / non-interactive run surface plus the absence of any external
> Word warning — the cause is the run surface, not an attached Word or the
> workflow structure.

## Fixture isolation

`data/uip-fixture.json` is a finite command/response map mounted only into coder-eval's host-side protected mock service. The evaluated agent receives a bounded `uip` client and cannot read the fixture or mock implementation.
