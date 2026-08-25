---
confidence: medium
---

# Append Text — "Archive file cannot be size zero"

## Context

What this looks like:
- `Append Text` (`UiPath.Word.Activities.WordAppendText`) — or the surrounding scope opening the document — faults with `Archive file cannot be size zero` (or a similar OpenXML/ZIP "cannot open / not a valid package" error)
- The target `.docx`/`.doc` exists but is **0 bytes**

What can cause it:
- A `.docx` is a ZIP/OpenXML package and **must contain internal XML structures**. A **0-byte file** — typically created by *New → Text Document* then renaming the extension to `.docx`, or left behind by a failed/truncated download or interrupted write — is not a valid Word archive, so the open/append fails.

What to look for:
- The size of the target file on disk (0 bytes is the tell).
- Whether the file was hand-created by renaming a `.txt`, or produced by an upstream download/write that may have failed.

## Investigation

1. Read the `Append Text` / scope node and resolve the target document path.
2. Check the file size at that path on the execution host (ask the user / someone with host access if off-host). A 0-byte file is the cause.
3. Determine how the file got there — a manually renamed empty file vs a truncated upstream output — so the fix addresses the source.

## Resolution

- **If the file is a hand-made empty placeholder** — delete the 0-byte file and let UiPath generate a valid template: check **Create if not exists** in the `Word Application Scope` properties (or use a real `.docx` saved from Word). On the next run the scope creates a structurally valid file.
- **If the 0-byte file came from a failed upstream step** (download/write produced an empty file) — fix that step so it writes a complete `.docx`, and add a guard (check file size > 0) before appending.
- **Never fabricate a `.docx` by renaming a `.txt`** — a true Word file needs the OpenXML package structure; the extension alone is not enough.

> Distinct from a *corrupt-but-non-empty* document (orphaned-lock / half-written) — see [word-scope-file-corrupted.md](./word-scope-file-corrupted.md). The `Create if not exists` option is the same one covered in [word-scope-file-path-not-found.md](./word-scope-file-path-not-found.md) for generating an absent file.
