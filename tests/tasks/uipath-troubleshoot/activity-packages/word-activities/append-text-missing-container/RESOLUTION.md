# Final Resolution

---

**Root Cause:** `Main.xaml` has the App-Integration **`Append Text`**
(`WordAppendText`) activity **loose in the sequence**, not inside a
`Word Application Scope` / `Use Word File`. That activity has **no file input
of its own** — it appends to the document held open by a surrounding
container. Placed outside one, it is invalid, so the job faults at start
with `Activity is valid only inside WordApplicationScope`.

**What went wrong:** The `AppendNotes` job (2026-06-17T10:20) faulted ~1
second after start with a validation error naming the `Append Text`
activity. No document was touched — the activity is structurally invalid
without a container.

**Why:** The Word pack ships an App-Integration `Append Text` that operates
on the document opened by its parent scope (same model as `Replace Text in
Document` / the Word-pack `Read Text`). It has a `Text` input but no file
path, so it cannot stand alone. A **separate** standalone `Append Text`
under the **Word Document** category *does* take a file path directly — the
two look alike but are different activities.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: AppendNotes -- Faulted at 2026-06-17T10:20:02Z (~1s)
- Folder: Doc Append (key `b0c1d2e3-f4a5-4193-8061-728394a5b6c7`), machine MOCK-ROBOT-15
- Final error: `UiPath.Word.Activities.WordException: Activity is valid only inside WordApplicationScope` -> `WordAppendText "Append Text"` -> `Sequence "Main Sequence"` -> `Main.xaml`.

### Project source (Root Cause)
- `Main.xaml`: the `Append Text` (`WordAppendText`) node sits directly in the `Main Sequence` with only a `Text` value bound — there is **no** `Word Application Scope` / `Use Word File` wrapping it, and no file path on the activity.

---

**Immediate fix:**

Pick the right Append Text surface for how you want to supply the file.

### Fix path A -- append to an open document (use a scope)
- Wrap the append in a **`Word Application Scope`** (or `Use Word File`) that
  opens the target document, and place the `Append Text` activity **inside
  its Do body**. The activity then appends to the container's open document.

### Fix path B -- append by path (no scope, no Word install)
- Replace the App-Integration `Append Text` with the standalone **`Append
  Text`** under the **Word Document** category, which takes the **file path
  directly** in its own properties — no container required.
- **Source:** `word-activities/playbooks/append-text-missing-container.md`

> This is a container/activity-surface configuration issue — the file, the
> document, and the Word install are not implicated (the activity never got
> far enough to touch a file).

---

**Preventive fix:**

1. **Match the Append Text surface to the design** — App-Integration Append
   Text (scoped) for workflows inside a Word scope; standalone Word Document
   Append Text for a one-off append by path.
   - **Who:** RPA developer.

2. **Resolve validation warnings before publishing** — the loose Append Text
   shows a design-time warning in Studio; fix it before deploy.
   - **Who:** RPA developer.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | The App-Integration Append Text is placed outside a Word Application Scope, so it is invalid and faults at start | High | Confirmed | Yes | Error "Activity is valid only inside WordApplicationScope" + Main.xaml has Append Text loose in the sequence, no container, no file path | Nest Append Text in a Word Application Scope, OR use the standalone Word Document Append Text |

---

Would you like help wrapping the append in a `Word Application Scope`, or
switching to the standalone `Word Document` `Append Text`?
