---
confidence: medium
---

# Write CSV — "Access to the path is denied"

## Context

What this looks like:
- `Write CSV` faults with `Access to the path '<path>' is denied` (`System.UnauthorizedAccessException`).

What can cause it:
- **The robot's Windows user lacks write permission** to the target folder/file (common on unattended robots writing to a protected or another user's directory).
- **The output file is read-only** (read-only attribute set).
- **The file is open in Microsoft Excel** (including a hidden background instance), so the OS denies the write.

What to look for:
- Whether the target path is in a location the robot user can write to (vs `C:\Program Files`, another user's profile, a protected share).
- Whether the file has the read-only attribute.
- Whether Excel (or a prior step) holds the file open.

## Investigation

1. Read the error and the target path from job evidence; confirm it is `Access to the path '<path>' is denied` (`UnauthorizedAccessException`) at `Write CSV` — a permissions/attribute/open-handle problem (distinct from `being used by another process`, which is the file-lock playbook, and from a missing directory).
2. Read the `Write CSV` `FilePath` from the `.xaml`; assess whether the robot user would have write access there.
3. Determine (ask the user / host check if off-host) whether the file is read-only or open in Excel on the host.

## Resolution

- **If the file is open in Excel:** ensure it is closed before the run; add a **Kill Process** activity targeting `EXCEL` right before the `Write CSV` to force-close stray/background instances.
- **If the robot user lacks permission:** grant the robot's Windows user **Read/Write** on the target folder, or write to a location the robot can write to (e.g. the project/output folder rather than a protected system path).
- **If the file is read-only:** clear the read-only attribute on the target file before writing.
- **Bulletproof alternative:** if the activity keeps failing on a stubborn environment, build the CSV text yourself — **Output Data Table** (DataTable → string) then **Write Text File** to a writable `.csv` path — which uses plain file I/O.

> **Related:** if the error is `The process cannot access the file because it is being used by another process` (an active lock) or an invalid/cloud path rather than a permissions denial, see [csv-file-locked-or-invalid-path.md](./csv-file-locked-or-invalid-path.md).
