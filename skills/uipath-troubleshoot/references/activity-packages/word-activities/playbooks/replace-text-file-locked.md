---
confidence: medium
---

# Replace Text in Document — File Lock / "File is Read-Only" on Save

## Context

What this looks like:
- Activity `Replace Text in Document` / `Replace Text` faults when the surrounding scope tries to persist the edit
- Error message contains one of:
  - `The process cannot access the file because it is being used by another process`
  - `The file is read-only` / `Cannot save the document because it is read-only`

What can cause it:
- The `Word Application Scope` / `Use Word File` container tries to **save changes while the same file is being accessed elsewhere** — most often when `Auto Save` is on and the document is touched by another activity in the same loop iteration, or a second job/sync client holds the handle
- A `Save As` / rename to the **same path** while the file is still open inside an active loop

What to look for:
- Whether `Auto Save` is enabled on the `Use Word File` scope.
- Whether the scope (or a save/rename) runs inside a loop over the same file path.

## Investigation

1. Read the scope and the `Replace Text in Document` node from the `.xaml`. Capture the file path, whether `Auto Save` is enabled, and whether the scope or any save/rename sits inside a `For Each` / `While` over the same path.
2. Check the robot host for a second process holding the file (orphaned WINWORD.EXE, a concurrent job, a sync/AV client) and whether the file's read-only attribute is set.

## Resolution

- **If Auto Save races another access in a loop** — uncheck **Auto Save** in the `Use Word File` properties so the document is written once on scope exit rather than continuously, removing the save-vs-access race.
- **If a `Save As` / rename reuses the same path inside a loop** — write to a distinct output path per iteration (build it with `Path.Combine`) instead of overwriting the open file; avoid `Save As` to the exact path the scope still holds open.
- **If another process holds the file** — clear the lock before the scope (`Kill Process` for `WINWORD`, stop the concurrent job, exclude the folder from sync/AV); see [word-scope-file-corrupted.md](./word-scope-file-corrupted.md) for the full lock-clearing steps.
- **If the file's read-only attribute is set** — clear it (`attrib -R <path>` or `Set-ItemProperty <path> -Name IsReadOnly -Value $false`) or copy to a writable working location before editing.
