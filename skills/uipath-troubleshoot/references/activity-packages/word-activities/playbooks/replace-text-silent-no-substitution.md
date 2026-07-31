---
confidence: medium
---

# Replace Text in Document — Placeholder Not Replaced (No Error, No Change)

## Context

What this looks like:
- Activity `Replace Text in Document` / `Replace Text` runs and the job **succeeds with no exception**, but the placeholder (e.g. `[Name]`, `{{Customer}}`) is left untouched in the output document
- Re-running does not help; the search term visibly matches the template text by eye

What can cause it:
- Word stores text as runs in its internal XML. A placeholder that was **typed, then partially edited (backspaced, retyped, or reformatted) in place** gets split across multiple runs. The displayed text reads `[Name]`, but in the XML it is fragmented (e.g. `[Na` + `me]`), so the activity's exact-string search never matches the contiguous term
- A formatting change mid-placeholder (bold on one character, a different font) also splits the run

What to look for:
- Whether the placeholder was edited in place in the template (a tell: it was typed with corrections).
- Whether part of the placeholder carries different formatting from the rest.

> **Workflow-source guard:** in workflow XAML, an activity attribute value wrapped in square brackets (e.g. `Replace="[employeeName]"`) is an **expression binding** to a variable — correct configuration, not a defect. Never report it as a bug and never propose removing the brackets; stripping them converts the binding into the literal text and BREAKS a working workflow. The defect in this failure class lives in the Word template's XML runs, not in the activity's property syntax.

## Investigation

1. Confirm the activity reports success and the `Search` value exactly matches the on-screen placeholder (character-for-character, including brackets and case).
2. Inspect the template: select the whole placeholder and check the formatting is uniform across every character. If unsure, inspect the document XML (`.docx` → rename to `.zip` → `word/document.xml`) and look for the placeholder split across multiple `<w:t>` runs.

## Resolution

- **If the placeholder is split across runs** — in the Word template, fully highlight the placeholder, delete it, and **retype it in one continuous motion** without backspaces or mid-word formatting changes, so it lands in a single run. Save the template and re-run.
- **Make templates robust** — author placeholders by typing them cleanly once (or paste as plain text), keep uniform formatting across the whole token, and avoid editing them character-by-character afterwards.
- **If you cannot control the template** — read the document text into a string, replace with `myString.Replace(...)` / regex in an `Assign`, and write it back, which operates on the flattened text rather than run boundaries.

> This is a silent failure — the activity throws nothing. Trace the **output document content** (or add a post-replace `Word`-read + assertion) rather than relying on the activity not faulting.
