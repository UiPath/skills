# Final Resolution

---

**Root Cause:** `Main.xaml` has the modern Word-pack **`Read Text`** activity
sitting **loose in the sequence**, not inside a `Use Word File` /
`Word Application Scope`. That activity has **no file input of its own** — it
reads the document held open by a surrounding container. Placed outside one,
it is invalid, so the job faults immediately with `The 'Read Text' activity
must be placed inside a 'Use Word File' or 'Word Application Scope'`.

**What went wrong:** The `ContractTextExtract` job (2026-06-16T08:05) faulted
~1 second after start with a validation error naming the `Read Text`
activity. No document was ever read — the activity is structurally invalid
without a container.

**Why:** The Word pack ships a `Read Text` that operates on the document
opened by its parent scope (the same model as `Replace Text in Document`).
It exposes an output (the extracted text) but no file path, so it cannot
stand alone. UiPath also ships a **separate** standalone `Read Text` under
`System > File > Word Document` that *does* take a file path directly — the
two look alike but are different activities.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: ContractTextExtract -- Faulted at 2026-06-16T08:05:02Z (ran ~1s)
- Folder: Doc Extract (key `e6f7a8b9-c0d1-4193-8b1c-7081920314a5`), machine MOCK-ROBOT-10
- Final error: `The 'Read Text' activity must be placed inside a 'Use Word File' or 'Word Application Scope'` -> `ReadTextInDocument "Read Text"` -> `Sequence "Main Sequence"` -> `Main.xaml`

### Project source (Root Cause)
- `Main.xaml`: the `Read Text` (`ReadTextInDocument`) node sits directly in the `Main Sequence` with only a `Text` output bound — there is **no** `Use Word File` / `Word Application Scope` wrapping it, and no file path on the activity.
- A loose Word-pack Read Text with no container is exactly the invalid configuration the error describes.

---

**Immediate fix:**

Pick the right Read Text surface for how you want to supply the file.

### Fix path A -- read from an open document (use a container)
- Wrap the read in a **`Use Word File`** container (or legacy
  `Word Application Scope`) that opens the target document, and place the
  `Read Text` activity **inside** it. The activity then reads the
  container's open document into the `Text` output.

### Fix path B -- stand-alone read by path (no container)
- Replace the Word-pack `Read Text` with the native **`Read Text`** under
  **`System > File > Word Document`**, which takes the **file path directly
  in its own properties** — no scope required.
- **Source:** `word-activities/playbooks/read-text-missing-container.md`

> This is a container/activity-surface configuration issue — the file,
> format, and Word install are not implicated (the activity never got far
> enough to touch a file).

---

**Preventive fix:**

1. **Match the Read Text surface to the design** — scoped Word-pack Read
   Text for workflows already inside a Word scope; standalone System Word
   Document Read Text for a one-off read by path.
   - **Why:** the two same-named activities have different requirements;
     mixing them up produces this validation fault.
   - **Who:** RPA developer.

2. **Resolve validation warnings before publishing** — the loose Read Text
   shows a design-time warning in Studio; fix it before deploy rather than
   discovering it as a runtime fault.
   - **Who:** RPA developer.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | The modern Word-pack Read Text is placed outside a Use Word File / Word Application Scope, so it is invalid and faults at start | High | Confirmed | Yes | Error "Read Text must be placed inside a Use Word File or Word Application Scope" + Main.xaml has Read Text loose in the sequence, no container, no file path | Nest Read Text in a Use Word File container, OR use the standalone System > File > Word Document Read Text |

---

Would you like help wrapping the read in a `Use Word File`, or switching to
the standalone `System > File > Word Document` `Read Text`?
