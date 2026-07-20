# Final Resolution

---

**Root Cause:** An **orphaned `WINWORD.EXE`** (a Word instance already
running on the host when the scope started) blocked the `Export to PDF`
COM call, which faulted with `System.Runtime.InteropServices.COMException:
The call was rejected by callee (0x80010001 RPC_E_CALL_REJECTED)`. The
intermittency — "re-running sometimes works" — confirms a transient
busy/locked Word state, not a workflow defect.

**What went wrong:** The scheduled `BatchPdfConvert` job (2026-06-17T06:00)
logged `Starting Microsoft Word`, then warned `A Microsoft Word instance was
already running on the host when the scope started`, opened the document,
and faulted at `Export to PDF` with the COM `RPC_E_CALL_REJECTED`. Because
the failure depends on whether Word is busy at the moment of the export
call, it reproduces only sometimes.

**Why:** `WordExportToPdf` drives Microsoft Word via COM Interop. When a
stale `WINWORD.EXE` from a prior run (or a scope that didn't dispose) is
still in memory, or the input document is locked, the export call is
rejected with `RPC_E_CALL_REJECTED` / similar HRESULTs. A scheduled job that
overlaps or leaves Word orphaned is the classic source.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: BatchPdfConvert -- Faulted at 2026-06-17T06:00:09Z (~6s), Schedule-triggered, machine MOCK-HOST
- Folder: Batch PDF (key `e7f8a9b0-c1d2-4193-de4f-5061728394a5`)
- Warning log: `[Word Application Scope] A Microsoft Word instance was already running on the host when the scope started.`
- Final error: `COMException: The call was rejected by callee. (Exception from HRESULT: 0x80010001 (RPC_E_CALL_REJECTED))` -> `WordExportToPdf "Export to PDF"` -> `WordApplicationScope` -> `Main.xaml`.

### Project source (context)
- `Main.xaml`: a `Word Application Scope` opens `data\Contract.docx` and exports to `data\out\Contract.pdf` (valid `.pdf` path, output folder present). The output path is fine — the failure is the COM call, consistent with the "Word already running" warning + intermittency.

---

**Immediate fix:**

The agent can't change the robot host. Hand the user the workflow change
and host checks.

### Workflow fix
1. Add a **Kill Process** activity with `ProcessName = "WINWORD"`
   **immediately before** the Word automation / export sequence to clear
   hung background instances. Ensure the `Word Application Scope` disposes on
   every path so it doesn't orphan WINWORD.EXE.
2. **If COM errors persist** after that, bypass the native activity with an
   **Invoke Code (C#)** export using Word Interop directly (import
   `Microsoft.Office.Interop.Word`):
   ```csharp
   // Arguments: argInputFile (String), argOutputFile (String)
   var wordApp = new Microsoft.Office.Interop.Word.Application();
   try {
       var doc = wordApp.Documents.Open(argInputFile);
       doc.ExportAsFixedFormat(argOutputFile, Microsoft.Office.Interop.Word.WdExportFormat.wdExportFormatPDF);
       doc.Close(false);
   }
   finally {
       wordApp.Quit();
   }
   ```
   The `finally { wordApp.Quit(); }` guarantees Word is released even on error.

### Host checks (Batch PDF / MOCK-HOST, as the robot's Windows user)
- Look for orphaned `WINWORD.EXE` instances (Task Manager / `Stop-Process -Name WINWORD -Force`).
- Confirm the input document isn't open/locked by another user/process; avoid overlapping schedules on the same host.
- **Source:** `word-activities/playbooks/export-pdf-com-hang.md`

---

**Preventive fix:**

1. **Always dispose Word scopes + avoid overlap** so no orphaned WINWORD.EXE
   lingers between scheduled runs; consider Kill Process WINWORD at the start
   of the workflow.
   - **Who:** RPA developer + scheduler owner.

2. **Make COM operations resilient** — wrap the export in a Retry Scope, or
   use the Invoke Code path with a guaranteed `Quit()` for batch conversion.
   - **Who:** RPA developer.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | An orphaned/busy WINWORD.EXE blocked the Export to PDF COM call (RPC_E_CALL_REJECTED) | Medium | Confirmed | Yes | `COMException 0x80010001 RPC_E_CALL_REJECTED` at WordExportToPdf + "Word already running on the host" warning + intermittent ("re-running sometimes works") | Kill Process WINWORD before the scope (+ dispose), ensure input free; persistent → Invoke Code C# ExportAsFixedFormat fallback |

---

Would you like help adding the Kill Process step (+ Retry Scope), or
converting the export to the Invoke Code `ExportAsFixedFormat` approach?
