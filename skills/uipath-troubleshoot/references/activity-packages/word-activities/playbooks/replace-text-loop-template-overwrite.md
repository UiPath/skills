---
confidence: medium
---

# Replace Text in Document — Placeholder Replaced Once, Then Missing in Loop Iterations

## Context

What this looks like:
- Activity `Replace Text in Document` / `Replace Text` works on the **first** iteration of a loop and then does nothing (or the output is wrong) on every subsequent iteration
- No exception is necessarily thrown — later rows simply come out with the placeholder gone / the first row's value baked in

What can cause it:
- The workflow opens and edits the **template file in place** inside the loop. Once the placeholder (e.g. `[Name]`) is replaced on iteration 1, the literal placeholder **no longer exists in the file**, so iteration 2 finds nothing to replace. Every later row inherits the mutated document instead of a clean template.

What to look for:
- Whether the `Use Word File` / `Word Application Scope` inside the loop points at the **same template path** every iteration.
- Whether a fresh copy of the template is made per iteration (it usually is not — that's the bug).

## Investigation

1. Read the loop body from the `.xaml`. Confirm the Word scope's file path is the template itself (same path each iteration), not a per-iteration copy.
2. Confirm the symptom: iteration 1 succeeds, later iterations leave the placeholder missing / stale. The template on disk is mutated after the first run.

## Resolution

- **Copy the template per iteration** — at the **start of each loop iteration**, use a `Copy File` activity to create a fresh temporary copy of the template (a unique per-row output path, e.g. built with `Path.Combine`), and point the `Use Word File` / `Word Application Scope` at **that temporary file** instead of the template. Each row then starts from a clean, unmodified template.
- **Never edit the source template in place** — treat the template as read-only; generate a new output document per row.
- **Source:** the placeholder is consumed by the first replacement; the fix is a fresh template copy per iteration.

> Distinct from [replace-text-silent-no-substitution.md](./replace-text-silent-no-substitution.md) (placeholder split across Word XML runs — fails on *every* row, including the first) and [replace-text-file-locked.md](./replace-text-file-locked.md) (`IOException` from Auto Save racing a shared file in a loop). Here the first row succeeds and the cause is template mutation, not a run-split token or a file lock.
