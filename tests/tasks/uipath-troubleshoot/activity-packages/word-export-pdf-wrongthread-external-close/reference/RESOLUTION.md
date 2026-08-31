# Final Resolution

---

**Root Cause:** `Word Application Scope` exposes no new-instance /
isolated-instance / attach control. A Microsoft Word (`WINWORD.EXE`) was
already running on the host when the run started, so the scope **attached to
that external instance**. The document's `_Document` COM object was therefore
owned by the external Word process's STA apartment. The user **closed that
Word window mid-run** (after the scope bound the document, before the export),
which tore down / replaced the apartment that owned the proxy. `Save Document
as PDF` then made a cross-apartment `QueryInterface` for
`Microsoft.Office.Interop.Word._Document` (IID `{0002096B-...}`) and faulted
with `System.InvalidCastException` / `0x8001010E RPC_E_WRONG_THREAD`.

`RPC_E_WRONG_THREAD` (not `0x80010108 RPC_E_DISCONNECTED`) is the signature of
a *replaced* apartment, not a clean server death — consistent with an
external Word being closed and re-marshalled rather than the Word server
simply dying.

**What went wrong:** The attended job
`b2c3d4e5-f6a7-4819-8b2c-3d4e5f607182` (`ContractPdfExport`) ran on
`MOCK-HOST` at 2026-06-19T14:22. The log shows the scope started Word, warned
it **attached to an already-running WINWORD.EXE**, opened
`data\Contract.docx`, warned the **attached Word window was closed by the
user** before the scope completed, then faulted at `Save Document as PDF`
with the wrong-thread cast.

**Why:** The export is the sole/last child of the scope that opened the
document — the workflow is structurally correct. The fault is environmental:
the document proxy was created on the external Word's apartment and that
apartment went away mid-run. This is not a bug in the export activity, the
document, or the output path.

---

**Evidence:**

### Orchestrator
- Job: `ContractPdfExport` (key `b2c3d4e5-...`) — Faulted at
  `2026-06-19T14:22:18Z` (~7s), Manual/Attended, machine `MOCK-HOST`, user
  `MOCK-HOST\analyst`.
- Folder: `Contracts` (key `a1b2c3d4-e5f6-4708-9a1b-2c3d4e5f6071`).
- Warning log: `[Word Application Scope] A Microsoft Word instance was
  already running on the host; the scope attached to the existing
  WINWORD.EXE`.
- Warning log: `[Word Application Scope] The attached Microsoft Word window
  was closed by the user before the scope completed.`
- Final error: `System.InvalidCastException: Unable to cast COM object ...
  Microsoft.Office.Interop.Word._Document ... IID
  '{0002096B-0000-0000-C000-000000000046}' ... marshalled for a different
  thread. (0x8001010E (RPC_E_WRONG_THREAD))` → `WordExportToPdf "Save
  Document as PDF"` → `WordApplicationScope` → `Main.xaml`.

### Project source (context)
- `Main.xaml`: `Word Application Scope` opens `data\Contract.docx`; `Save
  Document as PDF` to `data\out\Contract.pdf` is the **sole child** of that
  scope. No `Parallel`/`Pick`/`Invoke`/coded thread between scope-open and
  export — the workflow structure is correct, confirming an environmental
  (external-Word) cause.

### Cross-check — what this is NOT
- Not `RPC_E_DISCONNECTED` (0x80010108): the HRESULT is `RPC_E_WRONG_THREAD`,
  a replaced apartment, not a dead server.
- Not the orphaned/busy-WINWORD COM-hang (`RPC_E_CALL_REJECTED` 0x80010001):
  different HRESULT, different cause.
- Not a bad output path/document: the export is structurally fine and the
  error is a COM cast, not an I/O or document error.

---

**Immediate fix:**

The user is on the host (attended). The fix is procedural + a confirming
re-run.

1. **Ensure no external Word is open during the run.** Close all Microsoft
   Word (`WINWORD.EXE`) windows before the automation runs, and do not open or
   close Word on the host while it runs — let `Word Application Scope` own its
   own Word instance. (The scope has no isolated-instance setting, so it will
   always reuse a running Word.)
2. **Confirm with an A/B re-run:**
   - Trial A — open Word manually, let the scope attach, then close that Word
     window before the export → expect the `RPC_E_WRONG_THREAD` error.
   - Trial B — no external Word open → expect success.
   Error only in Trial A confirms the attach / mid-run-close cause.
3. **If the export must run while Word may be open (or unattended):** migrate
   the document-to-PDF step to the **System Word** activities (background, no
   Word UI, no shared interop instance), which remove the dependency on an
   interactive/external Word.
   - **Source:** `word-activities/playbooks/word-export-pdf-com-wrong-thread.md`

---

**Preventive fix:**

1. **Don't share the host's interactive Word with the robot.** On machines
   that run this automation, ensure no user has Word open during the run
   window; avoid attended runs that share the desktop's Word session.
   - **Who:** RPA developer + machine owner.
2. **Prefer System Word for unattended document export** so the path never
   depends on an external interactive Word instance.
   - **Who:** RPA developer.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Word Application Scope attached to an already-open external WINWORD.EXE that closed mid-run, replacing the STA apartment owning the _Document proxy → RPC_E_WRONG_THREAD | Medium | Confirmed | Yes | `0x8001010E RPC_E_WRONG_THREAD` casting to `_Document` (IID `{0002096B-...}`) at Save Document as PDF + "attached to already-running WINWORD" + "attached Word window closed by user" warnings; workflow structurally correct | Ensure no external Word open during the run (let the scope own its instance); A/B re-run to confirm; migrate to System Word for unattended/while-open export |

---

Would you like help adding a guard that fails fast if a `WINWORD.EXE` is
already running, or converting the export to the System Word (background)
activities?
