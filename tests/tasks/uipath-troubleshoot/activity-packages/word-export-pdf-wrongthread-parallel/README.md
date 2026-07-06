# Save Document as PDF — COM Wrong-Thread (Non-Creator Thread / Parallel)

This scenario reproduces a `Save Document as PDF` (`WordExportToPdf`) COM
failure that faults casting the document to
`Microsoft.Office.Interop.Word._Document` with
`0x8001010E RPC_E_WRONG_THREAD`. A **`Parallel`** activity between
scope-open and the export runs the export on a worker thread that is **not**
the STA that created the document.

## What this scenario uncovers

**Root Cause:** The `_Document` COM proxy is valid only on the apartment/thread
that created it (the thread `Word Application Scope` opened the document on).
The workflow nests `Save Document as PDF` inside a `Parallel` activity, so the
export executes on a different (non-creator) thread; its cross-apartment
`QueryInterface` for `_Document` fails with `RPC_E_WRONG_THREAD`. The run is
attended/foreground with no external Word — the cause is the threading
construct in the workflow source, visible both in `Main.xaml` and in the
stack trace (`at Parallel "Parallel — export + audit log"`).

This maps to:
`references/activity-packages/word-activities/playbooks/word-export-pdf-com-wrong-thread.md`

The correct agent behavior is to tie `RPC_E_WRONG_THREAD` + the IID
`{0002096B-...}` (`_Document`) to the `Parallel`/non-creator-thread cause
(reading the `Parallel` in `Main.xaml` and/or the stack frame), and recommend
moving the export onto the same thread/scope that opened the document (remove
the `Parallel` around the export) — without blaming the document or the
output path.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored `BulkDocPdf`; `Word Application Scope` opens `data\Invoice.docx`, with a `Parallel` inside the scope body whose branch runs `Save Document as PDF` → `data\out\Invoice.pdf` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses; `or jobs get` Info and the logs show the wrong-thread cast with a `Parallel` frame in the stack |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** Synthetic. The decisive evidence is the `Parallel`
> wrapping the export in `Main.xaml` (mirrored by the `Parallel` frame in the
> stack trace), on an attended run with no external Word — isolating the
> non-creator-thread cause.
