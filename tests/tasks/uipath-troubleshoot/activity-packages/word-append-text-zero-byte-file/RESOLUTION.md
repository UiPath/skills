# Final Resolution

---

**Root Cause:** The target document `Notes.docx` is a **0-byte file** — not a
valid OpenXML/ZIP package. A `.docx` must contain internal XML structures;
an empty file (typically created by *New → Text Document* then renaming the
extension to `.docx`, or left by a failed/truncated write) cannot be opened,
so the `Word Application Scope` faults opening it with `System.IO.InvalidDataException:
Archive file cannot be size zero` before `Append Text` runs.

**What went wrong:** The `ReportAppender` job (2026-06-17T11:05) started
Word, then faulted opening `C:\UiPath\Report Build\data\Notes.docx` with
`Archive file cannot be size zero`. The user notes the doc was created by a
teammate (likely a renamed empty text file).

**Why:** UiPath's Word engine reads `.docx` as an OpenXML ZIP archive. A
0-byte file has no archive structure at all, so the archive reader rejects it
immediately ("cannot be size zero"). The file extension alone does not make
a valid Word document.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: ReportAppender -- Faulted at 2026-06-17T11:05:05Z (~2s)
- Folder: Report Build (key `d2e3f4a5-b6c7-4193-a283-94a5b6c7d8e9`), machine MOCK-ROBOT-16
- Final error: `System.IO.InvalidDataException: Archive file cannot be size zero` opening `...\data\Notes.docx` -> `WordApplicationScope "Word Application Scope"` -> `Main.xaml`. The fault is at document open, before `Append Text`.

### Project source (context)
- `Main.xaml`: a `Word Application Scope` opens `data\Notes.docx` and appends text via `Append Text`. The activity placement is correct (Append Text is inside the scope); the failure is the invalid 0-byte input file.

---

**Immediate fix:**

The file is the problem, not the workflow structure.

### Fix path A -- delete the empty file + let UiPath create a valid one
- Delete the 0-byte `Notes.docx`, and check **Create if not exists** in the
  `Word Application Scope` properties so UiPath generates a structurally
  valid `.docx` template on the next run. (Or replace it with a real `.docx`
  saved from Word.)

### Fix path B -- fix the upstream that produced the empty file
- If the 0-byte file came from a failed/truncated download or write, fix that
  step so it writes a complete `.docx`, and add a guard (e.g. check file size
  > 0, or `Path Exists` + size) before the scope.
- **Never fabricate a `.docx` by renaming a `.txt`** — a true Word file needs
  the OpenXML package structure.
- **Source:** `word-activities/playbooks/append-text-zero-byte-file.md`

> Distinct from a *corrupt-but-non-empty* document (orphaned-lock /
> half-written), which surfaces as "the file appears to be corrupted" — see
> word-scope-file-corrupted.

---

**Preventive fix:**

1. **Never hand-create `.docx` by renaming a text file** — start from a real
   Word document or let `Create if not exists` generate one.
   - **Who:** template author / RPA developer.

2. **Guard inputs** — assert the file exists and is non-empty before opening
   it in a Word scope, so a 0-byte file fails fast with a clear message.
   - **Who:** RPA developer.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | The target .docx is a 0-byte file (not a valid OpenXML package), so opening it throws "Archive file cannot be size zero" | Medium | Confirmed | Yes | `InvalidDataException: Archive file cannot be size zero` opening Notes.docx at the scope (before Append Text) + doc hand-created by a teammate | Delete the empty file + Create if not exists, or fix the upstream write |

---

Would you like help enabling `Create if not exists` on the scope, or adding a
file-size guard before the append?
