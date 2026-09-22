# Final Resolution

---

**Root Cause:** The `_Document` COM proxy that `Word Application Scope`
creates is valid only on the STA/thread that opened the document. The
workflow nests `Save Document as PDF` inside a **`Parallel`** activity, so the
export executes on a worker thread that is **not** the scope-creator thread.
Its cross-apartment `QueryInterface` for
`Microsoft.Office.Interop.Word._Document` (IID `{0002096B-...}`) fails with
`System.InvalidCastException` / `0x8001010E RPC_E_WRONG_THREAD`.

**What went wrong:** The attended job
`f6a7b8c9-d0e1-4c4d-8f60-718293041526` (`BulkDocPdf`) ran on `MOCK-HOST` at
2026-06-19T10:05. The scope opened `data\Invoice.docx`, then the `Parallel`
dispatched the export on a non-creator thread, which faulted with the
wrong-thread cast. The stack trace shows the frame `at Parallel "Parallel —
export + audit log"` between `WordExportToPdf` and `WordApplicationScope`,
and `Main.xaml` confirms the `Parallel` wraps the export.

**Why:** Word interop is thread-affine. Running a child of `Word Application
Scope` on a different thread than the one that created the document
(`Parallel`/`Pick`/async/`Invoke Code`/coded `.cs`) marshals the proxy across
a foreign apartment and faults. The run is attended/foreground and there is
no external Word — so this is neither the external-attach/mid-run-close cause
nor the off-STA/Session-0 cause; it is the in-workflow threading construct.

---

**Evidence:**

### Orchestrator
- Job: `BulkDocPdf` (key `f6a7b8c9-...`) — Faulted at
  `2026-06-19T10:05:27Z` (~6s), Manual/Attended, machine `MOCK-HOST`, user
  `MOCK-HOST\operator`.
- Folder: `DocOps` (key `e5f6a7b8-c9d0-4b3c-9e5f-607182930415`).
- Final error: `System.InvalidCastException: Unable to cast COM object ...
  Microsoft.Office.Interop.Word._Document ... IID
  '{0002096B-0000-0000-C000-000000000046}' ... marshalled for a different
  thread. (0x8001010E (RPC_E_WRONG_THREAD))`.
- Stack frames (decisive): `at WordExportToPdf "Save Document as PDF"` →
  **`at Parallel "Parallel — export + audit log"`** → `at
  WordApplicationScope "Word Application Scope"` → `Main.xaml`.

### Project source (decisive)
- `Main.xaml`: inside `Word Application Scope.Body`, a `Parallel` activity
  ("Parallel — export + audit log") contains `Save Document as PDF`
  (`WordExportToPdf`) in one branch and a `Log Message` in another. The
  export therefore runs on a Parallel worker thread, not the scope-creator
  thread that opened `data\Invoice.docx`.

### Cross-check — what this is NOT
- Not the external-attach / mid-run-close cause: no "Word already running" /
  "attached Word closed" warning; the wrong-thread comes from the in-workflow
  `Parallel`, evidenced by the stack frame.
- Not the off-STA / Session-0 cause: the run is attended/foreground
  (`MOCK-HOST\operator`), not unattended Session 0.
- Not `RPC_E_DISCONNECTED` / `RPC_E_CALL_REJECTED`: the HRESULT is
  `RPC_E_WRONG_THREAD`.
- Not a bad output path/document: the error is a COM cast, not I/O.

---

**Immediate fix:**

Keep the Word interop work on the thread that owns the document.

1. **Move `Save Document as PDF` out of the `Parallel`** so it runs on the
   same thread/scope that opened the document. Run the export sequentially as
   a direct child of `Word Application Scope` (the audit `Log Message` can
   stay in the scope sequence, before or after the export). Re-run; the
   wrong-thread cast no longer occurs.
2. **General rule:** never place a child of `Word Application Scope`
   (`Save Document as PDF`, `Replace Text`, `Read Text`, …) inside a
   `Parallel`/`Pick`/`Invoke Code`/coded thread relative to the scope-open —
   Word interop is thread-affine.
   - **Source:** `word-activities/playbooks/word-export-pdf-com-wrong-thread.md`

---

**Preventive fix:**

1. **Don't parallelize Word interop activities.** If parallelism is needed
   for throughput, parallelize at the document/job level (separate scopes per
   thread), never share one scope's `_Document` across threads.
   - **Who:** RPA developer.
2. **Review gate:** flag any `Word Application Scope` child nested under
   `Parallel`/`Pick`/`Invoke` during code review.
   - **Who:** RPA reviewer.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Save Document as PDF runs inside a Parallel, on a non-creator thread, so the _Document proxy is accessed off the STA that created it → RPC_E_WRONG_THREAD | Medium | Confirmed | Yes | `0x8001010E RPC_E_WRONG_THREAD` casting to `_Document` (IID `{0002096B-...}`); stack frame `at Parallel "Parallel — export + audit log"`; `Main.xaml` nests the export in a Parallel; attended run, no external Word | Move the export out of the Parallel onto the scope-creator thread; never parallelize Word interop children |

---

Would you like help refactoring the workflow to run the export sequentially
inside the scope (removing the Parallel)?
