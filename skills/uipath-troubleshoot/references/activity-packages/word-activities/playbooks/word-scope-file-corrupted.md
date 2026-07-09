---
confidence: medium
---

# Word Application Scope — "The file appears to be corrupted"

## Context

What this looks like:
- Activity `Word Application Scope` (`UiPath.Word.Activities.WordApplicationScope`) faults opening or saving the document with a message containing `The file appears to be corrupted`, `Word experienced an error trying to open the file`, or `cannot be opened because there are problems with the contents`
- The same document opens cleanly when a user double-clicks it interactively — corruption is intermittent / robot-only

What can cause it (more than one may apply):
- **Background WINWORD.EXE holds a lock** — a previous run (or a crashed scope) left an orphaned WINWORD.EXE owning the file handle, so the new run cannot read/save and Word reports the half-written file as corrupted
- **Template reused in place** — the workflow opens a template `.docx`/`.dotx`, edits it, and writes back to the same path. A concurrent/locked handle leaves the source partially overwritten and unreadable on the next open
- **Mark-of-the-Web / Protected View** — the file came from the internet or an untrusted share; Word opens it in Protected View and the Interop write fails, surfacing as a content/corruption error

What to look for:
- Multiple `WINWORD.EXE` instances in Task Manager on the robot host with no visible window.
- Whether the input path and the output path are the **same file** (in-place template overwrite).

## Investigation

1. Read the `Word Application Scope` node from the `.xaml`. Capture the input document path and the path the workflow saves to. Note whether they are identical (in-place edit of a template).
2. Check the robot machine for orphaned `WINWORD.EXE` processes before the next run (Task Manager → instances with no window).
3. Ask the user to open the failing document interactively on the robot host as the robot's Windows user. If it opens in **Protected View** (yellow banner) or prompts for recovery, that is the blocking state.
4. Confirm the file is not held open by a sync client (OneDrive/SharePoint), antivirus, or a concurrent job at failure time.

## Resolution

- **If an orphaned WINWORD.EXE holds the file** — add a `Kill Process` activity configured for `WINWORD` immediately **before** the `Word Application Scope` to clear locked sessions. As a one-time cleanup, end stray instances via Task Manager or `Stop-Process -Name WINWORD -Force`. Going forward, ensure the scope always disposes (no `Try/Catch` swallowing its exit) so it closes Word cleanly.
- **If the workflow overwrites a template in place** — change the workflow to **save as a new file** (a distinct output path), leaving the source template untouched. Build the output path with `Path.Combine` rather than reusing the input path variable.
- **If the document opens in Protected View / Mark-of-the-Web** — unblock the file (`Right-click > Properties > Unblock`) or pre-process it with `Unblock-File <path>` in PowerShell before the workflow runs; or add the folder to Word Trusted Locations (`File > Options > Trust Center > Trust Center Settings > Trusted Locations`).
- **If the source file is genuinely corrupt** — open it interactively, use `File > Open > Open and Repair`, save a clean copy, and point the workflow at the repaired file.
