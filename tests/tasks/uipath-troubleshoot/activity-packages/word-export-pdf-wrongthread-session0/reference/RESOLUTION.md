# Final Resolution

---

**Root Cause:** Word COM interop requires an **interactive STA session**. The
`NightlyReportPdf` job ran **unattended in Session 0** (non-interactive). The
worker thread that executed `Save Document as PDF` is therefore not an
interactive STA that can own the document's `_Document` COM object, so the
cross-apartment `QueryInterface` for
`Microsoft.Office.Interop.Word._Document` (IID `{0002096B-...}`) failed with
`System.InvalidCastException` / `0x8001010E RPC_E_WRONG_THREAD`.

There is **no** external `WINWORD.EXE` involved here (no attach / mid-run-close
warning in the log) — the run surface itself is the cause.

**What went wrong:** The scheduled unattended job
`d4e5f6a7-b8c9-4a2b-8d4e-5f6071829304` ran at 2026-06-19T02:00 on
`MOCK-HOST` as `UIPATH\SVC_ROBOT`. The log notes execution started
`Unattended, Session 0, non-interactive`, the scope started Word and opened
`data\Report.docx`, then `Save Document as PDF` faulted with the wrong-thread
cast. The job's `RuntimeType` is `Unattended` and `RequiresUserInteraction`
is `false` (a background process).

**Why:** `WordExportToPdf` drives Microsoft Word via COM Interop, which is
only valid on an interactive STA. An unattended robot in Session 0 (or a
background process) has no interactive desktop session, so the document proxy
cannot be marshalled to the executing thread. The workflow is structurally
correct — the export is the sole child of the scope that opened the document
— so this is a runtime-surface problem, not a code/path/document defect.

---

**Evidence:**

### Orchestrator
- Job: `NightlyReportPdf` (key `d4e5f6a7-...`) — Faulted at
  `2026-06-19T02:00:10Z` (~6s), Schedule-triggered, **Unattended**, machine
  `MOCK-HOST`, account `UIPATH\SVC_ROBOT`.
- `RuntimeType: Unattended`, `RequiresUserInteraction: false`.
- Folder: `Reports` (key `c3d4e5f6-a7b8-491a-9c3d-4e5f60718293`).
- Log: `Execution started (Unattended, Session 0, non-interactive)`; no
  external-Word warning.
- Final error: `System.InvalidCastException: Unable to cast COM object ...
  Microsoft.Office.Interop.Word._Document ... IID
  '{0002096B-0000-0000-C000-000000000046}' ... marshalled for a different
  thread. (0x8001010E (RPC_E_WRONG_THREAD))` → `WordExportToPdf "Save
  Document as PDF"` → `WordApplicationScope` → `Main.xaml`.

### Project source (context)
- `Main.xaml`: `Word Application Scope` opens `data\Report.docx`; `Save
  Document as PDF` to `data\out\Report.pdf` is the **sole child** of the
  scope. No `Parallel`/`Pick`/`Invoke`/coded thread between scope-open and
  export — structure is correct.
- `project.json`: `isAttended: false`, `requiresUserInteraction: false` — a
  background process, consistent with a non-interactive Session-0 run.

### Cross-check — what this is NOT
- Not the external-attach / mid-run-close cause: no "Word already running" /
  "attached Word closed" warning; the run is unattended with no interactive
  user.
- Not a non-creator-thread (Parallel/Pick/Invoke) issue: the export is nested
  directly in the scope with no threading construct between them.
- Not `RPC_E_DISCONNECTED` / `RPC_E_CALL_REJECTED`: the HRESULT is
  `RPC_E_WRONG_THREAD`.
- Not a bad output path/document: the error is a COM cast, not I/O.

---

**Immediate fix:**

Word interop needs an interactive STA. Two supported paths:

1. **Run the automation in an interactive session.** Switch the process to
   **attended**, or run the unattended robot in an interactive
   (auto-logged-in) desktop session rather than Session 0 / background, so
   `Word Application Scope` has an interactive STA to own the document.
2. **Migrate the export to the System Word (background) activities.** The
   System Word group processes documents without opening the Word UI or
   sharing an interop instance, removing the dependency on an interactive
   STA — the correct path for genuinely unattended export. Verify the System
   Word group covers the document-to-PDF step before migrating.
   - **Source:** `word-activities/playbooks/word-export-pdf-com-wrong-thread.md`

---

**Preventive fix:**

1. **Don't run interop Word activities unattended in Session 0.** Reserve
   `Word Application Scope` / `Save Document as PDF` for attended/interactive
   runs; use System Word for unattended pipelines.
   - **Who:** RPA developer + automation scheduler owner.
2. **Gate at design time:** flag interop Word usage in unattended processes
   during review.
   - **Who:** RPA reviewer.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Save Document as PDF ran off the interactive STA on an unattended Session-0 / background runtime, so the _Document proxy could not be marshalled to the worker thread → RPC_E_WRONG_THREAD | Medium | Confirmed | Yes | `0x8001010E RPC_E_WRONG_THREAD` casting to `_Document` (IID `{0002096B-...}`); job `Unattended` / `RequiresUserInteraction: false`; log "Session 0, non-interactive"; no external-Word warning; workflow structurally correct | Run attended/interactive STA, or migrate the export to System Word (background) activities |

---

Would you like help converting the export to the System Word (background)
activities, or reconfiguring the process to run in an interactive session?
