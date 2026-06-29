# Final Resolution

---

**Root Cause:** The `Use Word File` scope in `Main.xaml` has **Auto Save
enabled** and edits the **same shared file** (`MasterContract.docx`) on
every iteration of the `For Each recipient` loop. Auto Save persists the
file while the next iteration is already opening/holding it, so the save
races another access and faults with
`System.IO.IOException: The process cannot access the file
'...MasterContract.docx' because it is being used by another process`. The
first iteration succeeds; the overlap on the second trips the lock.

**What went wrong:** The `ContractMerge` job (started
2026-06-14T13:30:02Z) opened the document and Auto-Saved it on iteration 1,
then opened it again on iteration 2 and faulted with the IOException at
`Replace Text in Document` inside `Use Word File` inside the `For Each`
loop. The per-iteration logs (`Iteration 1: Auto Save writing ...` ->
`Iteration 2: opened ...` -> IOException) show the save-vs-access race on
one shared file.

**Why:** With `Auto Save` on, the `Use Word File` scope writes the document
on each iteration. Because every iteration targets the same file path,
iteration N's save can still be in progress (or the handle not fully
released) when iteration N+1 opens it, so Word/the OS reports the file as
in use. The "works once, then dies" pattern is characteristic of an
Auto-Save-in-a-loop lock on a shared file — not a corrupt document, a
missing install, or a wrong path.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: ContractMerge -- Faulted at 2026-06-14T13:30:09.450Z (ran ~6.7s)
- Job type: Unattended, Queue-triggered, machine MOCK-ROBOT-06
- Folder: Contracts Batch (key `e6f7a8b9-c0d1-4193-2e3f-405162738495`)
- Per-iteration logs: `Iteration 1: Auto Save writing 'data\MasterContract.docx'` -> `Iteration 2: opened 'data\MasterContract.docx'` -> IOException
- Final error: `System.IO.IOException: The process cannot access the file '...MasterContract.docx' because it is being used by another process` -> `ReplaceTextInDocument` -> `WordApplicationCard "Use Word File"` -> `ForEach<String>` -> `Main.xaml`

### Project source (Root Cause)
- `Main.xaml`: the `Use Word File` (`WordApplicationCard`) has `AutoSave="True"` and `FilePath="data\MasterContract.docx"`, and sits inside `For Each recipient` - so the same file is opened, edited, and Auto-Saved on every iteration.
- The loop over a single shared path with Auto Save on is the structural cause of the save-vs-access race.

---

**Immediate fix:**

The lock is self-inflicted by Auto Save + the loop on one shared file. Any
of the following resolves it.

### Fix path A -- uncheck Auto Save (simplest)
- In the `Use Word File` properties, **uncheck Auto Save** so the document
  is written once on scope exit instead of continuously per iteration,
  removing the save-vs-next-open race.

### Fix path B -- write a distinct file per iteration
- Build a per-recipient output path with `Path.Combine` (e.g.
  `...\Output\Contract_<recipient>.docx`) and edit that, leaving the shared
  template untouched - no two iterations contend for the same file.

### Fix path C -- ensure no concurrent accessor
- If something else also opens `MasterContract.docx` during the run (a
  second job, sync/AV client, an interactive window), stop it; clear any
  orphaned `WINWORD.EXE` and the read-only attribute if set.
- **Source:** `word-activities/playbooks/replace-text-file-locked.md`

> The document is not corrupt and Word is installed - do not recreate the
> file or reinstall. The fix is the Auto-Save-in-a-loop save contention.

---

**Preventive fix:**

1. **Don't Auto Save a shared file in a loop** -- either disable Auto Save
   (write once on exit) or write a distinct output file per iteration.
   - **Why:** continuous saves on one shared path race the next access and
     intermittently lock.
   - **Who:** RPA developer.

2. **Open the scope once outside the loop when possible** -- if all
   iterations edit the same document, structure the workflow to open it
   once and write at the end, rather than re-entering the scope per item.
   - **Who:** RPA developer.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Use Word File with Auto Save edits the same shared file every loop iteration, so a save races the next iteration's access and faults with IOException | Medium | Confirmed | Yes | `IOException: being used by another process` at ReplaceTextInDocument inside Use Word File inside For Each + `AutoSave="True"` on a single shared FilePath + "first item works then dies" + per-iteration Auto Save / re-open logs | Uncheck Auto Save, or write a distinct output path per iteration, or clear the concurrent accessor |

---

Would you like help editing the workflow to disable Auto Save or write a
per-recipient output file, or the exact host checks for a concurrent
accessor on MOCK-ROBOT-06?
