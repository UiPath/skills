---
confidence: medium
---

# Append / Write CSV — File Locked or Invalid / Cloud Path

## Context

What this looks like:
- A CSV activity faults with `The process cannot access the file because it is being used by another process`, or
- `The filename, directory name, or volume label syntax is incorrect`.

What can cause it:
- **File locked (in use).** The target `.csv` is **open in Microsoft Excel**, held by another user/session, or still locked by a previous (or concurrent) job iteration. CSV write/append needs exclusive write access; an open Excel handle blocks it.
- **Invalid / cloud path.** The `Path` is a raw cloud URL (`https://...` SharePoint / OneDrive) or a malformed path. CSV activities operate on **local files only** — a web URL is not a valid local path, producing the "syntax is incorrect" error.

What to look for:
- The exact message: "being used by another process" → a **lock**; "syntax is incorrect" → an **invalid/cloud path**.
- The `Path` value: is it a local path, or an `https://` SharePoint/OneDrive link / mapped-but-unavailable drive?
- Whether Excel (or another job touching the same file) runs on the host at the same time.

## Investigation

1. Read the error and the CSV activity's `Path` from job evidence / the `.xaml`.
2. **If "being used by another process":** identify what holds the handle — an Excel instance with the file open, a prior `Use Excel File` / CSV step that did not release it, or a concurrent job writing the same file.
3. **If "syntax is incorrect":** inspect `Path` for an `https://` cloud URL, a malformed/relative path, or an unavailable mapped drive.

## Resolution

- **If the file is locked by Excel:** close the workbook, or add a **Kill Process** activity targeting `EXCEL` immediately before the CSV step to clear stray local instances. Ensure earlier activities released the file (don't keep it open across the append).
- **If a concurrent job/iteration locks it:** serialize access (write to per-iteration temp files and merge, or gate the write) so two writers don't collide.
- **If `Path` is a cloud URL:** do **not** pass a raw `https://` SharePoint/OneDrive link. Use the **Microsoft 365 activities** to **download** the file to a local path, run `Append To CSV` / `Write CSV` against that local copy, then **upload** it back to the cloud.
- **If `Path` is malformed / a dead mapped drive:** correct the path to a valid local location the robot user can write to.
