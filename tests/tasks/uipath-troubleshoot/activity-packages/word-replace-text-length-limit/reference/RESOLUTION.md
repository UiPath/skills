# Final Resolution

---

**Root Cause:** The classic `Replace Text` (`WordReplaceText`) activity in
`Main.xaml` enforces a hard **256-character limit** on its `Search` /
`Replace` inputs. The replacement clause bound to `Replace` exceeds 256
characters, so the activity faults with
`System.ArgumentException: Value cannot be longer than 256 characters.
(Parameter 'Replace')`. Shorter clauses pass because they are under the
cap; the longer one trips the limit.

**What went wrong:** The `TermsLetterGen` job (started
2026-06-13T11:40:02Z) opened the template, then faulted at the
`Replace Text` activity with the 256-character `ArgumentException` on the
`Replace` parameter. The project pins an older `UiPath.Word.Activities`
version (`[1.7.0]`) where the limit applies.

**Why:** Classic versions of `Replace Text` validate the input strings
against a 256-character maximum before passing them to Word. Any `Search`
or `Replace` value longer than 256 characters is rejected with
`ArgumentException` (older builds truncate silently instead). The limit is
a package-version constraint, not a Word or document problem — the template
opened fine and the fault is purely in the substitution input.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: TermsLetterGen -- Faulted at 2026-06-13T11:40:05.910Z (ran ~3.6s)
- Job type: Unattended, Queue-triggered, machine MOCK-ROBOT-04
- Folder: Mail Merge (key `d0e1f2a3-b4c5-4193-d7e8-f90124354607`)
- Logs: `Starting Microsoft Word` -> `Document 'data\TermsTemplate.docx' opened` -> error. The document opened successfully; the fault is at the substitution.
- Final error: `System.ArgumentException: Value cannot be longer than 256 characters. (Parameter 'Replace')` -> `WordReplaceText "Replace Text"` -> `WordApplicationScope` -> `Main.xaml`

### Project source (Root Cause)
- `Main.xaml`: the `Replace Text` (`WordReplaceText`) activity's `Replace` is bound to a long clause variable; `Search` is `[TermsPlaceholder]`.
- `project.json` pins `"UiPath.Word.Activities": "[1.7.0]"` - a classic version that enforces the 256-character input cap.
- The error names the `Replace` parameter specifically, confirming the long replacement value, not the search term, tripped the limit.

---

**Immediate fix:**

Either path resolves it; pick based on whether the package can be upgraded.

### Fix path A -- upgrade the package (preferred)
- Open `Manage Packages` in Studio, update `UiPath.Word.Activities` to the
  latest version (the 256-character limit is relaxed in current releases),
  rebuild, and re-publish. Re-pin the new version in `project.json`.

### Fix path B -- substitute in code (if the package cannot be upgraded)
- Read the document text into a `String`, perform the substitution with
  `myString.Replace("[TermsPlaceholder]", termsClause)` (or a regex) in an
  `Assign`, and write the result back. String/regex replacement has no
  256-character cap.
- **Source:** `word-activities/playbooks/replace-text-length-limit.md`

> The template and the document are fine - do not edit document content or
> the file path. The fix is the activity's input-length constraint.

---

**Preventive fix:**

1. **Keep activity packages current** -- track `UiPath.Word.Activities`
   versions; the classic 256-char cap is a legacy constraint removed in
   current releases.
   - **Who:** RPA developer.

2. **Guard long substitutions** -- when replacement text can be arbitrarily
   long (clauses, paragraphs), prefer string/regex manipulation over the
   activity's bounded inputs.
   - **Who:** RPA developer.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | The replacement clause exceeds the classic Replace Text 256-character input limit, so the activity throws ArgumentException | High | Confirmed | Yes | `ArgumentException: Value cannot be longer than 256 characters. (Parameter 'Replace')` at WordReplaceText + older UiPath.Word.Activities [1.7.0] + shorter clauses work | Upgrade UiPath.Word.Activities, or substitute via String.Replace / regex in code |

---

Would you like help upgrading the package and re-pinning `project.json`, or
converting the substitution to an in-code `String.Replace` / regex step?
