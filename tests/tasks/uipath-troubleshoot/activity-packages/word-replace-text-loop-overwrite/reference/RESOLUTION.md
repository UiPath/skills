# Final Resolution

---

**Root Cause:** The `For Each recipient` loop's `Use Word File` scope points
at the template `OfferTemplate.docx` and edits it **in place** every
iteration (with `Auto Save` on, no per-iteration copy). Iteration 1 replaces
`[Name]` and saves — so the placeholder **no longer exists in the file**.
Iterations 2+ open the already-mutated template, find **0 occurrences** of
`[Name]`, and leave it unchanged. The job completes **Successfully** (0
matches is not an error), but every letter after the first still shows the
literal `[Name]`.

**What went wrong:** The `BulkOfferLetters` job (2026-06-15T08:10) ran green
(State=Successful, no error logs). The per-iteration trace is the tell:
`Iteration 1: Replaced 1 occurrence(s) of '[Name]'` → `Iteration 2: Replaced
0 occurrence(s)` → `Iteration 3: Replaced 0 occurrence(s)`. The first row
consumed the placeholder; the rest had nothing to replace.

**Why:** The workflow treats the template as a mutable working file. Because
all iterations open and save the **same** path, the first replacement is
persisted into the template, destroying the placeholder for every later row.
This is template mutation across iterations — distinct from a run-split
placeholder (which fails on row 1 too) or an Auto-Save file lock (which
throws `IOException`).

---

**Evidence:**

### Orchestrator (Propagation)
- Job: BulkOfferLetters -- **Successful** at 2026-06-15T08:10:12Z; no faulted jobs in the folder; `or jobs logs --level Error` is empty
- Folder: Bulk Letters (key `f0a1b2c3-d4e5-4193-8607-1a2b3c4d5e6f`), machine MOCK-ROBOT-07
- Per-iteration trace: `Replaced 1 occurrence(s)` (iter 1) → `Replaced 0 occurrence(s)` (iter 2, 3). The 1→0 pattern is the signal.

### Project source (Root Cause)
- `Main.xaml`: `For Each recipient` → `Use Word File` (`WordApplicationCard`) with `FilePath="data\OfferTemplate.docx"` and `AutoSave="True"`, containing `Replace Text in Document` (`Search="[Name]"`). There is **no Copy File** — the template is opened and saved in place every iteration.
- The single shared template path + in-place save is the structural cause of the placeholder being consumed after row 1.

---

**Immediate fix:**

Treat the template as read-only and start each row from a clean copy.

### Workflow fix
1. At the **start of each loop iteration**, add a `Copy File` activity that
   copies the template to a **fresh temporary output path** unique per row
   (e.g. `Path.Combine(outputDir, "Offer_" + recipient + ".docx")`).
2. Point the `Use Word File` / `Word Application Scope` at **that temporary
   file**, not the template. Each row then starts from an unmodified
   template with the `[Name]` placeholder intact.
3. Leave `OfferTemplate.docx` untouched (read-only).
- **Source:** `word-activities/playbooks/replace-text-loop-template-overwrite.md`

> The job being **Successful is misleading** — 0 matches on rows 2+ is not an
> error. Validate the per-row output documents (or assert the placeholder is
> gone in each), don't rely on the green job state.

---

**Preventive fix:**

1. **Never edit a source template in place in a loop** — copy to a fresh
   per-iteration file and edit the copy.
   - **Why:** the first replacement consumes the placeholder for all later
     rows.
   - **Who:** RPA developer.

2. **Assert per-row output** — after each iteration, verify the placeholder
   was replaced so a 0-match becomes a visible failure, not a green-but-wrong
   run.
   - **Who:** RPA developer.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | The loop edits the template in place, so iteration 1 consumes the [Name] placeholder and later rows replace nothing | Medium | Confirmed | Yes | Job Successful + no error logs + per-iteration "Replaced 1" then "Replaced 0" + Use Word File on the template path with AutoSave, no Copy File | Copy the template to a fresh temp file per iteration; edit the copy, keep the template read-only |

---

Would you like help editing the workflow to add the per-iteration Copy File
and point the scope at the temporary document?
