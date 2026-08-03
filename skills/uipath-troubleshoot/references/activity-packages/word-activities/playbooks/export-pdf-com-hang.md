---
confidence: medium
---

# Export to PDF — COM Interop Hang / Crash / COMException

## Context

What this looks like:
- Activity `Export to PDF` / `Save Document as PDF` (`UiPath.Word.Activities.WordExportToPdf`) **freezes / hangs**, the job crashes, or it faults with a `System.Runtime.InteropServices.COMException`
- May be intermittent — succeeds on some runs, hangs/crashes on others

What can cause it:
- `WordExportToPdf` drives Microsoft Word via **COM Interop**. An **orphaned `WINWORD.EXE`** from a previous run left locked in memory blocks the new export, or the **input document is still open / locked** by another user, process, or a prior un-disposed scope. Word can't service the export call → hang or `COMException`.

What to look for:
- Orphaned `WINWORD.EXE` processes on the robot host (Task Manager, no visible window).
- Whether the input document is open elsewhere or held by a sync/AV client.
- Whether the surrounding `Word Application Scope` disposes cleanly on every path (an un-disposed scope leaves WINWORD.EXE behind).

## Investigation

1. Confirm the faulted activity is `Export to PDF` and capture the HRESULT if a `COMException` was thrown.
2. Ask the user (or someone with desktop access on the robot host, as the robot's Windows user) to check for orphaned `WINWORD.EXE` instances and whether the input document is open/locked elsewhere at run time.
3. Check whether prior runs left Word processes behind (a sign the scope isn't disposing).

## Resolution

- **Clear stale Word sessions** — add a **Kill Process** activity with `ProcessName = "WINWORD"` **immediately before** the Word automation / export sequence to clear hung background instances. Ensure the `Word Application Scope` disposes on every path so it doesn't orphan WINWORD.EXE. As a one-time cleanup, end stray `WINWORD.EXE` (`Stop-Process -Name WINWORD -Force`).
- **Ensure the input is free** — confirm the source document is fully closed and not locked by another user/application before exporting.
- **If COM errors persist after the above** — bypass the native activity and do the conversion in an **Invoke Code (C#)** step using Word Interop directly (import `Microsoft.Office.Interop.Word`):
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
  The `finally { wordApp.Quit(); }` guarantees Word is released even on error — addressing the orphaned-process root cause directly. Requires desktop Word installed on the host.

> Related COM failures: a modal dialog blocking Word (password / recovery / activation) → [word-scope-hangs-background-prompt.md](./word-scope-hangs-background-prompt.md); `RPC_E_SERVERCALL_RETRYLATER` busy signal → [replace-text-com-busy.md](./replace-text-com-busy.md); a startup `REGDB_E_CLASSNOTREG` (no desktop Word) → [word-scope-com-not-installed.md](./word-scope-com-not-installed.md).
