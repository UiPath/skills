# Save Document as PDF — COM Wrong-Thread (External Word Attached + Closed Mid-Run)

This scenario reproduces a `Save Document as PDF` (`WordExportToPdf`) COM
failure that faults casting the document to
`Microsoft.Office.Interop.Word._Document` with
`0x8001010E RPC_E_WRONG_THREAD`. A Microsoft Word (`WINWORD.EXE`) was already
open on the host when the run started; `Word Application Scope` attached to
that external instance (it exposes no isolated-instance option), and the user
closed that Word window mid-run before the export.

## What this scenario uncovers

**Root Cause:** `Word Application Scope` reused an already-running external
`WINWORD.EXE`, so the document's `_Document` COM object lived on that external
process's STA apartment. When the user closed that Word window mid-run, the
apartment owning the proxy was torn down / replaced, and the export's
cross-apartment `QueryInterface` failed with `RPC_E_WRONG_THREAD` (the
signature of a *replaced* apartment — distinct from `0x80010108
RPC_E_DISCONNECTED`, a clean server death). The workflow is structurally
correct: the export is the sole child of the scope that opened the document.

This maps to:
`references/activity-packages/word-activities/playbooks/word-export-pdf-com-wrong-thread.md`

The correct agent behavior is to tie `RPC_E_WRONG_THREAD` + the IID
`{0002096B-...}` (`_Document`) to the external-attach / mid-run-close cause
(using the attach + close warnings in the log), and recommend ensuring no
external Word is open during the run (let the scope own its own instance),
with an A/B re-run as confirmation — without blaming the document or the
output path.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored `ContractPdfExport`; `Word Application Scope` opens `data\Contract.docx`, `Save Document as PDF` → `data\out\Contract.pdf` (structurally correct, export is the sole child) |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses; `or jobs get` Info and the logs show the wrong-thread cast, with attach + mid-run-close warnings |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** Synthetic. The attended job ran on `MOCK-HOST` while
> an external Word was open; the log's attach + close warnings are the
> decisive evidence, not the workflow structure.
